import streamlit as st
import pandas as pd
import os
import re
import gspread
from google.oauth2 import service_account
import urllib.parse
import random
from datetime import datetime

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

# Controllo dei parametri URL per la navigazione dai tasti in basso
if "menu" in st.query_params:
    scelta_menu = st.query_params["menu"]
    if scelta_menu in ["home", "mc", "run", "admin"]:
        st.session_state["page"] = scelta_menu
    st.query_params.clear()
    st.rerun()

# Inizializzazione delle altre variabili di stato
if "sel_regione" not in st.session_state:
    st.session_state["sel_regione"] = "Tutte"
if "sel_mese" not in st.session_state:
    st.session_state["sel_mese"] = "Tutte"
if "evento_inviato" not in st.session_state:
    st.session_state["evento_inviato"] = False
if "giro_inviato" not in st.session_state:
    st.session_state["giro_inviato"] = False

# --- 2. CONNESSI A GOOGLE SHEETS (Secrets) ---
@st.cache_resource
def inizializza_connessione_google():
    try:
        credentials_info = dict(st.secrets["gcp_service_account"])
        if "private_key" in credentials_info:
            credentials_info["private_key"] = credentials_info["private_key"].replace("\\n", "\n")
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        credentials = service_account.Credentials.from_service_account_info(credentials_info, scopes=scopes)
        return gspread.authorize(credentials)
    except Exception as e:
        return None

gc = inizializza_connessione_google()
NOME_DEL_FOGLIO = "app motoraduni"
URL_APP = "https://app-motoraduni-6hqxxahyypkhyxmqmpsk2v.streamlit.app/"

# --- LISTA REGIONI STRUTTURATA ---
regioni_italia = ["Abruzzo", "Basilicata", "Calabria", "Campania", "Emilia-Romagna", 
                  "Friuli-Venezia Giulia", "Lazio", "Liguria", "Lombardia", "Marche", "Molise", 
                  "Piemonte", "Puglia", "Sardegna", "Sicilia", "Toscana", "Trentino-Alto Adige", 
                  "Umbria", "Valle d'Aosta", "Veneto"]

# --- 3. FUNZIONI DATI ---
if "voti_locali" not in st.session_state:
    st.session_state["voti_locali"] = set()

def registra_voto(chiave_evento):
    st.session_state["voti_locali"].add(str(chiave_evento))

def ha_gia_votato(chiave_evento):
    return str(chiave_evento) in st.session_state["voti_locali"]

def parsing_data_biker(testo_data):
    """
    Estrae la DATA DI FINE dell'evento per evitare che un raduno di più giorni
    venga rimosso prima del suo ultimo giorno.
    """
    testo = str(testo_data).lower().strip()
    if not testo or testo in ["nan", "vedi nel sito", "vedi nel file", "none"]:
        return pd.NaT

    mesi_map = {
        'gennaio': 1, 'gen': 1, 'febbraio': 2, 'feb': 2, 'marzo': 3, 'mar': 3,
        'aprile': 4, 'apr': 4, 'maggio': 5, 'mag': 5, 'giugno': 6, 'giu': 6,
        'luglio': 7, 'lug': 7, 'agosto': 8, 'ago': 8, 'settembre': 9, 'set': 9,
        'ottobre': 10, 'ott': 10, 'novembre': 11, 'nov': 11, 'dicembre': 12, 'dic': 12
    }

    # 1. Trova l'anno (es. 2026, 2027...)
    anno_match = re.findall(r'\b(202\d|203\d)\b', testo)
    anno = int(anno_match[-1]) if anno_match else 2026

    # 2. Cerca pattern di date con cifre (es. 28/29/30/08/2026 o 28/08 - 02/09/2026)
    matches_ddmm = re.findall(r'(\d{1,2})[/.-](\d{1,2})(?:[/.-](20\d\d))?', testo)

    if matches_ddmm:
        # Scorre i match al contrario per prendere l'ultima data di fine valida
        for u_giorno, u_mese, u_anno in reversed(matches_ddmm):
            g, m = int(u_giorno), int(u_mese)
            a = int(u_anno) if u_anno else anno
            if 1 <= g <= 31 and 1 <= m <= 12:
                try:
                    return pd.Timestamp(year=a, month=m, day=g)
                except:
                    pass

    # 3. Cerca mesi in formato testo (es. "dal 28 al 29 agosto 2027" o "12 - 13 - 14 Giugno 2026")
    mesi_trovati = []
    parole = re.findall(r'\b[a-z]+\b', testo)
    for parola in parole:
        for k, v in mesi_map.items():
            if parola == k or (len(parola) >= 3 and parola.startswith(k)):
                mesi_trovati.append(v)
                break

    if mesi_trovati:
        mese_fine = mesi_trovati[-1]  # Prende l'ultimo mese citato (utile per eventi a cavallo di 2 mesi)
        numeri = [int(n) for n in re.findall(r'\b\d{1,2}\b', testo)]
        giorni_validi = [n for n in numeri if 1 <= n <= 31 and n != mese_fine]
        if giorni_validi:
            giorno_fine = max(giorni_validi)  # Prende il giorno più alto
            try:
                return pd.Timestamp(year=anno, month=mese_fine, day=giorno_fine)
            except:
                pass

    # Fallback standard
    try:
        return pd.to_datetime(testo, dayfirst=True, errors='coerce')
    except:
        return pd.NaT

