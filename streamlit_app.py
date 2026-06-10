import streamlit as st
import gspread
from google.oauth2 import service_account

# 1. Configurazione iniziale della pagina Streamlit
st.set_page_config(page_title="Bikers Bot App", page_icon="🚴", layout="centered")
st.title("🚴 Bikers Bot - Pannello di Controllo")

# 2. Funzione ottimizzata e auto-riparante per connettersi a Google Sheets usando i Secrets
@st.cache_resource
def inizializza_connessione_google():
    try:
        # Trasforma i secrets in un dizionario modificabile in Python
        credentials_info = dict(st.secrets["gcp_service_account"])
        
        # SANIFICAZIONE DELLA CHIAVE (Risolve l'errore ASN.1 / Could not deserialize key data)
        raw_key = credentials_info["private_key"]
        
        # Rimuove spazi vuoti e tabulazioni invisibili all'inizio e alla fine di ogni riga
        lines = [line.strip() for line in raw_key.split('\n') if line.strip()]
        
        # Ricostruisce la chiave con gli "a capo" puliti ed esatti richiesti da Google
        cleaned_key = "\n".join(lines)
        
        # Gestisce i casi in cui ci siano caratteri "\n" scritti come testo letterale
        cleaned_key = cleaned_key.replace("\\n", "\n")
        
        # Se manca il carattere di a capo finale fondamentale, lo aggiunge
        if not cleaned_key.endswith("\n"):
            cleaned_key += "\n"
            
        # Sovrascrive la chiave corretta nel dizionario
        credentials_info["private_key"] = cleaned_key
        
        # Configura i permessi per Google Sheets e Drive
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Genera le credenziali sicure con la chiave appena riparata
        credentials = service_account.Credentials.from_service_account_info(credentials_info, scopes=scopes)
        
        # Autorizza e restituisce il client gspread
        return gspread.authorize(credentials)
        
    except Exception as e:
        st.error("Errore critico durante la sanificazione o la lettura delle credenziali Google.")
        st.exception(e)
        return None

# 3. Avvia la connessione automatica
gc = inizializza_connessione_google()

if gc is not None:
    st.success("⚡ Connessione a Google Cloud stabilita correttamente!")
    
    # =========================================================================
    # ⚠️ DA MODIFICARE: Inserisci qui sotto il nome ESATTO del tuo Foglio Google
    # =========================================================================
    NOME_DEL_FOGLIO = "app motoraduni" 
    
    try:
        # Apre il file di Google Sheets usando il nome
        foglio_di_calcolo = gc.open(NOME_DEL_FOGLIO)
        
        # Seleziona la prima scheda (Tab) del foglio
        scheda = foglio_di_calcolo.get_worksheet(0)
        
        st.subheader(f"Dati attuali nel foglio: *{NOME_DEL_FOGLIO}*")
        
        # Legge tutti i dati all'interno del foglio e li trasforma in una lista di dizionari
        dati = scheda.get_all_records()
        
        if dati:
            # Mostra i dati in una bellissima tabella interattiva su Streamlit
            st.dataframe(dati, use_container_width=True)
        else:
            st.info("Il foglio è connesso, ma sembra essere vuoto o privo di intestazioni nella prima riga.")
            
        # --- Form per aggiungere dati al foglio (Esempio) ---
        st.divider()
        st.subheader("Aggiungi una nuova riga nel foglio")
        with st.form("nuovo_inserimento"):
            campo_1 = st.text_input("Dato 1")
            campo_2 = st.text_input("Dato 2")
            submit = st.form_submit_button("Invia dati a Google Sheets")
            
            if submit:
                # Aggiunge i dati inseriti nel form in fondo al foglio Google
                scheda.append_row([campo_1, campo_2])
                st.success("Riga aggiunta con successo! Aggiorna la pagina per vederla.")
                
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Impossibile trovare il foglio chiamato '{NOME_DEL_FOGLIO}'.")
        st.info("Assicurati di aver digitato il nome maiuscole/minuscole comprese e di aver condiviso il foglio Google con l'email del bot.")
    except Exception as e:
        st.error("Si è verificato un errore durante la lettura dei dati:")
        st.exception(e)
