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

# Controllo dei parametri URL per la navigazione dai tasti in basso
if "menu" in st.query_params:
    scelta_menu = st.query_params["menu"]
    if scelta_menu in ["home", "mc", "admin"]:
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

# --- LISTA REGIONI STRUTTURATA ---
regioni_italia = ["Abruzzo", "Basilicata", "Calabria", "Campania", "Emilia-Romagna", 
                  "Friuli-Venezia Giulia", "Lazio", "Liguria", "Lombardia", "Marche", "Molise", 
                  "Piemonte", "Puglia", "Sardegna", "Sicilia", "Toscana", "Trentino-Alto Adige", 
                  "Umbria", "Valle d'Aosta", "Veneto"]

# --- 3. FUNZIONI DATI (SISTEMATE PER UTENTI MULTIPLI) ---
if "voti_locali" not in st.session_state:
    st.session_state["voti_locali"] = set()

def registra_voto(chiave_evento):
    st.session_state["voti_locali"].add(str(chiave_evento))

def ha_gia_votato(chiave_evento):
    return str(chiave_evento) in st.session_state["voti_locali"]

def parsing_data_biker(testo_data):
    testo = str(testo_data).lower().strip()
    if not testo or testo == "nan" or testo == "vedi nel sito" or testo == "vedi nel file": return pd.NaT
    
    # Prova prima il match diretto del formato standard GG/MM/AAAA (es. da motoraduni.it)
    match_standard = re.search(r'\b(\d{2})/(\d{2})/(202\d)\b', testo)
    if match_standard:
        try:
            return pd.Timestamp(year=int(match_standard.group(3)), month=int(match_standard.group(2)), day=int(match_standard.group(1)))
        except:
            pass

    mesi = {
        'gen': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'mag': 5, 'giu': 6, 
        'lug': 7, 'ago': 8, 'set': 9, 'ott': 10, 'nov': 11, 'dic': 12
    }
    mese_num = None
    for k, v in mesi.items():
        if k in testo:
            mese_num = v
            break
    if not mese_num:
        try: return pd.to_datetime(testo, dayfirst=True, errors='coerce')
        except: return pd.NaT
    anno_match = re.search(r'\b(202\d)\b', testo)
    anno = int(anno_match.group(1)) if anno_match else 2026
    giorno_match = re.search(r'\d+', testo)
    giorno = int(giorno_match.group(0)) if giorno_match else 1
    try: return pd.Timestamp(year=anno, month=mese_num, day=giorno)
    except: return pd.NaT

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

/* TRUCCO CSS: Nascondiamo la freccia predefinita e curiamo l'hover */
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

/* AGGIUNGE LA SCRITTA "CLICK HERE FOR INFO" SOTTO AL TITOLO */
div[data-testid="stExpander"] details summary p::after {{
    content: "CLICK HERE FOR INFO";
    display: block;
    color: #ff9100;
    font-family: 'Special Elite', cursive;
    font-size: 0.75rem;
    margin-top: 4px;
    letter-spacing: 1px;
}}
/* SE APERTO, CAMBIA IN "CHIUDI INFO" */
div[data-testid="stExpander"] details[open] summary p::after {{
    content: "CHIUDI INFO";
    color: #8a8d93;
}}

/* STILE NATIVO DEI PULSANTI (SE USATI DIRETTAMENTE) */
div[data-testid="stButton"] button, div[data-testid="stFormSubmitButton"] button {{ 
    background-color: #ff9100 !important; 
    color: black !important; 
    font-weight: bold !important; 
    font-family: 'Special Elite', cursive !important;
    border: 2px solid #ff9100 !important; 
    border-radius: 5px !important; 
    width: 100% !important; 
    padding: 10px !important;
    transition: all 0.2s;
}}
div[data-testid="stButton"] button:hover, div[data-testid="stFormSubmitButton"] button:hover {{ 
    background-color: transparent !important; 
    color: #ff9100 !important; 
    border: 2px solid #ff9100 !important; 
}}

/* NASCONDI RADIO LABEL E LABEL SELECT */
.stRadio > label {{ display: none !important; }}
.stSelectbox > label {{ display: none !important; }}

/* INFORMAZIONI EVENTO (TESTO BIANCO) */
.info-evento {{ color: white !important; line-height: 1.4 !important; font-size: 0.95rem; }}

