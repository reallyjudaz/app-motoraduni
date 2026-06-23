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
    anno = int(re.search(r'\b(202\d)\b', testo).group(1)) if re.search(r'\b(202\d)\b', testo) else 2026
    giorno = int(re.search(r'\d+', testo).group(0)) if re.search(r'\d+', testo) else 1
    try: return pd.Timestamp(year=anno, month=mese_num, day=giorno)
    except: return pd.NaT

# --- 4. CSS ---
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=UnifrakturMaguntia&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Special+Elite&display=swap');
.stApp {{ background-color: #161719; }}
#MainMenu, footer, header {{visibility: hidden !important;}}
.block-container {{ padding-top: 2rem !important; padding-bottom: 9rem !important; }}
.online-counter {{ position: absolute; top: -10px; right: 15px; background: #1f2124; border: 1px solid #ff9100; padding: 4px 8px; border-radius: 12px; font-family: 'Special Elite'; font-size: 0.75rem; color: #ffffff; display: flex; align-items: center; gap: 6px; z-index: 99999; }}
.dot-online {{ width: 6px; height: 6px; background-color: #00ffcc; border-radius: 50%; display: inline-block; animation: lampeggia 1.5s infinite; }}
@keyframes lampeggia {{ 0% {{ opacity: 0.3; }} 50% {{ opacity: 1; }} 100% {{ opacity: 0.3; }} }}
.titolo-gotico {{ font-family: 'UnifrakturMaguntia', cursive !important; text-align: center; color: #ff9100 !important; font-size: 2.6rem !important; margin-top: -10px !important; }}
.sottotitolo {{ font-family: 'UnifrakturMaguntia', cursive !important; text-align: center; color: #ff9100 !important; font-size: 1.4rem !important; margin-bottom: 20px !important; }}
div[data-testid="stExpander"] details summary svg, div[data-testid="stExpander"] [data-testid="stExpanderIcon"] {{ display: none !important; }}
div[data-testid="stExpander"] details summary {{ background-color: #1f2124 !important; color: white !important; cursor: pointer !important; padding-left: 15px !important; }}
.streamlit-expanderHeader {{ color: #ff9100 !important; font-weight: bold !important; font-size: 1.0rem !important; background-color: #1f2124 !important; }}
div[data-testid="stExpander"] details summary p::after {{ content: "CLICK HERE FOR INFO"; display: block; color: #ff9100; font-family: 'Special Elite'; font-size: 0.75rem; margin-top: 4px; letter-spacing: 1px; }}
div[data-testid="stExpander"] details[open] summary p::after {{ content: "CHIUDI INFO"; color: #ff9100 !important; }}
.riga-pulsante-anteprima {{ display: flex !important; align-items: center !important; justify-content: flex-start !important; gap: 10px !important; width: 100% !important; margin-top: 5px !important; margin-bottom: 30px !important; }}
.html-btn-civado {{ background-color: #ff9100 !important; color: black !important; font-weight: bold !important; font-family: 'Special Elite', cursive !important; border-radius: 5px !important; height: 40px !important; padding: 0px 20px !important; font-size: 0.95rem !important; text-decoration: none !important; display: inline-flex !important; align-items: center !important; }}
.locandina-anteprima-rettangolare {{ height: 40px !important; width: auto !important; max-width: 80px !important; object-fit: contain !important; border: 2px solid #ff9100; border-radius: 5px; }}
.separatore-evento {{ margin-bottom: 35px !important; border-bottom: 1px dashed rgba(255, 145, 0, 0.15); padding-bottom: 10px; }}
.lightbox-target {{ position: fixed; top: 0; left: 0; width: 0; height: 100%; background: rgba(10, 10, 11, 0.98); opacity: 0; z-index: 100000; display: flex; flex-direction: column; align-items: center; justify-content: center; transition: opacity 0.2s; }}
.lightbox-target:target {{ width: 100%; opacity: 1; }}
.lightbox-target img {{ max-width: 98%; max-height: 85vh; border: 2px solid #ff9100; border-radius: 6px; }}
.lightbox-close-btn {{ margin-top: 15px; background-color: #ff9100 !important; color: black !important; padding: 8px 30px; border-radius: 5px; text-decoration: none; font-family: 'Special Elite'; }}
</style>
""", unsafe_allow_html=True)

# UI PRINCIPALE
st.markdown(f"<div class='online-counter'><span class='dot-online'></span><span>{utenti_online} Online</span></div>", unsafe_allow_html=True)
if os.path.exists("logo_custom.png"): st.image("logo_custom.png", use_container_width=True)
st.markdown("<h1 class='titolo-gotico'>Iron & Rubber</h1>", unsafe_allow_html=True)
st.markdown("<p class='sottotitolo'>«Non è la meta, è la strada a rivelare chi sei.»</p>", unsafe_allow_html=True)

if gc is not None:
    try:
        foglio = gc.open(NOME_DEL_FOGLIO)
        if st.session_state["page"] == "home":
            scheda = foglio.get_worksheet(0)
            dati = scheda.get_all_values()
            if len(dati) > 1:
                df = pd.DataFrame(dati[1:], columns=dati[0])
                df['GSheet_Row'] = df.index + 2
                # (Logica filtri omessa per brevità, resta quella che hai)
                
                for idx, row in df.iterrows():
                    riga_foglio = int(row['GSheet_Row'])
                    chiave_voto = f"{row['Nome Evento / Raduno']}_{row['Data']}"
                    img_path = str(row.get('Locandina', '')).strip()
                    ha_locandina = img_path.startswith("http")
                    
                    with st.expander(f"{row['Data']} - {row['Nome Evento / Raduno']}"):
                        st.write(f"📍 {row['Luogo']} - 📝 {row.get('Dettagli / Note', '')}")
                        if ha_locandina:
                            st.html(f'<a href="#zoom_{idx}"><img src="{img_path}" style="max-width:100%;"></a>')
                    
                    # --- BLOCCO BOTTONE + MINIATURA + TRATTINI ---
                    conteggio = int(pd.to_numeric(row.get('Partecipanti', 0), errors='coerce'))
                    html_bottone = f'<a href="?vota={idx}" target="_self" class="html-btn-civado">CI VADO 🔥 {conteggio}</a>'
                    
                    st.html(f"""
                    <div class="riga-pulsante-anteprima">
                        {html_bottone}
                        <a href="#zoom_{idx}"><img src="{img_path}" class="locandina-anteprima-rettangolare"></a>
                    </div>
                    <div class='separatore-evento'></div>
                    """)

                    if ha_locandina:
                        st.html(f"""<div class="lightbox-target" id="zoom_{idx}"><img src="{img_path}"><a class="lightbox-close-btn" href="#_">CHIUDI</a></div>""")
    except Exception as e: st.error(f"Errore: {e}")

# Footer
st.markdown("""
<div style='position: fixed; bottom: 0; left: 0; width: 100%; background: #1f2124; display: flex; justify-content: flex-start; gap: 30px; padding: 15px 20px; border-top: 3px solid #ff9100; z-index: 9999;'>
    <a href='?menu=home' target='_self' style='font-family: Special Elite; color: #ff9100; font-weight: bold; text-decoration: none; font-size: 1.2rem;'>HOME</a>
    <a href='?menu=mc' target='_self' style='font-family: Special Elite; color: #ff9100; font-weight: bold; text-decoration: none; font-size: 1.2rem;'>MC</a>
    <a href='?menu=admin' target='_self' style='font-family: Special Elite; color: #ff9100; font-weight: bold; text-decoration: none; font-size: 1.2rem;'>ADMIN</a>
</div>
""", unsafe_allow_html=True)
