import streamlit as st
import pandas as pd
import pyproj
from pyproj import Transformer
import io

# Zapnutí sítě pro přesný převod (nutné pro ETRS89 <-> S-JTSK)
pyproj.network.set_network_enabled(active=True)

st.title("🎯 Kalibrátor: Ammann ↔ Sitech")
st.markdown("Nástroj pro nalezení offsetu z 'vibrační pasti' na křížku.")

# Inicializace transformátoru z ETRS89(GPS) do S-JTSK
@st.cache_resource
def get_transformer():
    return Transformer.from_crs("EPSG:4937", "EPSG:5514+5705", always_xy=True)

transformer = get_transformer()

col1, col2 = st.columns(2)
with col1:
    st.subheader("1. Data z Roveru (Sitech)")
    sitech_y = st.number_input("Y (Záporné)", value=-730744.68, format="%.3f")
    sitech_x = st.number_input("X (Záporné)", value=-1045566.67, format="%.3f")

with col2:
    st.subheader("2. CSV z válce")
    uploaded_file = st.file_uploader("Nahraj kalibrační jízdu", type=['csv'])

if uploaded_file is not None:
    # Rychlé načtení (využijeme tvoji logiku z předchozího kódu)
    sample_text = uploaded_file.getvalue()[:5000].decode("utf-8", errors="ignore")
    lines = sample_text.splitlines()
    header_idx = next((i for i, line in enumerate(lines) if "latitude" in line.lower() or "time" in line.lower()), 0)
    sep = ';' if lines[header_idx].count(';') > lines[header_idx].count(',') else ','
    
    df = pd.read_csv(io.BytesIO(uploaded_file.getvalue()), sep=sep, skiprows=header_idx, on_bad_lines='skip', dtype=str)
    df.columns = df.columns.str.strip().str.replace('"', '').str.replace("'", "")
    
    # Hledání správných sloupců
    col_lat = next((c for c in df.columns if 'lat' in c.lower()), None)
    col_lon = next((c for c in df.columns if 'lon' in c.lower()), None)
    col_vib = next((c for c in df.columns if any(x in c.lower() for x in ['amp', 'freq', 'vib'])), None)
    col_time = next((c for c in df.columns if 'time' in c.lower()), None)

    if all([col_lat, col_lon, col_vib, col_time]):
        df[col_lat] = pd.to_numeric(df[col_lat].astype(str).str.replace(',', '.'), errors='coerce')
        df[col_lon] = pd.to_numeric(df[col_lon].astype(str).str.replace(',', '.'), errors='coerce')
        df[col_vib] = pd.to_numeric(df[col_vib].astype(str).str.replace(',', '.'), errors='coerce')
        df['parsed_time'] = pd.to_datetime(df[col_time].astype(str).str.split(' GMT').str[0], errors='coerce')
        
        df = df.dropna(subset=[col_lat, col_lon, 'parsed_time']).sort_values('parsed_time').reset_index(drop=True)
        
        # Filtrujeme pouze vibrující body
        df_vib = df[df[col_vib] > 0.1]
        
        if not df_vib.empty:
            # Vezmeme posledních 5 vteřin vibrace (to je ten moment stání na křížku)
            end_time = df_vib['parsed_time'].max()
            start_time = end_time - pd.Timedelta(seconds=5)
            last_cluster = df_vib[df_vib['parsed_time'] >= start_time]
            
            # Zprůměrujeme WGS84 souřadnice pro vyhlazení šumu GPS
            avg_lon = last_cluster[col_lon].mean()
            avg_lat = last_cluster[col_lat].mean()
            
            # Převod Ammann GPS na hrubý S-JTSK
            am_y, am_x, _ = transformer.transform(avg_lon, avg_lat, 250.0)
            
            # Výpočet DELTY (posunu)
            delta_y = sitech_y - am_y
            delta_x = sitech_x - am_x
            
            st.success("✅ Nalezena vibrační past na křížku!")
            st.markdown(f"**Čas zastavení vibrace:** `{end_time}`")
            
            st.warning("🚨 **TOTO ZADEJ DO HLAVNÍ APLIKACE** 🚨")
            st.metric("Korekce Y (Delta Y)", f"{delta_y:+.3f} m")
            st.metric("Korekce X (Delta X)", f"{delta_x:+.3f} m")
            
            st.info("Logika: K převedeným S-JTSK souřadnicím z válce se musí PŘIČÍST tyto hodnoty, aby seděly na Sitech projekt.")
            
        else:
            st.error("V datech nebyla nalezena žádná vibrace. Nezapnul ji!")
    else:
        st.error("Nepodařilo se najít potřebné sloupce (Lat, Lon, Vib, Time).")