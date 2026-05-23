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

# 🚀 CLEAN DATAFEED IMPORT LOGIC
from data import CITY_ANCHORS, TOUR_DATABASE

# 1. Page Config
st.set_page_config(page_title="Amira Weather Pro", layout="wide")

# 2. State Management System
if "closet" not in st.session_state:
    st.session_state.closet = {"Hot": [], "Normal": [], "Cold": []}
if "city_mem" not in st.session_state: st.session_state.city_mem = "Casablanca"
if "data_mem" not in st.session_state: st.session_state.data_mem = None
if "tour_guide" not in st.session_state: st.session_state.tour_guide = False
if "selected_destination" not in st.session_state: st.session_state.selected_destination = None

# 3. Distance Calculation Engine (Haversine Formula)
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0 
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# 4. Core Utilities
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

# 5. SIDEBAR COMPONENT & BUTTON NAVIGATION
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

# 6. MAIN APPLICATIVE CONTEXT LOGIC
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
    st.markdown("<h1 style='text-align: center;'>Medina Navigation & Travel Guide</h1>", unsafe_allow_html=True)
    
    st.markdown("### 🎛️ Advanced Travel Destination Filters")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        selected_cat = st.radio("What are you looking for?", [
            "🍽️ Restaurants & Dining", 
            "🏛️ Monuments & Sightseeing", 
            "🛒 Shopping, Markets & Essentials"
        ], horizontal=True)
    with col_f2:
        selected_city = st.selectbox("Select Current Moroccan City Location:", [
            "Casablanca", "Marrakesh", "Fes", "Tangier", "Rabat", "Agadir", "Meknes", "Chefchaouen", "Dakhla"
        ])

    # SECOND-TIER DYNAMIC SUB-CATEGORY OPTIONS LAYER
    if "🍽️" in selected_cat:
        sub_options = ["All Culinary Spots", "Traditional Moroccan Restaurants", "Cafés, Coffee & Bakeries", "Seafood & Beach Grills"]
    elif "🏛️" in selected_cat:
        sub_options = ["All Monuments", "Palaces & Historical Houses", "Ancient Gates & Medina Walls", "Mosques & Spiritual Sites", "Scenic Streets & Plazas"]
    else:
        sub_options = ["All Retail Options", "Souks & Bazaars", "Jewelry Boutique Shops", "Supermarkets & Groceries", "Pharmacies & Health Services", "Malls & Modern Retail"]
        
    selected_sub = st.selectbox("Filter down into specific options:", sub_options)

    # DYNAMIC SMART ANCHORING
    current_user_coords = CITY_ANCHORS.get(selected_city, {"lat": 33.5731, "lon": -7.5898})
    u_lat = current_user_coords["lat"]
    u_lon = current_user_coords["lon"]

    st.success(f"🛰️ **Active System Anchor Point:** Calibrating smartphone trackers to **{selected_city} Center Core** (Lat: {u_lat}, Lon: {u_lon})")

    # Fixed Indentation Loop Architecture
    processed_list = []
    for place in TOUR_DATABASE:
        if place["cat"] == selected_cat and place["city"] == selected_city:
            is_sub_match = (selected_sub in ["All Culinary Spots", "All Monuments", "All Retail Options"]) or (place["sub"] == selected_sub)
            
            if is_sub_match:
                dist = calculate_distance(u_lat, u_lon, place["lat"], place["lon"])
                updated_place = place.copy()
                updated_place["distance"] = dist
                processed_list.append(updated_place)
                
    sorted_destinations = sorted(processed_list, key=lambda x: x["distance"])

    st.markdown("### 📍 Nearest Places Found (Alphabetical A-to-Z Database Sorted by Proximity)")
    display_names = [f"{p['name']} — 📏 {p['distance']:.2f} km away" for p in sorted_destinations]
    
    if display_names:
        selection = st.selectbox("Choose a specific landmark to calculate routing path vectors:", display_names)
        selected_idx = display_names.index(selection)
        active_target = sorted_destinations[selected_idx]
        st.session_state.selected_destination = active_target
    else:
        st.warning(f"No custom data points registered for '{selected_sub}' inside {selected_city} yet. Try shifting back to 'All Options' or changing cities!")
        st.session_state.selected_destination = None

    # 5. ROUTING ENVIRONMENT & DIRECTION OUTPUT ENGINE
    if st.session_state.selected_destination:
        target = st.session_state.selected_destination
        st.divider()
        st.subheader(f"🗺️ Active Real-Time Route Vectors: {target['name']}")
        
        c_nav1, c_nav2 = st.columns([1.2, 1])
        with c_nav1:
            st.markdown(f"**ℹ️ Overview:** {target['desc']}")
            st.markdown(f"**🏁 Total Travel Distance:** `{target['distance']:.3f} Kilometers`")
            st.error(f"🛰️ **Automated Route Directions:** {target['steps']}")
            
            nav_speech_text = f"Route calculations complete for {target['name']}. Current separation metric is {target['distance']:.2f} kilometers. Proceed according to the following route: {target['steps']}"
            nav_audio_file = speak(nav_speech_text, lang_code)
            if nav_audio_file:
                st.audio(nav_audio_file)
                
        with c_nav2:
            m_guide = folium.Map(location=[u_lat, u_lon], zoom_start=13)
            
            folium.Marker([u_lat, u_lon], tooltip="Your Active Smartphone GPS Pin", icon=folium.Icon(color='blue', icon='user')).add_to(m_guide)
            folium.Marker([target['lat'], target['lon']], tooltip=target['name'], icon=folium.Icon(color='red', icon='flag')).add_to(m_guide)
            folium.PolyLine(locations=[[u_lat, u_lon], [target['lat'], target['lon']]], color='#06b6d4', weight=6, opacity=0.85).add_to(m_guide)
            
            st_folium(m_guide, height=300, width=450, key="live_navigation_map")

# 7. Render Closet Assets
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
    __init__.py