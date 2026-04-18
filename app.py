import streamlit as st
import requests
from streamlit_lottie import st_lottie
from engine import WeatherEngine
from gtts import gTTS
from streamlit_folium import st_folium
import folium
import io

st.set_page_config(page_title="Amira Weather Pro", layout="wide")

# Memory
if "closet" not in st.session_state: st.session_state.closet = {"Hot":[], "Cold":[], "Normal":[]}
if "city_mem" not in st.session_state: st.session_state.city_mem = None
if "data_mem" not in st.session_state: st.session_state.data_mem = None

# Language Mapping (Voice code, display name)
LANGS = {"en": "English", "fr": "Français", "ar": "العربية", "es": "Español", "de": "Deutsch"}

def load_lottie(url):
    try: return requests.get(url, timeout=5).json()
    except: return None

def speak(text, lang_code):
    try:
        tts = gTTS(text=text, lang=lang_code)
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
        }}
        h1, h2, h3, p, span, .stMetric {{ color: black !important; font-weight: 900 !important; }}
        </style>
    """, unsafe_allow_html=True)

apply_ui(st.session_state.city_mem)
st.markdown("<h1 style='text-align: center;'>🌡️ Amira's Weather Station Pro</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.header("👤 AI Settings")
    # NEW: Language Selector
    lang_name = st.selectbox("🌐 App Language:", list(LANGS.values()))
    lang_code = [k for k, v in LANGS.items() if v == lang_name][0]
    
    gender = st.radio("Style Preference:", ["Feminine", "Masculine"])
    st.divider()
    st.subheader("📸 Virtual Closet")
    up = st.file_uploader("Upload clothing:", type=['jpg', 'png'])
    cat = st.selectbox("Weather Category:", ["Hot", "Normal", "Cold"])
    if st.button("Save to Closet"):
        if up: st.session_state.closet[cat].append(up); st.success("Saved!")

city_in = st.text_input("🌍 Search City...", placeholder="e.g. Casablanca")
if st.button("🚀 Run AI Analysis"):
    if city_in:
        # We tell the engine which language we want for the weather description
        data = WeatherEngine().get_weather(f"{city_in}?lang={lang_code}")
        if "error" not in data:
            st.session_state.city_mem, st.session_state.data_mem = city_in, data
            st.rerun()

if st.session_state.city_mem and st.session_state.data_mem:
    d = st.session_state.data_mem['current_condition'][0]
    temp, feel = int(d['temp_C']), int(d['FeelsLikeC'])
    desc = d['weatherDesc'][0]['value']
    lat, lon = float(st.session_state.data_mem['nearest_area'][0]['latitude']), float(st.session_state.data_mem['nearest_area'][0]['longitude'])

    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1.2])
    with c1:
        url = "https://lottie.host/8593a436-e630-4e31-893c-2384976c6696/vKAnK2FmQp.json" if temp > 22 else "https://lottie.host/80182885-3e28-4ce0-8c29-37365c1f03d2/y0eH95Ua26.json"
        l = load_lottie(url)
        if l: st_lottie(l, height=180, key="anim")
        st.metric(st.session_state.city_mem.capitalize(), f"{temp}°C", f"Feels like {feel}°C")
    with c2:
        st.write(f"☀️ **UV:** {d.get('uvIndex')} | 💧 **Hum:** {d.get('humidity')}%")
        st.write(f"🌬️ **Condition:** {desc}")
        
        # --- OUTFIT LOGIC WITH TRANSLATION FALLBACK ---
        w_cat = "Hot" if temp > 25 else "Cold" if temp < 15 else "Normal"
        
        # Basic translation logic for suggestions
        suggestions = {
            "en": {"Hot": "a sundress" if gender == "Feminine" else "shorts", "Cold": "a coat", "Normal": "a jacket"},
            "fr": {"Hot": "une robe d'été" if gender == "Feminine" else "un short", "Cold": "un manteau", "Normal": "une veste"},
            "ar": {"Hot": "فستان صيفي" if gender == "Feminine" else "شورت", "Cold": "معطف دافئ", "Normal": "سترة خفيفة"},
            "es": {"Hot": "un vestido" if gender == "Feminine" else "pantalones cortos", "Cold": "un abrigo", "Normal": "una chaqueta"}
        }
        
        sug = suggestions.get(lang_code, suggestions["en"])[w_cat]
        st.info(f"💡 AI Suggestion: {sug}")
        
        # VOICE IN SELECTED LANGUAGE
        voice_text = f"{st.session_state.city_mem}. {desc}. {sug}."
        audio = speak(voice_text, lang_code)
        if audio: st.audio(audio)

    with c3:
        m = folium.Map(location=[lat, lon], zoom_start=11)
        folium.Marker([lat, lon]).add_to(m)
        st_folium(m, height=180, width=320, key="map")
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.closet[w_cat]:
        st.subheader("🧥 Closet:")
        cols = st.columns(4)
        for i, img in enumerate(st.session_state.closet[w_cat]):
            cols[i % 4].image(img, use_column_width=True)