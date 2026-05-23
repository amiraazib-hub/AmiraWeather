import streamlit as st
import requests
from streamlit_lottie import st_lottie
from engine import WeatherEngine
from gtts import gTTS
from streamlit_folium import st_folium
import folium
import io
import math
from PIL import Image

# 1. Page Config
st.set_page_config(page_title="Amira Weather Pro", layout="wide")

# 2. State Management System
if "closet" not in st.session_state:
    st.session_state.closet = {"Hot": [], "Normal": [], "Cold": []}
if "city_mem" not in st.session_state: st.session_state.city_mem = "Casablanca"
if "data_mem" not in st.session_state: st.session_state.data_mem = None
if "tour_guide" not in st.session_state: st.session_state.tour_guide = False
if "selected_destination" not in st.session_state: st.session_state.selected_destination = None

# Reference GPS Anchor Coordinate (Casablanca, Morocco)
USER_LAT = 33.5731
USER_LON = -7.5898

# 3. Distance Calculation Engine (Haversine Formula)
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0 
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# 4. MASTER A-TO-Z EXTENDED MOROCCAN REPERTOIRE DATABASE
TOUR_DATABASE = [
    # --- EAT (A to Z) ---
    {"name": "Al Fassia Restaurant", "cat": "🍽️ Places to Eat", "lat": 31.6362, "lon": -8.0091, "city": "Marrakesh", "desc": "Renowned upscale traditional restaurant run by women, specializing in slow-cooked Moroccan tagines.", "steps": "Head into Gueliz, pass the plaza junction, turn right past the boulevard palm alignment."},
    {"name": "Café Hafa", "cat": "🍽️ Places to Eat", "lat": 35.7912, "lon": -5.8224, "city": "Tangier", "desc": "Historical cliffside café offering sweeping panoramic views across the Strait of Gibraltar.", "steps": "Walk past the old Marshan quarter streets, follow the cliff edge walkway downward to the stone seating tiers."},
    {"name": "Chiringuito Beach Dining", "cat": "🍽️ Places to Eat", "lat": 30.4222, "lon": -9.6012, "city": "Agadir", "desc": "Premium fresh seafood dining along the vibrant sunny coastal promenade.", "steps": "Follow the coastal strip avenue south, turn right directly into the beachfront dining pavilion area."},
    {"name": "Dar Roumana Dining", "cat": "🍽️ Places to Eat", "lat": 34.0645, "lon": -4.9782, "city": "Fes", "desc": "Fine Mediterranean-Moroccan fusion cuisine structured inside a beautifully restored historical courtyard house.", "steps": "Enter Fes El Bali via the Bab Guissa gate, walk down the main hill path, take the first left alleyway curve."},
    {"name": "Dakhla Lagoon Oyster Bar", "cat": "🍽️ Places to Eat", "lat": 23.7212, "lon": -15.9345, "city": "Dakhla", "desc": "Fresh locally harvested Atlantic oysters served directly on the scenic shoreline lagoon.", "steps": "Drive down the primary lagoon access highway, turn toward the shoreline boat dock station."},
    {"name": "Le Dhow River Boat Restaurant", "cat": "🍽️ Places to Eat", "lat": 34.0256, "lon": -6.8291, "city": "Rabat", "desc": "An elegant lounge and dining room built onto a replica wooden merchant vessel floating on the Bouregreg river.", "steps": "Park near the historical kasbah wall entrance, proceed along the river walk dock to the boarding bridge."},
    {"name": "Nomad Rooftop Cafe", "cat": "🍽️ Places to Eat", "lat": 31.6272, "lon": -7.9881, "city": "Marrakesh", "desc": "Modern Moroccan culinary creations served over vibrant architectural terraces.", "steps": "Head South toward Rahba Kedima, take a sharp left at the spice corner market stalls, climb the main staircase."},
    {"name": "Rick's Café Casablanca", "cat": "🍽️ Places to Eat", "lat": 33.6062, "lon": -7.6210, "city": "Casablanca", "desc": "Piano lounge designed to recreate the timeless cinematic atmosphere of the classic film.", "steps": "Follow Boulevard de la Corniche toward the port entrance gate, make a right at the white arched architecture."},

    # --- MONUMENTS (A to Z) ---
    {"name": "Bahia Palace", "cat": "🏛️ Monuments & Landmarks", "lat": 31.6218, "lon": -7.9817, "city": "Marrakesh", "desc": "A 19th-century palace complex showcasing the pinnacle of classical Moroccan mosaic tiles and carved cedarwood.", "steps": "From Jemaa El Fna, walk southeast down Rue Riad Zitoun el Jdid until reaching the gated courtyard entrance."},
    {"name": "Chefchaouen Blue Medina Lines", "cat": "🏛️ Monuments & Landmarks", "lat": 35.1689, "lon": -5.2631, "city": "Chefchaouen", "desc": "The globally recognized historic streets entirely coated in stunning shades of blue pigment.", "steps": "Enter through the historical Bab El Ain gateway arch, follow the rising brick paths straight up into the medina."},
    {"name": "Hassan II Mosque", "cat": "🏛️ Monuments & Landmarks", "lat": 33.6087, "lon": -7.6327, "city": "Casablanca", "desc": "Architectural wonder featuring a soaring minaret built directly over the edge of the Atlantic Ocean.", "steps": "Follow Avenue Sidi Mohammed Ben Abdallah directly West to the expansive open maritime plaza."},
    {"name": "Hassan Tower Monument", "cat": "🏛️ Monuments & Landmarks", "lat": 34.0242, "lon": -6.8227, "city": "Rabat", "desc": "The historic red sandstone minaret of an incomplete 12th-century mosque project standing over columns.", "steps": "Proceed up Boulevard Mohamed Lyazidi, turn into the open stone archaeological plaza overlook."},
    {"name": "Koutoubia Mosque", "cat": "🏛️ Monuments & Landmarks", "lat": 31.6238, "lon": -7.9936, "city": "Marrakesh", "desc": "The prominent historical landmark and largest structural mosque tower in Marrakesh.", "steps": "Walk West away from the central square marketplace, cross the grand boulevard avenue toward the rose gardens."},
    {"name": "Majorelle Botanical Garden", "cat": "🏛️ Monuments & Landmarks", "lat": 31.6318, "lon": -8.0033, "city": "Marrakesh", "desc": "A spectacular botanical sanctuary featuring cobalt blue cubist architecture.", "steps": "Drive toward the Gueliz district perimeter, proceed down Rue Yves Saint Laurent directly to the primary gate."},
    {"name": "Volubilis Roman Ruins", "cat": "🏛️ Monuments & Landmarks", "lat": 34.0733, "lon": -5.5544, "city": "Meknes", "desc": "Ancient archaeological preservation zone displaying beautifully preserved Roman mosaics.", "steps": "Take the main rural route North past Moulay Idriss Zerhoun, arrive directly at the visitor center entrance pavilion."},

    # --- BASIC SHOPPING & NEEDS (A to Z Expanded) ---
    {"name": "Asima Supermarket Grocery", "cat": "🛒 Basic Shopping & Needs", "lat": 33.5905, "lon": -7.6012, "city": "Casablanca", "desc": "Full-scale modern grocery store providing daily food items, household inventory, and bottled provisions.", "steps": "Proceed down Boulevard Mohamed V, turn right past the central tram line terminal intersection."},
    {"name": "Boulevard d'Anfa Pharmacy Hub", "cat": "🛒 Basic Shopping & Needs", "lat": 33.5852, "lon": -7.6234, "city": "Casablanca", "desc": "Comprehensive medical supplier offering wellness products and healthcare items.", "steps": "Walk along the main Anfa commercial district corridor, located immediately next to the primary banking center."},
    {"name": "Gold Souk Jewelry Bazaar", "cat": "🛒 Basic Shopping & Needs", "lat": 31.6279, "lon": -7.9895, "city": "Marrakesh", "desc": "Authentic market sector specializing in fine hand-engraved silver bracelets, gold networks, and traditional necklaces.", "steps": "Enter through the inner network paths of Souk Semmarine, turn right at the primary covered textile archway."},
    {"name": "Morocco Mall Commercial Hub", "cat": "🛒 Basic Shopping & Needs", "lat": 33.5760, "lon": -7.7083, "city": "Casablanca", "desc": "One of Africa's largest modern shopping malls, featuring global fashion retail brands and department stores.", "steps": "Follow Route d'El Jadida Southwest to the coastal loop road, enter via the central parking gate system."},
    {"name": "Marjane Agadir Central Mall", "cat": "🛒 Basic Shopping & Needs", "lat": 30.4012, "lon": -9.5634, "city": "Agadir", "desc": "Large scale multi-department commercial space stocking electronics, travel gear, groceries, and medical goods.", "steps": "Follow Avenue Mohammed V inland, turn right at the major commercial roundabout gateway."},
    {"name": "Souk Semmarine Clothing Passage", "cat": "🛒 Basic Shopping & Needs", "lat": 31.6285, "lon": -7.9892, "city": "Marrakesh", "desc": "The central avenue for authentic clothing items, traditional embroidered kaftans, and leather shoes.", "steps": "From the northern exit of the main square, enter the tall wooden-covered structural market street."},
    {"name": "Tangier Ville Port Station Bazaar", "cat": "🛒 Basic Shopping & Needs", "lat": 35.7865, "lon": -5.8012, "city": "Tangier", "desc": "A primary multi-service travel retail zone offering international electronics, essentials, and local SIM cards.", "steps": "Proceed straight past the high-speed maritime passenger terminal building, located along the main service lobby lane."}
]

