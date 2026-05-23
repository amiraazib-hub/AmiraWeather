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
    {"name": "Koutoubia Mosque Tower", "cat": "🏛️ Monuments & Sightseeing", "sub": "Mosques & Spiritual Sites", "lat": 31.6238, "lon": -7.