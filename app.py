import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timezone

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="GFS - Kerem Palancı", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- CSS ---
st.markdown("""
    <style>
        .stApp { background-color: #000000; color: #e0e0e0; }
        .block-container { padding-top: 0.5rem; padding-bottom: 2rem; padding-left: 0.5rem; padding-right: 0.5rem; }
        h1 { font-size: 1.6rem !important; color: #4FA5D6; text-align: center; margin-bottom: 10px; }
        .stSelectbox, .stMultiSelect { margin-bottom: 0px; }
        div.stButton > button { width: 100%; border-radius: 8px; font-weight: bold; background-color: #222; color: cyan; border: 1px solid cyan; }
        div.stButton > button:hover { background-color: cyan; color: black; }
        
        /* SHARPpy Tarzı Tablo */
        .sharppy-table {
            width: 100%; background-color: #000000; border: 1px solid #444;
            color: cyan; font-family: 'Courier New', monospace; font-size: 0.85rem;
            border-collapse: collapse; margin-top: 10px;
        }
        .sharppy-table td, .sharppy-table th { border: 1px solid #333; padding: 6px; text-align: center; }
        .header-cell { color: white; background-color: #222; font-weight: bold; }
        .val-cell { color: #00ff00; font-weight: bold; font-size: 1rem;}
        .risk-high { color: #ff00ff !important; font-weight: bold;}
        .risk-med { color: yellow !important; font-weight: bold;}
        .risk-low { color: #00ff00 !important; }
    </style>
""", unsafe_allow_html=True)

st.title("by Kerem Palancı")

# --- ŞEHİRLER ---
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
    if 3 <= hour < 9: return "00Z"
    elif 9 <= hour < 15: return "06Z"
    elif 15 <= hour < 21: return "12Z"
    else: return "18Z"

with st.expander("📍 Konum Ayarları", expanded=True):
    col_a, col_b = st.columns([3, 1])
    with col_a:
        secilen_il = st.selectbox("Şehir Seçiniz:", list(TR_ILLER.keys()), index=0)
        lat_il, lon_il = TR_ILLER[secilen_il]
    with col_b:
        st.write("")
        st.write("")
        btn_calistir = st.button("ANALİZİ BAŞLAT", type="primary")

st.caption(f"Model: **GFS** | Run: **{get_run_info()}**")

# --- SEKMELER ---
tab_diyagram, tab_expert = st.tabs(["📉 Senaryo Diyagramı", "🧬 Expert & Hodograf (Süper Hücre)"])

# ==========================================
# FONKSİYONLAR
# ==========================================

@st.cache_data(ttl=3600)
def get_ensemble_data(lat, lon, variables):
    # (Diyagram Verisi Çekme Fonksiyonu - Aynı Kaldı)
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

@st.cache_data(ttl=3600)
def get_expert_data(lat, lon):
    # (Expert Verisi Çekme - Geopotential Height Eklendi)
    levels = [1000, 950, 925, 900, 850, 800, 700, 600, 500, 400, 300, 250, 200, 150]
    vars = ["temperature_2m", "dewpoint_2m", "cape", "lifted_index"]
    for l in levels: vars.extend([f"temperature_{l}hPa", f"dewpoint_{l}hPa", f"windspeed_{l}hPa", f"winddirection_{l}hPa", f"geopotential_height_{l}hPa"])
    url = "https://api.open-meteo.com/v1/gfs"
    params = {"latitude": lat, "longitude": lon, "hourly": vars, "timezone": "auto", "forecast_days": 3}
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json(), levels
    except: return None, None

