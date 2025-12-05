import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timezone, timedelta
import os
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np

import os

# Klasör adın kodda tam olarak neyse onu yaz (gfs_analiz mi?)
klasor_adi = 'gfs_analiz'

if not os.path.exists(klasor_adi):
    os.makedirs(klasor_adi)
    print(f"{klasor_adi} klasörü oluşturuldu.")
# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="GFS Analiz Pro", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- CSS VE STİL ---
st.markdown("""
    <style>
        .block-container { padding-top: 1rem; padding-bottom: 0rem; }
        h1 { font-size: 1.5rem !important; }
        .stSelectbox { margin-bottom: 0px; }
    </style>
""", unsafe_allow_html=True)

st.title("GFS Analiz Merkezi")

# --- SABİTLER ---
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

HARITA_KLASOR = "haritalar"
if not os.path.exists(HARITA_KLASOR):
    os.makedirs(HARITA_KLASOR)

# --- YARDIMCI FONKSİYONLAR ---
def get_gfs_run_info():
    now_utc = datetime.now(timezone.utc)
    hour = now_utc.hour
    if 3 <= hour < 9: return "00Z"
    elif 9 <= hour < 15: return "06Z"
    elif 15 <= hour < 21: return "12Z"
    else: return "18Z"

def get_nomads_info():
    """Nomads sunucusu için tarih ve run bilgisini döndürür"""
    simdi = datetime.utcnow()
    if simdi.hour < 4: run = "18"; tarih = simdi - timedelta(days=1)
    elif simdi.hour < 10: run = "00"; tarih = simdi
    elif simdi.hour < 16: run = "06"; tarih = simdi
    else: run = "12"; tarih = simdi
    return tarih.strftime("%Y%m%d"), run

# --- HARİTA OLUŞTURMA FONKSİYONU ---
def haritalari_olustur():
    tarih, run = get_nomads_info()
    progress_bar = st.progress(0, text="Veri indirme başlıyor...")
    status_text = st.empty()
    
    # Şimdilik örnek olarak 72 saate kadar 6 saat arayla indirelim (Hız testi için)
    # İstersen 240 yapabilirsin: range(0, 241, 6)
    saat_araligi = range(0, 241, 6) 
    total_steps = len(saat_araligi)
    
    for i, saat in enumerate(saat_araligi):
        saat_str = f"{saat:03d}"
        status_text.text(f"İşleniyor: {saat}. Saat (GFS {run})")
        
        # URL
        url = (
            f"https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?"
            f"file=gfs.t{run}z.pgrb2.0p25.f{saat_str}&"
            f"lev_850_mb=on&var_TMP=on&"
            f"lev_surface=on&var_APCP=on&"
            f"subregion=&leftlon=20&rightlon=50&toplat=45&bottomlat=30&"
            f"dir=%2Fgfs.{tarih}%2F{run}%2Fatmos"
        )
        
        dosya_adi = f"temp_gfs_{saat_str}.grib2"
        
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                with open(dosya_adi, 'wb') as f:
                    f.write(r.content)
                
                # --- ÇİZİM: SICAKLIK ---
                try:
                    ds = xr.open_dataset(dosya_adi, engine='cfgrib', backend_kwargs={'filter_by_keys': {'shortName': 't'}})
                    t = ds['t'] - 273.15
                    
                    fig = plt.figure(figsize=(10, 6))
                    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
                    ax.add_feature(cfeature.COASTLINE); ax.add_feature(cfeature.BORDERS, linestyle=':')
                    ax.set_extent([25, 46, 35, 43], crs=ccrs.PlateCarree())
                    
                    t.plot.contourf(ax=ax, transform=ccrs.PlateCarree(), levels=np.arange(-15, 30, 2), 
                                    cmap='jet', cbar_kwargs={'label': 'Sıcaklık (°C)'})
                    plt.title(f"850hPa Sıcaklık | +{saat} Saat")
                    plt.savefig(f"{HARITA_KLASOR}/sicaklik_{saat_str}.png", bbox_inches='tight', dpi=90)
                    plt.close()
                    ds.close()
                except Exception as e:
                    print(f"Sıcaklık hatası: {e}")

                # --- ÇİZİM: YAĞIŞ ---
                try:
                    ds_rain = xr.open_dataset(dosya_adi, engine='cfgrib', backend_kwargs={'filter_by_keys': {'shortName': 'tp'}})
                    p = ds_rain['tp']
                    fig = plt.figure(figsize=(10, 6))
                    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
                    ax.add_feature(cfeature.COASTLINE); ax.add_feature(cfeature.BORDERS, linestyle=':')
                    ax.set_extent([25, 46, 35, 43], crs=ccrs.PlateCarree())
                    
                    levels = [0.1, 1, 2, 5, 10, 20, 50, 100]
                    p.plot.contourf(ax=ax, transform=ccrs.PlateCarree(), levels=levels, 
                                    cmap='BuPu', cbar_kwargs={'label': 'Yağış (mm)'})
                    plt.title(f"Toplam Yağış | +{saat} Saat")
                    plt.savefig(f"{HARITA_KLASOR}/yagis_{saat_str}.png", bbox_inches='tight', dpi=90)
                    plt.close()
                    ds_rain.close()
                except:
                    pass # Yağış yoksa geç

                os.remove(dosya_adi)
            
            progress_bar.progress((i + 1) / total_steps)
            
        except Exception as e:
            st.error(f"Hata oluştu: {e}")
            
    status_text.success("Haritalar güncellendi!")
    progress_bar.empty()

