import streamlit as st
import pandas as pd
import numpy as np
from pyproj import Geod
import io

st.title("🎯 Kalibrátor Ammann (Export na křížky)")

# 1. NAHRÁNÍ
uploaded_file = st.file_uploader("CSV z válce", type=['csv'])
offset_m = st.number_input("Podélný offset (m) - anténa za běhounem", value=2.0)
offset_transverse_m = st.number_input("Příčný offset (m) - (-0.2 = vlevo)", value=-0.2)

if uploaded_file:
    # Načtení (bez filtrace rychlosti!)
    df = pd.read_csv(uploaded_file, sep=None, engine='python')
    df.columns = df.columns.str.strip()
    
    # Detekce sloupce času a pozice
    lat_col = [c for c in df.columns if 'lat' in c.lower()][0]
    lon_col = [c for c in df.columns if 'lon' in c.lower()][0]
    time_col = [c for c in df.columns if 'time' in c.lower()][0]
    dir_col = [c for c in df.columns if 'dir' in c.lower()][0]
    
    geod = Geod(ellps="WGS84")
    
    # Výpočet azimutu z pojezdu před zastavením
    # Potřebujeme posunout anténu na běhoun
    # Pokud jsi jel 20m, azimut z jízdy je stabilní
    
    # Jednoduchý výpočet směru z předchozího bodu
    df['lat_prev'] = df[lat_col].shift(1)
    df['lon_prev'] = df[lon_col].shift(1)
    
    def get_azimuth(row):
        _, az, _ = geod.inv(row['lon_prev'], row['lat_prev'], row[lon_col], row[lat_col])
        return az

    df['azimuth'] = df.apply(get_azimuth, axis=1)
    
    # Aplikace tvé geometrie (Anténa -> Běhoun)
    # 1. Podélný posun
    lons_mid, lats_mid, _ = geod.fwd(df[lon_col], df[lat_col], df['azimuth'], np.full(len(df), offset_m))
    # 2. Příčný posun
    df['final_lon'], df['final_lat'], _ = geod.fwd(lons_mid, lats_mid, (df['azimuth'] + 90) % 360, np.full(len(df), offset_transverse_m))
    
    st.subheader("Vyberte bod, kdy jsi stál na křížku")
    st.dataframe(df[[time_col, 'final_lat', 'final_lon']])
    
    idx = st.number_input("Index řádku, kde jsi byl na křížku:", min_value=0, max_value=len(df)-1)
    
    st.subheader("Zadejte Sitech souřadnice")
    y_sit = st.number_input("Sitech Y", format="%.3f")
    x_sit = st.number_input("Sitech X", format="%.3f")
    
    if st.button("Vypočítat korekční vektor"):
        from pyproj import Transformer
        t = Transformer.from_crs("EPSG:4326", "EPSG:5514", always_xy=True)
        y_am, x_am = t.transform(df.loc[idx, 'final_lon'], df.loc[idx, 'final_lat'])
        
        st.metric("Delta Y (m)", f"{y_sit - y_am:.3f}")
        st.metric("Delta X (m)", f"{x_sit - x_am:.3f}")