def calculate_advanced_indices(hourly_data, idx, levels):
    # --- VERİ HAZIRLIĞI ---
    try:
        # CAPE & LI
        cape = hourly_data.get("cape", [0]*len(hourly_data["time"]))[idx]
        cin = 0 # GFS API'de free sürümde CIN her zaman gelmiyor, varsayılan 0
        li = hourly_data.get("lifted_index", [0]*len(hourly_data["time"]))[idx]
        
        # Rüzgar Bileşenlerini (u, v) ve Yükseklikleri (z) Al
        u_layers = []
        v_layers = []
        z_layers = []
        
        # Yer Seviyesi (Yaklaşık 10m)
        u_sfc = -hourly_data["windspeed_10m"][idx] * 0.27778 * np.sin(np.deg2rad(hourly_data["winddirection_10m"][idx])) # m/s
        v_sfc = -hourly_data["windspeed_10m"][idx] * 0.27778 * np.cos(np.deg2rad(hourly_data["winddirection_10m"][idx])) # m/s
        z_sfc = 10 # metre
        
        u_layers.append(u_sfc)
        v_layers.append(v_sfc)
        z_layers.append(z_sfc)

        for l in levels:
            try:
                w_spd = hourly[f"windspeed_{l}hPa"][idx] * 0.27778 # km/h -> m/s
                w_dir = hourly[f"winddirection_{l}hPa"][idx]
                z_hgt = hourly[f"geopotential_height_{l}hPa"][idx]
                
                u = -w_spd * np.sin(np.deg2rad(w_dir))
                v = -w_spd * np.cos(np.deg2rad(w_dir))
                
                u_layers.append(u)
                v_layers.append(v)
                z_layers.append(z_hgt)
            except: pass
        
        # NumPy dizisine çevir (İşlem kolaylığı için)
        u_arr = np.array(u_layers)
        v_arr = np.array(v_layers)
        z_arr = np.array(z_layers)
        
        # --- SHEAR (MAKASLAMA) HESABI (0-6km) ---
        # 0-6km (6000m) katmanını bul
        idx_6km = (np.abs(z_arr - 6000)).argmin()
        u_6km, v_6km = u_arr[idx_6km], v_arr[idx_6km]
        
        # Shear Vektörü Farkı
        shear_06 = np.sqrt((u_6km - u_sfc)**2 + (v_6km - v_sfc)**2)
        # m/s -> knots çevir (tablo için)
        shear_kt = shear_06 * 1.94384

        # --- SRH (HELISITE) HESABI (0-3km) ---
        # Basit "Storm Relative" hesabı için Fırtına Hareketini (Bunkers) tahmin etmemiz lazım.
        # Basitlik adına ID Metodu: Mean Wind (0-6km) - 7.5 m/s (Sağa sapma)
        u_mean_06 = np.mean(u_arr[:idx_6km+1])
        v_mean_06 = np.mean(v_arr[:idx_6km+1])
        
        # Fırtına Hareketi (Tahmini)
        cx = u_mean_06 # Basit tutalım
        cy = v_mean_06
        
        # SRH İntegrali (0-3km)
        srh_03 = 0
        idx_3km = (np.abs(z_arr - 3000)).argmin()
        
        for i in range(idx_3km):
            # SRH Formülü: (u[i+1]*v[i] - u[i]*v[i+1]) ... (Hodograf alanı)
            # Storm Motion çıkarılarak yapılır
            u_sr_1 = u_arr[i] - cx
            v_sr_1 = v_arr[i] - cy
            u_sr_2 = u_arr[i+1] - cx
            v_sr_2 = v_arr[i+1] - cy
            srh_03 += (u_sr_1 * v_sr_2) - (u_sr_2 * v_sr_1)
            
        srh_val = abs(int(srh_03))

        # --- SCP (SUPERCELL COMPOSITE PARAMETER) ---
        # Formül: (CAPE/1000) * (Shear06 / 20m/s) * (SRH03 / 50)
        # Shear m/s cinsinden olmalı
        scp_val = (cape / 1000) * (shear_06 / 20) * (srh_val / 50)
        
        # --- STP (SIGNIFICANT TORNADO PARAMETER) ---
        # Formül: (CAPE/1500) * ((2000-LCL)/1000) * (SRH01/150) * (Shear06/20)
        # Basitleştirilmiş: (CAPE/1500) * (SRH03/150) * (Shear06/20) (LCL verisi yoksa ihmal edilir)
        # LCL yaklaşık hesap:
        T_sfc_C = hourly_data["temperature_2m"][idx]
        Td_sfc_C = hourly_data["dewpoint_2m"][idx]
        lcl_h = 125 * (T_sfc_C - Td_sfc_C)
        
        lcl_term = (2000 - lcl_h) / 1000
        if lcl_term < 0: lcl_term = 0
        if lcl_term > 1: lcl_term = 1
        
        stp_val = (cape / 1500) * lcl_term * (srh_val / 150) * (shear_06 / 20)

        return {
            "CAPE": int(cape), "CIN": int(cin), "LI": round(li, 1), 
            "Shear": int(shear_kt), "SRH": srh_val, 
            "SCP": round(scp_val, 1), "STP": round(stp_val, 1),
            "LCL": int(lcl_h)
        }

    except:
        return {"CAPE":0, "CIN":0, "LI":0, "Shear":0, "SRH":0, "SCP":0, "STP":0, "LCL":0}


