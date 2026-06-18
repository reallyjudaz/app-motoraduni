import streamlit as st
import pandas as pd
import os
import re
import gspread
from google.oauth2 import service_account

# --- 1. CONFIGURAZIONE GRAFICA DELLA PAGINA ---
st.set_page_config(page_title="Iron & Rubber", layout="centered")

# --- IMPOSTAZIONI STATCOUNTER CONFIGURATE ---
SC_PROJECT = "13297832"    
SC_SECURITY = "54bb43fa"  

if "fake_online" not in st.session_state:
    import random
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

# --- 3. FUNZIONI DATI ---
def registra_voto(chiave_evento):
    with open("voti_fatti.txt", "a") as f:
        f.write(f"{chiave_evento}\n")

def ha_gia_votato(chiave_evento):
    if not os.path.exists("voti_fatti.txt"): return False
    with open("voti_fatti.txt", "r") as f:
        return str(chiave_evento) in f.read().splitlines()

def parsing_data_biker(testo_data):
    testo = str(testo_data).lower().strip()
    if not testo or testo == "nan": return pd.NaT
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

.stExpander {{ background-color: #1f2124 !important; border: 2px solid #ff9100 !important; border-radius: 10px !important; color: white !important; }}
.streamlit-expanderHeader {{ color: #ff9100 !important; font-weight: bold !important; font-size: 1.0rem !important; }}

div[data-testid="stButton"] button, div[data-testid="stFormSubmitButton"] button {{ 
    background-color: #ff9100 !important; 
    color: black !important; 
    font-weight: bold !important; 
    font-family: 'Special Elite', cursive !important; 
    border-radius: 5px !important; 
    height: 38px !important; 
    width: 100%;
}}

label, .stTextInput label, .stTextArea label {{ color: white !important; }}

div[data-testid="stHorizontalBlock"] {{
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 12px !important;
    width: 100% !important;
}}
div[data-testid="stHorizontalBlock"] > div {{
    max-width: 100% !important;
    width: 100% !important;
}}

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

/* Stile per le card dei MotoClub */
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

/* --- SISTEMA LIGHTBOX NATIVO PER REALE TUTTO SCHERMO --- */
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

/* Finestra sovrapposta (Lightbox) */
.lightbox-target {{
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(10, 10, 11, 0.95);
    width: 0;
    opacity: 0;
    overflow: hidden;
    z-index: 100000;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    transition: opacity 0.25s ease;
}}
/* Quando attivato dal link HTML */
.lightbox-target:target {{
    width: 100%;
    opacity: 1;
    bottom: 0;
    right: 0;
}}
/* Immagine dentro il tutto schermo */
.lightbox-target img {{
    max-width: 92%;
    max-height: 78vh;
    object-fit: contain;
    border: 2px solid #ff9100;
    border-radius: 8px;
    box-shadow: 0px 0px 20px rgba(255, 145, 0, 0.4);
}}
/* Pulsante BACK / CHIUDI personalizzato */
.lightbox-close-btn {{
    margin-top: 20px;
    background-color: #ff9100 !important;
    color: black !important;
    font-family: 'Special Elite', cursive !important;
    font-weight: bold !important;
    text-decoration: none !important;
    padding: 10px 35px;
    border-radius: 5px;
    font-size: 1rem;
    letter-spacing: 1px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    transition: background 0.2s;
    text-align: center;
}}
.lightbox-close-btn:hover {{
    background-color: #e07f00 !important;
}}
</style>

<!-- Widget Grafico Contatore -->
<div class="online-counter">
    <span class="dot-online"></span>
    <span>{utenti_online} Online</span>
</div>

<!-- Codice Invisibile di Tracciamento Realtime Statcounter -->
<script type="text/javascript">
var sc_project={SC_PROJECT}; 
var sc_invisible=1; 
var sc_security="{SC_SECURITY}"; 
</script>
<script type="text/javascript" src="https://www.statcounter.com/counter/counter.js" async></script>
<noscript><div class="statcounter"><a title="Web Analytics" href="https://statcounter.com/" target="_blank"><img class="statcounter" src="https://c.statcounter.com/{SC_PROJECT}/0/{SC_SECURITY}/1/" alt="Web Analytics" referrerPolicy="no-referrer-when-downgrade"></a></div></noscript>
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
                scheda_da_verificare = foglio_di_calcolo.add_worksheet(title="da verificare", rows="100", cols="20")
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
                        d = st.text_input("Data (es: 12 - 13 - 14 Giugno 2026)")
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
                eventi_passati = df[(df['Data_Date'].notna()) & (df['Data_Date'] < oggi)]
                if not eventi_passati.empty:
                    eventi_passati = eventi_passati.sort_values(by='GSheet_Row', ascending=False)
                    for _, riga_passata in eventi_passati.iterrows():
                        scheda.delete_rows(int(riga_passata['GSheet_Row']))
                    st.rerun()

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
                        
                        with st.expander(f"{row['Data']} - {row['Nome Evento / Raduno']}"):
                            st.write(f"📍 **Luogo:** {row['Luogo']} ({row['Regione']})")
                            st.write(f"📝 **Info:** {row.get('Dettagli / Note', 'Nessuna info')}")
                            
                            img_path = str(row.get('Locandina', '')).strip()
                            if img_path.startswith("http"):
                                # NUOVO SISTEMA DI ZOOm CINEMA CON TASTO DI CHIUSURA INTERNO DI TIPO "BACK"
                                st.html(f"""
                                <a href="#zoom_{idx}">
                                    <img src="{img_path}" class="locandina-cliccabile" alt="Locandina">
                                </a>
                                <div class="testo-aiuto-zoom">🔍 Clicca sulla locandina per aprirla a schermo intero</div>
                                
                                <!-- Struttura del tutto schermo sovrapposto (Lightbox) -->
                                <div class="lightbox-target" id="zoom_{idx}">
                                    <img src="{img_path}" alt="Zoom Locandina">
                                    <a class="lightbox-close-btn" href="#_">← TORNA ALL'EVENTO</a>
                                </div>
                                """)

                            pwd = st.text_input(f"Password per modificare {idx}", type="password", key=f"p_{idx}")
                            if pwd == "Judaz2026":
                                st.markdown("<div style='color: #00ffcc; font-size: 0.9rem; font-weight: bold;'>⚙️ MODALITÀ MODIFICA ATTIVA</div>", unsafe_allow_html=True)
                                
                                new_title = st.text_input(f"Modifica Titolo", value=str(row.get('Nome Evento / Raduno', '')), key=f"title_{idx}")
                                new_data = st.text_input(f"Modifica Data (Testo)", value=str(row.get('Data', '')), key=f"data_{idx}")
                                new_luogo = st.text_input(f"Modifica Luogo", value=str(row.get('Luogo', '')), key=f"luogo_{idx}")
                                
                                regione_attuale = str(row.get('Regione', 'Abruzzo')).strip()
                                idx_regione = 0
                                if regione_attuale in regioni_italia:
                                    idx_regione = regioni_italia.index(regione_attuale)
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

                        conteggio = int(row['Partecipanti'])
                        label = f"CI VADO 🔥 {conteggio}"
                        if ha_gia_votato(chiave_voto):
                            st.button(label, key=f"btn_{idx}", disabled=True)
                        else:
                            if st.button(label, key=f"btn_{idx}"):
                                scheda.update_cell(riga_foglio_google, 7, int(conteggio + 1))
                                registra_voto(chiave_voto)
                                st.rerun()
                else:
                    st.info("Nessun evento trovato con i filtri selezionati.")
            else:
                st.info("Il database su Google Sheets è vuoto.")

        # =========================================================
        # SCHERMATA 2: PAGINA MOTOCLUB (CORRETTA!)
        # =========================================================
        elif st.session_state["page"] == "mc":
            st.markdown("<h3 style='text-align: center; color: #ff9100; font-family: \"Special Elite\", cursive;'>I MOTO CLUB</h3>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: white; font-family: \"Special Elite\", cursive; font-size:0.9rem;'>«I club che hanno fatto la storia, le nostre origini. Dove la passione diventa fratellanza.»</p><br>", unsafe_allow_html=True)
            
            try:
                scheda_mc = foglio_di_calcolo.worksheet("motoclub")
                dati_mc = scheda_mc.get_all_values()
            except:
                scheda_mc = foglio_di_calcolo.add_worksheet(title="motoclub", rows="100", cols="10")
                scheda_mc.append_row(["Nome MotoClub", "Città", "Descrizione / Info", "Logo"])
                dati_mc = [["Nome MotoClub", "Città", "Descrizione / Info", "Logo"]]

            if len(dati_mc) > 1:
                for row_mc in dati_mc[1:]:
                    row_mc = (row_mc + [""] * 4)[:4]
                    nome_mc, citta_mc, info_mc, logo_mc = row_mc
                    
                    html_immagine = ""
                    if logo_mc.strip().startswith("http"):
                        html_immagine = f"""
                        <div class="logo-container-mc">
                            <a href="#zoom_mc_{nome_mc.replace(' ', '_')}">
                                <img src="{logo_mc.strip()}" class="logo-standard-mc" alt="Logo">
                            </a>
                        </div>
                        <!-- Lightbox anche per i Loghi dei Club -->
                        <div class="lightbox-target" id="zoom_mc_{nome_mc.replace(' ', '_')}">
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
        # SCHERMATA 3: ADMIN
        # =========================================================
        elif st.session_state["page"] == "admin":
            scheda = foglio_di_calcolo.get_worksheet(0)
            st.markdown("<h3 style='color: #ff9100; font-family: \"Special Elite\", cursive; text-align: center;'>Pannello Admin</h3>", unsafe_allow_html=True)
            pass_admin = st.text_input("Inserisci Password Amministratore", type="password", key="password_principale_admin")
            
            if pass_admin == "Judaz2026":
                st.markdown("<div style='color: #00ffcc; font-weight: bold; font-family: \"Special Elite\"; text-align: center;'>🔓 ACCESSO CONCESSO. SEI ONLINE.</div>", unsafe_allow_html=True)
                with st.form("admin_direct_form", clear_on_submit=True):
                    adm_n = st.text_input("Nome Evento")
                    adm_d = st.text_input("Data (es: 15 Luglio 2026)")
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
<div style='position: fixed; bottom: 0; left: 0; width: 100%; background: #1f2124; display: flex; justify-content: flex-start; gap: 30px; padding: 15px 20px; border-top: 3px solid #ff9100; z-index: 9999;'>
    <a href='?menu=home' target='_self' style='font-family: Special Elite; color: #ff9100; font-weight: bold; text-decoration: none; font-size: 1.2rem;'>HOME</a>
    <a href='?menu=mc' target='_self' style='font-family: Special Elite; color: #ff9100; font-weight: bold; text-decoration: none; font-size: 1.2rem;'>MC</a>
    <a href='?menu=admin' target='_self' style='font-family: Special Elite; color: #ff9100; font-weight: bold; text-decoration: none; font-size: 1.2rem;'>ADMIN</a>
</div>
""", unsafe_allow_html=True)
