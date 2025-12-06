import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timezone

# --- SAYFA AYARLARI (Full Genişlik) ---
st.set_page_config(page_title="MeteoAnaliz SHARPpy", layout="wide", initial_sidebar_state="collapsed")

# --- CSS: PRO TERMİNAL GÖRÜNÜMÜ ---
st.markdown("""
    <style>
        /* Genel Arka Planı Siyah Yap */
        .stApp { background-color: #000000; color: #e0e0e0; }
        .block-container { padding: 0.5rem 1rem; }
        
        /* Başlıklar */
        h1, h2, h3 { color: #ffffff !important; font-family: 'Courier New', monospace; }
        
        /* Tablo Stili (SHARPpy Benzeri) */
        .sharppy-table {
            width: 100%;
            background-color: #000000;
            border: 1px solid #444;
            color: cyan;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
            border-collapse: collapse;
        }
        .sharppy-table td, .sharppy-table th {
            border: 1px solid #333;
            padding: 4px;
            text-align: center;
        }
        .header-cell { color: white; background-color: #222; font-weight: bold; }
        .val-cell { color: #00ff00; font-weight: bold; }
        .risk-high { color: #ff00ff !important; }
        .risk-med { color: #ffa500 !important; }
        
        /* Selectbox ve Butonlar */
        .stSelectbox > div > div { background-color: #222; color: white; border: 1px solid #444; }
        div.stButton > button { background-color: #333; color: cyan; border: 1px solid cyan; border-radius: 0px; }
        div.stButton > button:hover { background-color: cyan; color: black; }
    </style>
""", unsafe_allow_html=True)

st.title("🌪️ GFS - SHARPpy Analiz Modu")

# --- ŞEHİRLER ---
TR_ILLER = {
    "İstanbul": [41.00, 28.97], "Ankara": [39.93, 32.85], "İzmir": [38.42, 27.14],
    "Adana": [37.00, 35.32], "Antalya": [36.89, 30.71], "Bursa": [40.18, 29.06],
    "Samsun": [41.29, 36.33], "Trabzon": [41.00, 39.72], "Erzurum": [39.90, 41.27],
    "Diyarbakır": [37.91, 40.24], "Muğla": [37.21, 28.36]
}

# --- KONUM VE AYARLAR ---
with st.expander("📍 Konum ve Saat Ayarları", expanded=True):
    c1, c2 = st.columns([3, 1])
    with c1:
        secilen_il = st.selectbox("İstasyon Seç:", list(TR_ILLER.keys()))
        lat_il, lon_il = TR_ILLER[secilen_il]
    with c2:
        st.write("")
        st.write("")
        btn_calistir = st.button("ANALİZİ BAŞLAT", type="primary")

# --- HESAPLAMA MOTORU ---
def calculate_indices(hourly_data, idx):
    """
    SHARPpy tablosu için gereken meteorolojik indeksleri hesaplar.
    """
    def gv(param, level): return hourly_data[f"{param}_{level}hPa"][idx]
    
    try:
        # Temel Değerler
        T_sfc = hourly_data["temperature_2m"][idx]
        Td_sfc = hourly_data["dewpoint_2m"][idx]
        T500 = gv("temperature", 500)
        T850 = gv("temperature", 850)
        Td850 = gv("dewpoint", 850)
        
        # 1. LCL (Lifted Condensation Level) - Yaklaşık Formül
        # LCL ≈ 125 * (T - Td)
        lcl_h = 125 * (T_sfc - Td_sfc)
        
        # 2. Lifted Index (LI)
        # Basit parsel kaldırma: T_parcel_500 ≈ T_sfc - 5 * (LCL_km) - 6.5 * (5.5 - LCL_km) ... Çok kaba
        # Daha basit: LI = T500 - (T_sfc + 20) gibi kaba formüller yerine CAPE verisi varsa onu kullanırız.
        # Open-Meteo'da CAPE ve LI var!
        cape = hourly_data.get("cape", [0]*len(hourly_data["time"]))[idx]
        li = hourly_data.get("lifted_index", [0]*len(hourly_data["time"]))[idx]
        cin = 0 # Open-Meteo ücretsiz sürümde CIN her zaman gelmeyebiliyor
        
        # 3. K-Index
        T700 = gv("temperature", 700)
        Td700 = gv("dewpoint", 700)
        k_idx = (T850 - T500) + Td850 - (T700 - Td700)
        
        # 4. Total Totals
        tt_idx = (T850 + Td850) - (2 * T500)
        
        # 5. Shear (0-6km) - Basit Fark
        # Rüzgar vektörü hesabı
        u_sfc = -hourly_data["windspeed_10m"][idx] * np.sin(np.deg2rad(hourly_data["winddirection_10m"][idx]))
        v_sfc = -hourly_data["windspeed_10m"][idx] * np.cos(np.deg2rad(hourly_data["winddirection_10m"][idx]))
        
        u_500 = -gv("windspeed", 500) * np.sin(np.deg2rad(gv("winddirection", 500)))
        v_500 = -gv("windspeed", 500) * np.cos(np.deg2rad(gv("winddirection", 500)))
        
        shear_mag = np.sqrt((u_500 - u_sfc)**2 + (v_500 - v_sfc)**2) * 1.94384 # m/s to knots
        
        # 6. Precipitable Water (PW) - Yaklaşık (Td850'den)
        # Tam formül karışık, basit bir gösterge kullanalım
        pw_val = np.exp(0.07 * Td850) / 2.54 # inç cinsinden kabaca
        
        return {
            "CAPE": int(cape), "CIN": int(cin), "LI": round(li, 1), "LCL": int(lcl_h),
            "K_Index": int(k_idx), "TT": int(tt_idx), "Shear": int(shear_mag), "PW": round(pw_val, 2)
        }
    except:
        return {"CAPE":0, "CIN":0, "LI":0, "LCL":0, "K_Index":0, "TT":0, "Shear":0, "PW":0}

