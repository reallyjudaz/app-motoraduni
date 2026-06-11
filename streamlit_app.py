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
NOME_DEL_FOGLIO = "app motoraduni"

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

# --- 4. CSS INTEGRATO ---
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

if os.path.exists("logo_custom.png"):
    st.image("logo_custom.png", use_container_width=True)

st.markdown("<h1 class='titolo-gotico'>Iron & Rubber</h1>", unsafe_allow_html=True)
st.markdown("<p class='sottotitolo'>«Non è la meta, è la strada a rivelare chi sei.»</p>", unsafe_allow_html=True)

if gc is None:
    st.error("Errore critico nella connessione a Google Cloud.")
else:
    try:
        foglio_di_calcolo = gc.open(NOME_DEL_FOGLIO)
        scheda = foglio_di_calcolo.get_worksheet(0)
        colonne_esatte = ["Nome Evento / Raduno", "Data", "Luogo", "Dettagli / Note", "Locandina", "Partecipanti"]
        
        tutti_i_dati = scheda.get_all_values()
        if tutti_i_dati and len(tutti_i_dati) > 1:
            righe_pulite = []
            for riga in tutti_i_dati[1:]:
                riga_6 = (riga + [""] * 6)[:6]
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
                url_inserito = st.text_input("Link della Locandina (URL internet - Consigliato)")
                f = st.file_uploader("Oppure carica file dal dispositivo (Temporaneo)", type=['jpg', 'png'])
             
                if st.form_submit_button("SALVA"):
                    path_finale = ""
                    if url_inserito.strip():
                        path_finale = url_inserito.strip()
                    elif f:
                        if not os.path.exists("locandine"): os.makedirs("locandine")
                        path_locale = os.path.join("locandine", f.name)
                        with open(path_locale, "wb") as file: file.write(f.getbuffer())
                        path_finale = path_locale
                    
                    scheda.append_row([n, d, l, i, path_finale, 0])
                    st.rerun()

        # --- LISTA EVENTI ---
        if not df.empty:
            df['GSheet_Row'] = df.index + 2
            df['Data_Date'] = df['Data'].apply(parsing_data_biker)
            df = df.sort_values(by='Data_Date', ascending=True, na_position='last')
            df['Partecipanti'] = pd.to_numeric(df['Partecipanti'], errors='coerce').fillna(0).astype(int)

            for idx, row in df.iterrows():
                riga_foglio_google = int(row['GSheet_Row'])
                chiave_voto = f"{row['Nome Evento / Raduno']}_{row['Data']}"
                
                with st.expander(f"{row['Data']} - {row['Nome Evento / Raduno']}"):
                    st.write(f"📍 **Luogo:** {row['Luogo']}")
                    st.write(f"📝 **Info:** {row.get('Dettagli / Note', 'Nessuna info')}")
                    
                    img_path = str(row.get('Locandina', '')).strip()
                    if img_path:
                        if img_path.startswith("http://") or img_path.startswith("https://"):
                            st.image(img_path, use_container_width=True)
                        elif os.path.exists(img_path):
                            st.image(img_path, use_container_width=True)
                    
                    # --- PANNELLO MODIFICA POTENZIATO ---
                    pwd = st.text_input(f"Password per modificare {idx}", type="password", key=f"p_{idx}")
                    if pwd == "Judaz2026":
                        new_info = st.text_area(f"Modifica Info {idx}", value=str(row.get('Dettagli / Note', '')), key=f"edit_{idx}")
                        new_img = st.text_input(f"Modifica Link Locandina URL {idx}", value=img_path, key=f"img_{idx}")
                        
                        if st.button("SALVA MODIFICHE", key=f"save_{idx}"):
                            # Aggiorna colonna 4 (Info) e colonna 5 (Locandina) su Google Sheets
                            scheda.update_cell(riga_foglio_google, 4, new_info)
                            scheda.update_cell(riga_foglio_google, 5, new_img)
                            st.rerun()

                # --- BOTTONE PARTECIPA ---
                conteggio = int(row['Partecipanti'])
                label = f"CI VADO 🔥 {conteggio}"
                if ha_gia_votato(chiave_voto):
                    st.button(label, key=f"btn_{idx}", disabled=True)
                else:
                    if st.button(label, key=f"btn_{idx}"):
                        scheda.update_cell(riga_foglio_google, 6, int(conteggio + 1))
                        registra_voto(chiave_voto)
                        st.rerun()
                
                st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.info("Il database su Google Sheets è vuoto.")

    except Exception as e:
        st.error(f"Errore: {e}")

# --- MENU FISSO ---
st.markdown("""
<div style='position: fixed; bottom: 0; left: 0; width: 100%; background: #1f2124; display: flex; justify-content: flex-start; gap: 30px; padding: 15px 20px; border-top: 3px solid #ff9100; z-index: 9999;'>
    <a href='#' style='font-family: Special Elite; color: #ff9100; font-weight: bold; text-decoration: none; font-size: 1.2rem;'>HOME</a>
    <a href='#' style='font-family: Special Elite; color: #ff9100; font-weight: bold; text-decoration: none; font-size: 1.2rem;'>MC</a>
    <a href='#' style='font-family: Special Elite; color: #ff9100; font-weight: bold; text-decoration: none; font-size: 1.2rem;'>ADMIN</a>
</div>
""", unsafe_allow_html=True)
