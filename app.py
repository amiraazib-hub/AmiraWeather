import streamlit as st
import requests
from streamlit_lottie import st_lottie
from engine import WeatherEngine
from gtts import gTTS
from streamlit_folium import st_folium
import folium
import io
from PIL import Image

# 1. Page Config
st.set_page_config(page_title="Amira Weather Pro", layout="wide")

# 2. State Management (The "Memory" of your app)
if "closet" not in st.session_state:
    st.session_state.closet = {"Hot": [], "Normal": [], "Cold": []}
if "city_mem" not in st.session_state: st.session_state.city_mem = None
if "data_mem" not in st.session_state: st.session_state.data_mem = None
if "tour_guide" not in st.session_state: st.session_state.tour_guide = False

# 3. Helper Functions
def load_lottie(url):
    try: return requests.get(url, timeout=5).json()
    except: return None

def speak(text, lang='en'):
    try:
        tts = gTTS(text=text, lang=lang)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp
    except: return None

def apply_ui(city):
    bg = f"https://source.unsplash.com/featured/?{city},monument" if city else "https://images.unsplash.com/photo-1521295121783-8a321d551ad2?q=80&w=1600"
    st.markdown(f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(255, 255, 255, 0.4), rgba(255, 255, 255, 0.4)), url("{bg}");
            background-size: cover !important; background-attachment: fixed !important;
        }}
        .glass {{
            background: rgba(255, 255, 255, 0.85) !important;
            border-radius: 20px; padding: 25px; backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.3);
        }}
        h1, h2, h3, p, span, .stMetric {{ color: black !important; font-weight: 900 !important; }}
        </style>
    """, unsafe_allow_html=True)

# 4. App UI - Sidebar
with st.sidebar:
    st.header("🌍 AI Settings")
    lang_choice = st.selectbox("Language / لغة", ["English", "Français", "العربية", "Español"])
    lang_map = {"English": "en", "Français": "fr", "العربية": "ar", "Español": "es"}
    lang_code = lang_map[lang_choice]
    
    gender = st.radio("Style Preference:", ["Feminine", "Masculine"])
    
    st.divider()
    st.subheader("📸 Build Your Virtual Closet")
    
    uploaded_file = st.file_uploader("Upload a clothing item:", type=['jpg', 'png', 'jpeg'])
    category = st.selectbox("Which weather is this for?", ["Hot", "Normal", "Cold"])
    
    if st.button("➕ Add to My Closet"):
        if uploaded_file is not None:
            img = Image.open(uploaded_file)
            st.session_state.closet[category].append(img)
            st.success(f"Added to {category} closet! Total items: {len(st.session_state.closet[category])}")
        else:
            st.warning("Please select a photo first!")

    if st.button("🗑️ Clear All Photos"):
        st.session_state.closet = {"Hot": [], "Normal": [], "Cold": []}
        st.rerun()

# 5. Main App Logic
apply_ui(st.session_state.city_mem)
st.markdown("<h1 style='text-align: center;'>🌡️ Amira's Weather Station Pro</h1>", unsafe_allow_html=True)

city_in = st.text_input("🌍 Enter City Name...", placeholder="e.g. Casablanca")

# Buttons Row
col_b1, col_b2 = st.columns(2)
with col_b1:
    if st.button("🚀 Analyze Weather", use_container_width=True):
        if city_in:
            data = WeatherEngine().get_weather(city_in)
            if "error" not in data:
                st.session_state.city_mem, st.session_state.data_mem = city_in, data
                st.session_state.tour_guide = False
                st.rerun()

with col_b2:
    if st.button("🗺️ Marrakesh AI Tour Guide", use_container_width=True):
        # Automatically fetch Marrakesh weather data
        data = WeatherEngine().get_weather("Marrakesh")
        if "error" not in data:
            st.session_state.city_mem, st.session_state.data_mem = "Marrakesh", data
            st.session_state.tour_guide = True
            st.rerun()

# 6. Display Results & Virtual Closet Integration
if st.session_state.city_mem and st.session_state.data_mem:
    d = st.session_state.data_mem['current_condition'][0]
    temp, feel = int(d['temp_C']), int(d['FeelsLikeC'])
    desc = d['weatherDesc'][0]['value']
    lat, lon = float(st.session_state.data_mem['nearest_area'][0]['latitude']), float(st.session_state.data_mem['nearest_area'][0]['longitude'])

    current_weather_cat = "Hot" if temp > 25 else "Cold" if temp < 15 else "Normal"

    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1.2])
    
    with c1:
        anim_url = "https://lottie.host/8593a436-e630-4e31-893c-2384976c6696/vKAnK2FmQp.json" if temp > 22 else "https://lottie.host/80182885-3e28-4ce0-8c29-37365c1f03d2/y0eH95Ua26.json"
        l = load_lottie(anim_url)
        if l: st_lottie(l, height=180, key="weather_anim")
        st.metric(st.session_state.city_mem.capitalize(), f"{temp}°C", f"Feels like {feel}°C")
        
    with c2:
        st.write(f"🌬️ **Condition:** {desc}")
        
        sug_map = {
            "en": {"Hot": "a sundress" if gender == "Feminine" else "shorts", "Cold": "a warm coat", "Normal": "a jacket"},
            "fr": {"Hot": "une robe" if gender == "Feminine" else "un short", "Cold": "un manteau", "Normal": "une veste"},
            "ar": {"Hot": "فستان خفيف", "Cold": "معطف ثقيل", "Normal": "سترة خfيفة"},
            "es": {"Hot": "un vestido", "Cold": "un abrigo", "Normal": "una chaqueta"}
        }
        text_sug = sug_map.get(lang_code, sug_map["en"])[current_weather_cat]
        
        st.info(f"💡 AI Suggestion: Since it's {current_weather_cat}, wear {text_sug}!")
        audio = speak(f"The weather in {st.session_state.city_mem} is {desc}. I suggest wearing {text_sug}.", lang_code)
        if audio: st.audio(audio)

    with c3:
        m = folium.Map(location=[lat, lon], zoom_start=11)
        folium.Marker([lat, lon]).add_to(m)
        st_folium(m, height=200, width=350, key="city_map")
    st.markdown("</div>", unsafe_allow_html=True)

    # 7. MARRAKESH TOUR GUIDE SPECIAL FEATURE
    if st.session_state.tour_guide:
        st.divider()
        st.header("🕌 Welcome to Marrakesh - AI Tour Itinerary")
        
        # Guide thresholds logic
        if temp > 30:
            st.warning("☀️ It is currently very hot in Marrakesh! We highly recommend staying indoors during the afternoon.")
            places = [
                {"name": "Le Jardin Secret", "desc": "A beautiful palace oasis inside the old Medina with indoor seating and cooling fountains.", "img": "https://images.unsplash.com/photo-1590050752117-238cb0612b1b?q=80&w=400"},
                {"name": "Dar El Bacha Museum", "desc": "Beautiful architecture inside a palace, famous for its luxurious, air-conditioned coffee rooms.", "img": "https://images.unsplash.com/photo-1539650116574-8efeb43e2750?q=80&w=400"}
            ]
        else:
            st.success("🌤️ Perfect walking weather! Time to explore the iconic outdoor landmarks.")
            places = [
                {"name": "Jemaa el-Fnaa Square", "desc": "The vibrant heart of Marrakesh filled with fresh orange juice stands, snake charmers, and street performers.", "img": "https://images.unsplash.com/photo-1548625361-155deee223d0?q=80&w=400"},
                {"name": "Majorelle Garden & Koutoubia", "desc": "Walk around the famous bright blue gardens and take pictures near the breathtaking Koutoubia Mosque.", "img": "https://images.unsplash.com/photo-1605649487212-47bdab064df7?q=80&w=400"}
            ]
            
        cols = st.columns(2)
        for idx, place in enumerate(places):
            with cols[idx]:
                st.markdown(f"### 📍 {place['name']}")
                st.image(place["img"], use_container_width=True)
                st.write(place["desc"])

    # Wardrobe Display
    st.divider()
    st.subheader(f"🧥 Your {current_weather_cat} Wardrobe")
    my_items = st.session_state.closet[current_weather_cat]
    if len(my_items) > 0:
        cols = st.columns(4)
        for i, img in enumerate(my_items):
            cols[i % 4].image(img, use_container_width=True, caption=f"Item {i+1}")
    else:
        st.warning(f"Your {current_weather_cat} closet is empty! Upload some photos in the sidebar to see them here.")
        