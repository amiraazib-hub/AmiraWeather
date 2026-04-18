import streamlit as st
import requests
from streamlit_lottie import st_lottie
from engine import WeatherEngine
from gtts import gTTS
from streamlit_folium import st_folium
import folium
import io

# 1. Page Config
st.set_page_config(page_title="Amira Weather Pro", layout="wide")

# 2. State Management
if "closet" not in st.session_state: st.session_state.closet = {"Hot":[], "Cold":[], "Normal":[]}
if "city_mem" not in st.session_state: st.session_state.city_mem = None
if "data_mem" not in st.session_state: st.session_state.data_mem = None

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
    # Dynamic Unsplash background based on city monument
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
        }}
        h1, h2, h3, p, span, .stMetric {{ color: black !important; font-weight: 900 !important; }}
        </style>
    """, unsafe_allow_html=True)

# 4. App UI
apply_ui(st.session_state.city_mem)
st.markdown("<h1 style='text-align: center;'>🌡️ Amira's Weather Station Pro</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.header("🌍 AI Settings")
    lang_choice = st.selectbox("Language / لغة", ["English", "Français", "العربية", "Español"])
    lang_map = {"English": "en", "Français": "fr", "العربية": "ar", "Español": "es"}
    lang_code = lang_map[lang_choice]
    
    gender = st.radio("Style Preference:", ["Feminine", "Masculine"])
    st.divider()
    st.subheader("📸 Virtual Closet")
    up = st.file_uploader("Upload clothing:", type=['jpg', 'png'])
    cat = st.selectbox("Category:", ["Hot", "Normal", "Cold"])
    if st.button("Save to Closet"):
        if up: st.session_state.closet[cat].append(up); st.success("Saved!")

# 5. Search Logic
city_in = st.text_input("🌍 Enter City Name...", placeholder="e.g. Casablanca")
if st.button("🚀 Analyze Weather"):
    if city_in:
        data = WeatherEngine().get_weather(city_in)
        if "error" not in data:
            st.session_state.city_mem, st.session_state.data_mem = city_in, data
            st.rerun()

# 6. Display Results
if st.session_state.city_mem and st.session_state.data_mem:
    d = st.session_state.data_mem['current_condition'][0]
    temp, feel = int(d['temp_C']), int(d['FeelsLikeC'])
    desc = d['weatherDesc'][0]['value']
    lat, lon = float(st.session_state.data_mem['nearest_area'][0]['latitude']), float(st.session_state.data_mem['nearest_area'][0]['longitude'])

    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1.2])
    
    with c1:
        # Dynamic Animation
        anim_url = "https://lottie.host/8593a436-e630-4e31-893c-2384976c6696/vKAnK2FmQp.json" if temp > 22 else "https://lottie.host/80182885-3e28-4ce0-8c29-37365c1f03d2/y0eH95Ua26.json"
        l = load_lottie(anim_url)
        if l: st_lottie(l, height=180, key="weather_anim")
        st.metric(st.session_state.city_mem.capitalize(), f"{temp}°C", f"Feels like {feel}°C")
        
    with c2:
        st.write(f"☀️ **UV Index:** {d.get('uvIndex')}")
        st.write(f"🌬️ **Condition:** {desc}")
        
        # Translation Logic
        w_cat = "Hot" if temp > 25 else "Cold" if temp < 15 else "Normal"
        sug_map = {
            "en": {"Hot": "a sundress" if gender == "Feminine" else "shorts", "Cold": "a warm coat", "Normal": "a jacket"},
            "fr": {"Hot": "une robe" if gender == "Feminine" else "un short", "Cold": "un manteau", "Normal": "une veste"},
            "ar": {"Hot": "فستان خفيف", "Cold": "معطف ثقيل", "Normal": "سترة خفيفة"},
            "es": {"Hot": "un vestido", "Cold": "un abrigo", "Normal": "una chaqueta"}
        }
        sug = sug_map.get(lang_code, sug_map["en"])[w_cat]
        
        st.info(f"💡 Amira Suggests: {sug}")
        audio = speak(f"{st.session_state.city_mem}. {desc}. {sug}.", lang_code)
        if audio: st.audio(audio)

    with c3:
        m = folium.Map(location=[lat, lon], zoom_start=11)
        folium.Marker([lat, lon]).add_to(m)
        st_folium(m, height=200, width=350, key="city_map")
    st.markdown("</div>", unsafe_allow_html=True)

    # Wardrobe Display
    if st.session_state.closet[w_cat]:
        st.subheader("🧥 Picked from your Closet:")
        cols = st.columns(4)
        for i, img in enumerate(st.session_state.closet[w_cat]):
            cols[i % 4].image(img, use_column_width=True)