# 5. Core Utilities
def speak(text, lang='en'):
    try:
        tts = gTTS(text=text, lang=lang)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp
    except: return None

def apply_ui(city):
    bg = f"https://source.unsplash.com/featured/?{city},landmark" if city else "https://images.unsplash.com/photo-1521295121783-8a321d551ad2?q=80&w=1600"
    st.markdown(f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(255, 255, 255, 0.4), rgba(255, 255, 255, 0.4)), url("{bg}");
            background-size: cover !important; background-attachment: fixed !important;
        }}
        .glass {{
            background: rgba(255, 255, 255, 0.9) !important;
            border-radius: 20px; padding: 25px; backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.4);
        }}
        h1, h2, h3, p, span, .stMetric {{ color: #020617 !important; font-weight: 800 !important; }}
        </style>
    """, unsafe_allow_html=True)

# 6. SIDEBAR COMPONENT & BUTTON NAVIGATION
with st.sidebar:
    st.markdown("## 🧭 Navigation Panel")
    
    if st.button("🗺️ Launch AI Tour Guide Mode", use_container_width=True, type="primary"):
        st.session_state.tour_guide = True
        st.rerun()
        
    if st.button("🌡️ Return to Standard Weather App", use_container_width=True):
        st.session_state.tour_guide = False
        st.session_state.selected_destination = None
        st.rerun()

    st.divider()
    st.header("🌍 Global Language Engine")
    lang_choice = st.selectbox("Language / لغة", ["English", "Français", "العربية", "Español"])
    lang_map = {"English": "en", "Français": "fr", "العربية": "ar", "Español": "es"}
    lang_code = lang_map[lang_choice]
    gender = st.radio("Style Profile Choice:", ["Feminine", "Masculine"])
    
    st.divider()
    st.subheader("📸 Virtual Wardrobe Drawer")
    uploaded_file = st.file_uploader("Upload clothing file:", type=['jpg', 'png', 'jpeg'])
    category = st.selectbox("Target Condition Profile:", ["Hot", "Normal", "Cold"])
    
    if st.button("➕ Upload Item Assets"):
        if uploaded_file is not None:
            img = Image.open(uploaded_file)
            st.session_state.closet[category].append(img)
            st.success(f"Asset cataloged into {category} drawer!")

# 7. MAIN APPLICATIVE CONTEXT LOGIC
apply_ui(st.session_state.city_mem)

if not st.session_state.tour_guide:
    # --- STANDARD MODE: AMIRA'S WEATHER DASHBOARD ---
    st.markdown("<h1 style='text-align: center;'>🌡️ Amira's Weather Station Pro</h1>", unsafe_allow_html=True)
    city_in = st.text_input("🌍 Enter Target City Name...", value=st.session_state.city_mem)
    
    if st.button("🚀 Execute Weather Analysis", use_container_width=True):
        if city_in:
            data = WeatherEngine().get_weather(city_in)
            if "error" not in data:
                st.session_state.city_mem, st.session_state.data_mem = city_in, data
                st.rerun()

    if st.session_state.data_mem:
        d = st.session_state.data_mem['current_condition'][0]
        temp = int(d['temp_C'])
        desc = d['weatherDesc'][0]['value']
        lat, lon = float(st.session_state.data_mem['nearest_area'][0]['latitude']), float(st.session_state.data_mem['nearest_area'][0]['longitude'])
        current_weather_cat = "Hot" if temp > 25 else "Cold" if temp < 15 else "Normal"

        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 1, 1.2])
        with c1:
            st.metric(st.session_state.city_mem.capitalize(), f"{temp}°C", f"Condition: {desc}")
        with c2:
            st.info(f"💡 AI Suggestion: It's a {current_weather_cat} day. Open your sidebar wardrobe to view items!")
            voice_text = f"The current atmospheric profile in {st.session_state.city_mem} is characterized by {desc} at {temp} degrees."
            audio = speak(voice_text, lang_code)
            if audio: st.audio(audio)
        with c3:
            m = folium.Map(location=[lat, lon], zoom_start=11)
            folium.Marker([lat, lon]).add_to(m)
            st_folium(m, height=180, width=320, key="std_map")
        st.markdown("</div>", unsafe_allow_html=True)

else:
    # --- TOUR GUIDE MODE: SMART GPS HUB ---
    st.markdown("<h1 style='text-align: center;'>🕌 Amira AI Geolocation & Route Guide</h1>", unsafe_allow_html=True)
    st.success(f"🛰️ **System Location Beacon Active** | Reference Coordinates: **Casablanca Base** (Lat: {USER_LAT}, Lon: {USER_LON})")
    
    st.markdown("### 🎛️ Select Travel Criteria Filters")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        selected_cat = st.radio("What are you looking for?", ["🍽️ Places to Eat", "🏛️ Monuments & Landmarks", "🛒 Basic Shopping & Needs"], horizontal=True)
    with col_f2:
        # COMPLETE MOROCCAN URBAN MATRIX SELECTION
        selected_city = st.selectbox("Filter Destinations by Moroccan City Location:", [
            "All Cities", "Casablanca", "Marrakesh", "Fes", "Tangier", "Rabat", 
            "Agadir", "Meknes", "Oujda", "Kenitra", "Tetouan", "Essaouira", 
            "Ouarzazate", "Chefchaouen", "Dakhla", "El Jadida", "Nador"
        ])

    # Dynamic Sorting and Calculations Matrix
    processed_list = []
    for place in TOUR_DATABASE:
        if place["cat"] == selected_cat:
            if selected_city == "All Cities" or place["city"] == selected_city:
                dist = calculate_distance(USER_LAT, USER_LON, place["lat"], place["lon"])
                updated_place = place.copy()
                updated_place["distance"] = dist
                processed_list.append(updated_place)
                
    # Sort array variables cleanly from closest (nearest) to farthest
    sorted_destinations = sorted(processed_list, key=lambda x: x["distance"])

    st.markdown("### 📍 Destinations Found (Automatically Sorted: Nearest to Farthest)")
    display_names = [f"{p['name']} ({p['city']}) — 📏 {p['distance']:.1f} km away" for p in sorted_destinations]
    
    if display_names:
        selection = st.selectbox("Choose a destination to activate real-time turn-by-turn routing lines:", display_names)
        selected_idx = display_names.index(selection)
        active_target = sorted_destinations[selected_idx]
        st.session_state.selected_destination = active_target
    else:
        st.warning("No cataloged destination points match your current category and city filter criteria.")
        st.session_state.selected_destination = None

    # 5. SAFE ROUTING ENVIRONMENT & DIRECTION OUTPUT ENGINE
    if st.session_state.selected_destination:
        target = st.session_state.selected_destination
        st.divider()
        st.subheader(f"🗺️ Active Real-Time Guidance: {target['name']}")
        
        c_nav1, c_nav2 = st.columns([1.2, 1])
        with c_nav1:
            st.markdown(f"**ℹ️ Overview:** {target['desc']}")
            st.markdown(f"**🏁 Total Travel Distance:** `{target['distance']:.2f} Kilometers`")
            
            # FULLY TRANSITIONED SYSTEM LABELS - ZERO LEGAL TRADEMARK RISK
            st.error(f"🛰️ **Automated Route Directions:** {target['steps']}")
            
            nav_speech_text = f"Route calculations complete for {target['name']}. Current separation metric is {target['distance']:.1f} kilometers. Proceed according to the following route: {target['steps']}"
            nav_audio_file = speak(nav_speech_text, lang_code)
            if nav_audio_file:
                st.audio(nav_audio_file)
                
        with c_nav2:
            m_guide = folium.Map(location=[(USER_LAT + target['lat'])/2, (USER_LON + target['lon'])/2], zoom_start=6)
            
            folium.Marker([USER_LAT, USER_LON], tooltip="Current System Anchor Point", icon=folium.Icon(color='blue', icon='user')).add_to(m_guide)
            folium.Marker([target['lat'], target['lon']], tooltip=target['name'], icon=folium.Icon(color='red', icon='flag')).add_to(m_guide)
            folium.PolyLine(locations=[[USER_LAT, USER_LON], [target['lat'], target['lon']]], color='#06b6d4', weight=6, opacity=0.85).add_to(m_guide)
            
            st_folium(m_guide, height=300, width=450, key="live_navigation_map")

# 8. Render Closet Assets
st.divider()
st.subheader("🧥 Active Weather Wardrobe View")
current_cat = "Normal" if "data_mem" not in st.session_state or not st.session_state.data_mem else ("Hot" if int(st.session_state.data_mem['current_condition'][0]['temp_C']) > 25 else "Cold" if int(st.session_state.data_mem['current_condition'][0]['temp_C']) < 15 else "Normal")
items = st.session_state.closet[current_cat]
if items:
    cols = st.columns(4)
    for idx, img in enumerate(items):
        cols[idx % 4].image(img, use_container_width=True)
else:
    st.caption("No clothes uploaded for this weather condition category yet.")