# --- 4. CSS INTEGRATO E COLORI ---
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=UnifrakturMaguntia&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Special+Elite&display=swap');

.stApp {{ background-color: #161719; }}
#MainMenu, footer, header {{visibility: hidden !important;}}
.block-container {{ padding-top: 2rem !important; padding-bottom: 9rem !important; }}

.online-counter {{
    position: absolute;
    top: -10px;
    right: 15px;
    background: #1f2124;
    border: 1px solid #ff9100;
    padding: 4px 8px;
    border-radius: 12px;
    font-family: 'Special Elite', cursive;
    font-size: 0.75rem;
    color: #ffffff;
    display: flex;
    align-items: center;
    gap: 6px;
    z-index: 99999;
}}
.dot-online {{
    width: 6px;
    height: 6px;
    background-color: #00ffcc;
    border-radius: 50%;
    display: inline-block;
    animation: lampeggia 1.5s infinite;
}}
@keyframes lampeggia {{
    0% {{ opacity: 0.3; }}
    50% {{ opacity: 1; }}
    100% {{ opacity: 0.3; }}
}}

.titolo-gotico {{ font-family: 'UnifrakturMaguntia', cursive !important; text-align: center; color: #ff9100 !important; font-size: 2.6rem !important; margin-top: -10px !important; }}
.sottotitolo {{ font-family: 'UnifrakturMaguntia', cursive !important; text-align: center; color: #ff9100 !important; font-size: 1.4rem !important; margin-bottom: 20px !important; }}

.stExpander {{ 
    background-color: #1f2124 !important; 
    border: 2px solid #ff9100 !important; 
    border-radius: 10px !important; 
    color: white !important; 
    margin-bottom: 4px !important;
}}

div[data-testid="stExpander"] details summary svg,
div[data-testid="stExpander"] [data-testid="stExpanderIcon"] {{
    display: none !important;
}}
div[data-testid="stExpander"] details summary {{
    padding-left: 15px !important;
    background-color: #1f2124 !important;
    color: white !important;
    cursor: pointer !important;
}}

div[data-testid="stExpander"] details summary, 
div[data-testid="stExpander"] details summary:hover, 
div[data-testid="stExpander"] details summary:focus,
div[data-testid="stExpander"] details summary:active,
div[data-testid="stExpander"] details[open] summary {{
    background-color: #1f2124 !important;
    color: white !important;
}}

.streamlit-expanderHeader {{ 
    color: #ff9100 !important; 
    font-weight: bold !important; 
    font-size: 1.0rem !important; 
    background-color: #1f2124 !important;
}}
div[data-testid="stExpander"] details summary p {{
    color: white !important;
    width: 100% !important;
    margin-bottom: 0px !important;
}}

div[data-testid="stExpander"] details summary p::after {{
    content: "CLICK HERE FOR INFO";
    display: block;
    color: #ff9100;
    font-family: 'Special Elite', cursive;
    font-size: 0.75rem;
    margin-top: 4px;
    letter-spacing: 1px;
}}
div[data-testid="stExpander"] details[open] summary p::after {{
    content: "CHIUDI INFO";
    color: #8a8d93;
}}

div[data-testid="stButton"] button, div[data-testid="stFormSubmitButton"] button {{ 
    background-color: #ff9100 !important; 
    color: black !important; 
    font-weight: bold !important; 
    font-family: 'Special Elite', cursive !important; 
    border-radius: 5px !important; 
    height: 42px !important; 
    width: 100%;
}}

div[data-testid="stHorizontalBlock"] {{
    display: flex !important;
    flex-direction: row !important;
    gap: 8px !important;
    width: 100% !important;
    align-items: center !important;
    margin-bottom: 20px !important;
}}
div[data-testid="stHorizontalBlock"] > div {{
    flex: 1 1 0% !important;
    min-width: 0 !important;
}}

label, .stTextInput label, .stTextArea label {{ color: white !important; }}

div[data-testid="stSelectbox"] > label {{
    color: #ff9100 !important;
    font-family: 'Special Elite', cursive !important;
    font-size: 0.85rem !important;
    margin-bottom: 2px !important;
}}
div[data-testid="stSelectbox"] div[data-baseweb="select"] {{
    background-color: #ffffff !important;
    border: 2px solid #ff9100 !important;
    border-radius: 5px !important;
}}
div[data-testid="stSelectbox"] div[data-baseweb="select"] div {{
    color: #000000 !important;
    font-family: 'Special Elite', cursive !important;
    font-size: 0.85rem !important;
}}

.card-mc {{
    background-color: #1f2124;
    border: 2px solid #ff9100;
    border-radius: 10px;
    padding: 15px;
    margin-bottom: 20px;
    color: white;
    display: flex;
    flex-direction: column;
    gap: 10px;
}}
.titolo-mc {{
    color: #ff9100;
    font-family: 'Special Elite', cursive;
    font-size: 1.3rem;
    margin-bottom: 2px;
}}
.citta-mc {{
    color: #00ffcc;
    font-size: 0.9rem;
    font-family: 'Special Elite', cursive;
    margin-bottom: 5px;
}}
.info-mc {{
    font-size: 0.95rem;
    line-height: 1.4;
    margin-bottom: 5px;
}}
.logo-container-mc {{
    text-align: center;
    margin-top: 5px;
    padding-top: 10px;
    border-top: 1px dashed rgba(255, 145, 0, 0.3);
}}
.logo-standard-mc {{
    width: 130px !important;
    height: 130px !important;
    object-fit: contain !important;
    border-radius: 5px;
    background-color: transparent;
}}

.maps-link {{
    text-decoration: none !important;
    font-size: 1.1rem;
    margin-left: 6px;
    display: inline-flex;
    align-items: center;
    vertical-align: middle;
    transition: transform 0.2s;
}}
.maps-link:hover {{
    transform: scale(1.2);
}}

.locandina-cliccabile {{
    width: 100%;
    max-width: 100%;
    height: auto;
    border-radius: 6px;
    border: 1px solid rgba(255, 145, 0, 0.4);
    cursor: pointer;
    transition: transform 0.2s;
}}
.locandina-cliccabile:hover {{
    transform: scale(1.01);
}}
.testo-aiuto-zoom {{
    color: #8a8d93;
    font-size: 0.8rem;
    font-family: 'Special Elite', cursive;
    margin-top: -8px;
    margin-bottom: 15px;
    text-align: center;
}}

.lightbox-target {{
    position: fixed;
    top: 0;
    left: 0;
    width: 0;
    height: 100%;
    background: rgba(10, 10, 11, 0.98);
    opacity: 0;
    overflow: hidden;
    z-index: 100000;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    transition: opacity 0.2s ease;
}}
.lightbox-target:target {{
    width: 100%;
    opacity: 1;
    bottom: 0;
    right: 0;
    left: 0;
}}
.lightbox-target img {{
    max-width: 98% !important;
    max-height: 85vh !important;
    object-fit: contain !important;
    border: 2px solid #ff9100;
    border-radius: 6px;
    box-shadow: 0px 0px 25px rgba(255, 145, 0, 0.5);
}}
.lightbox-close-btn {{
    margin-top: 15px;
    background-color: #ff9100 !important;
    color: black !important;
    font-family: 'Special Elite', cursive !important;
    font-weight: bold !important;
    text-decoration: none !important;
    padding: 8px 30px;
    border-radius: 5px;
    font-size: 0.95rem;
    letter-spacing: 1px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.4);
    text-align: center;
}}
.lightbox-close-btn:hover {{
    background-color: #e07f00 !important;
}}

.riga-pulsante-anteprima {{
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    gap: 10px !important;
    width: 100% !important;
    margin-top: 2px !important;
}}

.html-btn-civado {{
    background-color: #ff9100 !important;
    color: black !important;
    font-weight: bold !important;
    font-family: 'Special Elite', cursive !important;
    border-radius: 5px !important;
    height: 42px !important;
    padding: 0px 10px !important;
    font-size: 0.85rem !important;
    border: none !important;
    cursor: pointer !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-decoration: none !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    flex-grow: 1 !important;
}}
.html-btn-civado:hover {{
    background-color: #e07f00 !important;
}}
.html-btn-disabilitato {{
    background-color: #555555 !important;
    color: #bbbbbb !important;
    cursor: not-allowed !important;
}}

.html-btn-condividi {{
    background-color: #ff9100 !important;
    color: black !important;
    font-weight: bold !important;
    font-family: 'Special Elite', cursive !important;
    border-radius: 5px !important;
    height: 42px !important;
    padding: 0px 10px !important;
    font-size: 0.85rem !important;
    border: none !important;
    cursor: pointer !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 8px !important;
    text-decoration: none !important;
    width: 40% !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}}
.html-btn-condividi:hover {{
    background-color: #e07f00 !important;
    color: black !important;
}}

.locandina-anteprima-rettangolare {{
    height: 42px !important;
    width: auto !important;
    max-width: 55px !important;
    object-fit: contain !important;
    border: 2px solid #ff9100;
    border-radius: 5px;
    box-shadow: 0px 0px 10px rgba(255, 145, 0, 0.4);
    flex-shrink: 0 !important;
}}
.locandina-anteprima-rettangolare:hover {{
    transform: scale(1.05);
}}

.box-commenti {{ background-color: #1f2124; border: 1px dashed #ff9100; border-radius: 8px; padding: 12px; margin-top: 10px; margin-bottom: 15px; }}
.singolo-commento {{ border-bottom: 1px solid #333; padding: 6px 0px; font-size: 0.88rem; color: #ddd; }}
.singolo-commento b {{ color: #ff9100; }}
.html-btn-mappa {{
    background-color: #00ffcc !important;
    color: black !important;
    font-weight: bold !important;
    font-family: 'Special Elite', cursive !important;
    border-radius: 5px !important;
    height: 42px !important;
    padding: 0px 15px !important;
    font-size: 0.85rem !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-decoration: none !important;
    width: 100% !important;
}}
</style>

<div class="online-counter">
    <span class="dot-online"></span>
    <span>{utenti_online} Online</span>
</div>

<script type="text/javascript">
var sc_project={SC_PROJECT}; 
var sc_invisible=1; 
var sc_security="{SC_SECURITY}"; 
</script>
<script type="text/javascript" src="https://www.statcounter.com/counter/counter.js" async></script>
<noscript><div class="statcounter"><a title="Web Analytics" href="https://statcounter.com/" target="_blank"><img class="statcounter" src="https://c.statcounter.com/{SC_PROJECT}/0/{SC_SECURITY}/1/" alt="Web Analytics" referrerpolicy="no-referrer-when-downgrade"></a></div></noscript>
""", unsafe_allow_html=True)

if os.path.exists("logo_custom.png"):
    st.image("logo_custom.png", use_container_width=True)

st.markdown("<h1 class='titolo-gotico'>Iron & Rubber</h1>", unsafe_allow_html=True)
st.markdown("<p class='sottotitolo'>«Non è la meta, è la strada a rivelare chi sei.»</p>", unsafe_allow_html=True)

if gc is None:
    st.error("Errore critico nella connessione a Google Cloud.")
else:
    try:
        foglio_di_calcolo = gc.open(NOME_DEL_FOGLIO)
        
        # =========================================================
        # SCHERMATA 1: HOME (LISTA MOTORADUNI)
        # =========================================================
        if st.session_state["page"] == "home":
            scheda = foglio_di_calcolo.get_worksheet(0)
            
            try:
                scheda_da_verificare = foglio_di_calcolo.worksheet("da verificare")
            except:
                scheda_da_verificare = foglio_di_calcolo.add_worksheet(title="da verificare", rows=100, cols=20)
                scheda_da_verificare.append_row(["Nome Evento / Raduno", "Data", "Luogo", "Regione", "Dettagli / Note", "Locandina", "Partecipanti"])
                
            colonne_esatte = ["Nome Evento / Raduno", "Data", "Luogo", "Regione", "Dettagli / Note", "Locandina", "Partecipanti"]
            
            tutti_i_dati = scheda.get_all_values()
            if tutti_i_dati and len(tutti_i_dati) > 1:
                righe_pulite = []
                for riga in tutti_i_dati[1:]:
                    riga_7 = (riga + [""] * 7)[:7]
                    righe_pulite.append(riga_7)
                df = pd.DataFrame(righe_pulite, columns=colonne_esatte)
            else:
                df = pd.DataFrame(columns=colonne_esatte)

            # --- FORM UTENTE ---
            with st.expander("➕ AGGIUNGI EVENTO"):
                if st.session_state["evento_inviato"]:
                    st.markdown("""
                    <div style='background-color: #1f2124; border: 2px solid #ff9100; padding: 15px; border-radius: 8px; text-align: center; color: white; font-family: "Special Elite", cursive; margin-bottom: 20px;'>
                        🔥 Grazie per la tua segnalazione!<br>
                        Il raduno è stato inviato al nostro team e verrà pubblicato non appena verificato.<br><br>
                        Per modifiche o comunicazioni urgenti puoi scrivere a:<br> 
                        <strong style='color: #ff9100;'>ironandrubbercustom@gmail.com</strong>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("Aggiungi un altro evento"):
                        st.session_state["evento_inviato"] = False
                        st.rerun()
                else:
                    with st.form("add_form", clear_on_submit=True):
                        n = st.text_input("Nome Evento")
                        d = st.text_input("Data (es: 28/29/30/08/2026)")
                        l = st.text_input("Luogo (Città, Via, ecc.)")
                        reg_scelta = st.selectbox("Seleziona Regione", regioni_italia, key="add_regione_form")
                        i = st.text_area("Info")
                        url_inserito = st.text_input("Link della Locandina (es. da Postimages)")
                     
                        if st.form_submit_button("SALVA"):
                            path_finale = url_inserito.strip()
                            scheda_da_verificare.append_row([n, d, l, reg_scelta, i, path_finale, 0])
                            st.session_state["evento_inviato"] = True
                            st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center; color: #ff9100; font-family: \"Special Elite\", cursive; font-size: 1.4rem;'>Prossimi eventi</h3>", unsafe_allow_html=True)

            if not df.empty:
                df['GSheet_Row'] = df.index + 2
                df['Data_Date'] = df['Data'].apply(parsing_data_biker)
                df['Regione'] = df['Regione'].replace("", "Da definire").fillna("Da definire")
                
                oggi = pd.Timestamp.now().normalize()
                df = df[(df['Data_Date'].isna()) | (df['Data_Date'] >= oggi)]

                df = df.sort_values(by='Data_Date', ascending=True, na_position='last')
                df['Partecipanti'] = pd.to_numeric(df['Partecipanti'], errors='coerce').fillna(0).astype(int)

                opzioni_regioni = ["Tutte"] + regioni_italia
                mesi_ita = {1: 'Gennaio', 2: 'Febbraio', 3: 'Marzo', 4: 'Aprile', 5: 'Maggio', 6: 'Giugno', 
                            7: 'Luglio', 8: 'Agosto', 9: 'Settembre', 10: 'Ottobre', 11: 'Novembre', 12: 'Dicembre'}
                
                df['Mese_Filtro'] = df['Data_Date'].apply(lambda x: f"{mesi_ita[x.month]} {x.year}" if pd.notna(x) else "Da definire")
                opzioni_mesi = ["Tutte"] + [m for m in list(df['Mese_Filtro'].unique()) if m != "Da definire"]

                col_regione, col_data = st.columns(2)
                with col_regione:
                    regione_scelta = st.selectbox("Regione", opzioni_regioni, key="sel_regione")
                with col_data:
                    mese_scelto = st.selectbox("Mese", opzioni_mesi, key="sel_mese")

                ifDoc = df.copy()
                if regione_scelta != "Tutte":
                    ifDoc = ifDoc[ifDoc['Regione'].str.strip().str.lower() == regione_scelta.strip().lower()]
                if mese_scelto != "Tutte":
                    ifDoc = ifDoc[ifDoc['Mese_Filtro'] == mese_scelto]

                if not ifDoc.empty:
                    for idx, row in ifDoc.iterrows():
                        riga_foglio_google = int(row['GSheet_Row'])
                        chiave_voto = f"{row['Nome Evento / Raduno']}_{row['Data']}"
                        
                        img_path = str(row.get('Locandina', '')).strip()
                        ha_locandina = img_path.startswith("http")
                        
                        # --- 1. EXPANDER CON INFO E MODIFICA ---
                        with st.expander(f"{row['Data']} - {row['Nome Evento / Raduno']}"):
                            stringa_luogo = f"{row['Luogo']} {row['Regione']}"
                            stringa_safe = urllib.parse.quote_plus(stringa_luogo)
                            url_maps = f"https://www.google.com/maps/search/?api=1&query={stringa_safe}"
                            
                            st.markdown(f"📍 **Luogo:** {row['Luogo']} ({row['Regione']}) <a href='{url_maps}' target='_blank' class='maps-link' title='Apri Navigatore Maps'>🗺️</a>", unsafe_allow_html=True)
                            st.write(f"📝 **Info:** {row.get('Dettagli / Note', 'Nessuna info')}")
                            
                            if ha_locandina:
                                st.html(f"""
                                <a href="#zoom_{idx}">
                                    <img src="{img_path}" class="locandina-cliccabile" alt="Locandina">
                                </a>
                                <div class="testo-aiuto-zoom">🔍 Clicca sulla locandina per aprirla a schermo intero</div>
                                """)

                            pwd = st.text_input(f"Password per modificare {idx}", type="password", key=f"p_{idx}")
                            if pwd == "Judaz2026":
                                st.markdown("<div style='color: #00ffcc; font-size: 0.9rem; font-weight: bold;'>⚙️ MODALITÀ MODIFICA ATTIVA</div>", unsafe_allow_html=True)
                                
                                new_title = st.text_input(f"Modifica Titolo", value=str(row.get('Nome Evento / Raduno', '')), key=f"title_{idx}")
                                new_data = st.text_input(f"Modifica Data (Testo)", value=str(row.get('Data', '')), key=f"data_{idx}")
                                new_luogo = st.text_input(f"Modifica Luogo", value=str(row.get('Luogo', '')), key=f"luogo_{idx}")
                                
                                r_attuale = str(row.get('Regione', 'Abruzzo')).strip()
                                idx_regione = 0
                                if r_attuale in regioni_italia:
                                    idx_regione = regioni_italia.index(r_attuale)
                                new_regione = st.selectbox(f"Modifica Regione", regioni_italia, index=idx_regione, key=f"reg_{idx}")
                                
                                new_info = st.text_area(f"Modifica Info / Note", value=str(row.get('Dettagli / Note', '')), key=f"info_{idx}")
                                new_locandina = st.text_input(f"Modifica Link Locandina", value=img_path, key=f"loc_{idx}")
                                
                                if st.button("SALVA MODIFICHE", key=f"save_{idx}"):
                                    scheda.update_cell(riga_foglio_google, 1, new_title)
                                    scheda.update_cell(riga_foglio_google, 2, new_data)
                                    scheda.update_cell(riga_foglio_google, 3, new_luogo)
                                    scheda.update_cell(riga_foglio_google, 4, new_regione)
                                    scheda.update_cell(riga_foglio_google, 5, new_info)
                                    scheda.update_cell(riga_foglio_google, 6, new_locandina.strip())
                                    st.rerun()
                                    
                                if st.button("❌ ELIMINA EVENTO", key=f"delete_{idx}"):
                                    scheda.delete_rows(riga_foglio_google)
                                    st.rerun()

                        # --- LIGHTBOX GLOBALE ---
                        if ha_locandina:
                            st.html(f"""
                            <div class="lightbox-target" id="zoom_{idx}">
                                <img src="{img_path}" alt="Zoom Locandina">
                                <a class="lightbox-close-btn" href="#_">← TORNA ALL'EVENTO</a>
                            </div>
                            """)

                        # =========================================================
                        # 2. BLOCCO PULSANTI RESPONSIVE
                        # =========================================================
                        conteggio = int(row['Partecipanti'])
                        testo_condivisione = f"🏍️ {row['Nome Evento / Raduno']}\n📅 Data: {row['Data']}\n📍 Luogo: {row['Luogo']} ({row['Regione']})\n🔗 Guarda su Iron & Rubber: {URL_APP}"
                        url_whatsapp = f"https://api.whatsapp.com/send?text={urllib.parse.quote(testo_condivisione)}"

                        col_btn1, col_btn2 = st.columns(2)

                        with col_btn1:
                            if ha_locandina:
                                gia_votato = ha_gia_votato(chiave_voto)
                                if gia_votato:
                                    html_bottone = f'<div class="html-btn-civado html-btn-disabilitato">CI VADO 🔥 {conteggio}</div>'
                                else:
                                    html_bottone = f'<a href="?vota={idx}" target="_self" class="html-btn-civado">CI VADO 🔥 {conteggio}</a>'
                                
                                st.html(f"""
                                <div class="riga-pulsante-anteprima">
                                    {html_bottone}
                                    <a href="#zoom_{idx}">
                                        <img src="{img_path}" class="locandina-anteprima-rettangolare" alt="Preview">
                                    </a>
                                </div>
                                """)
                                
                                if f"vota" in st.query_params and st.query_params["vota"] == str(idx):
                                    if not gia_votato:
                                        scheda.update_cell(riga_foglio_google, 7, int(conteggio + 1))
                                        registra_voto(chiave_voto)
                                        st.query_params.clear()
                                        st.rerun()
                            else:
                                label_btn = f"CI VADO 🔥 {conteggio}"
                                if ha_gia_votato(chiave_voto):
                                    st.button(label_btn, key=f"btn_{idx}", disabled=True)
                                else:
                                    if st.button(label_btn, key=f"btn_{idx}"):
                                        scheda.update_cell(riga_foglio_google, 7, int(conteggio + 1))
                                        registra_voto(chiave_voto)
                                        st.rerun()

                        with col_btn2:
                            svg_share = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg>'
                            st.html(f"""
                            <a href="{url_whatsapp}" target="_blank" class="html-btn-condividi">
                                {svg_share} SHARE
                            </a>
                            """)
                            
                else:
                    st.info("Nessun evento trovato con i filtri selezionati.")
            else:
                st.info("Il database su Google Sheets è vuoto.")

        # =========================================================
        # SCHERMATA 2: PAGINA MOTOCLUB
        # =========================================================
        elif st.session_state["page"] == "mc":
            st.markdown("<h3 style='text-align: center; color: #ff9100; font-family: \"Special Elite\", cursive;'>I MOTO CLUB</h3>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: white; font-family: \"Special Elite\", cursive; font-size:0.9rem;'>«I club che hanno fatto la storia, le nostre origini. Where passion becomes brotherhood.»</p><br>", unsafe_allow_html=True)
            
            try:
                scheda_mc = foglio_di_calcolo.worksheet("motoclub")
                dati_mc = scheda_mc.get_all_values()
            except:
                scheda_mc = foglio_di_calcolo.add_worksheet(title="motoclub", rows=100, cols=10)
                scheda_mc.append_row(["Nome MotoClub", "Città", "Descrizione / Info", "Logo"])
                dati_mc = [["Nome MotoClub", "Città", "Descrizione / Info", "Logo"]]

            if len(dati_mc) > 1:
                for row_mc in dati_mc[1:]:
                    row_mc = (row_mc + [""] * 4)[:4]
                    nome_mc, citta_mc, info_mc, logo_mc = row_mc
                    
                    html_immagine = ""
                    if logo_mc.strip().startswith("http"):
                        id_safe = nome_mc.replace(' ', '_').replace("'", "_")
                        html_immagine = f"""
                        <div class="logo-container-mc">
                            <a href="#zoom_mc_{id_safe}">
                                <img src="{logo_mc.strip()}" class="logo-standard-mc" alt="Logo">
                            </a>
                        </div>
                        <div class="lightbox-target" id="zoom_mc_{id_safe}">
                            <img src="{logo_mc.strip()}" alt="Zoom Logo Club">
                            <a class="lightbox-close-btn" href="#_">← TORNA AI CLUB</a>
                        </div>
                        """
                    
                    st.html(f"""
                    <div class="card-mc">
                        <div class="titolo-mc">⚡ {nome_mc}</div>
                        <div class="citta-mc">📍 Sede: {citta_mc}</div>
                        <div class="info-mc">{info_mc}</div>
                        {html_immagine}
                    </div>
                    """)
            else:
                st.info("Nessun MotoClub registrato al momento. Aggiungili dal tuo file Google Sheets nella scheda 'motoclub'!")

        # =========================================================
        # SCHERMATA 3: RUN & ITINERARI
        # =========================================================
        elif st.session_state["page"] == "run":
            st.markdown("<h3 style='text-align: center; color: #ff9100; font-family: \"Special Elite\", cursive;'>RUN & ITINERARI BIKER</h3>", unsafe_allow_html=True)
            
            st.markdown("""
            <div style='text-align: center; color: white; font-family: "Special Elite", cursive; font-size: 0.95rem; line-height: 1.5; margin-bottom: 20px;'>
                🗺️ <b>Condividi e scopri i migliori percorsi provati dalla community Biker!</b><br>
                Inserisci la mappa del tuo giro preferito per consigliarlo agli altri fratelli della strada, vota gli itinerari più belli e lascia un commento.
            </div>
            """, unsafe_allow_html=True)

            with st.expander("➕ CARICA UN NUOVO GIRO / MAPPA"):
                if st.session_state["giro_inviato"]:
                    st.success("🔥 Giro caricato con successo e visibile alla community!")
                    if st.button("Invia un altro percorso"):
                        st.session_state["giro_inviato"] = False
                        st.rerun()
                else:
                    with st.form("form_nuovo_giro", clear_on_submit=True):
                        titolo_giro = st.text_input("Nome del Giro / Passi", placeholder="es. Anello del Passo dello Stelvio")
                        autore = st.text_input("Il tuo Nome / Nickname / MC", placeholder="es. Biker84")
                        regione_giro = st.selectbox("Regione principale:", regioni_italia)
                        km_totali = st.text_input("Distanza (es. 180 km)", placeholder="180")
                        stile_strada = st.selectbox("Tipo di percorso:", [
                            "Piega & Tornanti 🏍️",
                            "Panoramico / Relax 🌅",
                            "Off-Road / Enduro 🪵",
                            "Misto 🛣️"
                        ])
                        link_gmaps = st.text_input("Link Mappa Google Maps / Waze*", placeholder="https://maps.google.com/...")
                        sosta_bar = st.text_input("Sosta Birra/Ristoro Consigliata (Opzionale)")
                        note_percorso = st.text_area("Note / Consigli di guida")

                        if st.form_submit_button("PUBBLICA RUN 🗺️"):
                            if not titolo_giro.strip() or not link_gmaps.strip():
                                st.error("Inserisci almeno il Nome del Giro e il Link della Mappa!")
                            else:
                                try:
                                    try:
                                        ws_giri = foglio_di_calcolo.worksheet("giri")
                                    except:
                                        ws_giri = foglio_di_calcolo.add_worksheet(title="giri", rows=100, cols=10)
                                        ws_giri.append_row(["TITOLO", "AUTORE", "REGIONE", "KM", "STILE", "LINK_MAPPA", "SOSTA", "NOTE", "VOTI"])

                                    ws_giri.append_row([
                                        titolo_giro, autore, regione_giro, km_totali, 
                                        stile_strada, link_gmaps.strip(), sosta_bar, note_percorso, 0
                                    ])
                                    st.session_state["giro_inviato"] = True
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Errore nel salvataggio: {e}")

            st.markdown("<br>", unsafe_allow_html=True)

            try:
                df_commenti = pd.DataFrame()
                try:
                    ws_comm = foglio_di_calcolo.worksheet("commenti_giri")
                    d_comm = ws_comm.get_all_values()
                    if len(d_comm) > 1:
                        df_commenti = pd.DataFrame(d_comm[1:], columns=d_comm[0])
                        df_commenti.columns = df_commenti.columns.str.strip()
                except:
                    pass

                ws_giri = foglio_di_calcolo.worksheet("giri")
                dati_giri = ws_giri.get_all_values()

                if len(dati_giri) > 1:
                    headers_giri = dati_giri[0]
                    df_giri = pd.DataFrame(dati_giri[1:], columns=headers_giri)
                    df_giri.columns = df_giri.columns.str.strip()

                    col_idx_voti = headers_giri.index("VOTI") + 1 if "VOTI" in headers_giri else 9

                    for idx, riga in df_giri.iterrows():
                        riga_sheet = int(idx) + 2
                        chiave_giro = f"giro_like_{riga_sheet}_{riga.get('TITOLO','')}"
                        
                        titolo_g = riga.get("TITOLO", "Giro Biker")
                        reg_g = riga.get("REGIONE", "Italia")
                        km_g = riga.get("KM", "N.D.")
                        stile_g = riga.get("STILE", "Misto")
                        link_g = riga.get("LINK_MAPPA", "#")
                        autore_g = riga.get("AUTORE", "Anonimo")
                        sosta_g = riga.get("SOSTA", "")
                        note_g = riga.get("NOTE", "")
                        voti_g = int(riga.get("VOTI", 0)) if str(riga.get("VOTI", 0)).isdigit() else 0

                        with st.expander(f"🗺️ {titolo_g} ({reg_g})"):
                            st.markdown(f"""
                            👤 <b>Creato da:</b> {autore_g}<br>
                            📏 <b>Distanza:</b> {km_g} KM<br>
                            🛣️ <b>Stile:</b> {stile_g}<br>
                            {f'🍻 <b>Sosta Consigliata:</b> {sosta_g}<br>' if sosta_g else ''}
                            📝 <b>Note:</b> {note_g if note_g else 'Nessun dettaglio aggiuntivo.'}
                            """, unsafe_allow_html=True)
                            
                            st.markdown("<br><b>💬 Commenti della Community:</b>", unsafe_allow_html=True)
                            
                            commenti_giro = df_commenti[df_commenti["ID_GIRO"] == str(riga_sheet)] if not df_commenti.empty and "ID_GIRO" in df_commenti.columns else pd.DataFrame()
                            
                            if not commenti_giro.empty:
                                html_c = '<div class="box-commenti">'
                                for _, c_row in commenti_giro.iterrows():
                                    html_c += f'<div class="singolo-commento"><b>{c_row.get("AUTORE","Anonimo")}</b> ({c_row.get("DATA","")}): {c_row.get("COMMENTO","")}</div>'
                                html_c += '</div>'
                                st.markdown(html_c, unsafe_allow_html=True)
                            else:
                                st.markdown("<p style='color:#8a8d93; font-size:0.85rem;'>Nessun commento ancora. Scrivine uno tu!</p>", unsafe_allow_html=True)

                            with st.form(f"form_comm_{riga_sheet}", clear_on_submit=True):
                                c_autore = st.text_input("Il tuo Nome", key=f"c_aut_{riga_sheet}")
                                c_testo = st.text_input("Scrivi un commento...", key=f"c_txt_{riga_sheet}")
                                if st.form_submit_button("INVIA COMMENTO 💬"):
                                    if c_testo.strip():
                                        try:
                                            try:
                                                ws_comm = foglio_di_calcolo.worksheet("commenti_giri")
                                            except:
                                                ws_comm = foglio_di_calcolo.add_worksheet(title="commenti_giri", rows=100, cols=4)
                                                ws_comm.append_row(["ID_GIRO", "AUTORE", "COMMENTO", "DATA"])

                                            data_oggi = datetime.now().strftime("%d/%m/%Y %H:%M")
                                            ws_comm.append_row([str(riga_sheet), c_autore if c_autore.strip() else "Anonimo", c_testo, data_oggi])
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Errore invio commento: {e}")

                        c_g1, c_g2 = st.columns(2)
                        with c_g1:
                            if link_g and link_g != "#":
                                st.html(f'<a href="{link_g}" target="_blank" class="html-btn-mappa">APRI MAPPA 🗺️</a>')
                        with c_g2:
                            label_like = f"MI PIACE 👍 {voti_g}"
                            if ha_gia_votato(chiave_giro):
                                st.button(label_like, key=f"like_{riga_sheet}", disabled=True)
                            else:
                                if st.button(label_like, key=f"like_{riga_sheet}"):
                                    ws_giri.update_cell(riga_sheet, col_idx_voti, voti_g + 1)
                                    registra_voto(chiave_giro)
                                    st.rerun()
                else:
                    st.info("Nessun giro ancora caricato. Sii il primo a pubblicarne uno!")
            except Exception as e:
                st.info("La sezione Giri è pronta. Compila il form sopra per inaugurarla!")

        # =========================================================
        # SCHERMATA 4: ADMIN
        # =========================================================
        elif st.session_state["page"] == "admin":
            scheda = foglio_di_calcolo.get_worksheet(0)
            st.markdown("<h3 style='color: #ff9100; font-family: \"Special Elite\", cursive; text-align: center;'>Pannello Admin</h3>", unsafe_allow_html=True)
            pass_admin = st.text_input("Inserisci Password Amministratore", type="password", key="password_principale_admin")
            
            if pass_admin == "Judaz2026":
                st.markdown("<div style='color: #00ffcc; font-weight: bold; font-family: \"Special Elite\"; text-align: center;'>🔓 ACCESSO CONCESSO. SEI ONLINE.</div>", unsafe_allow_html=True)
                with st.form("admin_direct_form", clear_on_submit=True):
                    adm_n = st.text_input("Nome Evento")
                    adm_d = st.text_input("Data (es: 28/29/30/08/2026)")
                    adm_l = st.text_input("Luogo (Città)")
                    adm_reg = st.selectbox("Seleziona Regione", regioni_italia, key="admin_regione_form")
                    adm_i = st.text_area("Dettagli / Info")
                    adm_url = st.text_input("Link Locandina")
                    
                    if st.form_submit_button("PUBBLICA DIRETTAMENTE ONLINE"):
                        if adm_n and adm_d:
                            scheda.append_row([adm_n, adm_d, adm_l, adm_reg, adm_i, adm_url.strip(), 0])
                            st.success("🔥 Evento pubblicato istantaneamente sul database pubblico!")
                        else:
                            st.error("Nome e Data sono obbligatori!")

    except Exception as e:
        st.error(f"Errore generale: {e}")

# --- 5. MENU FISSO IN BASSO INTERATTIVO ---
st.markdown("""
<div style='position: fixed; bottom: 0; left: 0; width: 100%; background: #1f2124; display: flex; justify-content: flex-start; gap: 20px; padding: 15px 15px; border-top: 3px solid #ff9100; z-index: 9999;'>
    <a href='?menu=home' target='_self' style='font-family: Special Elite; color: #ff9100; font-weight: bold; text-decoration: none; font-size: 1.1rem;'>HOME</a>
    <a href='?menu=mc' target='_self' style='font-family: Special Elite; color: #ff9100; font-weight: bold; text-decoration: none; font-size: 1.1rem;'>MC</a>
    <a href='?menu=run' target='_self' style='font-family: Special Elite; color: #ff9100; font-weight: bold; text-decoration: none; font-size: 1.1rem;'>RUN</a>
    <a href='?menu=admin' target='_self' style='font-family: Special Elite; color: #ff9100; font-weight: bold; text-decoration: none; font-size: 1.1rem;'>ADMIN</a>
</div>
""", unsafe_allow_html=True)
