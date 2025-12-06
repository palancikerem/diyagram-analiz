import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timezone

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="MeteoAnaliz Expert", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- CSS ---
st.markdown("""
    <style>
        .block-container { padding-top: 0.5rem; padding-bottom: 2rem; }
        h1 { color: #4FA5D6; text-align: center; margin-bottom: 0px; font-size: 1.5rem !important;}
        .stMetric { background-color: #1E1E1E; padding: 10px; border-radius: 5px; border: 1px solid #333; }
        div.stButton > button { width: 100%; border-radius: 8px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🌪️ MeteoAnaliz Expert - GFS & Hodograf")

# --- ŞEHİRLER ---
TR_ILLER = {
    "İstanbul": [41.00, 28.97], "Ankara": [39.93, 32.85], "İzmir": [38.42, 27.14],
    "Adana": [37.00, 35.32], "Antalya": [36.89, 30.71], "Bursa": [40.18, 29.06],
    "Çanakkale": [40.15, 26.41], "Edirne": [41.68, 26.56], "Erzurum": [39.90, 41.27],
    "Eskişehir": [39.78, 30.52], "Gaziantep": [37.06, 37.38], "Kayseri": [38.73, 35.49],
    "Konya": [37.87, 32.48], "Samsun": [41.29, 36.33], "Trabzon": [41.00, 39.72],
    "Zonguldak": [41.45, 31.79], "Muğla": [37.21, 28.36], "Van": [38.50, 43.38]
}

# --- MATEMATİKSEL HESAPLAMALAR ---
def calculate_indices(hourly_data, idx):
    """
    K-Index, Total Totals ve LCL gibi kritik değerleri hesaplar.
    """
    try:
        # Verileri çek
        def get_val(param, level):
            return hourly_data[f"{param}_{level}hPa"][idx]

        T850 = get_val("temperature", 850)
        Td850 = get_val("dewpoint", 850)
        T700 = get_val("temperature", 700)
        Td700 = get_val("dewpoint", 700)
        T500 = get_val("temperature", 500)
        
        # --- K-INDEX ---
        # Formül: (T850 - T500) + Td850 - (T700 - Td700)
        k_index = (T850 - T500) + Td850 - (T700 - Td700)
        
        # --- TOTAL TOTALS (TT) ---
        # Formül: (T850 + Td850) - 2*T500
        tt_index = (T850 + Td850) - (2 * T500)
        
        # --- LCL (Yaklaşık Bulut Tabanı) ---
        # Formül: 125 * (T_yer - Td_yer)
        T_sfc = hourly_data["temperature_2m"][idx]
        Td_sfc = hourly_data["dewpoint_2m"][idx]
        lcl_m = 125 * (T_sfc - Td_sfc)
        
        return k_index, tt_index, lcl_m
    except:
        return None, None, None

# --- VERİ ÇEKME ---
@st.cache_data(ttl=3600)
def get_sounding_data(lat, lon):
    levels = [1000, 950, 925, 900, 850, 800, 700, 600, 500, 400, 300, 250, 200]
    vars = ["temperature_2m", "dewpoint_2m", "windspeed_10m", "winddirection_10m"]
    
    for lvl in levels:
        vars.append(f"temperature_{lvl}hPa")
        vars.append(f"dewpoint_{lvl}hPa")
        vars.append(f"windspeed_{lvl}hPa")
        vars.append(f"winddirection_{lvl}hPa")
        vars.append(f"geopotential_height_{lvl}hPa")
        
    url = "https://api.open-meteo.com/v1/gfs"
    params = {
        "latitude": lat, "longitude": lon, 
        "hourly": vars, 
        "timezone": "auto", 
        "forecast_days": 3 # 3 Günlük detaylı veri yeterli
    }
    
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json(), levels
    except: return None, None

# --- ARAYÜZ BAŞLANGIÇ ---
with st.expander("📍 Konum ve Ayarlar", expanded=True):
    c1, c2 = st.columns([3, 1])
    with c1:
        secilen_il = st.selectbox("Şehir Seç:", list(TR_ILLER.keys()))
        lat_il, lon_il = TR_ILLER[secilen_il]
    with c2:
        st.write("")
        st.write("")
        btn_calistir = st.button("ANALİZ ET", type="primary")

# --- ANA İŞLEM ---
if btn_calistir or 'expert_data' in st.session_state:
    if btn_calistir:
        with st.spinner("Atmosferik veriler ve rüzgar vektörleri işleniyor..."):
            data, levels = get_sounding_data(lat_il, lon_il)
            if data:
                st.session_state['expert_data'] = data
                st.session_state['expert_lvls'] = levels
            else:
                st.error("Veri sunucusuna ulaşılamadı.")

    if 'expert_data' in st.session_state:
        data = st.session_state['expert_data']
        levels = st.session_state['expert_lvls']
        hourly = data['hourly']
        time = pd.to_datetime(hourly['time'])
        
        # SAAT SEÇİMİ
        st.markdown("---")
        col_time, col_info = st.columns([2, 3])
        
        with col_time:
            selected_time_str = st.select_slider(
                "📅 Analiz Saati:",
                options=[t.strftime('%d %b %H:%M') for t in time],
                value=time[0].strftime('%d %b %H:%M')
            )
            idx = [t.strftime('%d %b %H:%M') for t in time].index(selected_time_str)

        # İNDEKS HESAPLAMA
        k_idx, tt_idx, lcl_val = calculate_indices(hourly, idx)
        
        with col_info:
            # Kritik Değerler Kartları
            cm1, cm2, cm3, cm4 = st.columns(4)
            
            with cm1:
                st.metric("Sıcaklık (2m)", f"{hourly['temperature_2m'][idx]}°C")
            with cm2:
                # K-Index Renklendirme
                k_durum = "Düşük"
                if k_idx > 30: k_durum = "Yüksek Risk!"
                elif k_idx > 20: k_durum = "Orta Risk"
                st.metric("K-Index (Oraj)", f"{k_idx:.1f}", k_durum)
            with cm3:
                # TT Renklendirme
                tt_durum = "Sakin"
                if tt_idx > 50: tt_durum = "Şiddetli!"
                elif tt_idx > 44: tt_durum = "Olası"
                st.metric("Total Totals", f"{tt_idx:.1f}", tt_durum)
            with cm4:
                st.metric("Bulut Tabanı (LCL)", f"{int(lcl_val)}m")

        # --- GRAFİK HAZIRLIĞI ---
        temps, dews, winds, dirs, press = [], [], [], [], []
        u_winds, v_winds = [], [] # Hodograf için

        for lvl in levels:
            try:
                t = hourly[f"temperature_{lvl}hPa"][idx]
                d = hourly[f"dewpoint_{lvl}hPa"][idx]
                w = hourly[f"windspeed_{lvl}hPa"][idx]
                wd = hourly[f"winddirection_{lvl}hPa"][idx]
                
                temps.append(t)
                dews.append(d)
                press.append(lvl)
                winds.append(w)
                dirs.append(wd)
                
                # Rüzgar Vektör Hesabı (HODOGRAF İÇİN)
                # Radyana çevir
                rad = np.deg2rad(wd)
                # U (Doğu-Batı), V (Kuzey-Güney) bileşenleri
                # Meteorolojide rüzgarın GELDİĞİ yön kullanılır, o yüzden - ile çarparız
                u = -w * np.sin(rad)
                v = -w * np.cos(rad)
                u_winds.append(u)
                v_winds.append(v)
                
            except: pass

        # --- ÇİFT KOLON DÜZENİ (SKEW-T SOLDA, HODOGRAF SAĞDA) ---
        col_skew, col_hodo = st.columns([2, 1])

        # ==========================
        # 1. SOL: SKEW-T / PROFIL
        # ==========================
        with col_skew:
            # 2 Subplot: Biri Sıcaklık, Biri Rüzgar Hızı
            fig = make_subplots(rows=1, cols=2, shared_yaxes=True, column_widths=[0.8, 0.2], horizontal_spacing=0.02)

            # A) SICAKLIK & DEWPOINT
            fig.add_trace(go.Scatter(x=temps, y=press, mode='lines+markers', name='Sıcaklık', line=dict(color='red', width=3)), row=1, col=1)
            fig.add_trace(go.Scatter(x=dews, y=press, mode='lines+markers', name='Dewpoint', line=dict(color='#00FF00', width=2)), row=1, col=1)
            
            # Alan Boyama (Shading) - Nemli alanı gösterir
            fig.add_trace(go.Scatter(
                x=temps + dews[::-1], # Poligon oluşturuyoruz
                y=press + press[::-1],
                fill='toself',
                fillcolor='rgba(0, 255, 0, 0.1)',
                line=dict(color='rgba(255,255,255,0)'),
                showlegend=False,
                hoverinfo='skip'
            ), row=1, col=1)

            # 0 Derece Çizgisi
            fig.add_vline(x=0, line_color="cyan", line_width=1, opacity=0.5, row=1, col=1, annotation_text="0°C")

            # B) RÜZGAR HIZI (Bar)
            fig.add_trace(go.Bar(
                x=winds, y=press, orientation='h', 
                name='Rüzgar (km/s)', 
                marker=dict(color=winds, colorscale='Viridis'),
                showlegend=False
            ), row=1, col=2)

            # AYARLAR
            fig.update_layout(
                title="🌡️ Atmosferik Profil (Skew-T Simülasyonu)",
                template="plotly_dark",
                height=600,
                yaxis=dict(title="Basınç (hPa)", autorange="reversed", tickvals=[1000, 850, 700, 500, 300, 200]),
                xaxis=dict(title="Sıcaklık (°C)", range=[-40, 35], dtick=5, gridcolor='#333'),
                xaxis2=dict(title="Rüzgar Hızı (km/s)", title_font=dict(size=10)),
                legend=dict(x=0, y=1, bgcolor='rgba(0,0,0,0)')
            )
            st.plotly_chart(fig, use_container_width=True)

        # ==========================
        # 2. SAĞ: HODOGRAF (Rüzgar Sarmalı)
        # ==========================
        with col_hodo:
            fig_hodo = go.Figure()
            
            # Hodograf Çizgisi
            fig_hodo.add_trace(go.Scatter(
                x=u_winds, y=v_winds,
                mode='lines+markers+text',
                text=[str(p) if p in [1000, 850, 700, 500, 300] else "" for p in press],
                textposition="top right",
                marker=dict(
                    size=8,
                    color=press, # Yüksekliğe göre renk
                    colorscale='Jet_r', # Alçak seviye sıcak, yüksek seviye soğuk renk
                    showscale=True,
                    colorbar=dict(title="hPa", len=0.5)
                ),
                line=dict(color='white', width=2),
                name="Rüzgar Vektörü"
            ))

            # Merkez Nokta (0,0)
            fig_hodo.add_trace(go.Scatter(x=[0], y=[0], mode='markers', marker=dict(color='white', symbol='cross', size=10), showlegend=False))

            # Halka Izgaralar (Hız Göstergesi)
            for r in [10, 20, 30, 50, 70]:
                fig_hodo.add_shape(type="circle", xref="x", yref="y", x0=-r, y0=-r, x1=r, y1=r, line_color="gray", opacity=0.3)

            fig_hodo.update_layout(
                title="🌀 Hodograf (Rüzgar Gülü)",
                template="plotly_dark",
                height=600,
                width=600,
                xaxis=dict(title="U Bileşeni (Doğu-Batı)", range=[-60, 60], zeroline=True, zerolinewidth=2),
                yaxis=dict(title="V Bileşeni (Kuzey-Güney)", range=[-60, 60], zeroline=True, zerolinewidth=2, scaleanchor="x", scaleratio=1),
                margin=dict(l=10, r=10, t=40, b=10)
            )
            
            st.plotly_chart(fig_hodo, use_container_width=True)
            
            st.info("""
            **Hodograf Nedir?**
            Rüzgarın yerden yükseldikçe nasıl yön değiştirdiğini gösterir.
            - Çizgi **saat yönünde** dönüyorsa (kırmızı->mavi), Süper Hücre riski artar.
            - Çizgi **düz** ise, rüzgar yönü sabittir.
            """)
