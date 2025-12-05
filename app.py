import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- Sayfa Ayarları ---
st.set_page_config(page_title="Forum Efsanesi v3 - Pro", layout="wide")

st.title("🌍 GFS Ultimate Analiz İstasyonu")
st.markdown("""
**Yerel veriler + Küresel Endeksler (AO/NAO).** Forumdaki 'Sistemci' arkadaşlara selam olsun.
""")

# --- Sidebar (Ayarlar) ---
with st.sidebar:
    st.header("📍 Konum Ayarları")
    lat = st.number_input("Enlem", value=41.00, format="%.4f")
    lon = st.number_input("Boylam", value=28.97, format="%.4f")
    
    st.divider()
    st.header("📊 Veri Seçimi")
    
    # Çoklu Seçim Kutusu (Multiselect)
    secilen_veriler = st.multiselect(
        "Grafiğe dökmek istediğin verileri seç:",
        [
            "Sıcaklık (2m)", "Sıcaklık (850hPa)", "Sıcaklık (500hPa)",
            "Kar Yağışı", "Toplam Yağış",
            "Rüzgar Hızı (10m)", "Rüzgar Hızı (850hPa)", "Jet Akımı (250hPa)",
            "MSL Basınç (Barometre)", 
            "CAPE (Oraj Enerjisi)", "Lifted Index",
            "Toplam Bulutluluk", "Toprak Nemi (0-10cm)"
        ],
        default=["Sıcaklık (850hPa)", "Kar Yağışı", "MSL Basınç (Barometre)"] # Varsayılanlar
    )

    st.divider()
    st.header("🌐 Teleconnections")
    show_teleconnections = st.checkbox("AO & NAO Endekslerini Göster", value=True)
    
    btn_calistir = st.button("Verileri Çek ve Analiz Et 🚀", type="primary")

# --- Yardımcı Fonksiyonlar ---

