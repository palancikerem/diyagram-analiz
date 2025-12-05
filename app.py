import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timezone

# --- Sayfa Ayarları ---
st.set_page_config(
    page_title="GFS Şehir Analiz", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- CSS (Mobil Uyum) ---
st.markdown("""
    <style>
        .block-container { padding-top: 1rem; padding-bottom: 0rem; padding-left: 1rem; padding-right: 1rem; }
        h1 { font-size: 1.5rem !important; }
    </style>
""", unsafe_allow_html=True)

st.title("🇹🇷 GFS Şehir Bazlı Analiz")
st.markdown("İl seç, arkana yaslan, GFS modelini yorumla.")

# --- 81 İL KOORDİNAT LİSTESİ ---
TR_ILLER = {
    "Adana": [37.00, 35.32], "Adıyaman": [37.76, 38.28], "Afyonkarahisar": [38.75, 30.54],
    "Ağrı": [39.72, 43.05], "Aksaray": [38.37, 34.03], "Amasya": [40.65, 35.83],
    "Ankara": [39.93, 32.85], "Antalya": [36.89, 30.71], "Ardahan": [41.11, 42.70],
    "Artvin": [41.18, 41.82], "Aydın": [37.84, 27.84], "Balıkesir": [39.65, 27.88],
    "Bartın": [41.63, 32.34], "Batman": [37.88, 41.13], "Bayburt": [40.26, 40.22],
    "Bilecik": [40.14, 29.98], "Bingöl": [38.88, 40.49], "Bitlis": [38.40, 42.10],
    "Bolu": [40.73, 31.61], "Burdur": [37.72, 30.29], "Bursa": [40.18, 29.06],
    "Çanakkale": [40.15, 26.41], "Çankırı": [40.60, 33.61], "Çorum": [40.55, 34.95],
    "Denizli": [37.77, 29.09], "Diyarbakır": [37.91, 40.24], "Düzce": [40.84, 31.16],
    "Edirne": [41.68, 26.56], "Elazığ": [38.68, 39.22], "Erzincan": [39.75, 39.50],
    "Erzurum": [39.90, 41.27], "Eskişehir": [39.78, 30.52], "Gaziantep": [37.06, 37.38],
    "Giresun": [40.91, 38.39], "Gümüşhane": [40.46, 39.48], "Hakkari": [37.58, 43.74],
    "Hatay": [36.40, 36.34], "Iğdır": [39.92, 44.04], "Isparta": [37.76, 30.56],
    "İstanbul": [41.00, 28.97], "İzmir": [38.42, 27.14], "Kahramanmaraş": [37.58, 36.93],
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

# --- GFS GÜNCELLEME TAHMİNİ ---
def get_gfs_run_info():
    # Şu anki UTC saati al
    now_utc = datetime.now(timezone.utc)
    hour = now_utc.hour
    
    # GFS döngüleri: 00, 06, 12, 18 UTC
    # Verinin işlenip API'ye düşmesi genelde 3-4 saat sürer.
    if 3 <= hour < 9:
        run = "00Z (Gece Güncellemesi)"
    elif 9 <= hour < 15:
        run = "06Z (Sabah Güncellemesi)"
    elif 15 <= hour < 21:
        run = "12Z (Öğle Güncellemesi)"
    else:
        run = "18Z (Akşam Güncellemesi)"
    
    return run

# --- KONUM VE AYARLAR ---
with st.expander("📍 Şehir Seçimi ve Ayarlar", expanded=True):
    # Sekmeli Yapı: İster listeden seç, ister manuel gir
    tab_sehir, tab_manuel = st.tabs(["🏙️ İl Listesi", "🗺️ Manuel Koordinat"])
    
    with tab_sehir:
        secilen_il = st.selectbox("Bir İl Seç:", list(TR_ILLER.keys()), index=38) # 38: İstanbul
        lat_il, lon_il = TR_ILLER[secilen_il]
    
    with tab_manuel:
        col1, col2 = st.columns(2)
        lat_man = col1.number_input("Enlem", value=41.00)
        lon_man = col2.number_input("Boylam", value=28.97)

    # Hangi koordinatı kullanacağız?
    if lat_man != 41.00 or lon_man != 28.97:
        final_lat, final_lon = lat_man, lon_man
        konum_adi = f"Manuel ({final_lat}, {final_lon})"
    else:
        final_lat, final_lon = lat_il, lon_il
        konum_adi = secilen_il

    secilen_veriler = st.multiselect(
        "Grafikler:",
        [
            "Sıcaklık (850hPa)", "Kar Yağışı (cm)", "Yağış (mm)",
            "Sıcaklık (2m)", "Rüzgar (Yerde)", "CAPE (Oraj)", "Basınç"
        ],
        default=["Sıcaklık (850hPa)", "Kar Yağışı (cm)"]
    )
    
    # GÜNCELLEME BİLGİSİ
    run_info = get_gfs_run_info()
    st.info(f"🕒 **Tahmini Model Çıktısı:** {run_info} | GFS Seamless")
    
    btn_calistir = st.button("Analizi Başlat 🚀", type="primary", use_container_width=True)

# --- FONSİYONLAR ---
def get_local_data(lat, lon, variables):
    var_map = {
        "Sıcaklık (850hPa)": "temperature_850hPa",
        "Kar Yağışı (cm)": "snowfall",
        "Yağış (mm)": "precipitation",
        "Sıcaklık (2m)": "temperature_2m",
        "Rüzgar (Yerde)": "windspeed_10m",
        "CAPE (Oraj)": "cape",
        "Basınç": "pressure_msl"
    }
    api_vars = [var_map[v] for v in variables]
    
    url = "https://ensemble-api.open-meteo.com/v1/ensemble"
    params = {
        "latitude": lat, "longitude": lon,
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

# --- ANA İŞLEM ---
if btn_calistir:
    if not secilen_veriler:
        st.error("Grafik seçimi yapmalısın.")
    else:
        with st.spinner(f'{konum_adi} için GFS verileri çekiliyor...'):
            data, mapping = get_local_data(final_lat, final_lon, secilen_veriler)
            
            if data:
                hourly = data['hourly']
                time = pd.to_datetime(hourly['time'])
                
                for secim in secilen_veriler:
                    api_kod = mapping[secim]
                    fig = go.Figure()
                    cols = [k for k in hourly.keys() if k.startswith(api_kod) and 'member' in k]
                    
                    # Senaryolar
                    for member in cols:
                        fig.add_trace(go.Scatter(
                            x=time, y=hourly[member],
                            mode='lines', line=dict(color='lightgrey', width=0.5),
                            opacity=0.5, showlegend=False, hoverinfo='skip'
                        ))
                    
                    # Ortalama
                    if cols:
                        df_m = pd.DataFrame(hourly)[cols]
                        mean_val = df_m.mean(axis=1)
                        c = 'cyan'
                        if "Sıcaklık" in secim: c = 'orange'
                        elif "Kar" in secim: c = 'white'
                        elif "CAPE" in secim: c = 'yellow'
                        
                        fig.add_trace(go.Scatter(
                            x=time, y=mean_val,
                            mode='lines', line=dict(color=c, width=2.5),
                            name='Ortalama'
                        ))
                    
                    # Kritik Çizgiler
                    if "850hPa" in secim:
                         fig.add_hline(y=-8, line_dash="dash", line_color="blue", opacity=0.5)

                    fig.update_layout(
                        title=dict(text=f"{secim} - {konum_adi}", font=dict(size=14)),
                        template="plotly_dark", height=300,
                        margin=dict(l=10, r=10, t=40, b=10),
                        hovermode="x unified", showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'staticPlot': False})
            else:
                st.error("Sunucu hatası, tekrar dene.")
