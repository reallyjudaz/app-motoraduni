import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Iron & Rubber Route", layout="wide")

# --- CONNESSIONE GOOGLE SHEETS ---
@st.cache_resource
def get_sheet():
    creds_dict = st.secrets["gcp_service_account"]
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/drive']
    # Correzione del metodo di autenticazione
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    # INSERISCI QUI IL NOME ESATTO DEL TUO FOGLIO GOOGLE
    return client.open("app motoraduni").sheet1

# Inizializza la connessione
try:
    sheet = get_sheet()
except Exception as e:
    st.error(f"Errore di connessione a Google Sheets: {e}")
    st.stop()

def carica_dati():
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    colonne = ["Data", "Regione", "Nome Evento / Raduno", "Luogo", "Dettagli / Note", "Locandina", "Partecipanti"]
    for col in colonne:
        if col not in df.columns: df[col] = ""
    df["Partecipanti"] = pd.to_numeric(df["Partecipanti"], errors='coerce').fillna(0).astype(int)
    return df

# --- INTERFACCIA ---
st.markdown("<h1 style='text-align: center; color: #ff9100;'>Iron & Rubber Route</h1>", unsafe_allow_html=True)

df = carica_dati()

# Visualizzazione eventi
for index, riga in df.iterrows():
    with st.container(border=True):
        st.write(f"### {riga['Nome Evento / Raduno']}")
        st.write(f"Data: {riga['Data']} | Luogo: {riga['Luogo']}")
        
        if st.button(f"👍 Partecipo a {riga['Nome Evento / Raduno']}", key=f"btn_{index}"):
            nuovo_valore = int(riga['Partecipanti']) + 1
            # Aggiorna su Google Sheets (+2 per compensare header e indice 0)
            sheet.update_cell(index + 2, df.columns.get_loc("Partecipanti") + 1, nuovo_valore)
            st.rerun()
        
        st.write(f"🔥 Partecipanti attuali: {riga['Partecipanti']}")
