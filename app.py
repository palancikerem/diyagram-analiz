import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timezone

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="MeteoAnaliz Ultimate", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- CSS (TÜM İHTİYAÇLAR İÇİN) ---
st.markdown("""
    <style>
        /* Mobil uyum için kenar boşluklarını daralt */
        .block-container { padding-top: 0.5rem; padding-bottom: 2rem; padding-left: 0.5rem; padding-right: 0.5rem; }
        h1 { font-size: 1.6rem !important; color: #4FA5D6; text-align: center; margin-bottom: 10px; }
        .stSelectbox, .stMultiSelect { margin-bottom: 0px; }
        div.stButton > button { width: 100%; border-radius: 8px; font-weight: bold; }
        /* Tab başlıklarını belirginleştir */
        button[data-baseweb="tab"] { font-size: 1.1rem; font-weight: 600; }
        /* Metrik kutuları */
        div[data-testid="stMetricValue"] { font-size: 1.4rem; }
        .stMetric { background-color: #1E1E1E; border: 1px solid #333; padding: 5px; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

st.title("🌪️ MeteoAnaliz Ultimate")

# --- ŞEHİR LİSTESİ ---
TR_ILLER = {
    "İstanbul": [41.00, 28.97], "Ankara": [39.93, 32.85], "İzmir": [38.42, 27.14],
    "Adana": [37.00, 35.32], "Antalya": [36.89, 30.71], "Bursa": [40.18, 29.06],
    "Çanakkale": [40.15, 26.41], "Edirne": [41.68, 26.56], "Erzurum": [39.90, 41.27],
    "Eskişehir": [39.78, 30.52], "Gaziantep": [37.06, 37.38], "Kayseri": [38.73, 35.49],
    "Konya": [37.87, 32.48], "Samsun": [41.29, 36.33], "Trabzon": [41.00, 39.72],
    "Zonguldak": [41.45, 31.79], "Muğla": [37.21, 28.36], "Van": [38.50, 43.38],
    "Diyarbakır": [37.91, 40.24]
}

def get_run_info():
    now_utc = datetime.now(timezone.utc)
    hour = now_utc.hour
    if 3 <= hour < 9: return "00Z (Gece)"
    elif 9 <= hour < 15: return "06Z (Sabah)"
    elif 15 <= hour < 21: return "12Z (Öğle)"
    else: return "18Z (Akşam)"

# --- ORTAK KONUM SEÇİMİ ---
with st.expander("📍 Konum Ayarları", expanded=True):
    secilen_il = st.selectbox("Şehir Seçiniz:", list(TR_ILLER.keys()), index=0)
    lat_il, lon_il = TR_ILLER[secilen_il]
    st.caption(f"Model: **GFS (Amerikan)** | Güncelleme: **{get_run_info()}**")

# --- ANA SEKMELER ---
tab_diyagram, tab_expert = st.tabs(["📉 GFS Diyagram (Topluluk)", "🌪️ Expert Profil & Hodograf"])

# ==============================================================================
# SEKME 1: GFS ENSEMBLE DİYAGRAMI (Sadeleştirilmiş Mobil Versiyon)
# ==============================================================================
with tab_diyagram:
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
        vurgulu_senaryolar = st.multiselect("Vurgula:", options=range(0, 31))

    btn_diyagram = st.button("Diyagramı Getir", type="primary")

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
            with st.spinner('Diyagram verileri hazırlanıyor...'):
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
                            # ORTALAMA LEJANTSIZ
                            fig.add_trace(go.Scatter(x=time, y=mean_val, mode='lines', line=dict(color=main_c, width=3.0), name="ORTALAMA", showlegend=False, hoverinfo='skip'))
                            if "850hPa" in secim: fig.add_hline(y=0, line_dash="dash", line_color="orange", opacity=0.5)
                            fig.update_layout(title=dict(text=f"{secim}", font=dict(size=14)), template="plotly_dark", height=500, margin=dict(l=2, r=2, t=30, b=5), hovermode="x unified", legend=dict(orientation="h", y=1, x=1))
                            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# ==============================================================================
# SEKME 2: EXPERT PROFIL & HODOGRAF (GÜZELLEŞTİRİLMİŞ SKEWT)
# ==============================================================================
with tab_expert:
    btn_expert = st.button("Expert Analizi Başlat (GFS Ana Çıktı)", type="primary")
    
    # --- Yardımcı Fonksiyonlar ---
    def calculate_indices(hourly_data, idx):
        try:
            def gv(p, l): return hourly_data[f"{p}_{l}hPa"][idx]
            T850, Td850 = gv("temperature", 850), gv("dewpoint", 850)
            T700, Td700 = gv("temperature", 700), gv("dewpoint", 700)
            T500 = gv("temperature", 500)
            k_idx = (T850 - T500) + Td850 - (T700 - Td700)
            tt_idx = (T850 + Td850) - (2 * T500)
            T_sfc, Td_sfc = hourly_data["temperature_2m"][idx], hourly_data["dewpoint_2m"][idx]
            lcl_m = 125 * (T_sfc - Td_sfc)
            return k_idx, tt_idx, lcl_m
        except: return None, None, None

    @st.cache_data(ttl=3600)
    def get_expert_data(lat, lon):
        levels = [1000, 975, 950, 925, 900, 875, 850, 825, 800, 775, 750, 725, 700, 675, 650, 625, 600, 575, 550, 525, 500, 475, 450, 425, 400, 375, 350, 325, 300, 275, 250, 225, 200, 175, 150, 125, 100]
        vars = ["temperature_2m", "dewpoint_2m"]
        for l in levels: vars.extend([f"temperature_{l}hPa", f"dewpoint_{l}hPa", f"windspeed_{l}hPa", f"winddirection_{l}hPa"])
        url = "https://api.open-meteo.com/v1/gfs"
        params = {"latitude": lat, "longitude": lon, "hourly": vars, "timezone": "auto", "forecast_days": 3}
        try:
            r = requests.get(url, params=params, timeout=15)
            r.raise_for_status()
            return r.json(), levels
        except: return None, None

    if btn_expert or 'ex_data' in st.session_state:
        if btn_expert:
            with st.spinner("Atmosferik katmanlar taranıyor..."):
                d, l = get_expert_data(lat_il, lon_il)
                if d: st.session_state['ex_data'], st.session_state['ex_lvls'] = d, l
                else: st.error("Veri alınamadı.")
        
        if 'ex_data' in st.session_state:
            data, levels = st.session_state['ex_data'], st.session_state['ex_lvls']
            hourly = data['hourly']
            time = pd.to_datetime(hourly['time'])

            st.markdown("---")
            c_time, c_info = st.columns([2, 3])
            with c_time:
                sel_time = st.select_slider("📅 Analiz Saati:", options=[t.strftime('%d %b %H:%M') for t in time], value=time[0].strftime('%d %b %H:%M'))
                idx = [t.strftime('%d %b %H:%M') for t in time].index(sel_time)
            
            k, tt, lcl = calculate_indices(hourly, idx)
            with c_info:
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Sıcaklık (2m)", f"{hourly['temperature_2m'][idx]}°C")
                k_d = "Yüksek Risk!" if k > 30 else ("Orta Risk" if k > 20 else "Düşük")
                m2.metric("K-Index", f"{k:.1f}", k_d)
                tt_d = "Şiddetli!" if tt > 50 else ("Olası" if tt > 44 else "Sakin")
                m3.metric("Total Totals", f"{tt:.1f}", tt_d)
                m4.metric("LCL (Bulut)", f"{int(lcl) if lcl else '?'}m")

            temps, dews, press, u_w, v_w = [], [], [], [], []
            for l in levels:
                try:
                    t, d = hourly[f"temperature_{l}hPa"][idx], hourly[f"dewpoint_{l}hPa"][idx]
                    w, wd = hourly[f"windspeed_{l}hPa"][idx], hourly[f"winddirection_{l}hPa"][idx]
                    temps.append(t); dews.append(d); press.append(l)
                    rad = np.deg2rad(wd)
                    u_w.append(-w * np.sin(rad)); v_w.append(-w * np.cos(rad))
                except: pass

            col_skew, col_hodo = st.columns([3, 2])

            # --- SOL: PROFESYONEL SKEWT DİYAGRAMI ---
            with col_skew:
                def skew_transform(T_val, p_val):
                    """Sıcaklığı eğik eksene dönüştür (SkewT transformasyonu)"""
                    return T_val + (np.log(1000/p_val) * 40)
                
                press_np = np.array(press)
                temps_np = np.array(temps)
                dews_np = np.array(dews)
                
                # Transform edilmiş koordinatlar
                T_skewed = skew_transform(temps_np, press_np)
                Td_skewed = skew_transform(dews_np, press_np)
                
                fig = go.Figure()
                
                # Kuru adiabatlar (turuncu)
                for theta in range(-40, 121, 10):
                    T_line, p_line = [], []
                    for p in np.linspace(1000, 100, 40):
                        T_adiabat = theta * (p/1000)**0.286
                        if -70 < T_adiabat < 50:
                            T_line.append(skew_transform(T_adiabat, p))
                            p_line.append(p)
                    if T_line:
                        fig.add_trace(go.Scatter(
                            x=T_line, y=p_line, mode='lines',
                            line=dict(color='rgba(255, 120, 0, 0.2)', width=1),
                            showlegend=False, hoverinfo='skip'
                        ))
                
                # Doygun adiabatlar (mavi)
                for T_start in range(-30, 51, 10):
                    T_line, p_line = [], []
                    for p in np.linspace(1000, 200, 30):
                        T_moist = T_start - (1000 - p) * 0.006
                        if -70 < T_moist < 50:
                            T_line.append(skew_transform(T_moist, p))
                            p_line.append(p)
                    if T_line:
                        fig.add_trace(go.Scatter(
                            x=T_line, y=p_line, mode='lines',
                            line=dict(color='rgba(0, 150, 255, 0.2)', width=1),
                            showlegend=False, hoverinfo='skip'
                        ))
                
                # Karışım oranı çizgileri (yeşil)
                for mixing in [1, 2, 4, 8, 12, 16, 20]:
                    T_line, p_line = [], []
                    for p in np.linspace(1000, 400, 20):
                        T_mix = -20 + mixing * 3 - (1000-p) * 0.01
                        if -70 < T_mix < 50:
                            T_line.append(skew_transform(T_mix, p))
                            p_line.append(p)
                    if T_line:
                        fig.add_trace(go.Scatter(
                            x=T_line, y=p_line, mode='lines',
                            line=dict(color='rgba(50, 200, 50, 0.2)', width=1),
                            showlegend=False, hoverinfo='skip'
                        ))
                
                # İzoterm çizgileri (gri dikey) - -50 ile +50 arası
                for temp in range(-50, 51, 10):
                    temp_line = [skew_transform(temp, p) for p in [1000, 100]]
                    fig.add_trace(go.Scatter(
                        x=temp_line, y=[1000, 100], mode='lines',
                        line=dict(color='rgba(150, 150, 150, 0.3)', width=0.8, dash='dot'),
                        showlegend=False, hoverinfo='skip'
                    ))
                
                # Sıcaklık - Çiğ noktası arası alan (yeşil gölge)
                fill_x = list(T_skewed) + list(Td_skewed[::-1])
                fill_y = list(press_np) + list(press_np[::-1])
                fig.add_trace(go.Scatter(
                    x=fill_x, y=fill_y,
                    fill='toself',
                    fillcolor='rgba(0, 255, 100, 0.15)',
                    line=dict(color='rgba(0,0,0,0)'),
                    showlegend=False,
                    hoverinfo='skip'
                ))
                
                # Sıcaklık profili (kırmızı) - Sadece çizgi, marker yok
                fig.add_trace(go.Scatter(
                    x=T_skewed, y=press_np,
                    mode='lines',
                    line=dict(color='#FF3333', width=3.5),
                    name='Sıcaklık',
                    hovertemplate='<b>%{text}</b><br>T: %{customdata:.1f}°C<extra></extra>',
                    text=[f'{int(p)} hPa' for p in press_np],
                    customdata=temps_np
                ))
                
                # Çiğ noktası profili (yeşil) - Sadece çizgi, marker yok
                fig.add_trace(go.Scatter(
                    x=Td_skewed, y=press_np,
                    mode='lines',
                    line=dict(color='#00FF66', width=3.5),
                    name='Çiğ Noktası',
                    hovertemplate='<b>%{text}</b><br>Td: %{customdata:.1f}°C<extra></extra>',
                    text=[f'{int(p)} hPa' for p in press_np],
                    customdata=dews_np
                ))
                
                # 0°C çizgisi (donma seviyesi)
                zero_line = [skew_transform(0, p) for p in [1000, 100]]
                fig.add_trace(go.Scatter(
                    x=zero_line, y=[1000, 100],
                    mode='lines',
                    line=dict(color='cyan', width=2, dash='dash'),
                    name='0°C',
                    showlegend=False,
                    hoverinfo='skip'
                ))
                
                # Layout ayarları
                fig.update_layout(
                    title=dict(
                        text="🌡️ SkewT-logP Atmosferik Profil",
                        font=dict(size=16, color='white'),
                        x=0.5,
                        xanchor='center'
                    ),
                    template="plotly_dark",
                    height=700,
                    yaxis=dict(
                        title="Basınç (hPa)",
                        type='log',
                        range=[np.log10(1000), np.log10(100)],
                        tickvals=[1000, 900, 850, 750, 700, 600, 500, 400, 300, 250, 200, 150, 100],
                        ticktext=['1000','900', '850', '750','700', '600', '500', '400',  '300', '250',  '200', '150', '100'],
                        gridcolor='rgba(100, 100, 100, 0.3)',
                        showgrid=True
                    ),
                    xaxis=dict(
                        title="Sıcaklık (°C) - Eğik Eksen",
                        gridcolor='rgba(100, 100, 100, 0.3)',
                        showgrid=True,
                        zeroline=False
                    ),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="center",
                        x=0.5,
                        bgcolor='rgba(0,0,0,0.7)',
                        bordercolor='white',
                        borderwidth=1
                    ),
                    margin=dict(l=60, r=40, t=60, b=50),
                    hovermode='closest',
                    plot_bgcolor='#0E1117',
                    paper_bgcolor='#0E1117'
                )
                
                st.plotly_chart(fig, use_container_width=True)

            # --- SAĞ: HODOGRAF ---
            with col_hodo:
                fig_h = go.Figure()
                # Rüzgar çizgisi - Sadece çizgi, marker yok
                fig_h.add_trace(go.Scatter(
                    x=u_w, y=v_w, 
                    mode='lines+text', 
                    text=[str(p) if p in [1000, 850, 700, 500, 300] else "" for p in press], 
                    textposition="top right",
                    line=dict(color='white', width=2.5),
                    name="Rüzgar Vektörü",
                    hovertemplate='<b>%{text} hPa</b><br>U: %{x:.1f} m/s<br>V: %{y:.1f} m/s<extra></extra>',
                    showlegend=False
                ))
                fig_h.add_trace(go.Scatter(x=[0], y=[0], mode='markers', marker=dict(color='white', symbol='cross', size=10), showlegend=False))
                for r in [20, 40, 60]: fig_h.add_shape(type="circle", xref="x", yref="y", x0=-r, y0=-r, x1=r, y1=r, line_color="gray", opacity=0.3)
                fig_h.update_layout(title="🌀 Hodograf", template="plotly_dark", height=500, width=500, xaxis=dict(title="U (Doğu-Batı)", range=[-70, 70], zeroline=True), yaxis=dict(title="V (Kuzey-Güney)", range=[-70, 70], zeroline=True, scaleanchor="x", scaleratio=1), margin=dict(l=10, r=10, t=40, b=10), showlegend=False)
                st.plotly_chart(fig_h, use_container_width=True)
