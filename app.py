import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timezone
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(
    page_title="GFS - KeremPalancı", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
        .block-container { padding-top: 0.5rem; padding-bottom: 1rem; padding-left: 0.2rem; padding-right: 0.2rem; }
        h1 { font-size: 1.3rem !important; color: #4FA5D6; text-align: center; margin-bottom: 0px; }
        .stSelectbox, .stMultiSelect { margin-bottom: 0px; }
        div.stButton > button { width: 100%; border-radius: 8px; }
        .main-svg { border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

st.title("Meteorolojik Diyagramlar - KeremPalancı")

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

with st.expander("📍 Ayarlar", expanded=True):
    col_a, col_b = st.columns([3, 1])
    with col_a:
        secilen_il = st.selectbox("Şehir:", list(TR_ILLER.keys()), index=0)
        lat_il, lon_il = TR_ILLER[secilen_il]
    with col_b:
        st.write("")
        st.write("") 
        btn_calistir = st.button("Başlat", type="primary", use_container_width=True)

    secilen_veriler = st.multiselect(
        "Veriler:",
        [
            "Sıcaklık (850hPa)", "Sıcaklık (2m)", "Kar Yağışı (cm)", 
            "Yağış (mm)", "Rüzgar (10m)", "Rüzgar Hamlesi", 
            "Bağıl Nem (2m)", "Bulutluluk (%)", "Donma Seviyesi (m)",
            "CAPE", "Basınç", "SkewT Diyagramı"
        ],
        default=["Sıcaklık (850hPa)", "Kar Yağışı (cm)"]
    )
    vurgulu_senaryolar = st.multiselect("Senaryo Seç", options=range(0, 31))
    st.caption(f"📅 Model: **{get_run_info()}**")

@st.cache_data(ttl=3600)
def get_data(lat, lon, variables):
    var_map = {
        "Sıcaklık (850hPa)": "temperature_850hPa",
        "Sıcaklık (2m)": "temperature_2m",
        "Kar Yağışı (cm)": "snowfall",
        "Yağış (mm)": "precipitation",
        "Rüzgar (10m)": "windspeed_10m",
        "Rüzgar Hamlesi": "windgusts_10m",
        "Bağıl Nem (2m)": "relativehumidity_2m",
        "Bulutluluk (%)": "cloudcover",
        "Donma Seviyesi (m)": "freezinglevel_height",
        "CAPE": "cape",
        "Basınç": "pressure_msl"
    }
    api_vars = [var_map[v] for v in variables if v in var_map]
    
    url = "https://ensemble-api.open-meteo.com/v1/ensemble"
    params = {
        "latitude": lat, 
        "longitude": lon, 
        "hourly": api_vars, 
        "models": "gfs_seamless", 
        "timezone": "auto"
    }
    
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json(), var_map
    except: 
        return None, None

@st.cache_data(ttl=3600)
def get_skewt_data(lat, lon):
    """SkewT için basınç seviyelerinde sıcaklık, nem ve rüzgar verisi"""
    pressure_levels = ["1000", "975", "950", "925", "900", "850", "800", "700", "600", "500", "400", "300", "250", "200", "150", "100"]
    
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": [
            f"temperature_{p}hPa" for p in pressure_levels
        ] + [
            f"relativehumidity_{p}hPa" for p in pressure_levels
        ] + [
            f"windspeed_{p}hPa" for p in pressure_levels
        ] + [
            f"winddirection_{p}hPa" for p in pressure_levels
        ],
        "temperature_unit": "celsius",
        "windspeed_unit": "ms"
    }
    
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json(), pressure_levels
    except:
        return None, None

def calculate_dewpoint(T, RH):
    """Çiğ noktası hesaplama (Magnus formülü)"""
    a, b = 17.27, 237.7
    alpha = ((a * T) / (b + T)) + np.log(RH/100.0)
    return (b * alpha) / (a - alpha)

def calculate_cape_simple(pressure, temperature, dewpoint):
    """Basitleştirilmiş CAPE hesaplama"""
    try:
        # Yüzey parseli
        T_parcel = temperature[0]
        Td_parcel = dewpoint[0]
        
        # Doygun adiabatik yükselme yaklaşımı
        cape = 0
        for i in range(len(pressure)-1):
            if temperature[i] < T_parcel:
                dp = pressure[i] - pressure[i+1]
                dT = temperature[i] - T_parcel
                cape += 9.81 * dT * dp / (temperature[i] + 273.15)
                T_parcel -= 0.0065 * dp  # Basitleştirilmiş soğuma
        
        return max(0, cape)
    except:
        return None

def create_skewt_plotly(data, pressure_levels, time_index, location_name):
    """Plotly ile profesyonel SkewT-logP diyagramı"""
    
    hourly = data['hourly']
    time_str = pd.to_datetime(hourly['time'][time_index]).strftime('%Y-%m-%d %H:%M')
    
    # Veri hazırlama
    p = np.array([float(lv) for lv in pressure_levels])
    T = np.array([hourly[f'temperature_{lv}hPa'][time_index] for lv in pressure_levels])
    rh = np.array([hourly[f'relativehumidity_{lv}hPa'][time_index] for lv in pressure_levels])
    
    # Çiğ noktası
    Td = calculate_dewpoint(T, rh)
    
    # Rüzgar
    wind_speed = np.array([hourly[f'windspeed_{lv}hPa'][time_index] for lv in pressure_levels])
    wind_dir = np.array([hourly[f'winddirection_{lv}hPa'][time_index] for lv in pressure_levels])
    
    # SkewT transformasyonu için
    def skew_transform(T_val, p_val):
        """Sıcaklığı eğik eksene dönüştür"""
        return T_val + (np.log(1000/p_val) * 30)
    
    # Transform edilmiş koordinatlar
    T_skewed = skew_transform(T, p)
    Td_skewed = skew_transform(Td, p)
    
    fig = go.Figure()
    
    # Kuru adiabatlar (sabit potansiyel sıcaklık çizgileri)
    for theta in range(-40, 121, 10):
        T_line = []
        p_line = []
        for press in np.linspace(1000, 100, 50):
            T_adiabat = theta * (press/1000)**0.286
            if -60 < T_adiabat < 60:
                T_line.append(skew_transform(T_adiabat, press))
                p_line.append(press)
        if T_line:
            fig.add_trace(go.Scatter(
                x=T_line, y=p_line,
                mode='lines',
                line=dict(color='rgba(255, 100, 0, 0.15)', width=0.8),
                showlegend=False,
                hoverinfo='skip'
            ))
    
    # Doygun adiabatlar yaklaşımı
    for T_start in range(-30, 51, 10):
        T_line = []
        p_line = []
        for press in np.linspace(1000, 200, 30):
            # Basitleştirilmiş doygun adiabat
            T_moist = T_start - (1000 - press) * 0.006
            if -60 < T_moist < 60:
                T_line.append(skew_transform(T_moist, press))
                p_line.append(press)
        if T_line:
            fig.add_trace(go.Scatter(
                x=T_line, y=p_line,
                mode='lines',
                line=dict(color='rgba(0, 100, 255, 0.15)', width=0.8),
                showlegend=False,
                hoverinfo='skip'
            ))
    
    # Karışım oranı çizgileri (izotherm benzeri)
    for mixing in [0.5, 1, 2, 4, 8, 12, 16, 20]:
        T_line = []
        p_line = []
        for press in np.linspace(1000, 400, 20):
            # Basitleştirilmiş karışım oranı çizgisi
            T_mix = -20 + mixing * 3 - (1000-press) * 0.01
            if -60 < T_mix < 60:
                T_line.append(skew_transform(T_mix, press))
                p_line.append(press)
        if T_line:
            fig.add_trace(go.Scatter(
                x=T_line, y=p_line,
                mode='lines',
                line=dict(color='rgba(0, 200, 0, 0.15)', width=0.8),
                showlegend=False,
                hoverinfo='skip'
            ))
    
    # İzotermal çizgiler (dikey)
    for temp in range(-60, 61, 10):
        temp_line = [skew_transform(temp, pr) for pr in [1000, 100]]
        fig.add_trace(go.Scatter(
            x=temp_line, y=[1000, 100],
            mode='lines',
            line=dict(color='rgba(150, 150, 150, 0.3)', width=0.8, dash='dot'),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Sıcaklık profili
    fig.add_trace(go.Scatter(
        x=T_skewed, y=p,
        mode='lines+markers',
        line=dict(color='red', width=3),
        marker=dict(size=6),
        name='Sıcaklık',
        hovertemplate='%{text}<extra></extra>',
        text=[f'{pr:.0f} hPa<br>T: {t:.1f}°C' for pr, t in zip(p, T)]
    ))
    
    # Çiğ noktası profili
    fig.add_trace(go.Scatter(
        x=Td_skewed, y=p,
        mode='lines+markers',
        line=dict(color='green', width=3),
        marker=dict(size=6),
        name='Çiğ Noktası',
        hovertemplate='%{text}<extra></extra>',
        text=[f'{pr:.0f} hPa<br>Td: {td:.1f}°C' for pr, td in zip(p, Td)]
    ))
    
    # CAPE hesaplama
    cape = calculate_cape_simple(p, T, Td)
    
    # Layout
    fig.update_layout(
        title=dict(
            text=f'<b>SkewT-logP Diyagramı</b><br>{location_name} - {time_str}',
            x=0.5,
            xanchor='center',
            font=dict(size=16)
        ),
        xaxis=dict(
            title='Sıcaklık (°C) - Eğik Eksen',
            gridcolor='rgba(200, 200, 200, 0.2)',
            zeroline=True,
            zerolinecolor='rgba(255, 255, 255, 0.3)'
        ),
        yaxis=dict(
            title='Basınç (hPa)',
            type='log',
            range=[np.log10(1000), np.log10(100)],
            gridcolor='rgba(200, 200, 200, 0.2)',
            tickvals=[1000, 850, 700, 500, 300, 200, 100],
            ticktext=['1000', '850', '700', '500', '300', '200', '100']
        ),
        template='plotly_dark',
        height=700,
        hovermode='closest',
        showlegend=True,
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor='rgba(0,0,0,0.6)',
            bordercolor='white',
            borderwidth=1
        )
    )
    
    # Parametre bilgileri
    info_text = f'<b>Atmosferik Parametreler:</b><br>'
    if cape is not None:
        info_text += f'CAPE: {cape:.0f} J/kg<br>'
    info_text += f'Yüzey T: {T[0]:.1f}°C<br>'
    info_text += f'Yüzey Td: {Td[0]:.1f}°C<br>'
    info_text += f'850 hPa T: {T[3]:.1f}°C'
    
    fig.add_annotation(
        text=info_text,
        xref='paper', yref='paper',
        x=0.98, y=0.02,
        xanchor='right', yanchor='bottom',
        showarrow=False,
        bgcolor='rgba(0, 0, 0, 0.7)',
        bordercolor='white',
        borderwidth=1,
        font=dict(size=11, color='white')
    )
    
    return fig

if btn_calistir:
    if not secilen_veriler:
        st.error("Veri seçin.")
    else:
        # SkewT seçildi mi kontrol et
        skewt_secildi = "SkewT Diyagramı" in secilen_veriler
        normal_veriler = [v for v in secilen_veriler if v != "SkewT Diyagramı"]
        
        # Normal veriler için
        if normal_veriler:
            with st.spinner('Veri alınıyor...'):
                data, mapping = get_data(lat_il, lon_il, normal_veriler)
                if data:
                    hourly = data['hourly']
                    time = pd.to_datetime(hourly['time'])
                    
                    for secim in normal_veriler:
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
                                
                                c, w, o, leg = 'lightgrey', 0.5, 0.4, False
                                h = 'skip'
                                if mem_num in vurgulu_senaryolar:
                                    c, w, o, leg = '#FF1493', 2.0, 1.0, True
                                    h = 'all' 
                                
                                fig.add_trace(go.Scatter(x=time, y=hourly[member], mode='lines', 
                                                        line=dict(color=c, width=w), opacity=o, 
                                                        name=f"S-{mem_num}", showlegend=leg, hoverinfo=h))

                            h_txt = [f"📅 <b>{t.strftime('%d.%m %H:%M')}</b><br>🔺 Max: {mx:.1f} (S-{mxn})<br>⚪ Ort: {mn:.1f}<br>🔻 Min: {mi:.1f} (S-{minn})" 
                                    for t, mx, mxn, mn, mi, minn in zip(time, max_val, max_mem, mean_val, min_val, min_mem)]
                            fig.add_trace(go.Scatter(x=time, y=mean_val, mode='lines', line=dict(width=0), 
                                                    hovertemplate="%{text}<extra></extra>", text=h_txt, showlegend=False))
                            
                            c_map = {"850hPa": "red", "2m": "orange", "Kar": "white", "Yağış": "cyan", 
                                    "Rüzgar": "green", "Hamlesi": "lime", "Bulut": "gray", 
                                    "Nem": "teal", "Basınç": "magenta"}
                            main_c = next((v for k, v in c_map.items() if k in secim), "cyan")
                            
                            fig.add_trace(go.Scatter(x=time, y=mean_val, mode='lines', 
                                                    line=dict(color=main_c, width=3.0), 
                                                    name="ORTALAMA", showlegend=False, hoverinfo='skip'))

                            if "850hPa" in secim: 
                                fig.add_hline(y=0, line_dash="dash", line_color="orange", opacity=0.5)

                            fig.update_layout(
                                title=dict(text=f"{secim}", font=dict(size=14)),
                                template="plotly_dark", height=500,
                                margin=dict(l=2, r=2, t=30, b=5), 
                                hovermode="x unified",
                                legend=dict(orientation="h", y=1, x=1)
                            )
                            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # SkewT için
        if skewt_secildi:
            st.markdown("---")
            st.subheader("🌡️ SkewT-logP Diyagramı")
            
            with st.spinner('SkewT verisi alınıyor...'):
                skewt_data, pressure_levels = get_skewt_data(lat_il, lon_il)
                
                if skewt_data and pressure_levels:
                    hourly = skewt_data['hourly']
                    times = pd.to_datetime(hourly['time'])
                    
                    # Zaman seçici
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        selected_time = st.select_slider(
                            "Zaman seçin:",
                            options=range(len(times)),
                            format_func=lambda x: times[x].strftime('%d.%m %H:%M'),
                            value=0
                        )
                    with col2:
                        st.write("")
                        st.write("")
                        if st.button("Diyagram Oluştur", type="primary"):
                            with st.spinner('SkewT diyagramı oluşturuluyor...'):
                                try:
                                    fig = create_skewt_plotly(
                                        skewt_data, 
                                        pressure_levels, 
                                        selected_time, 
                                        secilen_il
                                    )
                                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})
                                    st.success("✅ Diyagram başarıyla oluşturuldu!")
                                except Exception as e:
                                    st.error(f"Diyagram oluşturulurken hata: {str(e)}")
                else:
                    st.error("SkewT verisi alınamadı.")
