import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timezone

st.set_page_config(
    page_title="MeteoAnaliz - KeremPalancı", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
        .block-container { padding-top: 0.5rem; padding-bottom: 1rem; padding-left: 0.2rem; padding-right: 0.2rem; }
        h1 { font-size: 1.3rem !important; color: #4FA5D6; text-align: center; margin-bottom: 0px; }
        .stSelectbox, .stMultiSelect, .stTextInput, .stRadio { margin-bottom: 10px; }
        div.stButton > button { width: 100%; border-radius: 8px; }
        .main-svg { border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

st.title("Meteorolojik Analiz Sistemi - KeremPalancı")

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

def clean_filename(text):
    """Türkçe karakterleri ve boşlukları temizler"""
    tr_map = str.maketrans("ığüşöçİĞÜŞÖÇ ", "igusocIGUSOC_")
    return text.translate(tr_map)

def get_run_info():
    now_utc = datetime.now(timezone.utc)
    hour = now_utc.hour
    minute = now_utc.minute
    current_minutes = hour * 60 + minute
    
    if current_minutes >= (3 * 60 + 30) and current_minutes < (9 * 60 + 30):
        return "00Z (Sabah)"
    elif current_minutes >= (9 * 60 + 30) and current_minutes < (15 * 60 + 30):
        return "06Z (Öğle)"
    elif current_minutes >= (15 * 60 + 30) and current_minutes < (21 * 60 + 30):
        return "12Z (Akşam)"
    else:
        return "18Z (Gece)"

@st.cache_data
def search_location(query):
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": query, "count": 5, "language": "tr", "format": "json"}
    try:
        r = requests.get(url, params=params, timeout=5)
        r.raise_for_status()
        data = r.json()
        if "results" in data:
            return data["results"]
        return []
    except:
        return []

# NOAA Veri Çekme Fonksiyonu
@st.cache_data(ttl=86400)
def get_climate_index(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        lines = response.text.split('\n')
        data = []
        
        for line in lines:
            parts = line.split()
            if not parts: continue
            
            if parts[0].isdigit() and 1940 < int(parts[0]) < 2030:
                year = int(parts[0])
                for month_idx, value in enumerate(parts[1:]):
                    if month_idx < 12: 
                        try:
                            val = float(value)
                            if val < -90: val = None 
                            date_str = f"{year}-{month_idx+1:02d}-01"
                            data.append({"Tarih": date_str, "Değer": val})
                        except: continue

        df = pd.DataFrame(data)
        df['Tarih'] = pd.to_datetime(df['Tarih'])
        return df.dropna()
    except:
        return None

with st.expander("📍 Konum ve Analiz Ayarları", expanded=True):
    tab1, tab2 = st.tabs(["Listeden Seç", "🔍 Konum Ara (Tüm İlçeler)"])
    selected_lat, selected_lon, location_name = 41.00, 28.97, "İstanbul"

    with tab1:
        secilen_il = st.selectbox("Şehir Seçiniz:", list(TR_ILLER.keys()), index=0)
        if secilen_il:
            selected_lat, selected_lon = TR_ILLER[secilen_il]
            location_name = secilen_il

    with tab2:
        col_search, col_res = st.columns([2, 2])
        with col_search:
            arama_sorgusu = st.text_input("İlçe/Konum Yaz (Örn: Alanya)", placeholder="İlçe adı girin...")
        with col_res:
            if arama_sorgusu:
                sonuclar = search_location(arama_sorgusu)
                if sonuclar:
                    secenekler = {f"{s['name']} ({s.get('admin1', '')}, {s.get('country_code', '')})": (s['latitude'], s['longitude'], s['name']) for s in sonuclar}
                    secilen_sonuc = st.selectbox("Sonuç Seç:", list(secenekler.keys()))
                    if secilen_sonuc:
                        selected_lat, selected_lon, location_name = secenekler[secilen_sonuc]
                else:
                    st.warning("Bulunamadı.")
            else:
                st.info("Aramak için yazın.")

    st.divider()

    # YENİ MOD EKLENDİ
    calisma_modu = st.radio("Analiz Modu Seçin:", [
        "📉 GFS Senaryoları (Diyagram)", 
        "Model Kıyaslama (GFS vs ICON vs GEM)",
        "🌍 Küresel Endeksler (ENSO, NAO, vb.)"
    ], horizontal=True)

    secilen_veriler = []
    vurgulu_senaryolar = []
    
    COMPARISON_MAP = {
        "Sıcaklık (2m)": {"api": "temperature_2m", "unit": "°C"},
        "Sıcaklık (850hPa)": {"api": "temperature_850hPa", "unit": "°C"},
        "Yağış (mm)": {"api": "precipitation", "unit": "mm"},
        "Rüzgar Hızı (10m)": {"api": "windspeed_10m", "unit": "km/s"},
        "Basınç (hPa)": {"api": "pressure_msl", "unit": "hPa"},
        "Bulutluluk (%)": {"api": "cloudcover", "unit": "%"},
        "Jeopotansiyel Yükseklik (500hPa)": {"api": "geopotential_height_500hPa", "unit": "m"}
    }
    
    INDEX_URLS = {
        "ENSO (Niño 3.4)": "https://psl.noaa.gov/data/correlation/nina34.data",
        "NAO (Kuzey Atlantik Salınımı)": "https://psl.noaa.gov/data/correlation/nao.data",
        "AO (Arktik Salınımı)": "https://psl.noaa.gov/data/correlation/ao.data",
        "IOD (Hint Okyanusu Dipolü)": "https://psl.noaa.gov/data/correlation/dmi.data",
        "QBO (Quasi-Biennial Oscillation)": "https://psl.noaa.gov/data/correlation/qbo.data",
        "SOI (Southern Oscillation Index)": "https://psl.noaa.gov/data/correlation/soi.data"
    }

    savas_parametresi = "Sıcaklık (2m)"
    secilen_endeks = "ENSO (Niño 3.4)"
    yil_araligi = 5

    if calisma_modu == "📉 GFS Senaryoları (Diyagram)":
        secilen_veriler = st.multiselect(
            "Diyagram Verileri:",
            [
                "Sıcaklık (850hPa)", "Sıcaklık (500hPa)", "Sıcaklık (2m)", 
                "Kar Yağışı (cm)", "Kar Kalınlığı (cm)",
                "Yağış (mm)", "Lifted Index (LI)", "CAPE (J/kg)",
                "Rüzgar (10m)", "Rüzgar Hamlesi", 
                "Bağıl Nem (2m)", "Bulutluluk (%)", "Donma Seviyesi (m)",
                "Basınç"
            ],
            default=["Sıcaklık (850hPa)", "Yağış (mm)"]
        )
        vurgulu_senaryolar = st.multiselect("Senaryo Vurgula", options=range(0, 31))

    elif calisma_modu == "Model Kıyaslama (GFS vs ICON vs GEM)":
        savas_parametresi = st.selectbox(
            "Veri Seçiniz...",
            list(COMPARISON_MAP.keys())
        )
    
    elif calisma_modu == "🌍 Küresel Endeksler (ENSO, NAO, vb.)":
        col_i1, col_i2 = st.columns([1,1])
        with col_i1:
            secilen_endeks = st.selectbox("Endeks Seçin:", list(INDEX_URLS.keys()))
        with col_i2:
            yil_araligi = st.slider("Son Kaç Yıl?", 1, 50, 5)

    st.caption(f"📅 Sistemdeki Run: **{get_run_info()}**")
    btn_calistir = st.button("ANALİZİ BAŞLAT", type="primary", use_container_width=True)
    
    # Endeks modunda konum bilgisi gereksiz ama layout bozulmasın diye bırakıyoruz
    if calisma_modu != "🌍 Küresel Endeksler (ENSO, NAO, vb.)":
        st.caption(f"Seçili Konum: **{location_name}** ({selected_lat:.2f}, {selected_lon:.2f})")

def add_watermark(fig):
    fig.add_annotation(
        text="Analiz: KeremPalancı",
        xref="paper", yref="paper",
        x=0.99, y=0.01,
        showarrow=False,
        font=dict(size=12, color="rgba(255, 255, 255, 0.5)", family="Arial"),
        bgcolor="rgba(0,0,0,0.5)",
        borderpad=4
    )
    return fig

@st.cache_data(ttl=3600)
def get_ensemble_data(lat, lon, variables):
    var_map = {
        "Sıcaklık (850hPa)": "temperature_850hPa",
        "Sıcaklık (500hPa)": "temperature_500hPa",
        "Sıcaklık (2m)": "temperature_2m",
        "Kar Yağışı (cm)": "snowfall",
        "Kar Kalınlığı (cm)": "snow_depth",
        "Yağış (mm)": "precipitation",
        "Lifted Index (LI)": "lifted_index",
        "CAPE (J/kg)": "cape",
        "Rüzgar (10m)": "windspeed_10m",
        "Rüzgar Hamlesi": "windgusts_10m",
        "Bağıl Nem (2m)": "relativehumidity_2m",
        "Bulutluluk (%)": "cloudcover",
        "Donma Seviyesi (m)": "freezinglevel_height",
        "Basınç": "pressure_msl"
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
def get_comparison_data(lat, lon):
    variables = "temperature_2m,temperature_850hPa,precipitation,windspeed_10m,pressure_msl,cloudcover,geopotential_height_500hPa"
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": variables,
        "models": "gfs_seamless,icon_seamless,gem_global", 
        "timezone": "auto"
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        return r.json()
    except: return None

if btn_calistir:
    zaman_damgasi = datetime.now().strftime("%Y-%m-%d_%H-%M")
    clean_loc = clean_filename(location_name)

    if calisma_modu == "📉 GFS Senaryoları (Diyagram)":
        if not secilen_veriler: st.error("Lütfen en az bir veri seçin.")
        else:
            with st.spinner(f'{location_name} için diyagramlar oluşturuluyor...'):
                data, mapping = get_ensemble_data(selected_lat, selected_lon, secilen_veriler)
                
                if data:
                    hourly = data['hourly']
                    time = pd.to_datetime(hourly['time'])
                    
                    for secim in secilen_veriler:
                        api_kod = mapping[secim]
                        fig = go.Figure()
                        cols = [k for k in hourly.keys() if k.startswith(api_kod) and 'member' in k]
                        
                        if cols:
                            df_m = pd.DataFrame(hourly)[cols]
                            if secim == "Kar Kalınlığı (cm)": df_m = df_m * 100
                            
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
                                
                                fig.add_trace(go.Scatter(x=time, y=df_m[member], mode='lines', line=dict(color=c, width=w), opacity=o, name=f"S-{mem_num}", showlegend=leg, hoverinfo=h))
                            
                            c_map = {"850hPa": "red", "500hPa": "#00BFFF", "2m": "orange", "Kar": "white", "Yağış": "cyan", "LI": "#DC143C"}
                            main_c = next((v for k, v in c_map.items() if k in secim), "cyan")
                            
                            h_txt = [f"📅 <b>{t.strftime('%d.%m %H:%M')}</b><br>🔺 Max: {mx:.1f} (S-{mxn})<br>⚪ Ort: {mn:.1f}<br>🔻 Min: {mi:.1f} (S-{minn})" for t, mx, mxn, mn, mi, minn in zip(time, max_val, max_mem, mean_val, min_val, min_mem)]
                            
                            fig.add_trace(go.Scatter(x=time, y=mean_val, mode='lines', line=dict(width=0), hovertemplate="%{text}<extra></extra>", text=h_txt, showlegend=False, name="Bilgi"))
                            fig.add_trace(go.Scatter(x=time, y=mean_val, mode='lines', line=dict(color=main_c, width=3.0), name="ORTALAMA", showlegend=False, hoverinfo='skip'))

                            if "Sıcaklık" in secim: fig.add_hline(y=0, line_dash="dash", line_color="orange", opacity=0.5)
                            if "Lifted Index" in secim: fig.add_hline(y=0, line_dash="solid", line_color="white", opacity=0.8)

                            fig.update_layout(
                                title=dict(text=f"{location_name} - {secim}", font=dict(size=14)),
                                template="plotly_dark", height=500,
                                margin=dict(l=2, r=2, t=30, b=5), 
                                hovermode="x unified", legend=dict(orientation="h", y=1, x=1)
                            )
                            fig = add_watermark(fig)
                            
                            clean_type = clean_filename(secim)
                            dosya_adi = f"{clean_loc}_{clean_type}_{zaman_damgasi}"
                            
                            st.plotly_chart(
                                fig, 
                                use_container_width=True,
                                config={
                                    'displayModeBar': True,
                                    'toImageButtonOptions': {
                                        'format': 'png',
                                        'filename': dosya_adi,
                                        'height': 720,
                                        'width': 1280,
                                        'scale': 2
                                    }
                                }
                            )
                else:
                    st.error("Veri alınamadı.")

    elif calisma_modu == "Model Kıyaslama (GFS vs ICON vs GEM)":
        with st.spinner(f'{location_name} için modeller kıyaslanıyor...'):
            veri = get_comparison_data(selected_lat, selected_lon)
            
            if veri and 'hourly' in veri:
                try:
                    hourly = veri['hourly']
                    zaman = pd.to_datetime(hourly['time'])
                    
                    secilen_bilgi = COMPARISON_MAP[savas_parametresi]
                    api_key = secilen_bilgi["api"]
                    unit = secilen_bilgi["unit"]
                
                    temp_gfs = hourly.get(f'{api_key}_gfs_seamless', [])
                    temp_icon = hourly.get(f'{api_key}_icon_seamless', [])
                    temp_gem = hourly.get(f'{api_key}_gem_global', [])
                    
                    fig = go.Figure()
                    
                    if temp_gfs:
                        fig.add_trace(go.Scatter(x=zaman, y=temp_gfs, mode='lines', name='GFS', line=dict(color='red', width=2)))
                    if temp_icon:
                        fig.add_trace(go.Scatter(x=zaman, y=temp_icon, mode='lines', name='ICON', line=dict(color='green', width=2)))
                    if temp_gem:
                        fig.add_trace(go.Scatter(x=zaman, y=temp_gem, mode='lines', name='GEM', line=dict(color='blue', width=3, dash='dash')))
                    
                    fig.update_layout(
                        title=dict(text=f"Model Kıyaslaması: {location_name} - {savas_parametresi}", font=dict(size=16)),
                        template="plotly_dark",
                        xaxis_title="Tarih",
                        yaxis_title=f"Değer ({unit})",
                        hovermode="x unified",
                        legend=dict(orientation="h", y=1.1),
                        height=600
                    )
                    fig = add_watermark(fig)
                    
                    clean_type = clean_filename(savas_parametresi)
                    dosya_adi = f"{clean_loc}_KIYASLAMA_{clean_type}_{zaman_damgasi}"
                    
                    st.plotly_chart(
                        fig, 
                        use_container_width=True,
                        config={
                            'displayModeBar': True,
                            'toImageButtonOptions': {
                                'format': 'png',
                                'filename': dosya_adi,
                                'height': 720,
                                'width': 1280,
                                'scale': 2
                            }
                        }
                    )
                    
                except Exception as e:
                    st.error(f"Grafik çizilirken hata oldu: {e}")
            else:
                st.error("Model verisi çekilemedi.")
    
    elif calisma_modu == "🌍 Küresel Endeksler (ENSO, NAO, vb.)":
        if secilen_endeks:
            url = INDEX_URLS[secilen_endeks]
            with st.spinner(f"{secilen_endeks} verisi NOAA sunucularından çekiliyor..."):
                df_index = get_climate_index(url)
                
                if df_index is not None and not df_index.empty:
                    # Seçilen yıla göre filtrele
                    start_date = datetime.now() - pd.DateOffset(years=yil_araligi)
                    df_filtered = df_index[df_index['Tarih'] >= start_date]
                    
                    if not df_filtered.empty:
                        son_veri = df_filtered.iloc[-1]
                        son_tarih = son_veri['Tarih'].strftime("%B %Y")
                        son_deger = son_veri['Değer']
                        
                        # Renklendirme
                        colors = ['#FF4B4B' if v >= 0 else '#1E90FF' for v in df_filtered['Değer']]
                        
                        fig = go.Figure()
                        fig.add_trace(go.Bar(
                            x=df_filtered['Tarih'], 
                            y=df_filtered['Değer'],
                            marker_color=colors,
                            name=secilen_endeks
                        ))
                        
                        fig.update_layout(
                            title=f"<b>{secilen_endeks}</b> - Son Durum: {son_deger} ({son_tarih})",
                            yaxis_title="Anomali / Değer",
                            template="plotly_dark",
                            height=500,
                            margin=dict(l=20, r=20, t=40, b=20)
                        )
                        fig.add_hline(y=0, line_color="white", line_width=1)
                        fig = add_watermark(fig)

                        # İndirme Ayarları
                        clean_type = clean_filename(secilen_endeks.split(" (")[0])
                        dosya_adi = f"KURESEL_ENDEKS_{clean_type}_{zaman_damgasi}"

                        st.plotly_chart(
                            fig, 
                            use_container_width=True,
                            config={
                                'displayModeBar': True,
                                'toImageButtonOptions': {
                                    'format': 'png',
                                    'filename': dosya_adi,
                                    'height': 720,
                                    'width': 1280,
                                    'scale': 2
                                }
                            }
                        )
                        
                        # Bilgi Kutuları
                        if "ENSO" in secilen_endeks:
                            st.info("ℹ️ **ENSO (Niño 3.4):** +0.5 üzeri **El Niño** (Isınma), -0.5 altı **La Niña** (Soğuma) fazıdır.")
                        elif "NAO" in secilen_endeks:
                            st.info("ℹ️ **NAO:** Negatif fazda kutup soğuklarının Avrupa/Türkiye hattına inme ihtimali artar.")
                        elif "IOD" in secilen_endeks:
                            st.info("ℹ️ **IOD:** Pozitif faz, Doğu Afrika ve Türkiye çevresinde yağış artışını destekleyebilir.")
                    else:
                        st.warning("Seçilen tarih aralığında veri bulunamadı.")
                else:
                    st.error("Veri çekilirken bir hata oluştu veya NOAA sunucusu yanıt vermiyor.")