/* LAYOUT PULSANTI PER GLI EVENTI (IL NOSTRO HTML) */
.riga-pulsante-anteprima {{
    display: flex;
    justify-content: flex-start;
    align-items: center;
    gap: 15px;
    margin-bottom: 25px;
}}
.locandina-anteprima-rettangolare {{
    width: 140px; 
    height: 70px;
    object-fit: cover;
    object-position: center 20%;
    border-radius: 8px;
    border: 2px solid #333;
    cursor: pointer;
}}
/* STILE BOTTONE "CI VADO" HTML */
.html-btn-civado {{
    background-color: #ff9100 !important; 
    color: black !important; 
    font-weight: bold !important; 
    border: 2px solid #ff9100 !important; 
    border-radius: 5px !important;
    height: 38px !important;
    padding: 0px 20px !important;
    font-size: 0.95rem !important;
    font-family: 'Special Elite', cursive !important;
    cursor: pointer !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-decoration: none !important;
    transition: all 0.2s;
}}
.html-btn-civado:hover {{
    background-color: transparent !important; 
    color: #ff9100 !important; 
}}
.html-btn-disabilitato {{
    background-color: #3a3b3c !important; 
    color: #8a8d93 !important; 
    border: 2px solid #3a3b3c !important; 
    cursor: not-allowed !important; 
}}
.html-btn-disabilitato:hover {{
    background-color: #3a3b3c !important; 
    color: #8a8d93 !important; 
}}

/* STILE BOTTONE CONDIVIDI */
.html-btn-condividi {{
    background-color: transparent !important;
    color: #00ffcc !important;
    border: 2px solid #00ffcc !important;
    border-radius: 5px !important;
    height: 38px !important;
    padding: 0px 15px !important;
    font-size: 0.90rem !important;
    font-family: 'Special Elite', cursive !important;
    cursor: pointer !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-decoration: none !important;
    transition: all 0.2s;
}}
.html-btn-condividi:hover {{
    background-color: #00ffcc !important;
    color: black !important;
}}

