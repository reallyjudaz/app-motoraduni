import streamlit as st
import pandas as pd
import os
import re
import gspread
from google.oauth2 import service_account
import urllib.parse
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# --- 1. CONFIGURAZIONE GRAFICA DELLA PAGINA ---
st.set_page_config(page_title="Iron & Rubber", layout="centered")

# --- IMPOSTAZIONI STATCOUNTER & NOTIFICA EMAIL ---
SC_PROJECT = "13297832"
SC_SECURITY = "54bb43fa"

# --- CONFIGURAZIONE NOTIFICA VIA EMAIL ---
EMAIL_DESTINATARIO = "tuaemail@gmail.com"  # La mail dove vuoi ricevere le notifiche
EMAIL_MITTENTE = ""                       # Es. tuaemail@gmail.com
PASSWORD_APP = ""                         # Password per le app di Google (16 caratteri)

def invia_email_notifica(titolo_giro, autore, regione, km, link_mappa):
    """Invia una notifica via Email all'amministratore quando viene pubblicato un giro"""
    if EMAIL_MITTENTE and PASSWORD_APP and EMAIL_DESTINATARIO:
        try:
            msg = MIMEMultipart()
            msg['From'] = EMAIL_MITTENTE
            msg['To'] = EMAIL_DESTINATARIO
            msg['Subject'] = f"🔥 NUOVO GIRO PUBBLICATO: {titolo_giro}"

            corpo_mail = f"""
            Ciao Admin,

            Un biker ha appena pubblicato un nuovo giro sull'app Iron & Rubber!

            📍 Titolo Giro: {titolo_giro}
            👤 Pubblicato da: {autore}
            🏁 Regione: {regione}
            📏 Distanza: {km} km
            🗺️ Mappa Google: {link_mappa}

            -- 
            Iron & Rubber App
            """
            msg.attach(MIMEText(corpo_mail, 'plain', 'utf-8'))

            # Invio con server SMTP Gmail
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(EMAIL_MITTENTE, PASSWORD_APP)
            server.send_message(msg)
            server.quit()
        except Exception as e:
            pass

if "fake_online" not in st.session_state:
    st.session_state["fake_online"] = random.randint(1, 3)
utenti_online = st.session_state["fake_online"]

# --- GESTIONE DELLA NAVIGAZIONE (PAGINE) ---
if "page" not in st.session_state:
    st.session_state["page"] = "home"

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
    testo = str(testo_data).lower().strip()
    if not testo or testo == "nan" or testo == "vedi nel sito" or testo == "vedi nel file": return pd.NaT
    
    match_standard = re.search(r'\b(\d{2})/(\d{2})/(202\d)\b', testo)
    if match_standard:
        try:
            return pd.Timestamp(year=int(match_standard.group(3)), month=int(match_standard.group(2)), day=int(match_standard.group(1)))
        except:
            pass

    mesi = {'gen': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'mag': 5, 'giu': 6, 'lug': 7, 'ago': 8, 'set': 9, 'ott': 10, 'nov': 11, 'dic': 12}
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
    top: -10px; right: 15px;
    background: #1f2124; border: 1px solid #ff9100;
    padding: 4px 8px; border-radius: 12px;
    font-family: 'Special Elite', cursive; font-size: 0.75rem; color: #ffffff;
    display: flex; align-items: center; gap: 6px; z-index: 99999;
}}
.dot-online {{
    width: 6px; height: 6px; background-color: #00ffcc; border-radius: 50%; display: inline-block;
    animation: lampeggia 1.5s infinite;
}}
@keyframes lampeggia {{ 0% {{ opacity: 0.3; }} 50% {{ opacity: 1; }} 100% {{ opacity: 0.3; }} }}