def get_local_data(lat, lon, variables):
    # Kullanıcının seçtiği Türkçe isimleri API parametrelerine çevirelim
    var_map = {
        "Sıcaklık (2m)": "temperature_2m",
        "Sıcaklık (850hPa)": "temperature_850hPa",
        "Sıcaklık (500hPa)": "temperature_500hPa",
        "Kar Yağışı": "snowfall",
        "Toplam Yağış": "precipitation",
        "Rüzgar Hızı (10m)": "windspeed_10m",
        "Rüzgar Hızı (850hPa)": "windspeed_850hPa",
        "Jet Akımı (250hPa)": "windspeed_250hPa",
        "MSL Basınç (Barometre)": "pressure_msl",
        "CAPE (Oraj Enerjisi)": "cape",
        "Lifted Index": "lifted_index",
        "Toplam Bulutluluk": "cloudcover",
        "Toprak Nemi (0-10cm)": "soil_moisture_0_to_10cm"
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
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json(), var_map
    except Exception as e:
        st.error(f"Yerel veri hatası: {e}")
        return None, None

def fetch_noaa_index(index_type="ao"):
    # NOAA CPC'den ham metin verisini çekip parse eder
    # index_type: 'ao', 'nao', 'pna'
    base_url = "https://www.cpc.ncep.noaa.gov/products/precip/CWlink"
    if index_type == "ao":
        url = f"{base_url}/daily_ao_index/ao.sprd2.dat"
    elif index_type == "nao":
        url = f"{base_url}/pna/nao.sprd2.dat"
    elif index_type == "pna":
        url = f"{base_url}/pna/pna.sprd2.dat"
    
    try:
        # Pandas ile boşlukla ayrılmış dosyayı okuyalım
        # NOAA formatı: YIL AY GÜN INDEX_DEĞERİ ...
        df = pd.read_csv(url, delim_whitespace=True, header=None, engine='python')
        
        # Son 120 günü alalım (Geçmiş + Gelecek tahminleri içerir)
        df = df.tail(120).reset_index(drop=True)
        
        # Tarih sütunu oluştur
        df['Date'] = pd.to_datetime(df[[0, 1, 2]].astype(str).agg('-'.join, axis=1), format='%Y-%m-%d')
        df.columns = ['Year', 'Month', 'Day', 'Index', 'Spread1', 'Spread2', 'Spread3', 'Date']
        
        return df
    except Exception as e:
        # NOAA bazen sunucuları kapatır veya format değiştirir
        return None

# --- ANA AKIŞ ---
if btn_calistir:
    
    # 1. YEREL VERİLERİ İŞLE
    with st.spinner('Model verileri işleniyor...'):
        data, mapping = get_local_data(lat, lon, secilen_veriler)
        
        if data:
            hourly = data['hourly']
            time = pd.to_datetime(hourly['time'])
            
            # Seçilen her veri türü için ayrı bir grafik çizelim
            st.subheader(f"📍 Yerel Analiz ({lat}, {lon})")
            
            for secim in secilen_veriler:
                api_kod = mapping[secim]
                fig = go.Figure()
                
                # İlgili senaryoları bul (member01, member02...)
                cols = [k for k in hourly.keys() if k.startswith(api_kod) and 'member' in k]
                
                # Spaghettileri ekle
                for member in cols:
                    fig.add_trace(go.Scatter(
                        x=time, y=hourly[member],
                        mode='lines', line=dict(color='gray', width=1),
                        opacity=0.3, showlegend=False, hoverinfo='skip'
                    ))
                
                # Ortalamayı ekle
                if cols:
                    df_m = pd.DataFrame(hourly)[cols]
                    mean_val = df_m.mean(axis=1)
                    fig.add_trace(go.Scatter(
                        x=time, y=mean_val,
                        mode='lines', line=dict(color='cyan', width=3),
                        name=f'Ortalama {secim}'
                    ))
                
                # Başlık ve birim ayarları
                fig.update_layout(
                    title=f"📈 {secim} Senaryoları",
                    template="plotly_dark",
                    height=350,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)

    # 2. TELECONNECTIONS (AO / NAO / PNA)
    if show_teleconnections:
        st.divider()
        st.subheader("🌐 Küresel Endeksler (NOAA CPC Canlı Veri)")
        st.markdown("Negatif AO/NAO genelde Akdeniz çanağına sistem inmesine yardımcı olur (Kışın). Pozitif indeksler yüksek basınç (blokaj) getirebilir.")
        
        col_ao, col_nao, col_pna = st.tabs(["Arctic Oscillation (AO)", "North Atlantic Oscillation (NAO)", "PNA"])
        
        # AO Grafiği
        with col_ao:
            df_ao = fetch_noaa_index("ao")
            if df_ao is not None:
                fig_ao = go.Figure()
                # Geçmiş veriyi ve tahmini ayıralım (Basit yaklaşım: Son tarih bugünden büyükse tahmindir)
                fig_ao.add_trace(go.Bar(
                    x=df_ao['Date'], y=df_ao['Index'],
                    marker_color=df_ao['Index'].apply(lambda x: 'red' if x < 0 else 'blue'),
                    name='AO Index'
                ))
                fig_ao.add_hline(y=0, line_color="white", line_width=1)
                fig_ao.update_layout(title="AO Endeksi (Kırmızı: Negatif/Soğuk Salınım İhtimali)", template="plotly_dark")
                st.plotly_chart(fig_ao, use_container_width=True)
            else:
                st.warning("NOAA sunucularından AO verisi çekilemedi. Geçici bir sorun olabilir.")

        # NAO Grafiği
        with col_nao:
            df_nao = fetch_noaa_index("nao")
            if df_nao is not None:
                fig_nao = go.Figure()
                fig_nao.add_trace(go.Bar(
                    x=df_nao['Date'], y=df_nao['Index'],
                    marker_color=df_nao['Index'].apply(lambda x: 'red' if x < 0 else 'blue'),
                    name='NAO Index'
                ))
                fig_nao.add_hline(y=0, line_color="white", line_width=1)
                fig_nao.update_layout(title="NAO Endeksi", template="plotly_dark")
                st.plotly_chart(fig_nao, use_container_width=True)
            else:
                st.warning("NOAA sunucularından NAO verisi çekilemedi.")
                
        # PNA Grafiği
        with col_pna:
             df_pna = fetch_noaa_index("pna")
             if df_pna is not None:
                fig_pna = go.Figure()
                fig_pna.add_trace(go.Bar(
                    x=df_pna['Date'], y=df_pna['Index'],
                    marker_color=df_pna['Index'].apply(lambda x: 'red' if x < 0 else 'blue'),
                     name='PNA Index'
                ))
                fig_pna.add_hline(y=0, line_color="white", line_width=1)
                fig_pna.update_layout(title="PNA Endeksi", template="plotly_dark")
                st.plotly_chart(fig_pna, use_container_width=True)
             else:
                st.warning("NOAA sunucularından PNA verisi çekilemedi.")

else:
    st.info("👈 Menüden verileri seç ve analizi başlat kanka.")