# --- DİYAGRAM VERİSİ ÇEKME ---
def get_local_data(lat, lon, variables):
    var_map = {
        "Sıcaklık (850hPa)": "temperature_850hPa",
        "Sıcaklık (500hPa)": "temperature_500hPa", 
        "Sıcaklık (2m)": "temperature_2m",
        "Dewpoint (2m)": "dewpoint_2m",            
        "Kar Yağışı (cm)": "snowfall",
        "Yağış (mm)": "precipitation",
        "Rüzgar (10m)": "windspeed_10m",
        "CAPE": "cape",
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

# ================= ARAYÜZ YAPISI =================

tab1, tab2 = st.tabs(["📊 Diyagramlar", "🗺️ Haritalar"])

# --- TAB 1: DİYAGRAMLAR (Eski Kodun) ---
with tab1:
    with st.expander("Konum / Veri Seçimi", expanded=True):
        col_list, col_man = st.columns(2)
        with col_list:
            secilen_il = st.selectbox("İl Seç:", list(TR_ILLER.keys()), index=38) 
            lat_il, lon_il = TR_ILLER[secilen_il]
        
        with col_man:
            st.write("Veya Manuel Gir:")
            c1, c2 = st.columns(2)
            lat_man = c1.number_input("Enlem", value=41.00)
            lon_man = c2.number_input("Boylam", value=28.97)

        if lat_man != 41.00 or lon_man != 28.97:
            final_lat, final_lon = lat_man, lon_man
            konum_adi = f"K: {final_lat},{final_lon}"
        else:
            final_lat, final_lon = lat_il, lon_il
            konum_adi = secilen_il

        secilen_veriler = st.multiselect(
            "Veriler:",
            [ "Sıcaklık (850hPa)", "Sıcaklık (500hPa)", "Sıcaklık (2m)", "Dewpoint (2m)",        
              "Kar Yağışı (cm)", "Yağış (mm)", "Rüzgar (10m)", "CAPE", "Basınç"],
            default=["Sıcaklık (850hPa)", "Kar Yağışı (cm)"]
        )
        
        btn_diyagram = st.button("Diyagramı Çiz", type="primary")

    if btn_diyagram:
        if not secilen_veriler:
            st.error("Lütfen en az bir veri seç.")
        else:
            with st.spinner('Open-Meteo verisi çekiliyor...'):
                data, mapping = get_local_data(final_lat, final_lon, secilen_veriler)
                
                if data:
                    hourly = data['hourly']
                    time = pd.to_datetime(hourly['time'])
                    
                    for secim in secilen_veriler:
                        api_kod = mapping[secim]
                        fig = go.Figure()
                        cols = [k for k in hourly.keys() if k.startswith(api_kod) and 'member' in k]
                        
                        # Senaryolar (Gri çizgiler)
                        for member in cols:
                            fig.add_trace(go.Scatter(
                                x=time, y=hourly[member],
                                mode='lines', line=dict(color='lightgrey', width=0.5),
                                opacity=0.5, showlegend=False, hoverinfo='skip'
                            ))
                        
                        # Ortalama (Renkli çizgi)
                        if cols:
                            df_m = pd.DataFrame(hourly)[cols]
                            mean_val = df_m.mean(axis=1)
                            
                            c = 'cyan'
                            if "Sıcaklık (2m)" in secim: c = 'orange'
                            elif "850hPa" in secim: c = 'red'
                            elif "500hPa" in secim: c = 'purple' 
                            elif "Dewpoint" in secim: c = 'lime'
                            elif "Kar" in secim: c = 'white'
                            elif "CAPE" in secim: c = 'yellow'
                            
                            fig.add_trace(go.Scatter(
                                x=time, y=mean_val,
                                mode='lines', line=dict(color=c, width=2.5),
                                name='Ortalama'
                            ))
                        
                        if "850hPa" in secim:
                             fig.add_hline(y=-8, line_dash="dash", line_color="blue", opacity=0.5)

                        fig.update_layout(
                            title=dict(text=f"{secim} - {konum_adi}", font=dict(size=14)),
                            template="plotly_dark", height=300,
                            margin=dict(l=10, r=10, t=30, b=10),
                            hovermode="x unified", showlegend=False
                        )
                        st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: HARİTALAR (Yeni Eklenen Kısım) ---
with tab2:
    st.info("⚠️ Haritalar anlık olarak NOAA sunucusundan indirilir. 'Güncelle' butonu veriyi yeniler (3-5 dk sürebilir).")
    
    col_btn, col_info = st.columns([1, 2])
    with col_btn:
        if st.button("Haritaları İndir ve Güncelle", type="primary"):
            haritalari_olustur()
    
    st.divider()
    
    # Harita Gösterici
    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        harita_tipi = st.radio("Harita Tipi:", ["Sıcaklık (850hPa)", "Yağış"], horizontal=True)
        dosya_on_ek = "sicaklik" if "Sıcaklık" in harita_tipi else "yagis"
        
    with col_opt2:
        # 0'dan 240'a 6'şar saat atlayan slider
        secilen_saat = st.select_slider("Vade (Saat):", options=range(0, 241, 6))
        saat_str = f"{secilen_saat:03d}"

    # Resim Yolu
    resim_yolu = f"{HARITA_KLASOR}/{dosya_on_ek}_{saat_str}.png"
    import os
st.write("Mevcut dosyalar:", os.listdir('.')) # Ana dizindeki dosyaları gösterir
if os.path.exists('gfs_analiz'):
    st.write("GFS Klasörü içindekiler:", os.listdir('gfs_analiz'))
else:
    st.error("GFS Analiz klasörü hiç oluşmamış!")
    if os.path.exists(resim_yolu):
        st.image(resim_yolu, caption=f"GFS {harita_tipi} - Vade: +{secilen_saat} Saat", use_container_width=True)
    else:
        st.warning(f"Bu saat için harita bulunamadı ({secilen_saat}. saat). Lütfen 'Haritaları Güncelle' butonuna basın.")
