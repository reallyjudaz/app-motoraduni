import streamlit as st
import pandas as pd
import os
import re
import gspread
from google.oauth2 import service_account

# --- 1. CONFIGURAZIONE GRAFICA DELLA PAGINA ---
st.set_page_config(page_title="Iron & Rubber", layout="centered")

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
NOME_DEL_FOGLIO = "app motoraduni"  # Nome del tuo foglio Google

# --- 3. FUNZIONI DATI (Voti Locali sul Telefono e Parsing Date) ---
def registra_voto(chiave_evento):
    with open("voti_fatti.txt", "a") as f:
        f.write(f"{chiave_evento}\n")

def ha_gia_votato(chiave_evento):
    if not os.path.exists("voti_fatti.txt"): return False
    with open("voti_fatti.txt", "r") as f:
        return str(chiave_evento) in f.read().splitlines()

def parsing_data_biker(testo_data):
    """ Funzione intelligente che traduce le date testuali dei raduni in date reali per l'ordinamento """
    testo = str(testo_data).lower().strip()
    if not testo or testo == "nan": return pd.NaT
    
    # Dizionario dei mesi in italiano
    mesi = {
        'gen': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'mag': 5, 'giu': 6, 
        'lug': 7, 'ago': 8, 'set': 9, 'ott': 10, 'nov': 11, 'dic': 12
    }
    
    # Trova il mese nel testo
    mese_num = None
    for k, v in mesi.items():
        if k in testo:
            mese_num = v
            break
            
    # Se non trova un mese testuale, prova il parsing numerico standard italiano
    if not mese_num:
        try: return pd.to_datetime(testo, dayfirst=True, errors='coerce')
        except: return pd.NaT
        
    # Trova l'anno a 4 cifre (es: 2026), se manca imposta 2026 di default
    anno_match = re.search(r'\b(202\d)\b', testo)
    anno = int(anno_match.group(1)) if anno_match else 2026
    
    # Trova il primo numero nel testo (il giorno d'inizio del raduno)
    giorno_match = re.search(r'\d+', testo)
    giorno = int(giorno_match.group(0)) if giorno_match else 1
    
    try:
        return pd.Timestamp(year=anno, month=mese_num, day=giorno)
    except:
        return pd.NaT

# --- 4. CSS INTEGRATO ORIGINALE ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=UnifrakturMaguntia&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Special+Elite&display=swap');

