import streamlit as st
import pandas as pd
import os
import re
import gspread
from google.oauth2 import service_account
import urllib.parse
import random

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Iron & Rubber", layout="centered")

# --- STATCOUNTER ---
SC_PROJECT = "13297832"
SC_SECURITY = "54bb43fa"

if "page" not in st.session_state: st.session_state["page"] = "home"
if "menu" in st.query_params:
    st.session_state["page"] = st.query_params["menu"]
    st.query_params.clear()
    st.rerun()

# --- CONNESSIONE GOOGLE ---
@st.cache_resource
def inizializza_connessione_google():
    try:
        credentials_info = dict(st.secrets["gcp_service_account"])
        credentials_info["private_key"] = credentials_info["private_key"].replace("\\n", "\n")
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        credentials = service_account.Credentials.from_service_account_info(credentials_info, scopes=scopes)
        return gspread.authorize(credentials)
    except: return None

gc = inizializza_connessione_google()
NOME_DEL_FOGLIO = "app motoraduni"
regioni_italia = ["Abruzzo", "Basilicata", "Calabria", "Campania", "Emilia-Romagna", "Friuli-Venezia Giulia", "Lazio", "Liguria", "Lombardia", "Marche", "Molise", "Piemonte", "Puglia", "Sardegna", "Sicilia", "Toscana", "Trentino-Alto Adige", "Umbria", "Valle d'Aosta", "Veneto"]

# --- FUNZIONI UTILI ---
def parsing_data_biker(testo):
    testo = str(testo).lower()
    match = re.search(r'\b(\d{2})/(\d{2})/(202\d)\b', testo)
    if match: return pd.Timestamp(year=int(match.group(3)), month=int(match.group(2)), day=int(match.group(1)))
    return pd.NaT

# --- CSS ---
st.markdown("""
<style>
.stApp { background-color: #161719; }
.catena-separatore { display: block; width: 80%; max-width: 300px; margin: 30px auto; }
.titolo-gotico { font-family: 'UnifrakturMaguntia', cursive; text-align: center; color: #ff9100; }
.btn-civado { background-color: #ff9100; color: black; padding: 10px; text-decoration: none; font-weight: bold; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# --- LOGICA PRINCIPALE ---
st.markdown("<h1 class='titolo-gotico'>Iron & Rubber</h1>", unsafe_allow_html=True)

if gc:
    try:
        foglio = gc.open(NOME_DEL_FOGLIO).get_worksheet(0)
        dati = foglio.get_all_values()
        if len(dati) > 1:
            df = pd.DataFrame(dati[1:], columns=dati[0][:7]).iloc[:, :7]
            df.columns = ["Nome Evento / Raduno", "Data", "Luogo", "Regione", "Dettagli / Note", "Locandina", "Partecipanti"]
            
            # Filtri
            reg_scelta = st.selectbox("Regione", ["Tutte"] + regioni_italia)
            ifDoc = df.copy()
            if reg_scelta != "Tutte":
                ifDoc = ifDoc[ifDoc['Regione'].str.strip().str.lower() == reg_scelta.strip().lower()]
            
            # Lista Eventi
            for idx, row in ifDoc.iterrows():
                with st.expander(f"{row['Data']} - {row['Nome Evento / Raduno']}"):
                    st.write(f"📍 {row['Luogo']}")
                    st.markdown(f"<a href='?vota={idx}' class='btn-civado'>CI VADO 🔥 {row['Partecipanti']}</a>", unsafe_allow_html=True)
                
                # LA TUA CATENA
                st.image("catena_separatore.png", use_container_width=False, width=300)
        else:
            st.info("Database vuoto.")
    except Exception as e:
        st.error(f"Errore: {e}")

# --- MENU IN BASSO ---
st.markdown("""
<div style='position: fixed; bottom: 0; left: 0; width: 100%; background: #1f2124; padding: 15px; border-top: 2px solid #ff9100;'>
    <a href='?menu=home' style='color: #ff9100; margin-right: 20px;'>HOME</a>
    <a href='?menu=mc' style='color: #ff9100; margin-right: 20px;'>MC</a>
    <a href='?menu=admin' style='color: #ff9100;'>ADMIN</a>
</div>
""", unsafe_allow_html=True)
