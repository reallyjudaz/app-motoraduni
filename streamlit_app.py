import streamlit as st

# --- 1. INIZIALIZZAZIONE DATI ---
# (Se usi un database come Firebase o SQLite, sostituisci questo dizionario con le tue funzioni di lettura)
if 'eventi' not in st.session_state:
    st.session_state.eventi = {
        "id_1": {"titolo": "Riunione di Marketing", "data": "2026-06-15", "descrizione": "Discussione budget Q3"},
        "id_2": {"titolo": "Lancio Nuovo Prodotto", "data": "2026-07-01", "descrizione": "Presentazione Iron & Rubber"}
    }

# Stato per tracciare quale evento è selezionato per la modifica (None = nessuno)
if 'id_evento_in_modifica' not in st.session_state:
    st.session_state.id_evento_in_modifica = None


st.title("📅 Gestione Eventi")

# --- 2. MOSTRA LA LISTA DEGLI EVENTI ---
st.subheader("I tuoi Eventi")

# Usiamo list(...) per evitare errori nel ciclo se eliminiamo un elemento
for ev_id, ev_data in list(st.session_state.eventi.items()):
    col1, col2 = st.columns([4, 1])
    
    # Mostra titolo e data attuali
    col1.write(f"**{ev_data['titolo']}** — {ev_data['data']}")
    
    # Pulsante per aprire il pannello di modifica
    if col2.button("Modifica", key=f"btn_attiva_{ev_id}"):
        st.session_state.id_evento_in_modifica = ev_id
        st.rerun()


# --- 3. PANNELLO DI MODIFICA ED ELIMINAZIONE (Compare solo se un evento è selezionato) ---
if st.session_state.id_evento_in_modifica is not None:
    st.divider()
    id_corrente = st.session_state.id_evento_in_modifica
    
    # Controllo di sicurezza nel caso l'evento sia stato rimosso
    if id_corrente in st.session_state.eventi:
        evento_corrente = st.session_state.eventi[id_corrente]
        
        st.subheader(f"🛠️ Pannello di Modifica: {evento_corrente['titolo']}")
        
        # Utilizziamo st.form per bloccare il refresh continuo mentre l'utente scrive
        with st.form(key="form_modifica_evento"):
            
            # INPUT 1: Modifica del TITOLO (Modificabile come richiesto)
            nuovo_titolo = st.text_input("Titolo dell'evento", value=evento_corrente["titolo"])
            
            # Altri campi
            nuova_data = st.text_input("Data dell'evento", value=evento_corrente["data"])
            nuova_descrizione = st.text_area("Descrizione", value=evento_corrente["descrizione"])
            
            # Pulsanti di invio del Form (Salva / Annulla)
            col_salva, col_annulla = st.columns([1, 1])
            with col_salva:
                submit_salva = st.form_submit_button("Salva Modifiche", type="primary")
            with col_annulla:
                submit_annulla = st.form_submit_button("Annulla")
        
        # TASTO ELIMINA (Richiesto): Posizionato subito sotto il form per sicurezza,
        # separato dalle azioni di salvataggio per evitare click involontari.
        st.write("---")
        col_canc, _ = st.columns([1, 2])
        with col_canc:
            if st.button("🗑️ Elimina Evento", type="secondary", key="btn_elimina_definitivo"):
                # Rimuove l'evento dal dizionario (o esegui qui la query DELETE sul tuo DB)
                del st.session_state.eventi[id_corrente]
                
                # Reset dello stato e rinfresco pagina
                st.session_state.id_evento_in_modifica = None
                st.toast("Evento eliminato definitivamente!", icon="🗑️")
                st.rerun()

        # --- GESTIONE DELLE AZIONI DEL FORM ---
        if submit_salva:
            # Sovrascrive i dati nel session_state (o esegui qui la query UPDATE sul tuo DB)
            st.session_state.eventi[id_corrente]["titolo"] = nuovo_titolo
            st.session_state.eventi[id_corrente]["data"] = nuova_data
            st.session_state.eventi[id_corrente]["descrizione"] = nuova_descrizione
            
            # Chiude il pannello di modifica e aggiorna la schermata
            st.session_state.id_evento_in_modifica = None
            st.toast("Evento aggiornato con successo!", icon="✅")
            st.rerun()
            
        if submit_annulla:
            # Chiude semplicemente il pannello senza salvare nulla
            st.session_state.id_evento_in_modifica = None
            st.rerun()
            
    else:
        # Se l'evento corrente non esiste più nella lista, resetta lo stato di modifica
        st.session_state.id_evento_in_modifica = None
        st.rerun()
