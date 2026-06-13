import streamlit as st

# 1. Inizializzazione di un dizionario di eventi fittizio nello stato della sessione (se non esiste già)
# Sostituisci questo blocco con il caricamento dal tuo database (Firebase, SQLite, ecc.) se necessario
if 'eventi' not in st.session_state:
    st.session_state.eventi = {
        "id_1": {"titolo": "Riunione di Marketing", "data": "2026-06-15", "descrizione": "Discussione budget Q3"},
        "id_2": {"titolo": "Lancio Nuovo Prodotto", "data": "2026-07-01", "descrizione": "Presentazione Iron & Rubber"}
    }

# Stato per tracciare quale evento è in fase di modifica (None = nessuno)
if 'id_evento_in_modifica' not in st.session_state:
    st.session_state.id_evento_in_modifica = None


st.title("📅 Gestione Eventi - Iron & Rubber")

# --- SEZIONE 1: MOSTRA LA LISTA DEGLI EVENTI ---
st.subheader("I tuoi Eventi")

for ev_id, ev_data in list(st.session_state.eventi.items()):
    col1, col2 = st.columns([4, 1])
    
    # Mostra i dettagli dell'evento
    col1.write(f"**{ev_data['titolo']}** — {ev_data['data']}")
    
    # Tasto per entrare in modalità modifica
    if col2.button("Modifica", key=f"btn_edit_{ev_id}"):
        st.session_state.id_evento_in_modifica = ev_id
        st.rerun()


# --- SEZIONE 2: FORM DI MODIFICA (Compare solo se un evento è selezionato) ---
if st.session_state.id_evento_in_modifica is not None:
    st.divider()
    id_corrente = st.session_state.id_evento_in_modifica
    evento_corrente = st.session_state.eventi[id_corrente]
    
    st.subheader(f"🛠️ Modifica: {evento_corrente['titolo']}")
    
    # INPUT: Modifica del TITOLO (come richiesto)
    nuovo_titolo = st.text_input("Titolo dell'evento", value=evento_corrente["titolo"])
    
    # Altri campi dell'evento
    nuova_data = st.text_input("Data dell'evento", value=evento_corrente["data"])
    nuova_descrizione = st.text_area("Descrizione", value=evento_corrente["descrizione"])
    
    # Creiamo i pulsanti di azione in fondo al form di modifica
    col_salva, col_elimina, col_annulla = st.columns([1, 1, 2])
    
    # 1. Tasto Salva Modifiche
    if col_salva.button("Salva Modifiche", type="primary", key="save_changes"):
        # Aggiorna i dati nel session_state (o nel tuo database)
        st.session_state.eventi[id_corrente]["titolo"] = nuovo_titolo
        st.session_state.eventi[id_corrente]["data"] = nuova_data
        st.session_state.eventi[id_corrente]["descrizione"] = nuova_descrizione
        
        # Esci dalla modalità modifica e ricarica
        st.session_state.id_evento_in_modifica = None
        st.success("Evento aggiornato con successo!")
        st.rerun()
        
    # 2. Tasto ELIMINA EVENTO (Aggiunto come richiesto)
    if col_elimina.button("Elimina Evento", type="secondary", key="delete_event"):
        # Rimuove l'evento dal dizionario
        del st.session_state.eventi[id_corrente]
        
        # Reset dello stato di modifica e ricarica della pagina
        st.session_state.id_evento_in_modifica = None
        st.warning("Evento eliminato definitivamente.")
        st.rerun()
        
    # 3. Tasto Annulla
    if col_annulla.button("Annulla", key="cancel_edit"):
        st.session_state.id_evento_in_modifica = None
        st.rerun()
