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
if "city_mem" not in st.session_state: st.session_state.city_mem = "Casablanca"  # Defaults to user's local zone
if "data_mem" not in st.session_state: st.session_state.data_mem = None
if "tour_guide" not in st.session_state: st.session_state.tour_guide = False
if "selected_destination" not in st.session_state: st.session_state.selected_destination = None

# Simulated Live User Location (Defaults to Casablanca center coords)
USER_LAT = 33.5731
USER_LON = -7.5898

# 3. Distance Calculation Engine (Haversine Formula)
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0 # Radius of Earth in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# 4. Global Tour Destinations Database
TOUR_DATABASE = [
    # --- EAT ---
    {"name": "Nomad Rooftop Cafe", "cat": "🍽️ Places to Eat", "lat": 31.6272, "lon": -7.9881, "city": "Marrakesh", "desc": "Modern Moroccan gastronomy directly above ancient spice plazas.", "steps": "Head South toward Rahba Kedima, take a sharp left at the aroma merchants, climb the clay stairs to the roof."},
    {"name": "Rick's Café Casablanca", "cat": "🍽️ Places to Eat", "lat": 33.6062, "lon": -7.6210, "city": "Casablanca", "desc": "The iconic piano bar replicating the timeless cinematic atmosphere.", "steps": "Walk North along Boulevard de la Corniche, cross the gateway entry past the old port wall entrance."},
    # --- MONUMENTS ---
    {"name": "Hassan II Mosque", "cat": "🏛️ Monuments & Landmarks", "lat": 33.6087, "lon": -7.6327, "city": "Casablanca", "desc": "The second largest functioning mosque complex in the world, sitting over the Atlantic ocean.", "steps": "Follow Avenue Sidi Mohammed Ben Abdallah directly West toward the coastal vector line."},
    {"name": "Majorelle Botanical Garden", "cat": "🏛️ Monuments & Landmarks", "lat": 31.6318, "lon": -8.0033, "city": "Marrakesh", "desc": "The electric-blue architectural sanctuary designed by Jacques Majorelle.", "steps": "Head North down Avenue Yacoub El Mansour, enter through the cobalt blue archway checkpoint."},
    # --- BASIC PLACES ---
    {"name": "Morocco Mall Hub", "cat": "🛒 Basic Shopping & Needs", "lat": 33.5760, "lon": -7.7083, "city": "Casablanca", "desc": "The primary modern commercial center with global retail options.", "steps": "Follow Route d'El Jadida Southwest, stay in the right lane past the outer ocean promenade gates."},
    {"name": "Souk Semmarine Artisan Passage", "cat": "🛒 Basic Shopping & Needs", "lat": 31.6285, "lon": -7.9892, "city": "Marrakesh", "desc": "The sprawling focal point of authentic artisan metal work, textiles and jewelry.", "steps": "From Jemaa el-Fnaa northeast gate, follow the roofed structural walkway straight through the spice stalls."}
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
    
    # MASTER SWITCH: Placed cleanly at the very top of the sidebar
    if st.button("🗺️ Launch AI Tour Guide Mode", use_container_width=True, type="primary"):
        st.session_state.tour_guide = True
        st.rerun()
        
    if st.button("🌡️ Return to Standard Weather app", use_container_width=True):
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
    
    # 1. Immediate Location Recognition Display
    st.success(f"🛰️ **GPS Core Ping Active!** Detected Current Location Coordinate Base: **Casablanca, Morocco** (Lat: {USER_LAT}, Lon: {USER_LON})")
    
    # 2. Input Choice Layer
    st.markdown("### 🎛️ Select Travel Criteria Filters")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        selected_cat = st.radio("What are you looking for?", ["🍽️ Places to Eat", "🏛️ Monuments & Landmarks", "🛒 Basic Shopping & Needs"], horizontal=True)
    with col_f2:
        selected_city = st.selectbox("Filter Destinations by Moroccan City Location:", ["All Cities", "Casablanca", "Marrakesh"])

    # 3. Dynamic Distance Calculation and Math Matrix Sorting
    processed_list = []
    for place in TOUR_DATABASE:
        if place["cat"] == selected_cat:
            if selected_city == "All Cities" or place["city"] == selected_city:
                # Math formula executes relative proximity distances instantly
                dist = calculate_distance(USER_LAT, USER_LON, place["lat"], place["lon"])
                updated_place = place.copy()
                updated_place["distance"] = dist
                processed_list.append(updated_place)
                
    # CRITICAL: Automatically re-sorts array variables from closest (nearest) to farthest
    sorted_destinations = sorted(processed_list, key=lambda x: x["distance"])

    # 4. Interactive List Selection UI
    st.markdown("### 📍 Destinations Found (Automatically Sorted: Nearest to Farthest)")
    
    display_names = [f"{p['name']} ({p['city']}) — 📏 {p['distance']:.1f} km away" for p in sorted_destinations]
    
    if display_names:
        selection = st.selectbox("Choose a destination to activate real-time turn-by-turn routing lines:", display_names)
        selected_idx = display_names.index(selection)
        active_target = sorted_destinations[selected_idx]
        
        # Save selection across reloads
        st.session_state.selected_destination = active_target
    else:
        st.warning("No cataloged destination points match your current category and city filter criteria.")
        st.session_state.selected_destination = None

    # 5. LIVE ROUTING ENVIRONMENT & TURN AUDIO ENGINE
    if st.session_state.selected_destination:
        target = st.session_state.selected_destination
        st.divider()
        st.subheader(f"🗺️ Active Co-Pilot Guidance: {target['name']}")
        
        c_nav1, c_nav2 = st.columns([1.2, 1])
        with c_nav1:
            st.markdown(f"**ℹ️ Overview:** {target['desc']}")
            st.markdown(f"**🏁 Total Travel Distance:** `{target['distance']:.2f} Kilometers`")
            
            # The exact turn-by-turn path generation box
            st.error(f"🗣️ **Google-Style Live Navigation Feedback:** {target['steps']}")
            
            # Generate voice file simulation
            nav_speech_text = f"Navigation active to {target['name']}. Current distance metric is {target['distance']:.1f} kilometers. Turn profile instructions: {target['steps']}"
            nav_audio_file = speak(nav_speech_text, lang_code)
            if nav_audio_file:
                st.audio(nav_audio_file)
                
        with c_nav2:
            # Build full multi-point line mapping tracking system
            m_guide = folium.Map(location=[(USER_LAT + target['lat'])/2, (USER_LON + target['lon'])/2], zoom_start=7)
            
            # Blue Vector Pin representing User Phone Location
            folium.Marker([USER_LAT, USER_LON], tooltip="Your Live Smartphone GPS Pin", icon=folium.Icon(color='blue', icon='user')).add_to(m_guide)
            # Red Vector Pin representing target arrival destination
            folium.Marker([target['lat'], target['lon']], tooltip=target['name'], icon=folium.Icon(color='red', icon='flag')).add_to(m_guide)
            
            # Draw the Cyan Active Route PolyLine Vector matching Google Maps functionality
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