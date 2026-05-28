import streamlit as st
from pyproj import Transformer

st.title("🧮 Kalkulátor posunu (Opraveno)")
st.info("Ořezáno čistě na 2D (bez výšek), aby nepadal výpočet.")

# Převedeme Křováka 2D rovnou do GPS 2D (WGS84). 
# Žádné složité mřížky, takže žádné -inf.
@st.cache_resource
def get_transformer():
    return Transformer.from_crs("EPSG:5514", "EPSG:4326", always_xy=True)

t_to_gps = get_transformer()

col1, col2 = st.columns(2)
with col1:
    st.subheader("1. Křížek ze Sitechu")
    y_sit = st.number_input("Y (Záporné)", value=-730744.000, format="%.3f")
    x_sit = st.number_input("X (Záporné)", value=-1045566.000, format="%.3f")

with col2:
    st.subheader("2. Křížek z Válce")
    lat_am = st.number_input("Latitude", value=49.2793000, format="%.7f")
    lon_am = st.number_input("Longitude", value=17.0212000, format="%.7f")

if st.button("Vypočítat posun ve stupních", type="primary"):
    # Transformace pouze X a Y (bez výšky)
    lon_sit, lat_sit = t_to_gps.transform(y_sit, x_sit)
    
    # Výpočet rozdílu
    delta_lat = lat_sit - lat_am
    delta_lon = lon_sit - lon_am
    
    st.success("✅ Vypočítáno.")
    col3, col4 = st.columns(2)
    col3.metric("Korekce Latitude", f"{delta_lat:+.8f}")
    col4.metric("Korekce Longitude", f"{delta_lon:+.8f}")
