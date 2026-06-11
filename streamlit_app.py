import streamlit as st
import gspread
from google.oauth2 import service_account

# 1. Configurazione grafica della pagina
st.set_page_config(page_title="Bikers Bot App", page_icon="🚴", layout="centered")
st.title("🚴 Bikers Bot - Pannello di Controllo")

# 2. Connessione sicura e ottimizzata a Google Cloud
@st.cache_resource
def inizializza_connessione_google():
    try:
        # Carica le credenziali dai Secrets di Streamlit
        credentials_info = dict(st.secrets["gcp_service_account"])
        
        # Converte i caratteri letterali '\n' in reali ritorni a capo per la libreria RSA
        if "private_key" in credentials_info:
            credentials_info["private_key"] = credentials_info["private_key"].replace("\\n", "\n")
        
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        credentials = service_account.Credentials.from_service_account_info(credentials_info, scopes=scopes)
        return gspread.authorize(credentials)
    except Exception as e:
        st.error("Errore critico durante l'inizializzazione delle credenziali di Google.")
        st.exception(e)
        return None

# 3. Avvio della connessione
gc = inizializza_connessione_google()

if gc is not None:
    st.success("⚡ Connessione a Google Cloud stabilita correttamente!")
    
    # =========================================================================
    # ⚠️ CAMBIA SOLO QUESTA RIGA: Inserisci il nome ESATTO del tuo Foglio Google
    # =========================================================================
    NOME_DEL_FOGLIO = "app motoraduni" 
    
    try:
        # Apertura del database su Google Sheets
        foglio_di_calcolo = gc.open(NOME_DEL_FOGLIO)
        scheda = foglio_di_calcolo.get_worksheet(0)
        
        st.subheader(f"Dati attuali nel foglio: *{NOME_DEL_FOGLIO}*")
        dati = scheda.get_all_records()
        
        if dati:
            st.dataframe(dati, use_container_width=True)
        else:
            st.info("Il foglio è connesso, ma è attualmente vuoto o manca la riga di intestazione.")
            
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Impossibile trovare il file Google Sheets chiamato '{NOME_DEL_FOGLIO}'.")
        st.info("Verifica che il nome sia scritto bene e di aver condiviso il file del foglio con l'email del bot come Editor.")
    except Exception as e:
        st.error("Si è verificato un errore durante il recupero dei dati:")
        st.exception(e)
