import streamlit as st
import pandas as pd
import os
import re
import gspread
from google.oauth2 import service_account
import urllib.parse
import random

# --- 1. CONFIGURAZIONE GRAFICA DELLA PAGINA ---
st.set_page_config(page_title="Iron & Rubber", layout="centered")

# --- IMPOSTAZIONI STATCOUNTER CONFIGURATE ---
SC_PROJECT = "13297832"
SC_SECURITY = "54bb43fa"

if "fake_online" not in st.session_state:
    st.session_state["fake_online"] = random.randint(1, 3)
utenti_online = st.session_state["fake_online"]

# --- GESTIONE DELLA NAVIGAZIONE (PAGINE) ---
if "page" not in st.session_state:
    st.session_state["page"] = "home"

if "menu" in st.query_params:
    scelta_menu = st.query_params["menu"]
    if scelta_menu in ["home", "mc", "admin"]:
        st.session_state["page"] = scelta_menu
    st.query_params.clear()
    st.rerun()

if "sel_regione" not in st.session_state: st.session_state["sel_regione"] = "Tutte"
if "sel_mese" not in st.session_state: st.session_state["sel_mese"] = "Tutte"
if "evento_inviato" not in st.session_state: st.session_state["evento_inviato"] = False

# --- 2. CONNESSIONE A GOOGLE SHEETS ---
@st.cache_resource
def inizializza_connessione_google():
    try:
        credentials_info = dict(st.secrets["gcp_service_account"])
        if "private_key" in credentials_info:
            credentials_info["private_key"] = credentials_info["private_key"].replace("\\n", "\n")
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        credentials = service_account.Credentials.from_service_account_info(credentials_info, scopes=scopes)
        return gspread.authorize(credentials)
    except: return None

gc = inizializza_connessione_google()
NOME_DEL_FOGLIO = "app motoraduni"
regioni_italia = ["Abruzzo", "Basilicata", "Calabria", "Campania", "Emilia-Romagna", "Friuli-Venezia Giulia", "Lazio", "Liguria", "Lombardia", "Marche", "Molise", "Piemonte", "Puglia", "Sardegna", "Sicilia", "Toscana", "Trentino-Alto Adige", "Umbria", "Valle d'Aosta", "Veneto"]

# --- 3. FUNZIONI DATI ---
if "voti_locali" not in st.session_state: st.session_state["voti_locali"] = set()
def registra_voto(chiave_evento): st.session_state["voti_locali"].add(str(chiave_evento))
def ha_gia_votato(chiave_evento): return str(chiave_evento) in st.session_state["voti_locali"]

def parsing_data_biker(testo_data):
    testo = str(testo_data).lower().strip()
    if not testo or testo in ["nan", "vedi nel sito", "vedi nel file"]: return pd.NaT
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

# --- 4. CSS INTEGRATO ---
st.markdown(f"""
<style>
.stApp {{ background-color: #161719; }}
#MainMenu, footer, header {{visibility: hidden !important;}}
.block-container {{ padding-top: 2rem !important; padding-bottom: 9rem !important; }}
.catena-separatore {{ display: block; width: 90%; max-width: 400px; margin: 20px auto; opacity: 0.9; }}
.riga-pulsante-anteprima {{ display: flex !important; align-items: center !important; gap: 15px !important; width: 100% !important; margin-top: 5px !important; }}
.html-btn-civado {{ background-color: #ff9100 !important; color: black !important; font-weight: bold !important; font-family: 'Special Elite', cursive !important; border-radius: 5px !important; height: 38px !important; padding: 0px 25px !important; display: inline-flex !important; align-items: center !important; text-decoration: none !important; }}
.locandina-anteprima-rettangolare {{ height: 45px !important; width: auto !important; max-width: 90px !important; border: 2px solid #ff9100; border-radius: 5px; }}
.titolo-gotico {{ font-family: 'UnifrakturMaguntia', cursive !important; text-align: center; color: #ff9100 !important; font-size: 2.6rem !important; }}
.sottotitolo {{ font-family: 'UnifrakturMaguntia', cursive !important; text-align: center; color: #ff9100 !important; font-size: 1.4rem !important; }}
</style>
""", unsafe_allow_html=True)

if os.path.exists("logo_custom.png"): st.image("logo_custom.png", use_container_width=True)
st.markdown("<h1 class='titolo-gotico'>Iron & Rubber</h1>", unsafe_allow_html=True)
st.markdown("<p class='sottotitolo'>«Non è la meta, è la strada a rivelare chi sei.»</p>", unsafe_allow_html=True)

if gc:
    try:
        foglio_di_calcolo = gc.open(NOME_DEL_FOGLIO)
        if st.session_state["page"] == "home":
            scheda = foglio_di_calcolo.get_worksheet(0)
            df = pd.DataFrame(scheda.get_all_values()[1:], columns=["Nome Evento / Raduno", "Data", "Luogo", "Regione", "Dettagli / Note", "Locandina", "Partecipanti"])
            
            # --- Rendering Eventi ---
            df['GSheet_Row'] = df.index + 2
            df['Data_Date'] = df['Data'].apply(parsing_data_biker)
            df = df[(df['Data_Date'].isna()) | (df['Data_Date'] >= pd.Timestamp.now().normalize())]
            
            for idx, row in df.iterrows():
                riga_foglio_google = int(row['GSheet_Row'])
                img_path = str(row.get('Locandina', '')).strip()
                ha_locandina = img_path.startswith("http")
                
                with st.expander(f"{row['Data']} - {row['Nome Evento / Raduno']}"):
                    st.write(f"📍 **Luogo:** {row['Luogo']}")
                    st.write(f"📝 **Info:** {row.get('Dettagli / Note', 'Nessuna info')}")
                    
                    # Bottone e Anteprima ravvicinati
                    st.html(f"""
                    <div class="riga-pulsante-anteprima">
                        <a href="?vota={idx}" class="html-btn-civado">CI VADO 🔥 {row['Partecipanti']}</a>
                        <img src="{img_path}" class="locandina-anteprima-rettangolare">
                    </div>
                    """)
                
                # CATENA SEPARATORE
                st.html('<img src="catena_separatore.png" alt="separatore" class="catena-separatore">')

        elif st.session_state["page"] == "mc":
            # ... (logica MC invariata) ...
            pass
            
    except Exception as e: st.error(f"Errore: {e}")

# --- MENU IN BASSO ---
st.markdown("""
<div style='position: fixed; bottom: 0; left: 0; width: 100%; background: #1f2124; display: flex; gap: 30px; padding: 15px 20px; border-top: 3px solid #ff9100; z-index: 9999;'>
    <a href='?menu=home' target='_self' style='font-family: Special Elite; color: #ff9100; font-weight: bold; text-decoration: none;'>HOME</a>
    <a href='?menu=mc' target='_self' style='font-family: Special Elite; color: #ff9100; font-weight: bold; text-decoration: none;'>MC</a>
    <a href='?menu=admin' target='_self' style='font-family: Special Elite; color: #ff9100; font-weight: bold; text-decoration: none;'>ADMIN</a>
</div>
""", unsafe_allow_html=True)
