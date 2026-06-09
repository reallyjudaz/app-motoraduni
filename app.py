import streamlit as st
import pandas as pd
import os
import re
from PIL import Image

# Configurazione della pagina (Deve essere la prima istruzione)
st.set_page_config(page_title="Iron & Rubber Route v1.0", layout="wide")

PASSWORD_ADMIN = "judaz2026"

# Inizializzazione degli stati della sessione
if "admin_logged_in" not in st.session_state:
    st.session_state["admin_logged_in"] = False

if "mie_partecipazioni" not in st.session_state:
    st.session_state["mie_partecipazioni"] = {}

if "sezione_attiva" not in st.session_state:
    st.session_state["sezione_attiva"] = "Home"

if "evento_selezionato" not in st.session_state:
    st.session_state["evento_selezionato"] = None

if "reset_filtri" not in st.session_state:
    st.session_state["reset_filtri"] = False

# --- CONFIGURAZIONE DELLO STILE CSS RIGIDO ---
CODICE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=UnifrakturMaguntina&family=Space+Grotesk:wght=400;700&display=swap');

/* Sfondo generale ed extra-spazio in fondo per evitare sovrapposizioni con la barra */
.stApp {
    background-color: #161719;
    color: #e3e2e6;
    font-family: 'Space Grotesk', sans-serif;
    padding-bottom: 240px !important; 
}

/* Titolo Gotico */
.sub-cattivo {
    text-align: center; 
    color: #ff9100; 
    font-size: 2.2rem; 
    font-family: 'UnifrakturMaguntina', serif !important; 
    letter-spacing: 2px; 
    text-shadow: 3px 3px 0px #000000;
    margin-top: 5px !important;
    margin-bottom: 25px !important;
}

h3 {
    font-family: 'UnifrakturMaguntina', serif !important;
    color: #ffffff !important;
    letter-spacing: 2px;
    font-size: 2.3rem !important;
    text-shadow: 2px 2px 0px #000000;
    margin-top: 20px !important;
}

/* Badge della Data */
.card-data {
    background-color: #ff9100;
    color: #000000;
    padding: 4px 12px;
    border-radius: 4px;
    font-weight: bold;
    font-size: 14px;
    display: inline-block;
    margin-bottom: 8px;
    text-transform: uppercase;
}

/* Testo Luogo */
.card-luogo {
    color: #00bcd4;
    font-weight: bold;
    font-size: 15px;
    margin-bottom: 8px;
    line-height: 1.4;
    display: block;
}

/* Titolo dell'evento testuale pulito */
.titolo-evento-testo {
    color: #ffffff !important;
    font-size: 20px !important;
    font-weight: 700 !important;
    display: block;
    margin-top: 5px;
    margin-bottom: 15px;
}

/* Forza la leggibilità dei testi dentro i bottoni di azione info */
div[data-testid="stHorizontalBlock"] button p {
    color: #161719 !important;
    font-weight: bold !important;
}

/* Badge contatore fiamme - Sincronizzato con l'altezza dei bottoni */
.badge-counter {
    background-color: #242629;
    color: #ff9100;
    padding: 0px 14px;
    border-radius: 4px;
    font-weight: bold;
    border: 2px solid #ff9100;
    box-shadow: 2px 2px 0px #000000;
    display: inline-block;
    height: 38px;
    line-height: 34px;
    text-align: center;
    font-size: 16px;
    width: 100%;
    box-sizing: border-box;
}

/* Spaziatore salvavita per spingere l'ultimo elemento sopra la barra */
.spaziatore-fine-pagina {
    height: 160px;
    display: block;
    width: 100%;
}

/* Box dei dettagli evento singolo (Pulito e Sobrio) */
.dettaglio-box {
    background-color: #1f2124;
    border: 2px solid #ff9100;
    border-radius: 6px;
    padding: 25px;
    box-shadow: 5px 5px 0px #000000;
    margin-top: 15px;
    margin-bottom: 20px;
}

/* Container nativo della card di Streamlit (Pulito e Sobrio) */
[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #1f2124 !important;
    border: 2px solid #3a3f44 !important;
    border-radius: 6px !important;
    box-shadow: 5px 5px 0px #000000 !important;
    padding: 20px !important;
    margin-bottom: 15px !important;
}

