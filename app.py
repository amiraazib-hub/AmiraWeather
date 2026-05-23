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

# COMPLETE GEOLOCATION ANCHOR REGISTRY
CITY_ANCHORS = {
    "Casablanca": {"lat": 33.5731, "lon": -7.5898}, "Marrakesh": {"lat": 31.6295, "lon": -7.9811},
    "Fes": {"lat": 34.0333, "lon": -5.0000}, "Tangier": {"lat": 35.7595, "lon": -5.8340},
    "Rabat": {"lat": 34.0209, "lon": -6.8416}, "Agadir": {"lat": 30.4173, "lon": -9.5981},
    "Meknes": {"lat": 33.8938, "lon": -5.5547}, "Chefchaouen": {"lat": 35.1580, "lon": -5.2680},
    "Dakhla": {"lat": 23.6848, "lon": -15.9579}
}

# PART 1 DATABASE
TOUR_DATABASE = [
    {"name": "Al Fassia Fine Dining", "cat": "🍽️ Restaurants & Dining", "sub": "Traditional Moroccan Restaurants", "lat": 31.6362, "lon": -8.0091, "city": "Marrakesh", "desc": "Fine dining run entirely by women.", "steps": "Head into Gueliz, pass the plaza junction."},
    {"name": "Bacha Coffee Room", "cat": "🍽️ Restaurants & Dining", "sub": "Cafés, Coffee & Bakeries", "lat": 31.6258, "lon": -7.9899, "city": "Marrakesh", "desc": "Historical coffee palace.", "steps": "Enter Dar El Bacha palace museum."},
    {"name": "Bondi Coffee Kitchen", "cat": "🍽️ Restaurants & Dining", "sub": "Cafés, Coffee & Bakeries", "lat": 33.5812, "lon": -7.6322, "city": "Casablanca", "desc": "Modern workspace café.", "steps": "Head down Rue Taha Hussein."},
    {"name": "Cabestan Ocean View", "cat": "🍽️ Restaurants & Dining", "sub": "Seafood & Beach Grills", "lat": 33.6045, "lon": -7.6654, "city": "Casablanca", "desc": "Luxury seafood grill.", "steps": "Follow the main Corniche lighthouse."},
    {"name": "Café Hafa", "cat": "🍽️ Restaurants & Dining", "sub": "Cafés, Coffee & Bakeries", "lat": 35.7912, "lon": -5.8224, "city": "Tangier", "desc": "Historical cliffside café.", "steps": "Follow the perimeter road wall downward."},
    {"name": "Chiringuito Ocean Grill", "cat": "🍽️ Restaurants & Dining", "sub": "Seafood & Beach Grills", "lat": 30.4222, "lon": -9.6012, "city": "Agadir", "desc": "Fresh daily Atlantic catches.", "steps": "Proceed straight along the seaside resort walkway."},
    {"name": "Dar Roumana Gourmet", "cat": "🍽️ Restaurants & Dining", "sub": "Traditional Moroccan Restaurants", "lat": 34.0645, "lon": -4.9782, "city": "Fes", "desc": "Moroccan fusion menus.", "steps": "Pass beneath Bab Guissa archway."},
    {"name": "Dakhla Oyster Farm", "cat": "🍽️ Restaurants & Dining", "sub": "Seafood & Beach Grills", "lat": 23.7212, "lon": -15.9345, "city": "Dakhla", "desc": "Freshly harvested organic oysters.", "steps": "Follow the primary ocean coastal highway."},
    {"name": "Le Dhow Boat Lounge", "cat": "🍽️ Restaurants & Dining", "sub": "Cafés, Coffee & Bakeries", "lat": 34.0256, "lon": -6.8291, "city": "Rabat", "desc": "A beautiful lounge on a wooden boat replica.", "steps": "Park near the lower kasbah stone walls."},
    {"name": "La Sqala Fortress Cafe", "cat": "🍽️ Restaurants & Dining", "sub": "Traditional Moroccan Restaurants", "lat": 33.6025, "lon": -7.6202, "city": "Casablanca", "desc": "Authentic Moroccan breakfast.", "steps": "Walk past the old medina protective stonewall."},
    {"name": "Nomad Terrace Lounge", "cat": "🍽️ Restaurants & Dining", "sub": "Traditional Moroccan Restaurants", "lat": 31.6272, "lon": -7.9881, "city": "Marrakesh", "desc": "Modern twist on Moroccan classics.", "steps": "Proceed across the spice square market plaza."},
    {"name": "Rick's Café Casablanca", "cat": "🍽️ Restaurants & Dining", "sub": "Traditional Moroccan Restaurants", "lat": 33.6062, "lon": -7.6210, "city": "Casablanca", "desc": "World-famous thematic restaurant.", "steps": "Follow Boulevard de la Corniche."},
    {"name": "Bahia Palace Courtyard", "cat": "🏛️ Monuments & Sightseeing", "sub": "Palaces & Historical Houses", "lat": 31.6218, "lon": -7.9817, "city": "Marrakesh", "desc": "Grand 19th-century vizier palace.", "steps": "From the Mellah perimeter area, follow Rue Riad Zitoun."},
    {"name": "Bab Bou Jeloud (Blue Gate)", "cat": "🏛️ Monuments & Sightseeing", "sub": "Ancient Gates & Medina Walls", "lat": 34.0617, "lon": -4.9829, "city": "Fes", "desc": "The iconic blue-tiled gateway arch.", "steps": "Arrive at the primary taxi loop plaza."},
    {"name": "Chefchaouen Outa El Hammam", "cat": "🏛️ Monuments & Sightseeing", "sub": "Scenic Streets & Plazas", "lat": 35.1689, "lon": -5.2631, "city": "Chefchaouen", "desc": "The central square street corridor.", "steps": "Enter through Bab El Ain gate structure."},
    {"name": "Hassan II Mosque Pavilion", "cat": "🏛️ Monuments & Sightseeing", "sub": "Mosques & Spiritual Sites", "lat": 33.6087, "lon": -7.6327, "city": "Casablanca", "desc": "One of the world's most spectacular mosques.", "steps": "Follow Avenue Sidi Mohammed Ben Abdallah."},
    {"name": "Hassan Red Minaret Tower", "cat": "🏛️ Monuments & Sightseeing", "sub": "Mosques & Spiritual Sites", "lat": 34.0242, "lon": -6.8227, "city": "Rabat", "desc": "The historic sandstone tower.", "steps": "Drive up Boulevard Mohamed Lyazidi."},
    {"name": "Kasbah of the Udayas", "cat": "🏛️ Monuments & Sightseeing", "sub": "Palaces & Historical Houses", "lat": 34.0321, "lon": -6.8362, "city": "Rabat", "desc": "Ancient blue-and-white neighborhood.", "steps": "Climb the grand stone staircase entry point."},
    {"name": "Koutoubia Mosque Tower", "cat": "🏛️ Monuments & Sightseeing", "sub": "Mosques & Spiritual Sites", "lat": 31.6238, "lon": -7.9936, "city": "Marrakesh", "desc": "The grand historical tower.", "steps": "Walk West out of the central spice plaza."},
    {"name": "Mahkama du Pacha", "cat": "🏛️ Monuments & Sightseeing", "sub": "Palaces & Historical Houses", "lat": 33.5801, "lon": -7.6042, "city": "Casablanca", "desc": "Masterpiece of Moorish architecture.", "steps": "Head deep into the Habous Quarter."},
    {"name": "Majorelle Botanical Sanctuary", "cat": "🏛️ Monuments & Sightseeing", "sub": "Scenic Streets & Plazas", "lat": 31.6318, "lon": -8.0033, "city": "Marrakesh", "desc": "Cobalt-blue cubist villa structures.", "steps": "Travel down Avenue Yacoub El Mansour."},
    {"name": "Volubilis Roman Ruins", "cat": "🏛️ Monuments & Sightseeing", "sub": "Palaces & Historical Houses", "lat": 34.0733, "lon": -5.5544, "city": "Meknes", "desc": "Beautiful Roman mosaics.", "steps": "Take the main rural route North."},
    {"name": "Asima Central Provisioner", "cat": "🛒 Shopping, Markets & Essentials", "sub": "Supermarkets & Groceries", "lat": 33.5905, "lon": -7.6012, "city": "Casablanca", "desc": "Modern department supermarket.", "steps": "Proceed down Boulevard Mohamed V."},
    {"name": "Anfa Wellness Pharmacy Hub", "cat": "🛒 Shopping, Markets & Essentials", "sub": "Pharmacies & Health Services", "lat": 33.5852, "lon": -7.6234, "city": "Casablanca", "desc": "Travel healthcare goods.", "steps": "Walk past the main Anfa financial block."},
    {"name": "Carrefour Market Marrakesh", "cat": "🛒 Shopping, Markets & Essentials", "sub": "Supermarkets & Groceries", "lat": 31.6342, "lon": -8.0122, "city": "Marrakesh", "desc": "Western-style supermarket.", "steps": "Navigate to the lower baseline floor inside Carré Eden."},
    {"name": "Gold Souk Jewelry Alley", "cat": "🛒 Shopping, Markets & Essentials", "sub": "Jewelry Boutique Shops", "lat": 31.6279, "lon": -7.9895, "city": "Marrakesh", "desc": "Specialized market jewelry lane.", "steps": "Walk deep into Souk Semmarine."},
    {"name": "Habous Olive & Craft Souk", "cat": "🛒 Shopping, Markets & Essentials", "sub": "Souks & Bazaars", "lat": 33.5790, "lon": -7.6030, "city": "Casablanca", "desc": "Traditional market neighborhood.", "steps": "Walk past the main square arcade gates."},
    {"name": "Morocco Mall Global Retail", "cat": "🛒 Shopping, Markets & Essentials", "sub": "Malls & Modern Retail", "lat": 33.5760, "lon": -7.7083, "city": "Casablanca", "desc": "Mega commercial modern mall.", "steps": "Drive down the main beachfront ring road."},
    {"name": "Marjane Shopping Complex", "cat": "🛒 Shopping, Markets & Essentials", "sub": "Malls & Modern Retail", "lat": 30.4012, "lon": -9.5634, "city": "Agadir", "desc": "Giant hypermarket.", "steps": "Follow Avenue Mohammed V directly inland."},
    {"name": "Socco Alto Luxury Gold", "cat": "🛒 Shopping, Markets & Essentials", "sub": "Jewelry Boutique Shops", "lat": 33.5899, "lon": -7.6155, "city": "Casablanca", "desc": "Premium jeweler collection.", "steps": "Take the main elevator to the second floor."},
    {"name": "Souk Semmarine Fabric Bazaars", "cat": "🛒 Shopping, Markets & Essentials", "sub": "Souks & Bazaars", "lat": 31.6285, "lon": -7.9892, "city": "Marrakesh", "desc": "Historical marketplace route.", "steps": "From Jemaa El Fna northern exit."},
    {"name": "Souk El Henna Herbalists", "cat": "🛒 Shopping, Markets & Essentials", "sub": "Souks & Bazaars", "lat": 31.6268, "lon": -7.9888, "city": "Marrakesh", "desc": "Pure argan oils and cosmetics.", "steps": "Follow the narrow alleyway past the old hospital."},
    {"name": "Tangier Ville Harbor Station Shop", "cat": "🛒 Shopping, Markets & Essentials", "sub": "Pharmacies & Health Services", "lat": 35.7865, "lon": -5.8012, "city": "Tangier", "desc": "Local internet SIM cards and travel goods.", "steps": "Proceed straight into the main high-speed passenger port lobby."}
]

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
    st.markdown("<h1 style='text-align: center;'>Medina Navigation & Travel Guide</h1>", unsafe_allow_html=True)
    
    st.markdown("### 🎛️ Advanced Travel Destination Filters")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        selected_cat = st.radio("What are you looking for?", ["🍽️ Restaurants & Dining", "🏛️ Monuments & Sightseeing", "🛒 Shopping, Markets & Essentials"], horizontal=True)
    with col_f2:
        selected_city = st.selectbox("Select Current Moroccan City Location:", ["Casablanca", "Marrakesh", "Fes", "Tangier", "Rabat", "Agadir", "Meknes", "Chefchaouen", "Dakhla"])

    if "🍽️" in selected_cat:
        sub_options = ["All Culinary Spots", "Traditional Moroccan Restaurants", "Cafés, Coffee & Bakeries", "Seafood & Beach Grills"]
    elif "🏛️" in selected_cat:
        sub_options = ["All Monuments", "Palaces & Historical Houses", "Ancient Gates & Medina Walls", "Mosques & Spiritual Sites", "Scenic Streets & Plazas"]
    else:
        sub_options = ["All Retail Options", "Souks & Bazaars", "Jewelry Boutique Shops", "Supermarkets & Groceries", "Pharmacies & Health Services", "Malls & Modern Retail"]
        
    selected_sub = st.selectbox("Filter down into specific options:", sub_options)

    current_user_coords = CITY_ANCHORS.get(selected_city, {"lat": 33.5731, "lon": -7.5898})
    u_lat, u_lon = current_user_coords["lat"], current_user_coords["lon"]

    st.success(f"🛰️ **Active System Anchor Point:** Calibrating trackers to **{selected_city} Center**")

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

    st.markdown("### 📍 Nearest Places Found")
    display_names = [f"{p['name']} — 📏 {p['distance']:.2f} km away" for p in sorted_destinations]
    
    if display_names:
        selection = st.selectbox("Choose a specific landmark to calculate routing path vectors:", display_names)
        selected_idx = display_names.index(selection)
        st.session_state.selected_destination = sorted_destinations[selected_idx]
    else:
        st.warning(f"No custom data points registered inside {selected_city} under this category yet.")
        st.session_state.selected_destination = None

    if st.session_state.selected_destination:
        target = st.session_state.selected_destination
        st.divider()
        st.subheader(f"🗺️ Active Real-Time Route Vectors: {target['name']}")
        
        c_nav1, c_nav2 = st.columns([1.2, 1])
        with c_nav1:
            st.markdown(f"**ℹ️ Overview:** {target['desc']}")
            st.markdown(f"**🏁 Total Travel Distance:** `{target['distance']:.3f} Kilometers`")
            st.error(f"🛰️ **Automated Route Directions:** {target['steps']}")
            
            nav_speech_text = f"Route calculations complete for {target['name']}. Proceed according to the following route: {target['steps']}"
            nav_audio_file = speak(nav_speech_text, lang_code)
            if nav_audio_file: st.audio(nav_audio_file)
                
        with c_nav2:
            m_guide = folium.Map(location=[u_lat, u_lon], zoom_start=13)
            folium.Marker([u_lat, u_lon], tooltip="Your GPS Pin", icon=folium.Icon(color='blue', icon='user')).add_to(m_guide)
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
    for idx, img in enumerate(items): cols[idx % 4].image(img, use_container_width=True)
else:
    st.caption("No clothes uploaded for this weather condition category yet.")
    