import streamlit as st
import pandas as pd
import os
import re
import gspread
from google.oauth2 import service_account
import urllib.parse
import random

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Iron & Rubber", layout="centered")

if "fake_online" not in st.session_state:
    st.session_state["fake_online"] = random.randint(1, 3)
utenti_online = st.session_state["fake_online"]

if "page" not in st.session_state: st.session_state["page"] = "home"
if "menu" in st.query_params:
    st.session_state["page"] = st.query_params["menu"]
    st.query_params.clear()
    st.rerun()

# --- 2. CONNESSIONE GOOGLE ---
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

# --- 3. FUNZIONI E CSS ---
if "voti_locali" not in st.session_state: st.session_state["voti_locali"] = set()
def ha_gia_votato(chiave_evento): return str(chiave_evento) in st.session_state["voti_locali"]

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=UnifrakturMaguntia&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Special+Elite&display=swap');
.stApp {{ background-color: #161719; }}
.block-container {{ padding-top: 2rem !important; padding-bottom: 9rem !important; }}
.titolo-gotico {{ font-family: 'UnifrakturMaguntia', cursive !important; text-align: center; color: #ff9100 !important; font-size: 2.6rem !important; }}
.sottotitolo {{ font-family: 'UnifrakturMaguntia', cursive !important; text-align: center; color: #ff9100 !important; font-size: 1.4rem !important; margin-bottom: 20px !important; }}
div[data-testid="stExpander"] details summary {{ background-color: #1f2124 !important; color: white !important; }}
.streamlit-expanderHeader {{ color: #ff9100 !important; font-weight: bold !important; background-color: #1f2124 !important; }}
div[data-testid="stExpander"] details summary p::after {{ content: "CLICK HERE FOR INFO"; display: block; color: #ff9100; font-family: 'Special Elite'; font-size: 0.75rem; }}
div[data-testid="stExpander"] details[open] summary p::after {{ content: "CHIUDI INFO"; color: #ff9100 !important; }}
.riga-pulsante-anteprima {{ display: flex !important; align-items: center !important; justify-content: flex-start !important; gap: 10px !important; margin-top: 5px !important; margin-bottom: 30px !important; }}
.html-btn-civado {{ background-color: #ff9100 !important; color: black !important; font-weight: bold !important; font-family: 'Special Elite', cursive !important; border-radius: 5px !important; height: 40px !important; padding: 0px 20px !important; font-size: 0.95rem !important; text-decoration: none !important; display: inline-flex !important; align-items: center !important; }}
.html-btn-disabilitato {{ background-color: #555555 !important; color: #bbbbbb !important; }}
.locandina-anteprima-rettangolare {{ height: 40px !important; width: auto !important; max-width: 80px !important; object-fit: contain !important; border: 2px solid #ff9100; border-radius: 5px; }}
.separatore-evento {{ margin-bottom: 35px !important; border-bottom: 1px dashed rgba(255, 145, 0, 0.15); }}
</style>
""", unsafe_allow_html=True)

# UI
st.markdown(f"<div style='text-align: right; color: #ff9100; font-family: Special Elite;'>{utenti_online} Online</div>", unsafe_allow_html=True)
st.markdown("<h1 class='titolo-gotico'>Iron & Rubber</h1>", unsafe_allow_html=True)

if gc is not None:
    try:
        foglio = gc.open(NOME_DEL_FOGLIO).get_worksheet(0)
        dati = foglio.get_all_values()
        if len(dati) > 1:
            df = pd.DataFrame(dati[1:], columns=dati[0])
            for idx, row in df.iterrows():
                chiave_voto = f"{row['Nome Evento / Raduno']}_{row['Data']}"
                img_path = str(row.get('Locandina', '')).strip()
                ha_locandina = img_path.startswith("http")
                
                with st.expander(f"{row['Data']} - {row['Nome Evento / Raduno']}"):
                    st.write(f"📍 {row.get('Luogo', '')} - 📝 {row.get('Dettagli / Note', '')}")
                
                # CORREZIONE ERRORE SERIE: estrazione sicura del valore
                valore_p = row.get('Partecipanti', 0)
                conteggio = int(valore_p) if str(valore_p).isdigit() else 0
                
                if ha_gia_votato(chiave_voto):
                    html_bottone = f'<div class="html-btn-civado html-btn-disabilitato">CI VADO 🔥 {conteggio}</div>'
                else:
                    html_bottone = f'<a href="?vota={idx}" target="_self" class="html-btn-civado">CI VADO 🔥 {conteggio}</a>'
                
                st.html(f"""
                <div class="riga-pulsante-anteprima">
                    {html_bottone}
                    <img src="{img_path}" class="locandina-anteprima-rettangolare">
                </div>
                <div class='separatore-evento'></div>
                """)
    except Exception as e: st.error(f"Errore: {e}")

# Footer
st.markdown("""
<div style='position: fixed; bottom: 0; left: 0; width: 100%; background: #1f2124; padding: 15px; border-top: 3px solid #ff9100;'>
    <a href='?menu=home' target='_self' style='color: #ff9100; font-weight: bold; text-decoration: none;'>HOME</a>
</div>
""", unsafe_allow_html=True)