/* Forza l'allineamento dei widget orizzontali */
[data-testid="stHorizontalBlock"] {
    align-items: center !important;
}

/* BARRA DI NAVIGAZIONE ANCORATA IN BASSO */
div[data-testid="stBottomBlockContainer"] {
    background-color: #111214 !important;
    border-top: 3px solid #ff9100 !important;
    padding: 20px 40px !important;
    position: fixed !important;
    bottom: 0 !important;
    left: 0 !important;
    width: 100% !important;
    z-index: 99999 !important;
}

/* Pulsanti della barra inferiore arancione */
div[data-testid="stBottomBlockContainer"] button {
    background-color: #ff9100 !important;
    color: #000000 !important;
    font-weight: bold !important;
    font-size: 16px !important;
    box-shadow: 3px 3px 0px #000000 !important;
    border: none !important;
    width: 100% !important;
    height: 45px !important;
}

div[data-testid="stBottomBlockContainer"] button:hover {
    background-color: #e08000 !important;
    color: #000000 !important;
}
</style>
"""

st.markdown(CODICE_CSS, unsafe_allow_html=True)

FILE_EXCEL = "Lista_Eventi_Bikers_Judaz.xlsx"
CARTELLA_LOCANDINE = "locandine"

if not os.path.exists(CARTELLA_LOCANDINE):
    os.makedirs(CARTELLA_LOCANDINE)

LISTA_REGIONI = [
    "Tutta Italia", "Abruzzo", "Basilicata", "Calabria", "Campania", 
    "Emilia-Romagna", "Friuli-Venezia Giulia", "Lazio", "Liguria", 
    "Lombardia", "Marche", "Molise", "Piemonte", "Puglia", 
    "Sardegna", "Sicilia", "Toscana", "Trentino-Alto Adige", 
    "Umbria", "Valle d'Aosta", "Veneto"
]

# --- PARSER INTEGRALE CRONOLOGICO BLINDATO ---
def ordina_dataframe_per_data(dataframe):
    if dataframe.empty:
        return dataframe
    
    mesi_mappa = {
        "gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4, "maggio": 5, "giugno": 6,
        "luglio": 7, "agosto": 8, "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12,
        "gen": 1, "feb": 2, "mar": 3, "apr": 4, "mag": 5, "giu": 6,
        "lug": 7, "ago": 8, "set": 9, "ott": 10, "nov": 11, "dic": 12
    }
    
    def calcola_chiave_data(valore_data):
        stringa_data = str(valore_data).lower().strip()
        
        # 1. Controlla prima i mesi testuali per evitare falsi positivi con i range
        mese_trovato = None
        for mese_nome, identificatore in mesi_mappa.items():
            if mese_nome in stringa_data:
                mese_trovato = identificatore
                break
                
        if mese_trovato is not None:
            numeri = re.findall(r'\d+', stringa_data)
            giorno = int(numeri[0]) if numeri else 1
            return (mese_trovato, giorno)
            
        # 2. Se non c'è testo, cerca il formato numerico (es: 27/06/2026)
        match_barre = re.search(r'(\d{1,2})[\/\-](\d{1,2})', stringa_data)
        if match_barre:
            giorno = int(match_barre.group(1))
            mese = int(match_barre.group(2))
            return (mese, giorno)
            
        return (12, 31)
    
    df_copia = dataframe.copy()
    df_copia["_chiave_ordinamento"] = df_copia["Data"].apply(calcola_chiave_data)
    df_copia = df_copia.sort_values(by="_chiave_ordinamento").drop(columns=["_chiave_ordinamento"])
    return df_copia

def carica_dati():
    colonne_base = ["Data", "Regione", "Nome Evento / Raduno", "Luogo", "Dettagli / Note", "Locandina", "Partecipanti"]
    if not os.path.exists(FILE_EXCEL):
        df_vuoto = pd.DataFrame(columns=colonne_base)
        df_vuoto.to_excel(FILE_EXCEL, index=False)
        return df_vuoto
    df = pd.read_excel(FILE_EXCEL)
    df.columns = df.columns.str.strip()
    if "Regione" not in df.columns: df["Regione"] = ""
    if "Locandina" not in df.columns: df["Locandina"] = ""
    if "Partecipanti" not in df.columns: df["Partecipanti"] = 0
    df["Partecipanti"] = df["Partecipanti"].fillna(0).astype(int)
    
    df = ordina_dataframe_per_data(df)
    return df

df = carica_dati()

if st.session_state["reset_filtri"]:
    st.session_state["cerca_input"] = ""
    st.session_state["regione_input"] = "Tutta Italia"
    st.session_state["evento_selezionato"] = None
    st.session_state["reset_filtri"] = False

# --- CARICAMENTO LOGO ---
if os.path.exists("iron e rubber.png"):
    st.image("iron e rubber.png", use_container_width=True)
elif os.path.exists("logo_custom.png"):
    st.image("logo_custom.png", use_container_width=True)

st.markdown("<p class='sub-cattivo'>The Italian Biker Rallies Database</p>", unsafe_allow_html=True)

# ==========================================
#          NAVIGAZIONE SEZIONI
# ==========================================

if st.session_state["sezione_attiva"] == "Home":
    
    if st.session_state["evento_selezionato"] is not None:
        idx_ev = st.session_state["evento_selezionato"]
        
        if idx_ev in df.index:
            riga_ev = df.loc[idx_ev]
            
            if st.button("⬅️ Torna alla lista dei raduni"):
                st.session_state["evento_selezionato"] = None
                st.rerun()
                
            st.markdown(f"### 🦅 {riga_ev['Nome Evento / Raduno']}")
            
            note_pulite = riga_ev['Dettagli / Note']
            if pd.isna(note_pulite) or str(note_pulite).strip() == "" or str(note_pulite) == "nan":
                testo_dettagli = "Nessun dettaglio aggiuntivo inserito."
            else:
                testo_dettagli = str(note_pulite)

            st.markdown(f"""
            <div class="dettaglio-box">
                <span class="card-data">📅 {riga_ev['Data']}</span>
                <p class="card-luogo" style="font-size: 18px;">📍 {riga_ev['Luogo']} | 🗺️ {riga_ev['Regione']}</p>
                <hr style="border-color: #3a3f44;">
                <p style="font-size: 16px; white-space: pre-wrap;"><strong>Programma e Dettagli:</strong><br>{testo_dettagli}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # SEZIONE LOCANDINA RIDIMENSIONATA E COMODA
            path_locandina = riga_ev["Locandina"]
            if path_locandina and os.path.exists(str(path_locandina)) and str(path_locandina) != "nan":
                try:
                    col_sx, col_centro_img, col_dx = st.columns([1, 2, 1])
                    with col_centro_img:
                        st.image(Image.open(path_locandina), width=450)
                except:
                    st.error("Impossibile caricare la locandina.")
            
            # ELEMENTO SALVAVITA DETTAGLI
            st.markdown('<div class="spaziatore-fine-pagina"></div>', unsafe_allow_html=True)
            
        else:
            st.session_state["evento_selezionato"] = None
            st.rerun()

    else:
        # FILTRI DI RICERCA (Icona del razzo rimossa dal pulsante START)
        col_ricerca, col_btn_start, col_regione = st.columns([3, 1, 2])
        with col_ricerca:
            testo_cerca = st.text_input("🔍 Cerca parola chiave:", placeholder="Scrivi qui...", key="cerca_input")
        with col_btn_start:
            st.write("") ; st.write("")
            click_start = st.button("START", key="start_search")
        with col_regione:
            regione_scelta = st.selectbox("🗺️ Filtra per Regione:", LISTA_REGIONI, key="regione_input")

        df_filtrato = df.copy()
        if regione_scelta != "Tutta Italia":
            df_filtrato = df_filtrato[df_filtrato["Regione"].astype(str).str.lower().str.strip() == regione_scelta.lower().strip()]
        if testo_cerca:
            t = testo_cerca.lower()
            df_filtrato = df_filtrato[
                df_filtrato["Nome Evento / Raduno"].astype(str).str.lower().str.contains(t) |
                df_filtrato["Luogo"].astype(str).str.lower().str.contains(t)
            ]

        st.info(f"📋 Trovati {len(df_filtrato)} eventi in lista")
        st.write("### 📌 Eventi in programma")

        if df_filtrato.empty:
            st.warning("Nessun raduno trovato.")
        else:
            for index, riga in df_filtrato.iterrows():
                
                # CARD CON CONTAINER PULITO
                with st.container(border=True):
                    
                    st.markdown(f'<div class="card-data">📅 {riga["Data"]}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="card-luogo">📍 {riga["Luogo"]} | 🗺️ {riga["Regione"]}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="titolo-evento-testo">🏁 {riga["Nome Evento / Raduno"]}</div>', unsafe_allow_html=True)
                    
                    # Layout pulsanti
                    col_scopri, col_azione_btn, col_contatore = st.columns([2, 3, 1])
                    
                    with col_scopri:
                        if st.button("🔎 Vedi Info", key=f"info_{index}", use_container_width=True):
                            st.session_state["evento_selezionato"] = index
                            st.rerun()
                    
                    with col_azione_btn:
                        chiave_raduno = f"raduno_{index}"
                        ha_partecipato = st.session_state["mie_partecipazioni"].get(chiave_raduno, False)
                        
                        if not ha_partecipato:
                            if st.button("👍 Partecipo", key=f"part_{index}", use_container_width=True, type="primary"):
                                df_orig = pd.read_excel(FILE_EXCEL)
                                df_orig.at[index, "Partecipanti"] += 1
                                df_orig.to_excel(FILE_EXCEL, index=False)
                                st.session_state["mie_partecipazioni"][chiave_raduno] = True
                                st.rerun()
                        else:
                            if st.button("❌ Cancella", key=f"unpart_{index}", use_container_width=True):
                                df_orig = pd.read_excel(FILE_EXCEL)
                                if df_orig.at[index, "Partecipanti"] > 0:
                                    df_orig.at[index, "Partecipanti"] -= 1
                                df_orig.to_excel(FILE_EXCEL, index=False)
                                st.session_state["mie_partecipazioni"][chiave_raduno] = False
                                st.rerun()
                                
                    with col_contatore:
                        st.markdown(f"<div class='badge-counter'>🔥 {riga['Partecipanti']}</div>", unsafe_allow_html=True)
                    
                    # Amministrazione
                    if st.session_state["admin_logged_in"]:
                        with st.popover("📝 Opzioni Admin", use_container_width=True):
                            st.write(f"✏️ Modifica: {riga['Nome Evento / Raduno']}")
                            edit_data = st.text_input("Data:", value=riga['Data'], key=f"ed_dat_{index}")
                            edit_nome = st.text_input("Nome:", value=riga['Nome Evento / Raduno'], key=f"ed_nom_{index}")
                            edit_luogo = st.text_input("Luogo:", value=riga['Luogo'], key=f"ed_luo_{index}")
                            edit_regione = st.selectbox("Regione:", LISTA_REGIONI[1:], index=LISTA_REGIONI[1:].index(riga['Regione']) if riga['Regione'] in LISTA_REGIONI else 0, key=f"ed_reg_{index}")
                            edit_note = st.text_area("Note:", value=riga['Dettagli / Note'] if pd.notna(riga['Dettagli / Note']) else "", key=f"ed_not_{index}")
                            edit_foto = st.file_uploader("Aggiorna Locandina:", type=["png","jpg","jpeg"], key=f"ed_fot_{index}")
                            
                            col_salva, col_del = st.columns(2)
                            with col_salva:
                                if st.button("Salva", key=f"sub_ed_{index}", use_container_width=True):
                                    df_orig = pd.read_excel(FILE_EXCEL)
                                    df_orig.at[index, "Data"] = edit_data
                                    df_orig.at[index, "Nome Evento / Raduno"] = edit_nome
                                    df_orig.at[index, "Luogo"] = edit_luogo
                                    df_orig.at[index, "Regione"] = edit_regione
                                    df_orig.at[index, "Dettagli / Note"] = edit_note
                                    if edit_foto is not None:
                                        ext = os.path.splitext(edit_foto.name)[1]
                                        path_f = os.path.join(CARTELLA_LOCANDINE, f"mod_{index}{ext}")
                                        with open(path_f, "wb") as f: f.write(edit_foto.getbuffer())
                                        df_orig.at[index, "Locandina"] = path_f
                                    df_orig.to_excel(FILE_EXCEL, index=False)
                                    st.success("Modificato!")
                                    st.rerun()
                            with col_del:
                                if st.button("🗑️ Elimina", key=f"sub_del_{index}", use_container_width=True):
                                    df_orig = pd.read_excel(FILE_EXCEL)
                                    df_orig = df_orig.drop(index).reset_index(drop=True)
                                    df_orig.to_excel(FILE_EXCEL, index=False)
                                    st.rerun()
            
            # ELEMENTO SALVAVITA HOME
            st.markdown('<div class="spaziatore-fine-pagina"></div>', unsafe_allow_html=True)

