import streamlit as st
import pandas as pd
import os
import re
import gspread
from google.oauth2 import service_account
import urllib.parse
import random

# --- 1. CONFIGURAZIONE GRAFICA ---
st.set_page_config(page_title="Iron & Rubber", layout="centered")

SC_PROJECT = "13297832"
SC_SECURITY = "54bb43fa"

if "fake_online" not in st.session_state:
    st.session_state["fake_online"] = random.randint(1, 3)
utenti_online = st.session_state["fake_online"]

if "page" not in st.session_state:
    st.session_state["page"] = "home"

if "menu" in st.query_params:
    scelta_menu = st.query_params["menu"]
    if scelta_menu in ["home", "mc", "admin"]:
        st.session_state["page"] = scelta_menu
    st.query_params.clear()
    st.rerun()

if "voti_locali" not in st.session_state:
    st.session_state["voti_locali"] = set()

def registra_voto(chiave_evento): st.session_state["voti_locali"].add(str(chiave_evento))
def ha_gia_votato(chiave_evento): return str(chiave_evento) in st.session_state["voti_locali"]

def parsing_data_biker(testo_data):
    testo = str(testo_data).lower().strip()
    if not testo or testo == "nan": return pd.NaT
    match_standard = re.search(r'\b(\d{2})/(\d{2})/(202\d)\b', testo)
    if match_standard:
        try: return pd.Timestamp(year=int(match_standard.group(3)), month=int(match_standard.group(2)), day=int(match_standard.group(1)))
        except: pass
    mesi = {'gen': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'mag': 5, 'giu': 6, 'lug': 7, 'ago': 8, 'set': 9, 'ott': 10, 'nov': 11, 'dic': 12}
    mese_num = next((v for k, v in mesi.items() if k in testo), None)
    if not mese_num:
        try: return pd.to_datetime(testo, dayfirst=True, errors='coerce')
        except: return pd.NaT
    anno_match = re.search(r'\b(202\d)\b', testo)
    anno = int(anno_match.group(1)) if anno_match else 2026
    giorno_match = re.search(r'\d+', testo)
    giorno = int(giorno_match.group(0)) if giorno_match else 1
    try: return pd.Timestamp(year=anno, month=mese_num, day=giorno)
    except: return pd.NaT

# --- 4. CSS AGGIORNATO CON CATENA ---
st.markdown(f"""
<style>
.stApp {{ background-color: #161719; }}
#MainMenu, footer, header {{visibility: hidden !important;}}
.block-container {{ padding-top: 2rem !important; padding-bottom: 9rem !important; }}

.catena-separatore {{
    display: block; width: 90%; max-width: 400px; margin: 20px auto; opacity: 0.9;
}}

.online-counter {{
    position: absolute; top: -10px; right: 15px; background: #1f2124; border: 1px solid #ff9100;
    padding: 4px 8px; border-radius: 12px; font-family: 'Special Elite', cursive; font-size: 0.75rem; color: #ffffff;
}}

.titolo-gotico {{ font-family: 'UnifrakturMaguntia', cursive !important; text-align: center; color: #ff9100 !important; font-size: 2.6rem !important; }}
.sottotitolo {{ font-family: 'UnifrakturMaguntia', cursive !important; text-align: center; color: #ff9100 !important; font-size: 1.4rem !important; }}

div[data-testid="stExpander"] {{ background-color: #1f2124 !important; border: 2px solid #ff9100 !important; border-radius: 10px !important; margin-bottom: 4px !important; }}
div[data-testid="stButton"] button {{ background-color: #ff9100 !important; color: black !important; font-weight: bold !important; width: 100%; }}

.riga-pulsante-anteprima {{
    display: flex !important; align-items: center !important; justify-content: flex-start !important;
    gap: 15px !important; width: 100% !important; margin-top: 2px !important;
}}
.html-btn-civado {{
    background-color: #ff9100 !important; color: black !important; font-weight: bold !important; font-family: 'Special Elite', cursive !important;
    border-radius: 5px !important; height: 38px !important; padding: 0px 25px !important; text-decoration: none !important;
    display: inline-flex !important; align-items: center !important;
}}
.locandina-anteprima-rettangolare {{
    height: 45px !important; width: auto !important; max-width: 90px !important; border: 2px solid #ff9100; border-radius: 5px;
}}
</style>
""", unsafe_allow_html=True)

# ... (Il resto delle tue funzioni di connessione Google rimane invariato) ...

# --- LOGICA PRINCIPALE (Home) ---
if st.session_state["page"] == "home":
    # ... (caricamento dataframe) ...
    for idx, row in ifDoc.iterrows():
        # ... renderizza expander ...
        with st.expander(f"{row['Data']} - {row['Nome Evento / Raduno']}"):
            # ... dettagli evento ...
            
            # PULSANTE E ANTEPRIMA COMPATTI
            st.html(f"""
            <div class="riga-pulsante-anteprima">
                {html_bottone}
                <a href="#zoom_{idx}"><img src="{img_path}" class="locandina-anteprima-rettangolare"></a>
            </div>
            """)
            
        # INSERIMENTO CATENA
        st.html('<img src="catena_separatore.png" alt="separatore" class="catena-separatore">')

# --- (Il resto delle schermate MC e Admin resta uguale) ---
