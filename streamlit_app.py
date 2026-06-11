import streamlit as st
import pandas as pd
import os
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

# --- 3. FUNZIONI DATI (Voti Locali sul Telefono) ---
def registra_voto(chiave_evento):
    with open("voti_fatti.txt", "a") as f:
        f.write(f"{chiave_evento}\n")

def ha_gia_votato(chiave_evento):
    if not os.path.exists("voti_fatti.txt"): return False
    with open("voti_fatti.txt", "r") as f:
        return str(chiave_evento) in f.read().splitlines()

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
        
        # AUTO-GUARIGIONE: Forza le intestazioni corrette nella riga 1 del foglio Google
        colonne_esatte = ["Nome Evento / Raduno", "Data", "Luogo", "Dettagli / Note", "Locandina", "Partecipanti"]
        scheda.update(range_name='A1:F1', values=[colonne_esatte])
        
        # Recupero dei record correnti
        dati = scheda.get_all_records()
        if dati:
            df = pd.DataFrame(dati)
        else:
            df = pd.DataFrame(columns=colonne_esatte)

        # --- FORM AGGIUNGI EVENTO ---
        with st.expander("➕ AGGIUNGI EVENTO"):
            with st.form("add_form", clear_on_submit=True):
                n = st.text_input("Nome Evento")
                d = st.text_input("Data (es: 2026-12-31)")
                l = st.text_input("Luogo")
                i = st.text_area("Info")
                f = st.file_uploader("Locandina", type=['jpg', 'png'])
             
                if st.form_submit_button("SALVA"):
                    if not os.path.exists("locandine"): os.makedirs("locandine")
                    path = os.path.join("locandine", f.name) if f else ""
                    if f:
                        with open(path, "wb") as file: file.write(f.getbuffer())
                    
                    # Salva su Google Sheets rispettando l'ordine delle colonne corrette
                    scheda.append_row([n, d, l, i, path, 0])
                    st.rerun()

        # --- LISTA EVENTI ORDINATA ---
        if not df.empty:
            # Crea un indice di backup basato sulla posizione reale nel foglio Google (+2 perché Sheets parte da 1 e la riga 1 ha i titoli)
            df['GSheet_Row'] = df.index + 2
            
            # Conversione Data per ordinamento cronologico
            df['Data_Date'] = pd.to_datetime(df['Data'], errors='coerce')
            df = df.sort_values(by='Data_Date', ascending=True)
            
            # Forza partecipanti a numero intero
            df['Partecipanti'] = pd.to_numeric(df['Partecipanti'], errors='coerce').fillna(0).astype(int)

            for idx, row in df.iterrows():
                riga_foglio_google = int(row['GSheet_Row'])
                
                # Creiamo una chiave unica per il voto basata su Nome e Data (stabile e sicura)
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
