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
    "Casablanca": {"lat": 33.5731, "lon": -7.5898},
    "Marrakesh": {"lat": 31.6295, "lon": -7.9811},
    "Fes": {"lat": 34.0333, "lon": -5.0000},
    "Tangier": {"lat": 35.7595, "lon": -5.8340},
    "Rabat": {"lat": 34.0209, "lon": -6.8416},
    "Agadir": {"lat": 30.4173, "lon": -9.5981},
    "Meknes": {"lat": 33.8938, "lon": -5.5547},
    "Chefchaouen": {"lat": 35.1580, "lon": -5.2680},
    "Dakhla": {"lat": 23.6848, "lon": -15.9579}
}

# 3. Distance Calculation Engine (Haversine Formula)
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0 
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# 4. MASTER A-TO-Z MOROCCAN REGISTRY DATA
TOUR_DATABASE = [
    # === PLACES TO EAT ===
    {"name": "Al Fassia Fine Dining", "cat": "🍽️ Restaurants & Dining", "sub": "Traditional Moroccan Restaurants", "lat": 31.6362, "lon": -8.0091, "city": "Marrakesh", "desc": "Fine dining run entirely by women, specializing in slow-cooked chicken, lamb tagines, and pastilla.", "steps": "Head into Gueliz, pass the plaza junction, turn right past the boulevard palm alignment."},
    {"name": "Bacha Coffee Room", "cat": "🍽️ Restaurants & Dining", "sub": "Cafés, Coffee & Bakeries", "lat": 31.6258, "lon": -7.9899, "city": "Marrakesh", "desc": "Stunning historical coffee palace offering over 200 varieties of premium coffee origins inside a palace room.", "steps": "Enter Dar El Bacha palace museum, proceed past the courtyard columns straight to the reservation room entrance."},
    {"name": "Bondi Coffee Kitchen", "cat": "🍽️ Restaurants & Dining", "sub": "Cafés, Coffee & Bakeries", "lat": 33.5812, "lon": -7.6322, "city": "Casablanca", "desc": "Trendy, aesthetic modern workspace café serving specialty third-wave coffee, matchas, and fresh pastries.", "steps": "Head down Rue Taha Hussein, turn right at the corner flower market stall."},
    {"name": "Cabestan Ocean View", "cat": "🍽️ Restaurants & Dining", "sub": "Seafood & Beach Grills", "lat": 33.6045, "lon": -7.6654, "city": "Casablanca", "desc": "High-end luxury seafood grill sitting right on the edge of the rocky cliffs overlooking the ocean waves.", "steps": "Follow the main Corniche lighthouse vector line directly to the lower level valet circle entrance."},
    {"name": "Café Hafa", "cat": "🍽️ Restaurants & Dining", "sub": "Cafés, Coffee & Bakeries", "lat": 35.7912, "lon": -5.8224, "city": "Tangier", "desc": "Historical cliffside café serving traditional Moroccan mint tea over sweeping ocean views since 1921.", "steps": "Follow the perimeter road wall downward along the cliff staircase path."},
    {"name": "Chiringuito Ocean Grill", "cat": "🍽️ Restaurants & Dining", "sub": "Seafood & Beach Grills", "lat": 30.4222, "lon": -9.6012, "city": "Agadir", "desc": "Fresh daily Atlantic catches prepared over charcoal pits right on the sunny beach promenade.", "steps": "Proceed straight along the seaside resort walkway, locate the blue striped umbrellas pavilion."},
    {"name": "Dar Roumana Gourmet", "cat": "🍽️ Restaurants & Dining", "sub": "Traditional Moroccan Restaurants", "lat": 34.0645, "lon": -4.9782, "city": "Fes", "desc": "Mediterranean-infused Moroccan fusion menus created by professional chefs inside an ancient palace courtyard.", "steps": "Pass beneath Bab Guissa archway, follow the main down-slope street lane, make a sharp left curve."},
    {"name": "Dakhla Oyster Farm", "cat": "🍽️ Restaurants & Dining", "sub": "Seafood & Beach Grills", "lat": 23.7212, "lon": -15.9345, "city": "Dakhla", "desc": "Freshly harvested organic oysters and grilled lobster served directly on the scenic coastal water lagoon docks.", "steps": "Follow the primary ocean coastal highway vector line directly to the wood docking slips station."},
    {"name": "Le Dhow Boat Lounge", "cat": "🍽️ Restaurants & Dining", "sub": "Cafés, Coffee & Bakeries", "lat": 34.0256, "lon": -6.8291, "city": "Rabat", "desc": "A beautiful lounge constructed over a replica wooden river cargo vessel floating on the Bouregreg waters.", "steps": "Park near the lower kasbah stone walls, cross the shoreline wood gangway platform."},
    {"name": "La Sqala Fortress Cafe", "cat": "🍽️ Restaurants & Dining", "sub": "Traditional Moroccan Restaurants", "lat": 33.6025, "lon": -7.6202, "city": "Casablanca", "desc": "Authentic Moroccan breakfast tajines served inside an elegant garden enclosed by historic Portuguese cannons.", "steps": "Walk past the old medina protective stonewall parameter directly to the primary fortress entry archway."},
    {"name": "Nomad Terrace Lounge", "cat": "🍽️ Restaurants & Dining", "sub": "Traditional Moroccan Restaurants", "lat": 31.6272, "lon": -7.9881, "city": "Marrakesh", "desc": "Modern twist on Moroccan classics with highly popular rooftop seating views looking over the medina rooftops.", "steps": "Proceed across the spice square market plaza, climb the multi-tiered terracotta stairs."},
    {"name": "Rick's Café Casablanca", "cat": "🍽️ Restaurants & Dining", "sub": "Traditional Moroccan Restaurants", "lat": 33.6062, "lon": -7.6210, "city": "Casablanca", "desc": "World-famous thematic restaurant meticulously designed to copy the jazz piano lounge from the movie Casablanca.", "steps": "Follow Boulevard de la Corniche, turn right past the ancient white port gateway entrance arch."},
    
    # === HISTORICAL MONUMENTS ===
    {"name": "Bahia Palace Courtyard", "cat": "🏛️ Monuments & Sightseeing", "sub": "Palaces & Historical Houses", "lat": 31.6218, "lon": -7.9817, "city": "Marrakesh", "desc": "Grand 19th-century vizier palace featuring breathtaking marble courtyards, stained glass panels, and painted wood.", "steps": "From the Mellah perimeter area, follow Rue Riad Zitoun el Jdid directly to the structural gate."},
    {"name": "Bab Bou Jeloud (Blue Gate)", "cat": "🏛️ Monuments & Sightseeing", "sub": "Ancient Gates & Medina Walls", "lat": 34.0617, "lon": -4.9829, "city": "Fes", "desc": "The iconic, majestic blue-tiled gateway arch forming the historical entrance into the ancient Fes Medina.", "steps": "Arrive at the primary taxi loop plaza drop-off zone, the massive decorated archway will be directly ahead."},
    {"name": "Chefchaouen Outa El Hammam", "cat": "🏛️ Monuments & Sightseeing", "sub": "Scenic Streets & Plazas", "lat": 35.1689, "lon": -5.2631, "city": "Chefchaouen", "desc": "The central square street corridor completely surrounded by world-renowned blue-washed homes.", "steps": "Enter through Bab El Ain gate structure, follow the rising blue cobblestone paths upward."},
    {"name": "Hassan II Mosque Pavilion", "cat": "🏛️ Monuments & Sightseeing", "sub": "Mosques & Spiritual Sites", "lat": 33.6087, "lon": -7.6327, "city": "Casablanca", "desc": "One of the world's most spectacular mosques, standing dramatically over the open waves of the Atlantic.", "steps": "Follow Avenue Sidi Mohammed Ben Abdallah directly West onto the vast beachfront stone plaza."},
    {"name": "Hassan Red Minaret Tower", "cat": "🏛️ Monuments & Sightseeing", "sub": "Mosques & Spiritual Sites", "lat": 34.0242, "lon": -6.8227, "city": "Rabat", "desc": "The historic sandstone tower standing tall next to stone columns from an unfinished 12th-century empire mosque.", "steps": "Drive up Boulevard Mohamed Lyazidi, walk through the gated structural archaeology park zone."},
    {"name": "Kasbah of the Udayas", "cat": "🏛️ Monuments & Sightseeing", "sub": "Palaces & Historical Houses", "lat": 34.0321, "lon": -6.8362, "city": "Rabat", "desc": "Ancient, fortified blue-and-white clifftop neighborhood built overlooking where the river meets the sea.", "steps": "Climb the grand stone staircase entry point directly off the main shoreline avenue."},
    {"name": "Koutoubia Mosque Tower", "cat": "🏛️ Monuments & Sightseeing", "sub": "Mosques & Spiritual Sites", "lat": 31.6238, "lon": -7.9936, "city": "Marrakesh", "desc": "The grand historical tower standing as the tallest and most iconic skyline marker across Marrakesh.", "steps": "Walk West out of the central spice plaza clearing, proceed straight through the palm tree gardens lane."},
    {"name": "Mahkama du Pacha", "cat": "🏛️ Monuments & Sightseeing", "sub": "Palaces & Historical Houses", "lat": 33.5801, "lon": -7.6042, "city": "Casablanca", "desc": "An absolute masterpiece of Moorish architecture serving as a court building with breathtaking stucco carvings.", "steps": "Head deep into the Habous Quarter, look for the large wooden palace doors opposite the olive souk."},
    {"name": "Majorelle Botanical Sanctuary", "cat": "🏛️ Monuments & Sightseeing", "sub": "Scenic Streets & Plazas", "lat": 31.6318, "lon": -8.0033, "city": "Marrakesh", "desc": "A beautiful landscape garden collection featuring giant cacti and cobalt-blue cubist villa structures.", "steps": "Travel down Avenue Yacoub El Mansour into Gueliz, enter via the primary ticketing lane gate."},
    {"name": "Volubilis Roman Ruins", "cat": "🏛️ Monuments & Sightseeing", "sub": "Palaces & Historical Houses", "lat": 34.0733, "lon": -5.5544, "city": "Meknes", "desc": "Ancient archaeological preservation zone displaying beautifully preserved Roman mosaics.", "steps": "Take the main rural route North past Moulay Idriss Zerhoun, arrive directly at the visitor center entrance pavilion."},

    # === SHOPPING & ESSENTIALS ===
    {"name": "Asima Central Provisioner", "cat": "🛒 Shopping, Markets & Essentials", "sub": "Supermarkets & Groceries", "lat": 33.5905, "lon": -7.6012, "city": "Casablanca", "desc": "Modern department supermarket stocking fresh regional produce, packaged goods, and daily essentials.", "steps": "Proceed down Boulevard Mohamed V, locate the retail spaces right past the tram railway terminal arch."},
    {"name": "Anfa Wellness Pharmacy Hub", "cat": "🛒 Shopping, Markets & Essentials", "sub": "Pharmacies & Health Services", "lat": 33.5852, "lon": -7.6234, "city": "Casablanca", "desc": "Comprehensive medical center stocking essential travel healthcare goods, wellness supplies, and baby products.", "steps": "Walk past the main Anfa financial block, the pharmacy storefront sits adjacent to the primary bank tower."},
    {"name": "Carrefour Market Marrakesh", "cat": "🛒 Shopping, Markets & Essentials", "sub": "Supermarkets & Groceries", "lat": 31.6342, "lon": -8.0122, "city": "Marrakesh", "desc": "Large Western-style convenience supermarket providing international foods, tracking goods, and grocery products.", "steps": "Navigate to the lower baseline floor inside the Carré Eden shopping complex in the Gueliz district."},
    {"name": "Gold Souk Jewelry Alley", "cat": "🛒 Shopping, Markets & Essentials", "sub": "Jewelry Boutique Shops", "lat": 31.6279, "lon": -7.9895, "city": "Marrakesh", "desc": "Specialized market lane filled with master crafters designing silver bracelets, fine rings, and amber bead items.", "steps": "Walk deep into the middle junctions of Souk Semmarine, take a right hand turn past the carpet arches lane."},
    {"name": "Habous Olive & Craft Souk", "cat": "🛒 Shopping, Markets & Essentials", "sub": "Souks & Bazaars", "lat": 33.5790, "lon": -7.6030, "city": "Casablanca", "desc": "Beautiful traditional market neighborhood famous for rows of organic spices, olives, and tailored Moroccan fabrics.", "steps": "Walk past the main square arcade gates, take a right into the stone tunnel corridor lane."},
    {"name": "Morocco Mall Global Retail", "cat": "🛒 Shopping, Markets & Essentials", "sub": "Malls & Modern Retail", "lat": 33.5760, "lon": -7.7083, "city": "Casablanca", "desc": "Mega commercial modern mall featuring international luxury fashion boutiques, food courts, and tech stores.", "steps": "Drive down the main beachfront ring road Southwest, turn directly into the multi-level customer parking portal."},
    {"name": "Marjane Shopping Complex", "cat": "🛒 Shopping, Markets & Essentials", "sub": "Malls & Modern Retail", "lat": 30.4012, "lon": -9.5634, "city": "Agadir", "desc": "Giant hypermarket offering electronics, household items, affordable clothing, luggage, and a pharmacy.", "steps": "Follow Avenue Mohammed V directly inland toward the primary metropolitan highway loop junction."},
    {"name": "Socco Alto Luxury Gold", "cat": "🛒 Shopping, Markets & Essentials", "sub": "Jewelry Boutique Shops", "lat": 33.5899, "lon": -7.6155, "city": "Casablanca", "desc": "Modern premium jeweler collection showcasing luxury gold watches, authentic Moroccan silver, and wedding bands.", "steps": "Take the main elevator to the second floor retail tier inside the commercial center."},
    {"name": "Souk Semmarine Fabric Bazaars", "cat": "🛒 Shopping, Markets & Essentials", "sub": "Souks & Bazaars", "lat": 31.6285, "lon": -7.9892, "city": "Marrakesh", "desc": "The primary historical marketplace route packing thousands of kaftans, leather shoes, lamps, and spices.", "steps": "From Jemaa El Fna northern exit, walk directly into the tall, iron-roofed historical covered arcade lane."},
    {"name": "Souk El Henna Herbalists", "cat": "🛒 Shopping, Markets & Essentials", "sub": "Souks & Bazaars", "lat": 31.6268, "lon": -7.9888, "city": "Marrakesh", "desc": "An ancient open courtyard square specializing in pure argan oils, natural cosmetics, soaps, and traditional henna plants.", "steps": "Follow the narrow alleyway leading past the old hospital structures straight into the brick courtyard center."},
    {"name": "Tangier Ville Harbor Station Shop", "cat": "🛒 Shopping, Markets & Essentials", "sub": "Pharmacies & Health Services", "lat": 35.7865, "lon": -5.8012, "city": "Tangier", "desc": "Multi-purpose travel center providing local internet SIM cards, chargers, water bottles, and quick snacks.", "steps": "Proceed straight into the main high-speed passenger port lobby hall building, row position number 4."}
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
        # COMPREHENSIVE CITY DROPDOWN LIST MATCHING ALL OPTIONS
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

    # Dynamic Array Sorting and Distance Calculations Matrix
    processed_list = []
    for place in TOUR_DATABASE:
        if place["cat"] == selected_cat and place["city"] == selected_city:
            is_sub_match = (selected_sub in ["All Culinary Spots", "All Monuments", "All Retail Options"]) or (place["sub"] == selected_sub)
            
            if is_sub_match:
                dist = calculate_distance(u_lat, u_lon, place["lat"], place["lon"])
                updated_place = place.copy()
                updated_place["distance"] = dist
                processed_list.append(