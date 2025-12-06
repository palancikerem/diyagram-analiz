import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timezone

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="MeteoAnaliz Pro", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- CSS (MOBİL UYUM VE GÖRSELLİK) ---
st.markdown("""
    <style>
        .block-container { padding-top: 0.5rem; padding-bottom: 1rem; padding-left: 0.2rem; padding-right: 0.2rem; }
        h1 { font-size: 1.4rem !important; color: #4FA5D6; text-align: center; margin-bottom: 5px; }
        .stSelectbox { margin-bottom: 0px; }
        div.stButton > button { width: 100%; border-radius: 8px; font-weight: bold; }
        /* Tab Başlıklarını Güzelleştir */
        button[data-baseweb="tab"] { font-size: 1rem; font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

st.title("🌪️ MeteoAnaliz Pro")

# --- ŞEHİR LİSTESİ ---
TR_ILLER = {
    "İstanbul": [41.00, 28.97], "Ankara": [39.93, 32.85], "İzmir": [38.42, 27.14],
    "Adana": [37.00, 35.32], "Adıyaman": [37.76, 38.28], "Afyonkarahisar": [38.75, 30.54],
    "Ağrı": [39.72, 43.05], "Aksaray": [38.37, 34.03], "Amasya": [40.65, 35.83],
    "Antalya": [36.89, 30.71], "Ardahan": [41.11, 42.70], "Artvin": [41.18, 41.82],
    "Aydın": [37.84, 27.84], "Balıkesir": [39.65, 27.88], "Bartın": [41.63, 32.34],
    "Batman": [37.88, 41.13], "Bayburt": [40.26, 40.22], "Bilecik": [40.14, 29.98],
    "Bingöl": [38.88, 40.49], "Bitlis": [38.40, 42.10], "Bolu": [40.73, 31.61],
    "Burdur": [37.72, 30.29], "Bursa": [40.18, 29.06], "Çanakkale": [40.15, 26.41],
    "Çankırı": [40.60, 33.61], "Çorum": [40.55, 34.95], "Denizli": [37.77, 29.09],
    "Diyarbakır": [37.91, 40.24], "Düzce": [40.84, 31.16], "Edirne": [41.68, 26.56],
    "Elazığ": [38.68, 39.22], "Erzincan": [39.75, 39.50], "Erzurum": [39.90, 41.27],
    "Eskişehir": [39.78, 30.52], "Gaziantep": [37.06, 37.38], "Giresun": [40.91, 38.39],
    "Gümüşhane": [40.46, 39.48], "Hakkari": [37.58, 43.74], "Hatay": [36.40, 36.34],
    "Iğdır": [39.92, 44.04], "Isparta": [37.76, 30.56], "Kahramanmaraş": [37.58, 36.93],
    "Karabük": [41.20, 32.62], "Karaman": [37.18, 33.22], "Kars": [40.60, 43.10],
    "Kastamonu": [41.38, 33.78], "Kayseri": [38.73, 35.49], "Kırıkkale": [39.85, 33.51],
    "Kırklareli": [41.73, 27.22], "Kırşehir": [39.15, 34.17], "Kilis": [36.71, 37.11],
    "Kocaeli": [40.85, 29.88], "Konya": [37.87, 32.48], "Kütahya": [39.42, 29.98],
    "Malatya": [38.35, 38.31], "Manisa": [38.61, 27.43], "Mardin": [37.32, 40.74],
    "Mersin": [36.80, 34.64], "Muğla": [37.21, 28.36], "Muş": [38.74, 41.49],
    "Nevşehir": [38.62, 34.71], "Niğde": [37.97, 34.68], "Ordu": [40.98, 37.88],
    "Osmaniye": [37.07, 36.25], "Rize": [41.02, 40.52], "Sakarya": [40.77, 30.40],
    "Samsun": [41.29, 36.33], "Siirt": [37.93, 41.94], "Sinop": [42.03, 35.15],
    "Sivas": [39.75, 37.02], "Şanlıurfa": [37.16, 38.79], "Şırnak": [37.52, 42.46],
    "Tekirdağ": [40.98, 27.51], "Tokat": [40.31, 36.55], "Trabzon": [41.00, 39.72],
    "Tunceli": [39.11, 39.55], "Uşak": [38.68, 29.41], "Van": [38.50, 43.38],
    "Yalova": [40.65, 29.27], "Yozgat": [39.82, 34.81], "Zonguldak": [41.45, 31.79]
}

def get_run_info():
    now_utc = datetime.now(timezone.utc)
    hour = now_utc.hour
    if 3 <= hour < 9: return "00Z (Gece)"
    elif 9 <= hour < 15: return "06Z (Sabah)"
    elif 15 <= hour < 21: return "12Z (Öğle)"
    else: return "18Z (Akşam)"

# --- ARAYÜZ ---
with st.expander("📍 Konum Ayarları", expanded=True):
    secilen_il = st.selectbox("Şehir Seçiniz:", list(TR_ILLER.keys()), index=0)
    lat_il, lon_il = TR_ILLER[secilen_il]
    st.caption(f"Model: **GFS (Amerikan)** | Güncelleme: **{get_run_info()}**")

# --- SEKMELER ---
tab_diyagram, tab_sounding = st.tabs(["📉 Senaryo Diyagramı", "🧬 Dikey Profil (Sounding)"])

# ==========================================
# 1. SEKME: GFS SENARYO DİYAGRAMI
# ==========================================
with tab_diyagram:
    st.markdown("#### GFS Topluluk (Ensemble) Diyagramı")
    
    col_d1, col_d2 = st.columns([3, 1])
    with col_d1:
        secilen_veriler = st.multiselect(
            "Veriler:",
            ["Sıcaklık (850hPa)", "Sıcaklık (2m)", "Kar Yağışı (cm)", "Yağış (mm)", 
             "Rüzgar (10m)", "Rüzgar Hamlesi", "Bağıl Nem (2m)", "Bulutluluk (%)", 
             "Donma Seviyesi (m)", "CAPE", "Basınç"],
            default=["Sıcaklık (850hPa)", "Kar Yağışı (cm)"]
        )
    with col_d2:
        vurgulu_senaryolar = st.multiselect("Vurgula (0=Ana):", options=range(0, 31))

    btn_diyagram = st.button("Diyagramı Oluştur", type="primary")

    # --- Ensemble Veri Çekme ---
    @st.cache_data(ttl=3600)
    def get_ensemble_data(lat, lon, variables):
        var_map = {
            "Sıcaklık (850hPa)": "temperature_850hPa", "Sıcaklık (2m)": "temperature_2m",
            "Kar Yağışı (cm)": "snowfall", "Yağış (mm)": "precipitation",
            "Rüzgar (10m)": "windspeed_10m", "Rüzgar Hamlesi": "windgusts_10m",
            "Bağıl Nem (2m)": "relativehumidity_2m", "Bulutluluk (%)": "cloudcover",
            "Donma Seviyesi (m)": "freezinglevel_height", "CAPE": "cape", "Basınç": "pressure_msl"
        }
        api_vars = [var_map[v] for v in variables]
        url = "https://ensemble-api.open-meteo.com/v1/ensemble"
        params = {"latitude": lat, "longitude": lon, "hourly": api_vars, "models": "gfs_seamless", "timezone": "auto"}
        try:
            r = requests.get(url, params=params, timeout=15)
            r.raise_for_status()
            return r.json(), var_map
        except: return None, None

    if btn_diyagram:
        if not secilen_veriler: st.error("Lütfen veri seçin.")
        else:
            with st.spinner('Senaryolar indiriliyor...'):
                data, mapping = get_ensemble_data(lat_il, lon_il, secilen_veriler)
                if data:
                    hourly = data['hourly']
                    time = pd.to_datetime(hourly['time'])
                    
                    for secim in secilen_veriler:
                        api_kod = mapping[secim]
                        fig = go.Figure()
                        cols = [k for k in hourly.keys() if k.startswith(api_kod) and 'member' in k]
                        
                        if cols:
                            df_m = pd.DataFrame(hourly)[cols]
                            mean_val = df_m.mean(axis=1)
                            max_val = df_m.max(axis=1)
                            min_val = df_m.min(axis=1)
                            max_mem = df_m.idxmax(axis=1).apply(lambda x: x.split('member')[1] if 'member' in x else '?')
                            min_mem = df_m.idxmin(axis=1).apply(lambda x: x.split('member')[1] if 'member' in x else '?')

                            for member in cols:
                                try: mem_num = int(member.split('member')[1])
                                except: mem_num = -1
                                c, w, o, leg, h = 'lightgrey', 0.5, 0.4, False, 'skip'
                                if mem_num in vurgulu_senaryolar:
                                    c, w, o, leg, h = '#FF1493', 2.0, 1.0, True, 'all'
                                fig.add_trace(go.Scatter(x=time, y=hourly[member], mode='lines', line=dict(color=c, width=w), opacity=o, name=f"S-{mem_num}", showlegend=leg, hoverinfo=h))

                            h_txt = [f"📅 <b>{t.strftime('%d.%m %H:%M')}</b><br>🔺 Max: {mx:.1f} (S-{mxn})<br>⚪ Ort: {mn:.1f}<br>🔻 Min: {mi:.1f} (S-{minn})" for t, mx, mxn, mn, mi, minn in zip(time, max_val, max_mem, mean_val, min_val, min_mem)]
                            fig.add_trace(go.Scatter(x=time, y=mean_val, mode='lines', line=dict(width=0), hovertemplate="%{text}<extra></extra>", text=h_txt, showlegend=False))
                            
                            c_map = {"850hPa": "red", "2m": "orange", "Kar": "white", "Yağış": "cyan", "Rüzgar": "green", "Hamlesi": "lime", "Bulut": "gray", "Nem": "teal", "Basınç": "magenta"}
                            main_c = next((v for k, v in c_map.items() if k in secim), "cyan")
                            fig.add_trace(go.Scatter(x=time, y=mean_val, mode='lines', line=dict(color=main_c, width=3.0), name="ORTALAMA", showlegend=False, hoverinfo='skip'))

                            if "850hPa" in secim: fig.add_hline(y=0, line_dash="dash", line_color="orange", opacity=0.5)

                            fig.update_layout(title=dict(text=f"{secim}", font=dict(size=14)), template="plotly_dark", height=500, margin=dict(l=2, r=2, t=30, b=5), hovermode="x unified", legend=dict(orientation="h", y=1, x=1))
                            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# ==========================================
# 2. SEKME: DIKEY PROFIL (SOUNDING)
# ==========================================
with tab_sounding:
    st.markdown("#### Atmosferik Dikey Profil (GFS Ana Çıktı)")
    st.info("Bu modül, GFS'in ana çıktısından (Deterministic) tüm katmanları çeker. Yağış türü (Kar/Yağmur/Donan Yağmur) analizi için kullanılır.")
    
    btn_profil = st.button("Profil Verisini İndir ve Analiz Et")

    @st.cache_data(ttl=3600)
    def get_sounding_data(lat, lon):
        levels = [1000, 950, 925, 900, 850, 800, 700, 600, 500, 400, 300]
        vars = ["temperature_2m", "precipitation"]
        for lvl in levels:
            vars.append(f"temperature_{lvl}hPa")
            vars.append(f"dewpoint_{lvl}hPa")
        
        url = "https://api.open-meteo.com/v1/gfs" # GFS Deterministic
        params = {"latitude": lat, "longitude": lon, "hourly": vars, "timezone": "auto", "forecast_days": 10}
        try:
            r = requests.get(url, params=params, timeout=15)
            r.raise_for_status()
            return r.json(), levels
        except: return None, None

    if btn_profil or 'sounding_data' in st.session_state:
        if btn_profil:
            with st.spinner('Atmosfer katmanları taranıyor...'):
                s_data, s_levels = get_sounding_data(lat_il, lon_il)
                if s_data:
                    st.session_state['sounding_data'] = s_data
                    st.session_state['s_levels'] = s_levels
                else: st.error("Veri alınamadı.")

        if 'sounding_data' in st.session_state:
            s_data = st.session_state['sounding_data']
            s_levels = st.session_state['s_levels']
            hourly = s_data['hourly']
            time = pd.to_datetime(hourly['time'])
            
            # Zaman Seçici Slider
            selected_time_str = st.select_slider(
                "Analiz Saati:",
                options=[t.strftime('%d %b %H:%M') for t in time],
                value=time[0].strftime('%d %b %H:%M')
            )
            idx = [t.strftime('%d %b %H:%M') for t in time].index(selected_time_str)

            # Verileri Hazırla
            temps, dews, press = [], [], []
            for lvl in s_levels:
                try:
                    t_val = hourly[f"temperature_{lvl}hPa"][idx]
                    d_val = hourly[f"dewpoint_{lvl}hPa"][idx]
                    temps.append(t_val)
                    dews.append(d_val)
                    press.append(lvl)
                except: pass
            
            # Profil Grafiği
            fig_skew = go.Figure()
            fig_skew.add_trace(go.Scatter(x=temps, y=press, mode='lines+markers', name='Sıcaklık', line=dict(color='red', width=4)))
            fig_skew.add_trace(go.Scatter(x=dews, y=press, mode='lines+markers', name='Çiy Noktası', line=dict(color='#00FF00', width=3, dash='dot')))
            fig_skew.add_vline(x=0, line_color="cyan", line_width=2, annotation_text="0°C")

            # Basit Analiz
            sfc_t = hourly['temperature_2m'][idx]
            t850 = hourly['temperature_850hPa'][idx]
            msg, color = "Standart Atmosfer", "blue"
            
            if sfc_t < 0 and t850 > 0: msg, color = "⚠️ ENVERZİYON / DONAN YAĞMUR RİSKİ!", "orange"
            elif sfc_t < 1 and t850 < -5: msg, color = "❄️ KAR İÇİN UYGUN PROFİL", "green"
            elif sfc_t > 2 and t850 < -4: msg, color = "🌧️ SOĞUK YAĞMUR / KKY SINIRI", "white"

            st.markdown(f"### Durum: :{color}[{msg}]")

            fig_skew.update_layout(
                title=f"Dikey Profil: {selected_time_str}",
                template="plotly_dark", height=500,
                yaxis=dict(title="Basınç (hPa)", autorange="reversed"), # Basınç yukarı doğru azalır
                xaxis=dict(title="Sıcaklık (°C)", range=[-40, 25], dtick=5),
                legend=dict(orientation="h", y=1.05)
            )
            # Kar Bölgesi Boyama
            fig_skew.add_vrect(x0=-60, x1=0, fillcolor="blue", opacity=0.1, layer="below")
            st.plotly_chart(fig_skew, use_container_width=True)
