import streamlit as st
import pyproj
from pyproj import Transformer

# Aktivace přesných českých mřížek
pyproj.network.set_network_enabled(active=True)

st.title("🧮 Neomylný kalkulátor posunu")
st.info("Zadej souřadnice ze stejného fyzického bodu (např. z tvého křížku).")

# Transformátory
@st.cache_resource
def get_transformers():
    t_to_jtsk = Transformer.from_crs("EPSG:4937", "EPSG:5514+5705", always_xy=True)
    return t_to_jtsk

t_to_jtsk = get_transformers()

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Data z Roveru (Sitech)")
    y_sit = st.number_input("Y (S-JTSK, záporné)", value=-730744.000, format="%.3f", step=1.0)
    x_sit = st.number_input("X (S-JTSK, záporné)", value=-1045566.000, format="%.3f", step=1.0)

with col2:
    st.subheader("2. Data z Válce (Ammann)")
    lat_am = st.number_input("Latitude (WGS84)", value=49.2793000, format="%.7f", step=0.00001)
    lon_am = st.number_input("Longitude (WGS84)", value=17.0212000, format="%.7f", step=0.00001)

if st.button("Vypočítat korekční konstanty", type="primary"):
    # 1. Převod Ammann WGS84 na hrubý S-JTSK
    # (Výšku dáme průměrnou 250m, pro polohu to udělá rozdíl v desetinách milimetru, takže je to jedno)
    y_am, x_am, _ = t_to_jtsk.transform(lon_am, lat_am, 250.0)
    
    # 2. Výpočet čistého rozdílu
    delta_y = y_sit - y_am
    delta_x = x_sit - x_am
    
    st.success("✅ Hotovo. Tyto hodnoty zadej do svých hlavních programů.")
    col3, col4 = st.columns(2)
    col3.metric("KOREKCE Y", f"{delta_y:+.3f} m")
    col4.metric("KOREKCE X", f"{delta_x:+.3f} m")
