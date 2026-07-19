import streamlit as st
import pandas as pd
import re
import gspread
from google.oauth2 import service_account

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Iron & Rubber", layout="centered")

if "voti_locali" not in st.session_state:
    st.session_state["voti_locali"] = set()

def registra_voto(chiave_evento):
    st.session_state["voti_locali"].add(str(chiave_evento))

def ha_gia_votato(chiave_evento):
    return str(chiave_evento) in st.session_state["voti_locali"]

def parsing_data_biker(testo_data):
    testo = str(testo_data).lower().strip()
    if not testo or testo in ["nan", "vedi nel sito", "vedi nel file"]: return pd.NaT
    match_standard = re.search(r'\b(\d{2})/(\d{2})/(202\d)\b', testo)
    if match_standard:
        try: return pd.Timestamp(year=int(match_standard.group(3)), month=int(match_standard.group(2)), day=int(match_standard.group(1)))
        except: pass
    mesi = {'gen': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'mag': 5, 'giu': 6, 'lug': 7, 'ago': 8, 'set': 9, 'ott': 10, 'nov': 11, 'dic': 12}
    mese_num = next((v for k, v in mesi.items() if k in testo), None)
    if not mese_num:
        try: return pd.to_datetime(testo, dayfirst=True, errors='coerce')
        except: return pd.NaT
    anno = int(re.search(r'\b(202\d)\b', testo).group(1)) if re.search(r'\b(202\d)\b', testo) else 2026
    giorno = int(re.search(r'\d+', testo).group(0)) if re.search(r'\d+', testo) else 1
    try: return pd.Timestamp(year=anno, month=mese_num, day=giorno)
    except: return pd.NaT

@st.cache_resource
def inizializza_connessione_google():
    try:
        credentials_info = dict(st.secrets["gcp_service_account"])
        if "private_key" in credentials_info:
            credentials_info["private_key"] = credentials_info["private_key"].replace("\\n", "\n")
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        credentials = service_account.Credentials.from_service_account_info(credentials_info, scopes=scopes)
        return gspread.authorize(credentials)
    except: return None

gc = inizializza_connessione_google()
NOME_DEL_FOGLIO = "app motoraduni"
URL_APP = "https://app-motoraduni-6hqxxahyypkhyxmqmpsk2v.streamlit.app/"

# --- CSS ---
st.markdown("""
<style>
.stApp { background-color: #161719; }
</style>
""", unsafe_allow_html=True)

# --- LOGICA ---
if gc:
    foglio_di_calcolo = gc.open(NOME_DEL_FOGLIO)
    scheda = foglio_di_calcolo.get_worksheet(0)
    tutti_i_dati = scheda.get_all_values()
    df = pd.DataFrame(tutti_i_dati[1:], columns=tutti_i_dati[0]) if tutti_i_dati else pd.DataFrame()
    
    if not df.empty:
        df['GSheet_Row'] = df.index + 2
        df['Data_Date'] = df['Data'].apply(parsing_data_biker)
        df = df[(df['Data_Date'].isna()) | (df['Data_Date'] >= pd.Timestamp.now().normalize())]
        
        for idx, row in df.iterrows():
            riga_foglio_google = int(row['GSheet_Row'])
            chiave_voto = f"{row['Nome Evento / Raduno']}_{row['Data']}"
            img_path = str(row.get('Locandina', '')).strip()
            ha_locandina = img_path.startswith("http")
            
            with st.expander(f"{row['Data']} - {row['Nome Evento / Raduno']}"):
                st.write(f"📍 **Luogo:** {row['Luogo']} ({row['Regione']})")
                st.write(f"{row['Info']}")
                
                if ha_locandina:
                    st.markdown(f'<a href="{img_path}" target="_blank"><img src="{img_path}" style="width:100%; border-radius:5px; border:2px solid #ff9100;"></a>', unsafe_allow_html=True)
                    st.caption("🔍 Clicca sulla locandina per aprirla a schermo intero")
                
                # --- AREA AZIONI IN BASSO ---
                st.write("---")
                gia_votato = ha_gia_votato(chiave_voto)
                
                # Creiamo la riga delle azioni
                c1, c2, c3 = st.columns([3, 1, 1])
                
                with c1:
                    if gia_votato:
                        st.button(f"CI VADO 🔥 {row.get('Partecipanti', 0)}", key=f"btn_{idx}", disabled=True)
                    else:
                        if st.button(f"CI VADO 🔥 {row.get('Partecipanti', 0)}", key=f"btn_{idx}"):
                            scheda.update_cell(riga_foglio_google, 7, int(row.get('Partecipanti', 0)) + 1)
                            registra_voto(chiave_voto)
                            st.rerun()
                
                with c2:
                    # Bottone Condividi nativo
                    st.link_button("🔗", URL_APP, help="Condividi evento")
                
                with c3:
                    # Mini anteprima
                    if ha_locandina:
                        st.markdown(f'<a href="{img_path}" target="_blank"><img src="{img_path}" style="width:40px; border-radius:5px; border:1px solid #ff9100;"></a>', unsafe_allow_html=True)