.stApp { background-color: #161719; }
#MainMenu, footer, header {visibility: hidden !important;}
.block-container { padding-top: 0rem !important; padding-bottom: 7rem !important; }

.titolo-gotico { font-family: 'UnifrakturMaguntia', cursive !important; text-align: center; color: #ff9100 !important; font-size: 2.6rem !important; margin-top: -20px !important; }
.sottotitolo { font-family: 'UnifrakturMaguntia', cursive !important; text-align: center; color: #ff9100 !important; font-size: 1.4rem !important; margin-bottom: 20px !important; }

.stExpander { background-color: #1f2124 !important; border: 2px solid #ff9100 !important; border-radius: 10px !important; color: white !important; }
.streamlit-expanderHeader { color: #ff9100 !important; font-weight: bold !important; font-size: 1.0rem !important; }

div[data-testid="stButton"] button { 
    background-color: #ff9100 !important; color: black !important; font-weight: bold !important; font-family: 'Special Elite', cursive !important; border-radius: 5px !important; height: 38px !important; width: 100%;
}

label, .stTextInput label, .stTextArea label, .stFileUploader label { color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- 5. HEADER (Logo) ---
if os.path.exists("logo_custom.png"):
    st.image("logo_custom.png", use_container_width=True)

st.markdown("<h1 class='titolo-gotico'>Iron & Rubber</h1>", unsafe_allow_html=True)
st.markdown("<p class='sottotitolo'>«Non è la meta, è la strada a rivelare chi sei.»</p>", unsafe_allow_html=True)

# --- 6. LOGICA DI CARICAMENTO ED ESECUZIONE ---
if gc is None:
    st.error("Errore critico nella connessione a Google Cloud nei Secrets.")
else:
    try:
        # Connessione alla scheda di Google Sheets
        foglio_di_calcolo = gc.open(NOME_DEL_FOGLIO)
        scheda = foglio_di_calcolo.get_worksheet(0)
        
        colonne_esatte = ["Nome Evento / Raduno", "Data", "Luogo", "Dettagli / Note", "Locandina", "Partecipanti"]
        
        # Lettura dei valori grezzi dal foglio
        tutti_i_dati = scheda.get_all_values()
        
        if tutti_i_dati and len(tutti_i_dati) > 1:
            righe_pulite = []
            for riga in tutti_i_dati[1:]:
                riga_6 = (riga + [""] * 6)[:6]  # Forza a 6 elementi per sicurezza
                righe_pulite.append(riga_6)
            df = pd.DataFrame(righe_pulite, columns=colonne_esatte)
        else:
            df = pd.DataFrame(columns=colonne_esatte)

        # --- FORM AGGIUNGI EVENTO ---
        with st.expander("➕ AGGIUNGI EVENTO"):
            with st.form("add_form", clear_on_submit=True):
                n = st.text_input("Nome Evento")
                d = st.text_input("Data (es: 12 - 13 - 14 Giugno 2026)")
                l = st.text_input("Luogo")
                i = st.text_area("Info")
                f = st.file_uploader("Locandina", type=['jpg', 'png'])
             
                if st.form_submit_button("SALVA"):
                    if not os.path.exists("locandine"): os.makedirs("locandine")
                    path = os.path.join("locandine", f.name) if f else ""
                    if f:
                        with open(path, "wb") as file: file.write(f.getbuffer())
                    
                    # Salva nel foglio Google
                    scheda.append_row([n, d, l, i, path, 0])
                    st.rerun()

        # --- LISTA EVENTI ORDINATA ---
        if not df.empty:
            # Crea un indice basato sulla posizione REALE nel foglio (+2 per via di intestazione e indice che parte da 1)
            df['GSheet_Row'] = df.index + 2
            
            # APPLICAZIONE PARSING INTELLIGENTE DELLE DATE
            df['Data_Date'] = df['Data'].apply(parsing_data_biker)
            
            # Ordina in modo cronologico perfetto. Eventuali date completamente illeggibili vanno in fondo.
            df = df.sort_values(by='Data_Date', ascending=True, na_position='last')
            
            # Forza partecipanti a numero intero
            df['Partecipanti'] = pd.to_numeric(df['Partecipanti'], errors='coerce').fillna(0).astype(int)

            for idx, row in df.iterrows():
                riga_foglio_google = int(row['GSheet_Row'])
                chiave_voto = f"{row['Nome Evento / Raduno']}_{row['Data']}"
                
                # Apertura Blocco Rettangolo Evento (Expander)
                with st.expander(f"{row['Data']} - {row['Nome Evento / Raduno']}"):
                    st.write(f"📍 **Luogo:** {row['Luogo']}")
                    st.write(f"📝 **Info:** {row.get('Dettagli / Note', 'Nessuna info')}")
                    
                    img_path = str(row.get('Locandina', ''))
                    if img_path and os.path.exists(img_path):
                        st.image(img_path, use_container_width=True)
                    
                    # Modifica Protetta con Password
                    pwd = st.text_input(f"Password per modificare {idx}", type="password", key=f"p_{idx}")
                    if pwd == "Judaz2026":
                        new_info = st.text_area(f"Modifica Info {idx}", value=str(row.get('Dettagli / Note', '')), key=f"edit_{idx}")
                        if st.button("SALVA MODIFICHE", key=f"save_{idx}"):
                            scheda.update_cell(riga_foglio_google, 4, new_info)
                            st.rerun()

                # --- POSIZIONATO ESATTAMENTE SOTTO L'EVENTO (FUORI DAL RETTANGOLO) ---
                conteggio = int(row['Partecipanti'])
                label = f"CI VADO 🔥 {conteggio}"
                
                if ha_gia_votato(chiave_voto):
                    st.button(label, key=f"btn_{idx}", disabled=True)
                else:
                    if st.button(label, key=f"btn_{idx}"):
                        scheda.update_cell(riga_foglio_google, 6, int(conteggio + 1))
                        registra_voto(chiave_voto)
                        st.rerun()
                
                # Spazio vuoto distanziatore tra un evento e l'altro
                st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.info("Il database su Google Sheets è vuoto. Aggiungi il tuo primo evento!")

    except Exception as e:
        st.error(f"Errore durante l'elaborazione dei dati: {e}")

# --- 7. MENU FISSO IN BASSO ---
st.markdown("""
<div style='position: fixed; bottom: 0; left: 0; width: 100%; background: #1f2124; display: flex; justify-content: flex-start; gap: 30px; padding: 15px 20px; border-top: 3px solid #ff9100; z-index: 9999;'>
    <a href='#' style='font-family: Special Elite; color: #ff9100; font-weight: bold; text-decoration: none; font-size: 1.2rem;'>HOME</a>
    <a href='#' style='font-family: Special Elite; color: #ff9100; font-weight: bold; text-decoration: none; font-size: 1.2rem;'>MC</a>
    <a href='#' style='font-family: Special Elite; color: #ff9100; font-weight: bold; text-decoration: none; font-size: 1.2rem;'>ADMIN</a>
</div>
""", unsafe_allow_html=True)