# ==========================================
# 1. SEKME: DİYAGRAM
# ==========================================
with tab_diyagram:
    col_d1, col_d2 = st.columns([3, 1])
    with col_d1:
        secilen_veriler = st.multiselect(
            "Veriler:",
            ["Sıcaklık (850hPa)", "Sıcaklık (2m)", "Kar Yağışı (cm)", "Yağış (mm)", "Rüzgar (10m)", "Rüzgar Hamlesi", "Bağıl Nem (2m)", "Bulutluluk (%)", "Donma Seviyesi (m)", "CAPE", "Basınç"],
            default=["Sıcaklık (850hPa)", "Kar Yağışı (cm)"]
        )
    with col_d2:
        vurgulu_senaryolar = st.multiselect("Vurgula:", options=range(0, 31))

    if st.button("DİYAGRAMI ÇİZ", type="primary"):
        if not secilen_veriler: st.error("Veri seçin.")
        else:
            with st.spinner('Diyagram hazırlanıyor...'):
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
                                c, w, o, leg, h = '#333', 0.5, 0.4, False, 'skip'
                                if mem_num in vurgulu_senaryolar: c, w, o, leg, h = '#FF1493', 2.0, 1.0, True, 'all'
                                fig.add_trace(go.Scatter(x=time, y=hourly[member], mode='lines', line=dict(color=c, width=w), opacity=o, name=f"S-{mem_num}", showlegend=leg, hoverinfo=h))
                            h_txt = [f"📅 <b>{t.strftime('%d.%m %H:%M')}</b><br>🔺 Max: {mx:.1f} (S-{mxn})<br>⚪ Ort: {mn:.1f}<br>🔻 Min: {mi:.1f} (S-{minn})" for t, mx, mxn, mn, mi, minn in zip(time, max_val, max_mem, mean_val, min_val, min_mem)]
                            fig.add_trace(go.Scatter(x=time, y=mean_val, mode='lines', line=dict(width=0), hovertemplate="%{text}<extra></extra>", text=h_txt, showlegend=False))
                            c_map = {"850hPa": "red", "2m": "orange", "Kar": "white", "Yağış": "cyan", "Rüzgar": "green", "Hamlesi": "lime", "Bulut": "gray", "Nem": "teal", "Basınç": "magenta"}
                            main_c = next((v for k, v in c_map.items() if k in secim), "cyan")
                            fig.add_trace(go.Scatter(x=time, y=mean_val, mode='lines', line=dict(color=main_c, width=3.0), name="ORTALAMA", showlegend=False, hoverinfo='skip'))
                            if "850hPa" in secim: fig.add_hline(y=0, line_dash="dash", line_color="orange", opacity=0.5)
                            fig.update_layout(title=dict(text=f"{secim}", font=dict(size=14, color='white')), template="plotly_dark", height=500, margin=dict(l=2, r=2, t=30, b=5), hovermode="x unified", plot_bgcolor='black', paper_bgcolor='black')
                            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# ==========================================