# --- SEZIONE MC D'ITALIA ---
elif st.session_state["sezione_attiva"] == "MC":
    st.write("### 🦅 Motorcycle Clubs d'Italia")
    st.write("Sezione dedicata alla mappatura e alla lista di tutti i Club MC d'Italia.")
    st.markdown('<div class="spaziatore-fine-pagina"></div>', unsafe_allow_html=True)

# --- SEZIONE ADMIN ---
elif st.session_state["sezione_attiva"] == "Admin":
    st.write("### ⚙️ Pannello di Controllo Gestione")
    
    if not st.session_state["admin_logged_in"]:
        pwd_inserita = st.text_input("Password di Accesso:", type="password")
        if st.button("Sblocca Sistema"):
            if pwd_inserita == PASSWORD_ADMIN:
                st.session_state["admin_logged_in"] = True
                st.success("Accesso Egevole Eseguito!")
                st.rerun()
            else:
                st.error("Password errata!")
    else:
        st.write("🟢 **Sei connesso come Amministratore**")
        if st.button("Disconnetti ed Esci"):
            st.session_state["admin_logged_in"] = False
            st.rerun()
            
        st.write("---")
        st.write("### ➕ Aggiungi un Nuovo Raduno in Lista")
        with st.form("nuovo_evento_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                n_data = st.text_input("Data (es. 12-14 Luglio o 27/06/2026):")
                n_nome = st.text_input("Nome Evento / Raduno:")
            with c2:
                n_luogo = st.text_input("Luogo (Città e Prov):")
                n_regione = st.selectbox("Regione:", LISTA_REGIONI[1:], index=19)
            n_note = st.text_area("Dettagli / Programma Completo:")
            n_foto = st.file_uploader("Carica l'immagine della Locandina:", type=["jpg", "jpeg", "png", "webp"])
            
            if st.form_submit_button("💾 SALVA NEL DATABASE"):
                if not n_data or not n_nome or not n_luogo:
                    st.error("Compila i dati obbligatori!")
                else:
                    path_foto_salvata = ""
                    if n_foto is not None:
                        ext = os.path.splitext(n_foto.name)[1]
                        nome_p = n_nome.lower().replace(" ", "_")[:15]
                        path_foto_salvata = os.path.join(CARTELLA_LOCANDINE, f"{nome_p}{ext}")
                        with open(path_foto_salvata, "wb") as f: f.write(n_foto.getbuffer())
                    
                    df_salva = pd.read_excel(FILE_EXCEL)
                    nuovo_rec = pd.DataFrame([{"Data": n_data, "Regione": n_regione, "Nome Evento / Raduno": n_nome, "Luogo": n_luogo, "Dettagli / Note": n_note, "Locandina": path_foto_salvata, "Partecipanti": 0}])
                    pd.concat([df_salva, nuovo_rec], ignore_index=True).to_excel(FILE_EXCEL, index=False)
                    st.success("Raduno inserito con successo!")
                    
    st.markdown('<div class="spaziatore-fine-pagina"></div>', unsafe_allow_html=True)


# ==========================================
#  BARRA DI NAVIGAZIONE ANCORATA TOTALE
# ==========================================
with st.bottom:
    col_nav1, col_nav2, col_nav3 = st.columns(3)

    with col_nav1:
        if st.button("🏠 HOME", key="nav_home", use_container_width=True):
            st.session_state["sezione_attiva"] = "Home"
            st.session_state["evento_selezionato"] = None 
            st.session_state["reset_filtri"] = True  
            st.rerun()

    with col_nav2:
        if st.button("🦅 MC", key="nav_mc", use_container_width=True):
            st.session_state["sezione_attiva"] = "MC"
            st.rerun()

    with col_nav3:
        testo_tasto_admin = "⚙️ ADMIN (Attivo)" if st.session_state["admin_logged_in"] else "⚙️ ADMIN"
        if st.button(testo_tasto_admin, key="nav_admin", use_container_width=True):
            st.session_state["sezione_attiva"] = "Admin"
            st.rerun()