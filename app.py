import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timezone, timedelta

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
    tr_map = str.maketrans("ığüşöçİĞÜŞÖÇ ", "igusocIGUSOC_")
    return text.translate(tr_map)

def get_run_info():
    now_utc = datetime.now(timezone.utc)
    hour = now_utc.hour
    minute = now_utc.minute
    current_minutes = hour * 60 + minute
    if current_minutes >= (3 * 60 + 30) and current_minutes < (9 * 60 + 30): return "00Z (Sabah)"
    elif current_minutes >= (9 * 60 + 30) and current_minutes < (15 * 60 + 30): return "06Z (Öğle)"
    elif current_minutes >= (15 * 60 + 30) and current_minutes < (21 * 60 + 30): return "12Z (Akşam)"
    else: return "18Z (Gece)"

@st.cache_data
def search_location(query):
    try:
        r = requests.get("https://geocoding-api.open-meteo.com/v1/search", params={"name": query, "count": 5, "language": "tr", "format": "json"}, timeout=5)
        r.raise_for_status()
        data = r.json()
        if "results" in data: return data["results"]
        return []
    except: return []

# --- NOAA VERİ ÇEKME ---
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
    except: return None

# --- MJO/GWO FAZ VERİSİ ÇEKME ---
@st.cache_data(ttl=3600)
def get_phase_data():
    # BOM (Avustralya) MJO Verisi - En temiz ve stabil kaynak
    url = "http://www.bom.gov.au/climate/mjo/graphics/rmm.74toRealtime.txt"
    try:
        r = requests.get(url, timeout=10)
        lines = r.text.split('\n')
        data = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 7 and parts[0].isdigit(): # Yıl ile başlayan satırlar
                try:
                    year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                    rmm1 = float(parts[3])
                    rmm2 = float(parts[4])
                    # 2024 ve sonrası verileri alalım (Performans için)
                    if year >= 2024:
                        date = datetime(year, month, day)
                        data.append({"Tarih": date, "RMM1": rmm1, "RMM2": rmm2})
                except: continue
        return pd.DataFrame(data)
    except: return None

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
                else: st.warning("Bulunamadı.")
            else: st.info("Aramak için yazın.")

    st.divider()

    # YENİ MOD: FAZ DİYAGRAMLARI EKLENDİ
    calisma_modu = st.radio("Analiz Modu Seçin:", [
        "📉 GFS Senaryoları (Diyagram)", 
        "Model Kıyaslama (GFS vs ICON vs GEM)",
        "🌍 Küresel Endeksler (ENSO, NAO, vb.)",
        "🌀 Faz Diyagramları (MJO / GWO)"
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
        "QBO": "https://psl.noaa.gov/data/correlation/qbo.data",
    }
    savas_parametresi = "Sıcaklık (2m)"
    secilen_endeks = "ENSO (Niño 3.4)"
    yil_araligi = 5
    faz_gun_sayisi = 40

    if calisma_modu == "📉 GFS Senaryoları (Diyagram)":
        secilen_veriler = st.multiselect("Diyagram Verileri:", ["Sıcaklık (850hPa)", "Sıcaklık (2m)", "Kar Yağışı (cm)", "Yağış (mm)", "Rüzgar (10m)", "Basınç"], default=["Sıcaklık (850hPa)", "Yağış (mm)"])
        vurgulu_senaryolar = st.multiselect("Senaryo Vurgula", options=range(0, 31))
    elif calisma_modu == "Model Kıyaslama (GFS vs ICON vs GEM)":
        savas_parametresi = st.selectbox("Veri Seçiniz...", list(COMPARISON_MAP.keys()))
    elif calisma_modu == "🌍 Küresel Endeksler (ENSO, NAO, vb.)":
        col_i1, col_i2 = st.columns([1,1])
        with col_i1: secilen_endeks = st.selectbox("Endeks Seçin:", list(INDEX_URLS.keys()))
        with col_i2: yil_araligi = st.slider("Son Kaç Yıl?", 1, 50, 5)
    elif calisma_modu == "🌀 Faz Diyagramları (MJO / GWO)":
        st.info("⚠️ GWO ham verisi şu an sunucularda stabil değil. Aşağıdaki grafik **MJO** verisidir ancak mantık (Phase Space) GWO ile birebir aynıdır.")
        faz_gun_sayisi = st.slider("Son Kaç Günün Hareketi Gösterilsin?", 10, 90, 40)

    st.caption(f"📅 Sistemdeki Run: **{get_run_info()}**")
    btn_calistir = st.button("ANALİZİ BAŞLAT", type="primary", use_container_width=True)

def add_watermark(fig):
    fig.add_annotation(text="Analiz: KeremPalancı", xref="paper", yref="paper", x=0.99, y=0.01, showarrow=False, font=dict(size=12, color="rgba(255, 255, 255, 0.5)", family="Arial"), bgcolor="rgba(0,0,0,0.5)", borderpad=4)
    return fig

@st.cache_data(ttl=3600)
def get_ensemble_data(lat, lon, variables):
    # (Önceki fonksiyonun aynısı - Yer kaplamasın diye kısalttım ama kodda tam olmalı)
    var_map = {"Sıcaklık (850hPa)": "temperature_850hPa", "Sıcaklık (2m)": "temperature_2m", "Kar Yağışı (cm)": "snowfall", "Yağış (mm)": "precipitation", "Rüzgar (10m)": "windspeed_10m", "Basınç": "pressure_msl"}
    api_vars = [var_map.get(v, "temperature_2m") for v in variables]
    try:
        r = requests.get("https://ensemble-api.open-meteo.com/v1/ensemble", params={"latitude": lat, "longitude": lon, "hourly": api_vars, "models": "gfs_seamless", "timezone": "auto"}, timeout=15)
        return r.json(), var_map
    except: return None, None

@st.cache_data(ttl=3600)
def get_comparison_data(lat, lon):
    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast", params={"latitude": lat, "longitude": lon, "hourly": "temperature_2m,temperature_850hPa,precipitation,windspeed_10m,pressure_msl,cloudcover,geopotential_height_500hPa", "models": "gfs_seamless,icon_seamless,gem_global", "timezone": "auto"}, timeout=10)
        return r.json()
    except: return None

if btn_calistir:
    zaman_damgasi = datetime.now().strftime("%Y-%m-%d_%H-%M")
    clean_loc = clean_filename(location_name)

    # --- 1. MOD: DİYAGRAM ---
    if calisma_modu == "📉 GFS Senaryoları (Diyagram)":
        if not secilen_veriler: st.error("Veri seçmedin.")
        else:
            with st.spinner('Diyagram çiziliyor...'):
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
                            if "Kar" in secim: df_m = df_m * 100
                            mean_val, max_val, min_val = df_m.mean(axis=1), df_m.max(axis=1), df_m.min(axis=1)
                            
                            for member in cols:
                                try: mem_num = int(member.split('member')[1])
                                except: mem_num = -1
                                c, w, o = 'lightgrey', 0.5, 0.4
                                if mem_num in vurgulu_senaryolar: c, w, o = '#FF1493', 2.0, 1.0
                                fig.add_trace(go.Scatter(x=time, y=df_m[member], mode='lines', line=dict(color=c, width=w), opacity=o, showlegend=False, hoverinfo='skip'))
                            
                            c_map = {"850hPa": "red", "2m": "orange", "Kar": "white", "Yağış": "cyan", "Basınç": "magenta"}
                            main_c = next((v for k, v in c_map.items() if k in secim), "cyan")
                            
                            h_txt = [f"📅 {t.strftime('%d.%m %H:%M')}<br>🔺 Max: {mx:.1f}<br>⚪ Ort: {mn:.1f}<br>🔻 Min: {mi:.1f}" for t, mx, mn, mi in zip(time, max_val, mean_val, min_val)]
                            fig.add_trace(go.Scatter(x=time, y=mean_val, mode='lines', width=0, hovertemplate="%{text}<extra></extra>", text=h_txt, showlegend=False))
                            fig.add_trace(go.Scatter(x=time, y=mean_val, mode='lines', line=dict(color=main_c, width=3.0), showlegend=False, hoverinfo='skip'))
                            
                            fig.update_layout(title=f"{location_name} - {secim}", template="plotly_dark", height=500, margin=dict(l=2, r=2, t=30, b=5), hovermode="x unified")
                            fig = add_watermark(fig)
                            st.plotly_chart(fig, use_container_width=True, config={'toImageButtonOptions': {'format': 'png', 'filename': f'{clean_loc}_{secim}_{zaman_damgasi}', 'height': 720, 'width': 1280, 'scale': 2}})
    
    # --- 2. MOD: KIYASLAMA ---
    elif calisma_modu == "Model Kıyaslama (GFS vs ICON vs GEM)":
        with st.spinner('Modeller kapıştırılıyor...'):
            veri = get_comparison_data(selected_lat, selected_lon)
            if veri and 'hourly' in veri:
                hourly = veri['hourly']
                zaman = pd.to_datetime(hourly['time'])
                info = COMPARISON_MAP[savas_parametresi]
                api_key, unit = info["api"], info["unit"]
                
                fig = go.Figure()
                for mod, c in [('gfs_seamless', 'red'), ('icon_seamless', 'green'), ('gem_global', 'blue')]:
                    if f'{api_key}_{mod}' in hourly:
                        fig.add_trace(go.Scatter(x=zaman, y=hourly[f'{api_key}_{mod}'], mode='lines', name=mod.split('_')[0].upper(), line=dict(color=c, width=2)))
                
                fig.update_layout(title=f"{location_name} - {savas_parametresi}", template="plotly_dark", height=500, hovermode="x unified", legend=dict(orientation="h", y=1.1))
                fig = add_watermark(fig)
                st.plotly_chart(fig, use_container_width=True, config={'toImageButtonOptions': {'format': 'png', 'filename': f'KIYAS_{clean_loc}_{zaman_damgasi}', 'scale': 2}})

    # --- 3. MOD: KÜRESEL ENDEKSLER ---
    elif calisma_modu == "🌍 Küresel Endeksler (ENSO, NAO, vb.)":
        with st.spinner('NOAA verileri çekiliyor...'):
            df = get_climate_index(INDEX_URLS[secilen_endeks])
            if df is not None:
                df = df[df['Tarih'] >= (datetime.now() - pd.DateOffset(years=yil_araligi))]
                colors = ['#FF4B4B' if v >= 0 else '#1E90FF' for v in df['Değer']]
                fig = go.Figure(go.Bar(x=df['Tarih'], y=df['Değer'], marker_color=colors))
                fig.update_layout(title=f"{secilen_endeks}", template="plotly_dark", height=500)
                fig.add_hline(y=0, line_color="white")
                fig = add_watermark(fig)
                st.plotly_chart(fig, use_container_width=True, config={'toImageButtonOptions': {'format': 'png', 'filename': f'ENDEKS_{secilen_endeks}_{zaman_damgasi}', 'scale': 2}})
            else: st.error("Veri çekilemedi.")

    # --- 4. MOD: FAZ DİYAGRAMLARI (MJO/GWO) ---
    elif calisma_modu == "🌀 Faz Diyagramları (MJO / GWO)":
        with st.spinner('Faz verileri işleniyor...'):
            df_phase = get_phase_data()
            if df_phase is not None:
                # Son N günü filtrele
                df_plot = df_phase.iloc[-faz_gun_sayisi:].reset_index(drop=True)
                
                fig = go.Figure()

                # Arkaplan Daireleri (Büyüklük = 1, 2, 3...)
                for r in [1, 2, 3]:
                    fig.add_shape(type="circle", xref="x", yref="y", x0=-r, y0=-r, x1=r, y1=r, line_color="grey", line_dash="dot", opacity=0.3)
                
                # Eksen Çizgileri
                fig.add_hline(y=0, line_color="white", opacity=0.2)
                fig.add_vline(x=0, line_color="white", opacity=0.2)

                # Bölge İsimleri (Annotations)
                regions = [
                    (1.5, -1.5, "Batı Pasifik"), (-1.5, -1.5, "Hint Okyanusu"),
                    (-1.5, 1.5, "Batı Yarıküre"), (1.5, 1.5, "Afrika")
                ]
                for x, y, text in regions:
                    fig.add_annotation(x=x, y=y, text=text, showarrow=False, font=dict(size=14, color="white"), opacity=0.5)

                # Renkli "Salyangoz" Çizgisi
                # Eskiden yeniye renk değişimi için Marker kullanıyoruz
                colors = np.linspace(0, 1, len(df_plot))
                
                # Çizgi (İnce)
                fig.add_trace(go.Scatter(
                    x=df_plot['RMM1'], y=df_plot['RMM2'],
                    mode='lines',
                    line=dict(color='grey', width=1),
                    hoverinfo='skip',
                    showlegend=False
                ))

                # Noktalar (Renkli)
                fig.add_trace(go.Scatter(
                    x=df_plot['RMM1'], y=df_plot['RMM2'],
                    mode='markers+text',
                    marker=dict(
                        size=10,
                        color=colors,
                        colorscale='Turbo', # Renk skalası (Mavi -> Kırmızı)
                        colorbar=dict(title="Zaman (Eski -> Yeni)")
                    ),
                    text=[d.strftime('%d %b') if i % 5 == 0 or i == len(df_plot)-1 else "" for i, d in enumerate(df_plot['Tarih'])],
                    textposition="top center",
                    textfont=dict(color="white", size=10),
                    name="Faz Hareketi",
                    hovertemplate="<b>Tarih:</b> %{text}<br>RMM1: %{x:.2f}<br>RMM2: %{y:.2f}<extra></extra>",
                    customdata=df_plot['Tarih'].dt.strftime('%d %B %Y')
                ))

                # Başlangıç ve Bitiş İşaretleri
                fig.add_annotation(x=df_plot['RMM1'].iloc[0], y=df_plot['RMM2'].iloc[0], text="BAŞLA", ax=20, ay=20, arrowcolor="white", font=dict(color="cyan"))
                fig.add_annotation(x=df_plot['RMM1'].iloc[-1], y=df_plot['RMM2'].iloc[-1], text="SON", ax=20, ay=20, arrowcolor="white", font=dict(color="red", size=15))

                fig.update_layout(
                    title=f"MJO Faz Diyagramı (Son {faz_gun_sayisi} Gün)",
                    xaxis=dict(title="RMM1", range=[-4, 4], zeroline=False),
                    yaxis=dict(title="RMM2", range=[-4, 4], zeroline=False),
                    width=700, height=700, # Kare format önemli
                    template="plotly_dark",
                    showlegend=False
                )
                fig = add_watermark(fig)
                
                st.plotly_chart(fig, use_container_width=True, config={'toImageButtonOptions': {'format': 'png', 'filename': f'MJO_PHASE_{zaman_damgasi}', 'scale': 2}})
            else:
                st.error("Faz verisi çekilemedi.")