# 2. SEKME: EXPERT (RENKLİ HODOGRAF & YENİ İNDEKSLER)
# ==========================================
with tab_expert:
    if st.button("EXPERT ANALİZİ BAŞLAT", type="primary"):
        with st.spinner("Gelişmiş atmosfer analizi yapılıyor..."):
            d, l = get_expert_data(lat_il, lon_il)
            if d: st.session_state['ex_data'], st.session_state['ex_lvls'] = d, l
            else: st.error("Veri yok.")

    if 'ex_data' in st.session_state:
        data = st.session_state['ex_data']
        levels = st.session_state['ex_lvls']
        hourly = data['hourly']
        time = pd.to_datetime(hourly['time'])

        col_t1, col_t2 = st.columns([1, 4])
        with col_t1:
            sel_time = st.selectbox("Saat:", [t.strftime('%d %b %H:%M') for t in time], index=0)
            idx = [t.strftime('%d %b %H:%M') for t in time].index(sel_time)

        # İNDEKS HESAPLA
        stats = calculate_advanced_indices(hourly, idx, levels)

        # GRAFİK VERİSİ HAZIRLA
        temps, dews, press, u, v, spd, heights_z = [], [], [], [], [], [], []
        
        # Hodograf Renklendirme Grupları
        u_03, v_03 = [], [] # 0-3km (Kırmızı)
        u_36, v_36 = [], [] # 3-6km (Yeşil)
        u_69, v_69 = [], [] # 6-9km (Sarı)
        u_9p, v_9p = [], [] # 9+km (Mavi)

        for l in levels:
            try:
                temps.append(hourly[f"temperature_{l}hPa"][idx])
                dews.append(hourly[f"dewpoint_{l}hPa"][idx])
                press.append(l)
                
                h_z = hourly[f"geopotential_height_{l}hPa"][idx]
                heights_z.append(h_z)
                
                wd = hourly[f"winddirection_{l}hPa"][idx]
                ws = hourly[f"windspeed_{l}hPa"][idx] * 0.539957 # knots
                spd.append(ws)
                rad = np.deg2rad(wd)
                
                # U, V bileşenleri (Knots cinsinden Hodograf için)
                uu = -ws * np.sin(rad)
                vv = -ws * np.cos(rad)
                u.append(uu)
                v.append(vv)

                # Katmanlara ayır
                if h_z < 3000:
                    u_03.append(uu); v_03.append(vv)
                elif h_z < 6000:
                    u_36.append(uu); v_36.append(vv)
                elif h_z < 9000:
                    u_69.append(uu); v_69.append(vv)
                else:
                    u_9p.append(uu); v_9p.append(vv)

            except: pass
            
        # Bağlantı kopmaması için geçiş noktalarını ekle (birleştirme)
        if u_03 and u_36: u_36.insert(0, u_03[-1]); v_36.insert(0, v_03[-1])
        if u_36 and u_69: u_69.insert(0, u_36[-1]); v_69.insert(0, v_36[-1])
        if u_69 and u_9p: u_9p.insert(0, u_69[-1]); v_9p.insert(0, v_69[-1])

        col_skew, col_hodo = st.columns([2, 1])

        # SKEW-T
        with col_skew:
            fig = make_subplots(rows=1, cols=2, shared_yaxes=True, column_widths=[0.85, 0.15], horizontal_spacing=0.01)
            fig.add_trace(go.Scatter(x=temps, y=press, mode='lines', name='Temp', line=dict(color='#FF0000', width=3)), row=1, col=1)
            fig.add_trace(go.Scatter(x=dews, y=press, mode='lines', name='Dewpoint', line=dict(color='#00FF00', width=3)), row=1, col=1)
            # 0 Derece
            fig.add_vline(x=0, line_color="cyan", line_width=1, opacity=0.5, row=1, col=1)
            # Rüzgar Bar
            fig.add_trace(go.Bar(x=spd, y=press, orientation='h', marker=dict(color='cyan'), showlegend=False), row=1, col=2)
            
            fig.update_layout(
                plot_bgcolor='black', paper_bgcolor='black', height=600,
                xaxis=dict(title="C", range=[-40, 40], dtick=10, gridcolor='#333', zeroline=False, tickfont=dict(color='white')),
                yaxis=dict(title="hPa", range=[1050, 100], gridcolor='#444', tickfont=dict(color='white')),
                xaxis2=dict(title="Kts", gridcolor='#333', range=[0, 100], tickfont=dict(color='white')),
                showlegend=False, margin=dict(l=40, r=10, t=10, b=10)
            )
            st.plotly_chart(fig, use_container_width=True)

        # HODOGRAF (RENKLİ & SINIRLI)
        with col_hodo:
            fig_h = go.Figure()
            # Izgaralar
            for r in [10, 20, 30, 40, 50]: 
                fig_h.add_shape(type="circle", xref="x", yref="y", x0=-r, y0=-r, x1=r, y1=r, line_color="#333", opacity=0.8)
            fig_h.add_vline(x=0, line_color="#444"); fig_h.add_hline(y=0, line_color="#444")

            # Renkli Çizgiler
            fig_h.add_trace(go.Scatter(x=u_03, y=v_03, mode='lines', line=dict(color='red', width=3), name='0-3km'))
            fig_h.add_trace(go.Scatter(x=u_36, y=v_36, mode='lines', line=dict(color='green', width=3), name='3-6km'))
            fig_h.add_trace(go.Scatter(x=u_69, y=v_69, mode='lines', line=dict(color='yellow', width=3), name='6-9km'))
            fig_h.add_trace(go.Scatter(x=u_9p, y=v_9p, mode='lines', line=dict(color='cyan', width=3), name='9km+'))

            # SINIRLAMA (-50 / +50)
            fig_h.update_layout(
                title=dict(text="HODOGRAPH (kts)", font=dict(color='white', family='Courier New')),
                plot_bgcolor='black', paper_bgcolor='black', height=400, width=400,
                xaxis=dict(range=[-50, 50], showgrid=False, zeroline=False, tickfont=dict(color='white')), # BURADA SINIRLADIK
                yaxis=dict(range=[-50, 50], showgrid=False, zeroline=False, tickfont=dict(color='white'), scaleanchor="x", scaleratio=1),
                margin=dict(l=10, r=10, t=40, b=10), showlegend=True,
                legend=dict(x=0, y=1, bgcolor='rgba(0,0,0,0.5)', font=dict(size=8, color='white'))
            )
            st.plotly_chart(fig_h, use_container_width=True)

        # YENİ EKLENEN ENDEKSLER TABLOSU
        cape_color = "#ff00ff" if stats['CAPE'] > 2000 else ("red" if stats['CAPE'] > 1000 else "cyan")
        stp_color = "#ff00ff" if stats['STP'] > 1 else ("yellow" if stats['STP'] > 0.5 else "cyan")
        
        st.markdown(f"""
        <table class="sharppy-table">
            <tr>
                <td class="header-cell">CAPE</td>
                <td class="header-cell">CIN</td>
                <td class="header-cell">LCL</td>
                <td class="header-cell">LI</td>
                <td class="header-cell">Shear(0-6)</td>
                <td class="header-cell">SRH(0-3)</td>
                <td class="header-cell">SCP</td>
                <td class="header-cell">STP</td>
            </tr>
            <tr>
                <td class="val-cell" style="color:{cape_color}">{stats['CAPE']}</td>
                <td class="val-cell">{stats['CIN']}</td>
                <td class="val-cell">{stats['LCL']}m</td>
                <td class="val-cell">{stats['LI']}</td>
                <td class="val-cell" style="color:{'magenta' if stats['Shear']>40 else 'cyan'}">{stats['Shear']} kt</td>
                <td class="val-cell" style="color:{'red' if stats['SRH']>150 else 'cyan'}">{stats['SRH']}</td>
                <td class="val-cell">{stats['SCP']}</td>
                <td class="val-cell" style="color:{stp_color}">{stats['STP']}</td>
            </tr>
        </table>
        """, unsafe_allow_html=True)
