import streamlit as st
from pyproj import Geod, Transformer

st.title("🧮 Ultimátní Kalibrátor (s posunem antény na běhoun)")
st.info("Aplikuje tvou vlastní Geod logiku přímo na manuálně zadaný bod z kabiny.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Křížek ze Sitechu (S-JTSK)")
    y_sit = st.number_input("Y (Záporné)", value=-730744.00, format="%.2f")
    x_sit = st.number_input("X (Záporné)", value=-1045566.00, format="%.2f")

with col2:
    st.subheader("2. Data z kabiny Ammann (GPS)")
    lat_am = st.number_input("Latitude (Anténa z CSV)", value=49.2793000, format="%.7f")
    lon_am = st.number_input("Longitude (Anténa z CSV)", value=17.0212000, format="%.7f")
    # Musíš zadat směr, kterým válec na křížku zrovna stál, aby se ty 2 metry hodily správným směrem
    azimut = st.number_input("Azimut jízdy (0=S, 90=V, 180=J, 270=Z)", value=90.0, step=1.0)

st.subheader("3. Parametry stroje (jako v hlavním kódu)")
col3, col4 = st.columns(2)
with col3:
    offset_m = st.number_input("Podélný posun anténa -> běhoun (m)", value=2.0, step=0.1)
with col4:
    offset_transverse_m = st.number_input("Příčný posun (m)", value=0.20, step=0.05)

if st.button("Vypočítat finální posun (v metrech)", type="primary"):
    geod = Geod(ellps="WGS84")
    
    # --- TVOJE GEOMETRICKÁ LOGIKA ---
    # 1. Podélný posun
    mid_lon, mid_lat, _ = geod.fwd(lon_am, lat_am, azimut, offset_m)
    # 2. Příčný posun (+90 stupňů doprava)
    drum_lon, drum_lat, _ = geod.fwd(mid_lon, mid_lat, (azimut + 90) % 360, offset_transverse_m)
    
    # --- BEZPEČNÝ PŘEVOD DO 2D KŘOVÁKA ---
    t_to_jtsk = Transformer.from_crs("EPSG:4326", "EPSG:5514", always_xy=True)
    y_am, x_am = t_to_jtsk.transform(drum_lon, drum_lat)
    
    # --- VÝPOČET ROZDÍLU ---
    delta_y = y_sit - y_am
    delta_x = x_sit - x_am
    
    st.success("✅ Vypočítáno! Geometrie stroje zohledněna.")
    res1, res2 = st.columns(2)
    res1.metric("Finální Korekce Y", f"{delta_y:+.3f} m")
    res2.metric("Finální Korekce X", f"{delta_x:+.3f} m")