/* GESTIONE POPUP (MODAL PER IMMAGINI E AVVISI) */
.overlay {{
    position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
    background: rgba(0,0,0,0.85); z-index: 9999;
    display: flex; justify-content: center; align-items: center;
}}
.popup-img {{ max-width: 95vw; max-height: 90vh; border-radius: 10px; border: 3px solid #ff9100; }}
.close-btn {{ position: absolute; top: 20px; right: 30px; font-size: 40px; color: #ff9100; text-decoration: none; font-weight: bold; background: rgba(0,0,0,0.5); padding: 5px 15px; border-radius: 5px; }}

.bottone-sottile {{
    display: block; width: 100%; text-align: center; background-color: #1f2124; 
    color: #ff9100; border: 1px solid #ff9100; border-radius: 5px; 
    padding: 5px 0; margin-top: 15px; font-family: 'Special Elite', cursive; 
    text-decoration: none; font-size: 0.9rem; margin-bottom: 25px; transition: all 0.2s;
}}
.bottone-sottile:hover {{ background-color: #ff9100; color: black; }}

/* MESSAGGIO DI ERRORE STILE HACKER */
.hacker-alert {{
    background-color: rgba(255, 0, 0, 0.1) !important;
    border: 1px solid red !important;
    color: #ff4c4c !important;
    font-family: 'Special Elite', cursive !important;
    padding: 10px !important;
    border-radius: 5px !important;
    text-align: center !important;
    margin-bottom: 15px !important;
}}

/* MENU INFERIORE (BOTTOM NAVIGATION BAR) */
.bottom-nav {{
    position: fixed;
    bottom: 0; left: 0; right: 0;
    height: 70px;
    background-color: rgba(31, 33, 36, 0.95);
    backdrop-filter: blur(5px);
    border-top: 2px solid #ff9100;
    display: flex;
    justify-content: space-around;
    align-items: center;
    z-index: 10000;
    padding-bottom: env(safe-area-inset-bottom);
}}
.nav-item {{
    text-decoration: none;
    color: #8a8d93;
    font-family: 'Special Elite', cursive;
    display: flex;
    flex-direction: column;
    align-items: center;
    font-size: 0.75rem;
    flex: 1;
    text-align: center;
}}
.nav-item i {{
    font-size: 1.5rem;
    margin-bottom: 4px;
}}
.nav-item.active {{
    color: #ff9100;
    font-weight: bold;
}}
.nav-item:hover {{ color: white; }}
</style>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
""", unsafe_allow_html=True)

# --- 5. COMPONENTE NAVIGAZIONE INFERIORE (HTML/JS) ---
def render_bottom_nav(active_page):
    home_active = "active" if active_page == "home" else ""
    mc_active = "active" if active_page == "mc" else ""
    admin_active = "active" if active_page == "admin" else ""
    
    html = f"""
    <div class="bottom-nav">
        <a href="?menu=home" class="nav-item {home_active}" target="_self">
            <i class="fa-solid fa-motorcycle"></i>
            RADUNI
        </a>
        <a href="?menu=mc" class="nav-item {mc_active}" target="_self">
            <i class="fa-solid fa-skull"></i>
            LISTA M.C.
        </a>
        <a href="?menu=admin" class="nav-item {admin_active}" target="_self">
            <i class="fa-solid fa-user-shield"></i>
            SEGNALA
        </a>
    </div>
    """
    st.html(html)

# =====================================================================
# PAGINA 1: EVENTI E RADUNI (HOME)
# =====================================================================
if st.session_state["page"] == "home":
    st.markdown(f'<div class="online-counter"><span class="dot-online"></span>{utenti_online} Online</div>', unsafe_allow_html=True)
    st.markdown("<h1 class='titolo-gotico'>IRON & RUBBER</h1>", unsafe_allow_html=True)
    st.markdown("<h2 class='sottotitolo'>Motoraduni Biker Italia 2026</h2>", unsafe_allow_html=True)

    if gc:
        try:
            scheda = gc.open(NOME_DEL_FOGLIO).sheet1
            dati = scheda.get_all_records()
            if dati:
                df = pd.DataFrame(dati)
                df.columns = df.columns.str.strip()

                colonne_richieste = ['Data', 'Nome Evento / Raduno', 'Luogo', 'Regione', 'Organizzazione', 'Link', 'Partecipanti']
                for col in colonne_richieste:
                    if col not in df.columns:
                        if col == 'Partecipanti':
                            df['Partecipanti'] = 0
                            scheda.update_cell(1, len(df.columns), 'Partecipanti')
                            for r in range(2, len(df)+2): scheda.update_cell(r, len(df.columns), 0)
                        else: df[col] = "N.D."
                
                df['Partecipanti'] = pd.to_numeric(df['Partecipanti'], errors='coerce').fillna(0).astype(int)
                
                df['Data_Formattata'] = df['Data'].apply(parsing_data_biker)
                df_valido = df.dropna(subset=['Data_Formattata']).copy()
                
                # --- GESTIONE DEI FILTRI ---
                c1, c2 = st.columns(2)
                with c1:
                    regioni_presenti = ['Tutte'] + sorted([r for r in df_valido['Regione'].unique() if pd.notna(r) and r.strip() != "" and r.strip() != "N.D."])
                    st.session_state["sel_regione"] = st.selectbox("Regione:", regioni_presenti, index=regioni_presenti.index(st.session_state["sel_regione"]) if st.session_state["sel_regione"] in regioni_presenti else 0)
                
                with c2:
                    df_valido['Mese_Anno'] = df_valido['Data_Formattata'].dt.strftime('%B %Y').str.capitalize()
                    mesi_ordinati = df_valido['Data_Formattata'].dt.to_period('M').sort_values().unique()
                    mesi_etichette = ['Tutte'] + [p.strftime('%B %Y').capitalize() for p in mesi_ordinati]
                    st.session_state["sel_mese"] = st.selectbox("Mese:", mesi_etichette, index=mesi_etichette.index(st.session_state["sel_mese"]) if st.session_state["sel_mese"] in mesi_etichette else 0)

                if st.session_state["sel_regione"] != 'Tutte':
                    df_valido = df_valido[df_valido['Regione'].str.contains(st.session_state["sel_regione"], case=False, na=False)]
                
                if st.session_state["sel_mese"] != 'Tutte':
                    df_valido = df_valido[df_valido['Mese_Anno'] == st.session_state["sel_mese"]]

                df_valido = df_valido.sort_values(by='Data_Formattata', ascending=True)

                if not df_valido.empty:
                    st.markdown("<hr style='border:1px solid #333; margin-top:5px; margin-bottom:20px'>", unsafe_allow_html=True)
                    
                    # LOGICA DI CONTROLLO URL PER POPUP IMMAGINE
                    url_params = st.query_params
                    
                    for index, row in df_valido.iterrows():
                        riga_foglio_google = int(index) + 2
                        chiave_voto = f"{riga_foglio_google}_{row['Nome Evento / Raduno']}"
                        
                        img_path = str(row['Link']).strip()
                        ha_locandina = img_path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')) and img_path.startswith('http')
                        
                        # LOGICA EXPANDER (TITOLO DELL'EVENTO)
                        titolo_card = f"{row['Nome Evento / Raduno']} ({row['Regione']})"
                        with st.expander(titolo_card, expanded=False):
                            st.markdown(f"""
                            <div class="info-evento">
                            🗓️ <b>Data:</b> {row['Data']}<br>
                            📍 <b>Luogo:</b> {row['Luogo']}<br>
                            🏁 <b>Regione:</b> {row['Regione']}<br>
                            ☠️ <b>Organizzatore:</b> {row['Organizzazione']}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown("<br>", unsafe_allow_html=True)

                            if ha_locandina:
                                st.markdown(f"""
                                <a href="?menu=home" id="zoom_{riga_foglio_google}" class="overlay" style="display:none;">
                                    <span class="close-btn">&times;</span>
                                    <img src="{img_path}" class="popup-img">
                                </a>
                                <style>
                                    #zoom_{riga_foglio_google}:target {{ display: flex !important; }}
                                </style>
                                """, unsafe_allow_html=True)

                        # =========================================================
                        # PULSANTE PARTECIPAZIONE E CONDIVISIONE
                        # =========================================================
                        conteggio = int(row['Partecipanti'])
                        
                        if ha_locandina:
                            gia_votato = ha_gia_votato(chiave_voto)
                            if gia_votato:
                                html_bottone = f'<div class="html-btn-civado html-btn-disabilitato">CI VADO 🔥 {conteggio}</div>'
                            else:
                                html_bottone = f'<a href="?vota={riga_foglio_google}" target="_self" class="html-btn-civado">CI VADO 🔥 {conteggio}</a>'
                            
                            # --- GENERAZIONE LINK DI CONDIVISIONE WHATSAPP ---
                            testo_da_inviare = f"🔥 Guarda questo raduno: {row['Nome Evento / Raduno']}!\n📅 Data: {row['Data']}\n📍 Luogo: {row['Luogo']} ({row['Regione']})\n\nScoprilo sull'app Iron & Rubber!"
                            testo_url_safe = urllib.parse.quote(testo_da_inviare)
                            link_condivisione = f"https://api.whatsapp.com/send?text={testo_url_safe}"
                            
                            st.html(f"""
                            <div class="riga-pulsante-anteprima">
                                {html_bottone}
                                <a href="#zoom_{riga_foglio_google}" title="Ingrandisci Locandina">
                                    <img src="{img_path}" class="locandina-anteprima-rettangolare" alt="Preview">
                                </a>
                                <a href="{link_condivisione}" target="_blank" class="html-btn-condividi" title="Condividi su WhatsApp">
                                    CONDIVIDI 📲
                                </a>
                            </div>
                            """)
                            
                            if f"vota" in st.query_params and st.query_params["vota"] == str(riga_foglio_google):
                                if not gia_votato:
                                    scheda.update_cell(riga_foglio_google, 7, int(conteggio + 1))
                                    registra_voto(chiave_voto)
                                    st.query_params.clear()
                                    st.rerun()

                        else:
                            gia_votato = ha_gia_votato(chiave_voto)
                            if gia_votato:
                                html_bottone = f'<div class="html-btn-civado html-btn-disabilitato">CI VADO 🔥 {conteggio}</div>'
                            else:
                                html_bottone = f'<a href="?vota_noimg={riga_foglio_google}" target="_self" class="html-btn-civado">CI VADO 🔥 {conteggio}</a>'
                            
                            st.html(f"""
                            <div style="margin-bottom:25px;">
                                {html_bottone}
                            </div>
                            """)
                            
                            if f"vota_noimg" in st.query_params and st.query_params["vota_noimg"] == str(riga_foglio_google):
                                if not gia_votato:
                                    scheda.update_cell(riga_foglio_google, 7, int(conteggio + 1))
                                    registra_voto(chiave_voto)
                                    st.query_params.clear()
                                    st.rerun()
                else:
                    st.warning("Nessun raduno trovato per questa combinazione.")
            else:
                st.info("Il database dei raduni è momentaneamente vuoto.")
        except Exception as e:
            st.error(f"Errore di lettura dal database: {e}")
    else:
         st.error("Errore di connessione a Google Sheets.")
    
    render_bottom_nav("home")

# =====================================================================
# PAGINA 2: LISTA MOTOCLUB ITALIA (HARDCODED)
# =====================================================================
elif st.session_state["page"] == "mc":
    st.markdown("<h1 class='titolo-gotico'>Motorcycle Club 1% Italia</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:white;'>Lista dei Motorcycle Club che operano sul territorio italiano. Respect. Manca il tuo? Vai in area contatti.</p>", unsafe_allow_html=True)
    
    lista_mc = [
        "Hells Angels MC",
        "Bandidos MC",
        "Outlaws MC",
        "Gremium MC",
        "Golden Drakes MC",
        "Born To Be Wild MC"
    ]
    
    for mc in sorted(lista_mc):
        st.markdown(f"""
        <div style="background-color:#1f2124; border-left:4px solid #ff9100; padding:10px 15px; margin-bottom:10px; border-radius:4px; color:white; font-family:'Special Elite', cursive; font-size:1.1rem;">
            ☠️ {mc}
        </div>
        """, unsafe_allow_html=True)
    
    render_bottom_nav("mc")

# =====================================================================
# PAGINA 3: SEGNALAZIONE E CONTATTI (FORM)
# =====================================================================
elif st.session_state["page"] == "admin":
    st.markdown("<h1 class='titolo-gotico'>Segnala o Correggi</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:white; text-align:center;'>Aggiungi un evento, correggi una locandina sbagliata o inserisci il tuo MC. L'aggiornamento è manuale, quindi porta pazienza, fratello.</p>", unsafe_allow_html=True)
    
    if st.session_state["evento_inviato"]:
        st.success("Messaggio ricevuto. Verrà valutato e inserito al più presto. Grazie!")
        if st.button("Invia un'altra segnalazione"):
            st.session_state["evento_inviato"] = False
            st.rerun()
    else:
        with st.form("form_segnalazione", clear_on_submit=True):
            tipo = st.selectbox("Cosa vuoi segnalare?", ["Nuovo Raduno", "Errore in un Raduno", "Aggiunta MC", "Altro"])
            nome_evento = st.text_input("Nome Evento / Motoclub")
            data_evento = st.text_input("Data dell'evento (es. 15 Maggio 2026)")
            luogo = st.text_input("Città e Regione")
            link_img = st.text_input("Link diretto alla Locandina (JPG/PNG) - Opzionale")
            note = st.text_area("Messaggio / Dettagli aggiuntivi")
            
            submitted = st.form_submit_button("INVIA SEGNALAZIONE")
            if submitted:
                if nome_evento.strip() == "":
                    st.markdown("<div class='hacker-alert'>ERRORE: Inserisci almeno il nome!</div>", unsafe_allow_html=True)
                else:
                    if gc:
                        try:
                            # TENTA DI SCRIVERE SUL FOGLIO "segnalazioni"
                            try:
                                sh = gc.open(NOME_DEL_FOGLIO)
                                ws = sh.worksheet("segnalazioni")
                            except:
                                # Se non esiste, lo crea
                                ws = gc.open(NOME_DEL_FOGLIO).add_worksheet(title="segnalazioni", rows="100", cols="6")
                                ws.append_row(["TIPO", "NOME", "DATA", "LUOGO", "LINK", "NOTE"])
                            
                            ws.append_row([tipo, nome_evento, data_evento, luogo, link_img, note])
                            st.session_state["evento_inviato"] = True
                            st.rerun()
                        except Exception as e:
                            st.error(f"Errore nell'invio: {e}")
                    else:
                        st.error("Connessione al database assente. Impossibile inviare.")

    render_bottom_nav("admin")

# --- INTEGRATORE STATCOUNTER JAVASCRIPT CORRETTO ---
statcounter_js = f"""
<!-- Statcounter code for App -->
<script type="text/javascript">
var sc_project={SC_PROJECT}; 
var sc_invisible=1; 
var sc_security="{SC_SECURITY}"; 
</script>
<script type="text/javascript"
src="https://www.statcounter.com/counter/counter.js"
async></script>
<noscript><div class="statcounter"><a title="Web Analytics"
href="https://statcounter.com/" target="_blank"><img
class="statcounter"
src="https://c.statcounter.com/{SC_PROJECT}/0/{SC_SECURITY}/1/"
alt="Web Analytics"
referrerPolicy="no-referrer-when-downgrade"></a></div></noscript>
<!-- End of Statcounter Code -->
"""
st.components.v1.html(statcounter_js, height=0)