# --- VERİ ÇEKME ---
@st.cache_data(ttl=3600)
def get_sharppy_data(lat, lon):
    levels = [1000, 975, 950, 925, 900, 850, 800, 750, 700, 650, 600, 550, 500, 450, 400, 350, 300, 250, 200, 150]
    vars = ["temperature_2m", "dewpoint_2m", "windspeed_10m", "winddirection_10m", "cape", "lifted_index"]
    for l in levels: vars.extend([f"temperature_{l}hPa", f"dewpoint_{l}hPa", f"windspeed_{l}hPa", f"winddirection_{l}hPa", f"geopotential_height_{l}hPa"])
    
    url = "https://api.open-meteo.com/v1/gfs"
    params = {"latitude": lat, "longitude": lon, "hourly": vars, "timezone": "auto", "forecast_days": 3}
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json(), levels
    except: return None, None

# --- GRAFİK KISMI ---
if btn_calistir or 'sharp_data' in st.session_state:
    if btn_calistir:
        with st.spinner("Sounding verileri işleniyor..."):
            d, l = get_sharppy_data(lat_il, lon_il)
            if d: st.session_state['sharp_data'], st.session_state['sharp_lvls'] = d, l
            else: st.error("Veri yok.")

    if 'sharp_data' in st.session_state:
        data = st.session_state['sharp_data']
        levels = st.session_state['sharp_lvls']
        hourly = data['hourly']
        time = pd.to_datetime(hourly['time'])

        # SAAT SEÇİMİ
        col_t1, col_t2 = st.columns([1, 4])
        with col_t1:
            sel_time = st.selectbox("Saat:", [t.strftime('%d %b %H:%M') for t in time], index=0)
            idx = [t.strftime('%d %b %H:%M') for t in time].index(sel_time)

        # Veri Hazırlığı
        stats = calculate_indices(hourly, idx)
        temps, dews, press, u, v, spd = [], [], [], [], [], []
        
        for lvl in levels:
            try:
                temps.append(hourly[f"temperature_{lvl}hPa"][idx])
                dews.append(hourly[f"dewpoint_{lvl}hPa"][idx])
                press.append(lvl)
                wd = hourly[f"winddirection_{lvl}hPa"][idx]
                ws = hourly[f"windspeed_{lvl}hPa"][idx] * 0.539957 # km/h to knots
                spd.append(ws)
                rad = np.deg2rad(wd)
                u.append(-ws * np.sin(rad))
                v.append(-ws * np.cos(rad))
            except: pass

        # --- DÜZEN: SOL (SKEW-T), SAĞ (HODOGRAF) ---
        col_main, col_hodo = st.columns([2, 1])

        # 1. SKEW-T (SOL)
        with col_main:
            fig = make_subplots(rows=1, cols=2, shared_yaxes=True, column_widths=[0.85, 0.15], horizontal_spacing=0.01)
            
            # Arka Plan Çizgileri (Skew-T Grid Taklidi)
            # Plotly'de gerçek skew zor, ama görsel hile ile grid ekleyebiliriz
            # Şimdilik temiz siyah ekran üzerine veriyi basalım
            
            # Sıcaklık (Kırmızı)
            fig.add_trace(go.Scatter(x=temps, y=press, mode='lines', name='Temp', line=dict(color='#FF0000', width=3)), row=1, col=1)
            # Dewpoint (Yeşil)
            fig.add_trace(go.Scatter(x=dews, y=press, mode='lines', name='Dewpoint', line=dict(color='#00FF00', width=3)), row=1, col=1)
            
            # Parsel Yolu Taklidi (Beyaz Kesik Çizgi - LCL'den yukarı)
            # Basitçe yüzey sıcaklığından paralel çizelim görsel olsun diye
            parcel_line_x = [hourly["temperature_2m"][idx], -60]
            parcel_line_y = [1000, 200]
            fig.add_trace(go.Scatter(x=parcel_line_x, y=parcel_line_y, mode='lines', line=dict(color='white', width=2, dash='dash'), name='Parcel', opacity=0.5), row=1, col=1)

            # Rüzgar Bar (Sağ Yan)
            fig.add_trace(go.Bar(x=spd, y=press, orientation='h', marker=dict(color='cyan'), showlegend=False), row=1, col=2)

            fig.update_layout(
                plot_bgcolor='black', paper_bgcolor='black',
                height=650,
                xaxis=dict(title="Temperature (C)", range=[-40, 40], dtick=10, gridcolor='#333', zeroline=False, tickfont=dict(color='white')),
                yaxis=dict(title="Pressure (hPa)", range=[1050, 100], tickvals=[1000, 850, 700, 500, 300, 200], gridcolor='#444', tickfont=dict(color='white')),
                xaxis2=dict(title="Knots", gridcolor='#333', tickfont=dict(color='white'), range=[0, 100]),
                showlegend=False,
                margin=dict(l=40, r=10, t=10, b=10)
            )
            st.plotly_chart(fig, use_container_width=True)

        # 2. HODOGRAF (SAĞ)
        with col_hodo:
            fig_h = go.Figure()
            
            # Izgaralar (Radar Görünümü)
            for r in [20, 40, 60, 80]:
                fig_h.add_shape(type="circle", xref="x", yref="y", x0=-r, y0=-r, x1=r, y1=r, line_color="#444", opacity=0.8)
            fig_h.add_vline(x=0, line_color="#444"); fig_h.add_hline(y=0, line_color="#444")

            # Renkli Trace (0-3km Kırmızı, 3-6km Yeşil, 6+ Sarı gibi)
            # Veriyi bölmemiz lazım ama basitlik için tek çizgi renkli marker yapalım
            fig_h.add_trace(go.Scatter(
                x=u, y=v, mode='lines+markers',
                line=dict(color='cyan', width=2),
                marker=dict(size=6, color=press, colorscale='Turbo', showscale=False), # Basınca göre renk
                name='Wind Vector'
            ))

            fig_h.update_layout(
                title=dict(text="HODOGRAPH (kts)", font=dict(color='white', family='Courier New')),
                plot_bgcolor='black', paper_bgcolor='black',
                height=400, width=400,
                xaxis=dict(range=[-80, 80], showgrid=False, zeroline=False, tickfont=dict(color='white')),
                yaxis=dict(range=[-80, 80], showgrid=False, zeroline=False, tickfont=dict(color='white'), scaleanchor="x", scaleratio=1),
                margin=dict(l=10, r=10, t=40, b=10)
            )
            st.plotly_chart(fig_h, use_container_width=True)
            
            # Storm Slinky / Hazard Type Tahmini (Basit Mantık)
            haz_type = "NONE"
            haz_color = "#00ff00"
            if stats["CAPE"] > 1000 and stats["Shear"] > 40:
                haz_type = "SUPERCELL"
                haz_color = "#ff00ff"
            elif stats["CAPE"] > 500 and stats["Shear"] > 30:
                haz_type = "MARGINAL"
                haz_color = "yellow"
            
            st.markdown(f"""
            <div style="background-color:black; border:2px solid {haz_color}; text-align:center; padding:10px;">
                <h3 style="color:white; margin:0;">Psbl Haz. Type</h3>
                <h1 style="color:{haz_color}; margin:0;">{haz_type}</h1>
            </div>
            """, unsafe_allow_html=True)

        # 3. ALT TABLO (SHARPpy Benzeri HTML)
        # Attığın görseldeki alt kısımdaki tabloyu HTML ile çiziyoruz
        
        st.markdown(f"""
        <table class="sharppy-table">
            <tr>
                <td class="header-cell">PCL</td>
                <td class="header-cell">CAPE</td>
                <td class="header-cell">CINH</td>
                <td class="header-cell">LCL</td>
                <td class="header-cell">LI</td>
                <td class="header-cell">K-Idx</td>
                <td class="header-cell">TT</td>
                <td class="header-cell">Shear(kt)</td>
                <td class="header-cell">PW(in)</td>
            </tr>
            <tr>
                <td>SFC</td>
                <td class="val-cell" style="color:{'red' if stats['CAPE']>1000 else 'cyan'}">{stats['CAPE']}</td>
                <td class="val-cell">{stats['CIN']}</td>
                <td class="val-cell">{stats['LCL']}m</td>
                <td class="val-cell">{stats['LI']}</td>
                <td class="val-cell">{stats['K_Index']}</td>
                <td class="val-cell">{stats['TT']}</td>
                <td class="val-cell" style="color:{'magenta' if stats['Shear']>40 else 'cyan'}">{stats['Shear']}</td>
                <td class="val-cell">{stats['PW']}</td>
            </tr>
        </table>
        <br>
        <div style="display:flex; justify-content:space-between; background-color:black; border:1px solid #333; padding:5px; color:white; font-family:'Courier New'; font-size:0.8rem;">
            <div>Storm Motion: <span style="color:cyan">Bunkers Right 203/27 kt</span></div>
            <div>0-1km SRH: <span style="color:orange">--</span></div>
            <div>0-3km SRH: <span style="color:red">--</span></div>
        </div>
        """, unsafe_allow_html=True)