.titolo-gotico {{ font-family: 'UnifrakturMaguntia', cursive !important; text-align: center; color: #ff9100 !important; font-size: 2.6rem !important; margin-top: -10px !important; }}
.sottotitolo {{ font-family: 'UnifrakturMaguntia', cursive !important; text-align: center; color: #ff9100 !important; font-size: 1.4rem !important; margin-bottom: 20px !important; }}

.stExpander {{ 
    background-color: #1f2124 !important; 
    border: 2px solid #ff9100 !important; 
    border-radius: 10px !important; 
    color: white !important; 
    margin-bottom: 12px !important;
}}

div[data-testid="stExpander"] details summary svg,
div[data-testid="stExpander"] [data-testid="stExpanderIcon"] {{ display: none !important; }}
div[data-testid="stExpander"] details summary {{ padding-left: 15px !important; background-color: #1f2124 !important; color: white !important; cursor: pointer !important; }}
div[data-testid="stExpander"] details summary, 
div[data-testid="stExpander"] details summary:hover, 
div[data-testid="stExpander"] details summary:focus,
div[data-testid="stExpander"] details summary:active,
div[data-testid="stExpander"] details[open] summary {{ background-color: #1f2124 !important; color: white !important; }}

.streamlit-expanderHeader {{ color: #ff9100 !important; font-weight: bold !important; font-size: 1.0rem !important; background-color: #1f2124 !important; }}
div[data-testid="stExpander"] details summary p {{ color: white !important; width: 100% !important; margin-bottom: 0px !important; }}

div[data-testid="stExpander"] details summary p::after {{
    content: "CLICK HERE FOR INFO"; display: block; color: #ff9100;
    font-family: 'Special Elite', cursive; font-size: 0.75rem; margin-top: 4px; letter-spacing: 1px;
}}
div[data-testid="stExpander"] details[open] summary p::after {{ content: "CHIUDI INFO"; color: #8a8d93; }}

/* STILE PULSANTI */
div[data-testid="stButton"] button, div[data-testid="stFormSubmitButton"] button {{ 
    background-color: #ff9100 !important; color: black !important; font-weight: bold !important; 
    font-family: 'Special Elite', cursive !important; border: 2px solid #ff9100 !important; 
    border-radius: 5px !important; width: 100% !important; padding: 10px !important; transition: all 0.2s;
}}
div[data-testid="stButton"] button:hover, div[data-testid="stFormSubmitButton"] button:hover {{ background-color: transparent !important; color: #ff9100 !important; border: 2px solid #ff9100 !important; }}

.stRadio > label {{ display: none !important; }}
.stSelectbox > label {{ display: none !important; }}
.info-evento {{ color: white !important; line-height: 1.4 !important; font-size: 0.95rem; }}

.riga-pulsante-anteprima {{ display: flex; justify-content: flex-start; align-items: center; gap: 15px; margin-bottom: 25px; }}
.locandina-anteprima-rettangolare {{ width: 140px; height: 70px; object-fit: cover; object-position: center 20%; border-radius: 8px; border: 2px solid #333; cursor: pointer; }}

.html-btn-civado {{
    background-color: #ff9100 !important; color: black !important; font-weight: bold !important; 
    border: 2px solid #ff9100 !important; border-radius: 5px !important; height: 38px !important;
    padding: 0px 20px !important; font-size: 0.95rem !important; font-family: 'Special Elite', cursive !important;
    cursor: pointer !important; display: inline-flex !important; align-items: center !important; justify-content: center !important; text-decoration: none !important; transition: all 0.2s;
}}
.html-btn-civado:hover {{ background-color: transparent !important; color: #ff9100 !important; }}
.html-btn-disabilitato {{ background-color: #3a3b3c !important; color: #8a8d93 !important; border: 2px solid #3a3b3c !important; cursor: not-allowed !important; }}

.html-btn-condividi {{
    background-color: transparent !important; color: #00ffcc !important; border: 2px solid #00ffcc !important;
    border-radius: 5px !important; height: 38px !important; padding: 0px 15px !important; font-size: 0.90rem !important;
    font-family: 'Special Elite', cursive !important; cursor: pointer !important; display: inline-flex !important;
    align-items: center !important; justify-content: center !important; text-decoration: none !important; transition: all 0.2s;
}}
.html-btn-condividi:hover {{ background-color: #00ffcc !important; color: black !important; }}

.html-btn-mappa {{
    background-color: #00ffcc !important; color: black !important; font-weight: bold !important;
    border: 2px solid #00ffcc !important; border-radius: 5px !important; height: 38px !important;
    padding: 0px 15px !important; font-size: 0.90rem !important; font-family: 'Special Elite', cursive !important;
    cursor: pointer !important; display: inline-flex !important; align-items: center !important; justify-content: center !important; text-decoration: none !important; transition: all 0.2s;
}}
.html-btn-mappa:hover {{ background-color: transparent !important; color: #00ffcc !important; }}

.box-commenti {{ background-color: #1a1c1e; border: 1px dashed #444; border-radius: 8px; padding: 12px; margin-top: 10px; margin-bottom: 20px; }}
.singolo-commento {{ border-bottom: 1px solid #2a2c2e; padding: 6px 0px; font-size: 0.88rem; color: #ddd; }}
.singolo-commento b {{ color: #ff9100; }}

.overlay {{ position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.85); z-index: 9999; display: flex; justify-content: center; align-items: center; }}
.popup-img {{ max-width: 95vw; max-height: 90vh; border-radius: 10px; border: 3px solid #ff9100; }}
.close-btn {{ position: absolute; top: 20px; right: 30px; font-size: 40px; color: #ff9100; text-decoration: none; font-weight: bold; background: rgba(0,0,0,0.5); padding: 5px 15px; border-radius: 5px; }}

.hacker-alert {{ background-color: rgba(255, 0, 0, 0.1) !important; border: 1px solid red !important; color: #ff4c4c !important; font-family: 'Special Elite', cursive !important; padding: 10px !important; border-radius: 5px !important; text-align: center !important; margin-bottom: 15px !important; }}

/* MENU INFERIORE CON 4 TASTI */
.bottom-nav {{
    position: fixed; bottom: 0; left: 0; right: 0; height: 70px;
    background-color: rgba(31, 33, 36, 0.95); backdrop-filter: blur(5px);
    border-top: 2px solid #ff9100; display: flex; justify-content: space-around; align-items: center; z-index: 10000; padding-bottom: env(safe-area-inset-bottom);
}}
.nav-item {{ text-decoration: none; color: #8a8d93; font-family: 'Special Elite', cursive; display: flex; flex-direction: column; align-items: center; font-size: 0.68rem; flex: 1; text-align: center; }}
.nav-item i {{ font-size: 1.3rem; margin-bottom: 4px; }}
.nav-item.active {{ color: #ff9100; font-weight: bold; }}
.nav-item:hover {{ color: white; }}
</style>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
""", unsafe_allow_html=True)

# --- 5. COMPONENTE NAVIGAZIONE INFERIORE (4 BOTTONI) ---
def render_bottom_nav(active_page):
    home_active = "active" if active_page == "home" else ""
    mc_active = "active" if active_page == "mc" else ""
    run_active = "active" if active_page == "run" else ""
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
        <a href="?menu=run" class="nav-item {run_active}" target="_self">
            <i class="fa-solid fa-map-location-dot"></i>
            RUN / GIRI
        </a>
        <a href="?menu=admin" class="nav-item {admin_active}" target="_self">
            <i class="fa-solid fa-user-shield"></i>
            SEGNALA
        </a>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

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
            dati_raw = scheda.get_all_values()
            
            if len(dati_raw) > 1:
                intestazioni = dati_raw[0]
                df = pd.DataFrame(dati_raw[1:], columns=intestazioni)
                df = df.loc[:, ~df.columns.duplicated()]
                df.columns = df.columns.str.strip()

                try: col_idx_partecipanti = intestazioni.index('Partecipanti') + 1
                except ValueError: col_idx_partecipanti = len(intestazioni) + 1

                colonne_richieste = ['Data', 'Nome Evento / Raduno', 'Luogo', 'Regione', 'Organizzazione', 'Link', 'Partecipanti']
                for col in colonne_richieste:
                    if col not in df.columns:
                        if col == 'Partecipanti':
                            df['Partecipanti'] = 0
                            scheda.update_cell(1, col_idx_partecipanti, 'Partecipanti')
                            for r in range(2, len(df)+2): scheda.update_cell(r, col_idx_partecipanti, 0)
                        else: df[col] = "N.D."
                
                df['Partecipanti'] = pd.to_numeric(df['Partecipanti'], errors='coerce').fillna(0).astype(int)
                df['Data_Formattata'] = df['Data'].apply(parsing_data_biker)
                df_valido = df.dropna(subset=['Data_Formattata']).copy()
                
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
                    
                    for index, row in df_valido.iterrows():
                        riga_foglio_google = int(index) + 2
                        chiave_voto = f"{riga_foglio_google}_{row['Nome Evento / Raduno']}"
                        img_path = str(row['Link']).strip()
                        ha_locandina = img_path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')) and img_path.startswith('http')
                        
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
                                <style>#zoom_{riga_foglio_google}:target {{ display: flex !important; }}</style>
                                """, unsafe_allow_html=True)

                        conteggio = int(row['Partecipanti'])
                        
                        if ha_locandina:
                            gia_votato = ha_gia_votato(chiave_voto)
                            html_bottone = f'<div class="html-btn-civado html-btn-disabilitato">CI VADO 🔥 {conteggio}</div>' if gia_votato else f'<a href="?vota={riga_foglio_google}" target="_self" class="html-btn-civado">CI VADO 🔥 {conteggio}</a>'
                            testo_da_inviare = f"🔥 Guarda questo raduno: {row['Nome Evento / Raduno']}!\n📅 Data: {row['Data']}\n📍 Luogo: {row['Luogo']} ({row['Regione']})\n\nScoprilo sull'app Iron & Rubber!"
                            link_condivisione = f"https://api.whatsapp.com/send?text={urllib.parse.quote(testo_da_inviare)}"
                            
                            st.markdown(f"""
                            <div class="riga-pulsante-anteprima">
                                {html_bottone}
                                <a href="#zoom_{riga_foglio_google}" title="Ingrandisci Locandina">
                                    <img src="{img_path}" class="locandina-anteprima-rettangolare" alt="Preview">
                                </a>
                                <a href="{link_condivisione}" target="_blank" class="html-btn-condividi" title="Condividi su WhatsApp">
                                    CONDIVIDI 📲
                                </a>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if f"vota" in st.query_params and st.query_params["vota"] == str(riga_foglio_google):
                                if not gia_votato:
                                    scheda.update_cell(riga_foglio_google, col_idx_partecipanti, int(conteggio + 1))
                                    registra_voto(chiave_voto)
                                    st.query_params.clear()
                                    st.rerun()

                        else:
                            gia_votato = ha_gia_votato(chiave_voto)
                            html_bottone = f'<div class="html-btn-civado html-btn-disabilitato">CI VADO 🔥 {conteggio}</div>' if gia_votato else f'<a href="?vota_noimg={riga_foglio_google}" target="_self" class="html-btn-civado">CI VADO 🔥 {conteggio}</a>'
                            
                            st.markdown(f'<div style="margin-bottom:25px;">{html_bottone}</div>', unsafe_allow_html=True)
                            
                            if f"vota_noimg" in st.query_params and st.query_params["vota_noimg"] == str(riga_foglio_google):
                                if not gia_votato:
                                    scheda.update_cell(riga_foglio_google, col_idx_partecipanti, int(conteggio + 1))
                                    registra_voto(chiave_voto)
                                    st.query_params.clear()
                                    st.rerun()
                else: st.warning("Nessun raduno trovato per questa combinazione.")
            else: st.info("Il database dei raduni è momentaneamente vuoto.")
        except Exception as e: st.error(f"Errore di lettura dal database: {e}")
    else: st.error("Errore di connessione a Google Sheets.")
    
    render_bottom_nav("home")

# =====================================================================
# PAGINA 2: LISTA MOTOCLUB ITALIA
# =====================================================================
elif st.session_state["page"] == "mc":
    st.markdown("<h1 class='titolo-gotico'>Motorcycle Club 1% Italia</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:white;'>Lista dei Motorcycle Club che operano sul territorio italiano. Respect. Manca il tuo? Vai in area contatti.</p>", unsafe_allow_html=True)
    
    lista_mc = ["Hells Angels MC", "Bandidos MC", "Outlaws MC", "Gremium MC", "Golden Drakes MC", "Born To Be Wild MC"]
    for mc in sorted(lista_mc):
        st.markdown(f"""
        <div style="background-color:#1f2124; border-left:4px solid #ff9100; padding:10px 15px; margin-bottom:10px; border-radius:4px; color:white; font-family:'Special Elite', cursive; font-size:1.1rem;">
            ☠️ {mc}
        </div>
        """, unsafe_allow_html=True)
    
    render_bottom_nav("mc")

# =====================================================================
# PAGINA 3: RUN & ITINERARI (CON VOTI 👍, COMMENTI 💬 ED EMAIL ADMIN 📧)
# =====================================================================
elif st.session_state["page"] == "run":
    st.markdown("<h1 class='titolo-gotico'>RUN & ITINERARI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:white;'>I migliori percorsi provati dai Biker. Scarica la mappa, metti Mi Piace e scopri i commenti!</p>", unsafe_allow_html=True)
    
    # --- FORM PUBBLICAZIONE NUOVO GIRO ---
    with st.expander("➕ PUBBLICA UN NUOVO GIRO / MAPPA GOOGLE", expanded=False):
        if st.session_state["giro_inviato"]:
            st.success("Giro pubblicato con successo e visibile a tutti!")
            if st.button("Inserisci un altro giro"):
                st.session_state["giro_inviato"] = False
                st.rerun()
        else:
            with st.form("form_nuovo_giro", clear_on_submit=True):
                titolo_giro = st.text_input("Nome del Giro / Passi", placeholder="es. Anello del Passo dello Stelvio")
                autore = st.text_input("Il tuo Nome / Nickname / MC", placeholder="es. Biker84")
                regione_giro = st.selectbox("Regione principale:", regioni_italia)
                km_totali = st.text_input("Distanza (es. 180 km)", placeholder="180")
                stile_strada = st.selectbox("Tipo di percorso:", ["Piega & Tornanti 🏍️", "Panoramico / Relax 🌅", "Off-Road / Enduro 🪵", "Misto 🛣️"])
                link_gmaps = st.text_input("Link Mappa Google Maps / Waze*", placeholder="https://maps.google.com/...")
                sosta_bar = st.text_input("Sosta Birra/Ristoro Consigliata (Opzionale)")
                note_percorso = st.text_area("Note / Consigli di guida")
                
                btn_pubblica = st.form_submit_button("PUBLISH RUN 🗺️")
                
                if btn_pubblica:
                    if not titolo_giro.strip() or not link_gmaps.strip():
                        st.markdown("<div class='hacker-alert'>ERRORE: Inserisci almeno il Nome e il Link Mappa!</div>", unsafe_allow_html=True)
                    else:
                        if gc:
                            try:
                                sh = gc.open(NOME_DEL_FOGLIO)
                                try: ws_giri = sh.worksheet("giri")
                                except:
                                    ws_giri = sh.add_worksheet(title="giri", rows="100", cols="9")
                                    ws_giri.append_row(["TITOLO", "AUTORE", "REGIONE", "KM", "STILE", "LINK_MAPPA", "SOSTA", "NOTE", "VOTI"])
                                
                                ws_giri.append_row([titolo_giro, autore, regione_giro, km_totali, stile_strada, link_gmaps, sosta_bar, note_percorso, 0])
                                st.session_state["giro_inviato"] = True
                                
                                # INVIA NOTIFICA VIA EMAIL ALL'ADMIN
                                invia_email_notifica(titolo_giro, autore, regione_giro, km_totali, link_gmaps)
                                
                                st.rerun()
                            except Exception as e: st.error(f"Errore salvataggio: {e}")
                        else: st.error("Database non disponibile.")

    st.markdown("<hr style='border:1px solid #333; margin-top:15px; margin-bottom:20px'>", unsafe_allow_html=True)

    # --- LETTURA E VISUALIZZAZIONE GIRI ---
    if gc:
        try:
            sh = gc.open(NOME_DEL_FOGLIO)
            # CARICAMENTO COMMENTI
            df_commenti = pd.DataFrame()
            try:
                ws_comm = sh.worksheet("commenti_giri")
                d_comm = ws_comm.get_all_values()
                if len(d_comm) > 1:
                    df_commenti = pd.DataFrame(d_comm[1:], columns=d_comm[0])
                    df_commenti.columns = df_commenti.columns.str.strip()
            except:
                pass

            # CARICAMENTO GIRI
            try:
                ws_giri = sh.worksheet("giri")
                dati_giri = ws_giri.get_all_values()
                
                if len(dati_giri) > 1:
                    intestazioni_giri = dati_giri[0]
                    df_giri = pd.DataFrame(dati_giri[1:], columns=intestazioni_giri)
                    df_giri.columns = df_giri.columns.str.strip()
                    
                    try: col_idx_voti_giri = intestazioni_giri.index('VOTI') + 1
                    except ValueError: col_idx_voti_giri = len(intestazioni_giri) + 1

                    for idx, riga in df_giri.iterrows():
                        riga_sheet_giro = int(idx) + 2
                        chiave_voto_giro = f"giro_like_{riga_sheet_giro}_{riga.get('TITOLO','')}"
                        
                        titolo_g = riga.get("TITOLO", "Giro Biker")
                        reg_g = riga.get("REGIONE", "Italia")
                        km_g = riga.get("KM", "N.D.")
                        stile_g = riga.get("STILE", "Misto")
                        link_g = riga.get("LINK_MAPPA", "#")
                        autore_g = riga.get("AUTORE", "Biker Anonimo")
                        sosta_g = riga.get("SOSTA", "")
                        note_g = riga.get("NOTE", "")
                        voti_g = int(riga.get("VOTI", 0)) if str(riga.get("VOTI", 0)).isdigit() else 0

                        with st.expander(f"🗺️ {titolo_g} ({reg_g})", expanded=False):
                            st.markdown(f"""
                            <div class="info-evento">
                            👤 <b>Creato da:</b> {autore_g}<br>
                            📏 <b>Distanza:</b> {km_g} KM<br>
                            🛣️ <b>Stile:</b> {stile_g}<br>
                            {f'🍻 <b>Sosta Consigliata:</b> {sosta_g}<br>' if sosta_g else ''}
                            📝 <b>Note:</b> {note_g if note_g else 'Nessun dettaglio aggiuntivo.'}
                            </div>
                            """, unsafe_allow_html=True)
                            st.markdown("<br>", unsafe_allow_html=True)

                            # SEZIONE COMMENTI ALL'INTERNO DELLA SCHEDA
                            st.markdown("<b>💬 Commenti della Community:</b>", unsafe_allow_html=True)
                            
                            commenti_questo_giro = df_commenti[df_commenti['ID_GIRO'] == str(riga_sheet_giro)] if not df_commenti.empty and 'ID_GIRO' in df_commenti.columns else pd.DataFrame()
                            
                            if not commenti_questo_giro.empty:
                                html_comm = '<div class="box-commenti">'
                                for _, c_row in commenti_questo_giro.iterrows():
                                    html_comm += f'<div class="singolo-commento"><b>{c_row.get("AUTORE", "Anonimo")}</b> ({c_row.get("DATA", "")}): {c_row.get("COMMENTO", "")}</div>'
                                html_comm += '</div>'
                                st.markdown(html_comm, unsafe_allow_html=True)
                            else:
                                st.markdown("<p style='color:#8a8d93; font-size:0.85rem;'>Nessun commento ancora. Scrivine uno tu!</p>", unsafe_allow_html=True)

                            # FORM AGGIUNGI COMMENTO
                            with st.form(f"form_commento_{riga_sheet_giro}", clear_on_submit=True):
                                c_autore = st.text_input("Il tuo Nome", key=f"c_aut_{riga_sheet_giro}")
                                c_testo = st.text_input("Scrivi un commento (es. Tante curve strette, bello!)", key=f"c_txt_{riga_sheet_giro}")
                                btn_invia_comm = st.form_submit_button("INVIA COMMENTO 💬")
                                
                                if btn_invia_comm:
                                    if c_testo.strip() != "":
                                        try:
                                            try: ws_c = sh.worksheet("commenti_giri")
                                            except:
                                                ws_c = sh.add_worksheet(title="commenti_giri", rows="200", cols="4")
                                                ws_c.append_row(["ID_GIRO", "AUTORE", "COMMENTO", "DATA"])
                                            
                                            data_ora = datetime.now().strftime("%d/%m %H:%M")
                                            ws_c.append_row([str(riga_sheet_giro), c_autore if c_autore.strip() else "Anonimo", c_testo, data_ora])
                                            st.rerun()
                                        except Exception as e: st.error(f"Errore nell'invio del commento: {e}")

                        # RIGA BOTTONI: MAPPA GOOGLE + LIKES 👍
                        gia_votato_g = ha_gia_votato(chiave_voto_giro)
                        btn_like_html = f'<div class="html-btn-civado html-btn-disabilitato">👍 {voti_g}</div>' if gia_votato_g else f'<a href="?vota_giro={riga_sheet_giro}" target="_self" class="html-btn-civado">👍 MI PIACE ({voti_g})</a>'
                        
                        st.markdown(f"""
                        <div class="riga-pulsante-anteprima">
                            <a href="{link_g}" target="_blank" class="html-btn-mappa">
                                APRI MAPPA GOOGLE 🗺️
                            </a>
                            {btn_like_html}
                        </div>
                        """, unsafe_allow_html=True)

                        # LOGICA INCREMENTO VOTO GIRO
                        if "vota_giro" in st.query_params and st.query_params["vota_giro"] == str(riga_sheet_giro):
                            if not gia_votato_g:
                                ws_giri.update_cell(riga_sheet_giro, col_idx_voti_giri, int(voti_g + 1))
                                registra_voto(chiave_voto_giro)
                                st.query_params.clear()
                                st.rerun()

                else: st.info("Nessun giro pubblicato finora. Sii il primo a pubblicarne uno dal pulsante in alto!")
            except Exception: st.info("La lista dei giri è attualmente vuota. Aggiungi il primo giro col form qui sopra!")
        except Exception as e: st.error(f"Errore caricamento: {e}")
    else: st.error("Impossibile connettersi al database.")

    render_bottom_nav("run")

# =====================================================================
# PAGINA 4: SEGNALAZIONE E CONTATTI
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
                            sh = gc.open(NOME_DEL_FOGLIO)
                            try: ws = sh.worksheet("segnalazioni")
                            except:
                                ws = sh.add_worksheet(title="segnalazioni", rows="100", cols="6")
                                ws.append_row(["TIPO", "NOME", "DATA", "LUOGO", "LINK", "NOTE"])
                            
                            ws.append_row([tipo, nome_evento, data_evento, luogo, link_img, note])
                            st.session_state["evento_inviato"] = True
                            st.rerun()
                        except Exception as e: st.error(f"Errore nell'invio: {e}")
                    else: st.error("Connessione al database assente. Impossibile inviare.")

    render_bottom_nav("admin")

# --- INTEGRATORE STATCOUNTER JAVASCRIPT ---
statcounter_js = f"""
<!-- Statcounter code for App -->
<script type="text/javascript">
var sc_project={SC_PROJECT}; 
var sc_invisible=1; 
var sc_security="{SC_SECURITY}"; 
</script>
<script type="text/javascript" src="https://www.statcounter.com/counter/counter.js" async></script>
<noscript><div class="statcounter"><a title="Web Analytics" href="https://statcounter.com/" target="_blank"><img class="statcounter" src="https://c.statcounter.com/{SC_PROJECT}/0/{SC_SECURITY}/1/" alt="Web Analytics" referrerPolicy="no-referrer-when-downgrade"></a></div></noscript>
<!-- End of Statcounter Code -->
"""
st.components.v1.html(statcounter_js, height=0)
