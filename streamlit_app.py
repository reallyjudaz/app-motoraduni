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
.riga-pulsante-anteprima { display: flex !important; align-items: center !important; gap: 10px !important; margin-top: 10px !important; margin-bottom: 10px !important; }
.html-btn-civado { background-color: #ff9100 !important; color: black !important; font-weight: bold !important; font-family: 'Special Elite', cursive !important; border-radius: 5px !important; height: 38px !important; padding: 0px 20px !important; text-decoration: none !important; display: flex; align-items: center; justify-content: center; }
.html-btn-condividi { background-color: #333333 !important; color: white !important; font-family: 'Special Elite', cursive !important; border-radius: 5px !important; height: 38px !important; width: 45px !important; padding: 0px !important; border: none !important; cursor: pointer !important; display: flex !important; align-items: center !important; justify-content: center !important; font-size: 1.2rem !important; }
.locandina-anteprima-rettangolare { height: 38px !important; width: auto !important; max-width: 70px !important; object-fit: contain !important; border: 2px solid #ff9100; border-radius: 5px; }
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
                if ha_locandina:
                    gia_votato = ha_gia_votato(chiave_voto)
                    html_bottone = f'<div class="html-btn-civado" style="background:#555!important">CI VADO 🔥 {row.get("Partecipanti", 0)}</div>' if gia_votato else f'<a href="?vota={idx}" target="_self" class="html-btn-civado">CI VADO 🔥 {row.get("Partecipanti", 0)}</a>'
                    
                    st.html(f"""
                    <script>
                    function condividiEvento(titolo) {{
                        if (navigator.share) {{ 
                            navigator.share({{ title: titolo, url: '{URL_APP}' }}); 
                        }} else {{ alert('Condivisione non supportata'); }}
                    }}
                    </script>
                    <div class="riga-pulsante-anteprima">
                        {html_bottone}
                        <button class="html-btn-condividi" onclick="condivisiEvento('{row['Nome Evento / Raduno']}')">🔗</button>
                        <a href="{img_path}" target="_blank"><img src="{img_path}" class="locandina-anteprima-rettangolare"></a>
                    </div>
                    """)
                    
                    if f"vota" in st.query_params and st.query_params["vota"] == str(idx) and not gia_votato:
                        scheda.update_cell(riga_foglio_google, 7, int(row.get('Partecipanti', 0)) + 1)
                        registra_voto(chiave_voto)
                        st.rerun()
