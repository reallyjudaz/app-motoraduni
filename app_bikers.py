import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import shutil
from PIL import Image, ImageTk

FILE_EXCEL = "Lista_Eventi_Bikers_Judaz.xlsx"
CARTELLA_LOCANDINE = "locandine"

if not os.path.exists(CARTELLA_LOCANDINE):
    os.makedirs(CARTELLA_LOCANDINE)

percorso_foto_nuovo_evento = ""

LISTA_REGIONI = [
    "Tutta Italia", "Abruzzo", "Basilicata", "Calabria", "Campania", 
    "Emilia-Romagna", "Friuli-Venezia Giulia", "Lazio", "Liguria", 
    "Lombardia", "Marche", "Molise", "Piemonte", "Puglia", 
    "Sardegna", "Sicilia", "Toscana", "Trentino-Alto Adige", 
    "Umbria", "Valle d'Aosta", "Veneto"
]

# Dizionario di auto-aiuto per indovinare la regione dal testo del Luogo
DIZIONARIO_PROVINCE_REGIONI = {
    "lombardia": ["mi", "bg", "bs", "co", "cr", "lc", "lo", "mn", "mb", "pv", "so", "va", "milano", "bergamo", "brescia", "como", "cremona", "lecco", "lodi", "mantova", "monza", "pavia", "sondrio", "varese"],
    "veneto": ["ve", "bl", "pd", "ro", "tv", "vr", "vi", "venezia", "belluno", "padova", "rovigo", "treviso", "verona", "vicenza"],
    "piemonte": ["to", "al", "at", "bi", "cn", "no", "vb", "vc", "torino", "alessandria", "asti", "biella", "cuneo", "novara", "verbania", "vercelli"],
    "emilia-romagna": ["bo", "fe", "fc", "mo", "pr", "pc", "ra", "re", "rn", "bologna", "ferrara", "forlì", "cesena", "modena", "parma", "piacenza", "ravenna", "reggio", "rimini"],
    "toscana": ["fi", "ar", "gr", "li", "lu", "ms", "pi", "po", "pt", "si", "firenze", "arezzo", "grosseto", "livorno", "lucca", "massa", "pisa", "pistoia", "prato", "siena"],
    "lazio": ["rm", "fr", "lt", "ri", "vt", "roma", "frosinone", "latina", "rieti", "viterbo"],
    "campania": ["na", "av", "bn", "ce", "sa", "napoli", "avellino", "benevento", "caserta", "salerno"],
    "puglia": ["ba", "br", "fg", "le", "ta", "bt", "bari", "brindisi", "foggia", "lecce", "taranto", "andria", "barletta", "trani"],
    "sicilia": ["pa", "ag", "cl", "ct", "en", "me", "rg", "sr", "tp", "palermo", "agrigento", "caltanissetta", "catania", "enna", "messina", "ragusa", "siracusa", "trapani"],
    "sardegna": ["ca", "nu", "or", "ss", "su", "cagliari", "nuoro", "oristano", "sassari"],
    "liguria": ["ge", "im", "sp", "sv", "genova", "imperia", "la spezia", "savona"],
    "marche": ["an", "ap", "fm", "mc", "pu", "ancona", "ascoli", "fermo", "macerata", "pesaro", "urbino"],
    "abruzzo": ["aq", "ch", "pe", "te", "l'aquila", "chieti", "pescara", "teramo"],
    "friuli-venezia giulia": ["ts", "go", "pn", "ud", "trieste", "gorizia", "pordenone", "udine"],
    "trentino-alto adige": ["tn", "bz", "trento", "bolzano"],
    "umbria": ["pg", "tr", "perugia", "terni"],
    "calabria": ["cz", "cs", "kr", "rc", "vv", "catanzaro", "cosenza", "crotone", "reggio calabria", "vibo"],
    "basilicata": ["pz", "mt", "potenza", "matera"],
    "molise": ["cb", "is", "campobasso", "isernia"],
    "valle d'aosta": ["ao", "aosta"]
}

def indovina_regione(luogo_testo):
    if pd.isna(luogo_testo):
        return "Non Specificata"
    testo = str(luogo_testo).lower().replace("(", " ").replace(")", " ").replace(",", " ")
    parole = testo.split()
    
    for regione, parole_chiave in DIZIONARIO_PROVINCE_REGIONI.items():
        for p in parole:
            if p.strip() in parole_chiave:
                # Restituisce il nome formattato correttamente prendendolo dalla lista ufficiale
                for r_ufficiale in LISTA_REGIONI:
                    if r_ufficiale.lower() == regione:
                        return r_ufficiale
    return "Non Specificata"

def carica_dati():
    colonne_base = [
        "Data", "Regione", "Nome Evento / Raduno", 
        "Luogo", "Dettagli / Note", "Locandina"
    ]
    if not os.path.exists(FILE_EXCEL):
        df_vuoto = pd.DataFrame(columns=colonne_base)
        df_vuoto.to_excel(FILE_EXCEL, index=False)
        return df_vuoto
        
    df = pd.read_excel(FILE_EXCEL)
    df.columns = df.columns.str.strip()
    
    # Se manca proprio la colonna Regione creala vuota
    if "Regione" not in df.columns:
        df["Regione"] = ""
        
    if "Locandina" not in df.columns:
        df["Locandina"] = ""

    # SISTEMA DI AUTO-RIPARAZIONE DELLE REGIONI VUOTE o "Non Specificata"
    modificato = False
    for idx, riga in df.iterrows():
        valore_regione = str(riga["Regione"]).strip()
        if valore_regione == "" or valore_regione.lower() == "nan" or valore_regione.lower() == "non specificata":
            regione_indovinata = indovina_regione(riga["Luogo"])
            if regione_indovinata != "Non Specificata":
                df.at[idx, "Regione"] = region_test = regione_indovinata
                modificato = True
            else:
                df.at[idx, "Regione"] = "Non Specificata"

    # Se l'app ha corretto delle regioni vecchie, salva subito sul file Excel fisso
    if modificato:
        try:
            df.to_excel(FILE_EXCEL, index=False)
        except Exception:
            pass # Se il file è temporaneamente aperto da Excel non bloccare l'app
            
    return df

def aggiorna_tabella(df_da_mostrare):
    for i in tabella.get_children():
        tabella.delete(i)
    for index, riga in df_da_mostrare.iterrows():
        reg = riga["Regione"] if pd.notna(riga["Regione"]) else "Non Specificata"
        not_h = riga["Dettagli / Note"] if pd.notna(riga["Dettagli / Note"]) else ""
        loc_h = riga["Locandina"] if pd.notna(riga["Locandina"]) else ""
        valori_riga = (
            riga["Data"], reg, riga["Nome Evento / Raduno"], 
            riga["Luogo"], not_h, loc_h
        )
        tabella.insert("", "end", values=valori_riga)

def filtra_per_regione(event=None):
    regione_scelta = combo_regione.get()
    entry_ricerca.delete(0, tk.END)
    
    df_completo = carica_dati()
    if df_completo.empty:
        return

    if regione_scelta != "Tutta Italia":
        scelta_pulita = regione_scelta.lower().replace("-", " ").strip()
        col_reg_pulita = df_completo["Regione"].astype(str).str.lower().str.replace("-", " ").str.strip()
        df_filtrato = df_completo[col_reg_pulita == scelta_pulita]
    else:
        df_filtrato = df_completo

    aggiorna_tabella(df_filtrato)

def cerca_testo_libero(event=None):
    testo = entry_ricerca.get().lower()
    if combo_regione.get() != "Tutta Italia":
        combo_regione.set("Tutta Italia")
    
    df_completo = carica_dati()
    if df_completo.empty:
        return

    if testo:
        cond_nome = df_completo["Nome Evento / Raduno"].astype(str).str.lower().str.contains(testo)
        cond_luogo = df_completo["Luogo"].astype(str).str.lower().str.contains(testo)
        cond_data = df_completo["Data"].astype(str).str.lower().str.contains(testo)
        df_filtrato = df_completo[cond_nome | cond_luogo | cond_data]
    else:
        df_filtrato = df_completo
        
    aggiorna_tabella(df_filtrato)

def apri_excel():
    if os.path.exists(FILE_EXCEL):
        os.startfile(FILE_EXCEL)
    else:
        messagebox.showerror("Errore", "File Excel non trovato!")

def seleziona_locandina_form():
    global percorso_foto_nuovo_evento
    file_scelto = filedialog.askopenfilename(
        title="Seleziona la Locandina",
        filetypes=[("Immagini", "*.jpg *.jpeg *.png *.bmp *.webp")]
    )
    if file_scelto:
        percorso_foto_nuovo_evento = file_scelto
        nome_f = os.path.basename(file_scelto)
        lbl_stato_foto_form.config(text=f"✔️ {nome_f}", fg="#2ecc71")

def aggiungi_nuovo_evento():
    global percorso_foto_nuovo_evento
    data = entry_data.get().strip()
    regione = combo_regione_form.get()
    nome = entry_nome.get().strip()
    luogo = entry_luogo.get().strip()
    note = entry_note.get().strip()

    if not data or not nome or not luogo:
        messagebox.showwarning("Attenzione", "Campi obbligatori mancanti!")
        return

    percorso_salvato_foto = ""
    if percorso_foto_nuovo_evento and os.path.exists(percorso_foto_nuovo_evento):
        estensione = os.path.splitext(percorso_foto_nuovo_evento)[1]
        nome_pulito = nome.lower().replace(" ", "_").replace('"', "").replace("'", "")[:20]
        percorso_salvato_foto = os.path.join(CARTELLA_LOCANDINE, f"{nome_pulito}{estensione}")
        try:
            shutil.copy(percorso_foto_nuovo_evento, percorso_salvato_foto)
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile copiare la foto: {e}")
            return

    df_attuale = carica_dati()
    nuovo_evento = pd.DataFrame([{
        "Data": data,
        "Regione": regione,
        "Nome Evento / Raduno": nome,
        "Luogo": luogo,
        "Dettagli / Note": note,
        "Locandina": percorso_salvato_foto
    }])
    df_aggiornato = pd.concat([df_attuale, nuovo_evento], ignore_index=True)

    try:
        df_aggiornato.to_excel(FILE_EXCEL, index=False)
        entry_data.delete(0, tk.END)
        entry_nome.delete(0, tk.END)
        entry_luogo.delete(0, tk.END)
        entry_note.delete(0, tk.END)
        percorso_foto_nuovo_evento = ""
        lbl_stato_foto_form.config(text="Nessuna immagine", fg="white")
        combo_regione.set("Tutta Italia")
        entry_ricerca.delete(0, tk.END)
        aggiorna_tabella(df_aggiornato)
        messagebox.showinfo("Successo", "Raduno salvato nel database Excel!")
    except Exception as e:
        messagebox.showerror("Errore", f"Impossibile salvare: {e}")

def associa_foto_a_evento(nome_evento, frame_foto, finestra_pop):
    file_scelto = filedialog.askopenfilename(
        title="Seleziona la Locandina",
        filetypes=[("Immagini", "*.jpg *.jpeg *.png *.bmp *.webp")]
    )
    if not file_scelto:
        return
    estensione = os.path.splitext(file_scelto)[1]
    nome_pulito = nome_evento.lower().replace(" ", "_").replace('"', "").replace("'", "")[:20]
    nuovo_percorso_foto = os.path.join(CARTELLA_LOCANDINE, f"{nome_pulito}{estensione}")
    try:
        shutil.copy(file_scelto, nuevo_percorso_foto)
        df = carica_dati()
        col_nome_ev = df["Nome Evento / Raduno"]
        df.loc[col_nome_ev == nome_evento, "Locandina"] = nuovo_percorso_foto
        df.to_excel(FILE_EXCEL, index=False)
        
        combo_regione.set("Tutta Italia")
        entry_ricerca.delete(0, tk.END)
        aggiorna_tabella(df)

        for child in frame_foto.winfo_children():
            child.destroy()
        img = Image.open(nuovo_percorso_foto)
        img = img.resize((300, 400), Image.Resampling.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)
        lbl_img = tk.Label(frame_foto, image=img_tk, bg="#2c3e50")
        lbl_img.image = img_tk
        lbl_img.pack(expand=True)
        messagebox.showinfo("Successo", "Locandina aggiornata!")
    except Exception as e:
        messagebox.showerror("Errore", f"Errore nel salvataggio: {e}")

def mostra_dettagli_completi(event):
    item_selezionato = tabella.selection()
    if not item_selezionato:
        return
    valori = tabella.item(item_selezionato, "values")
    data, regione, nome, luogo, note = valori[0], valori[1], valori[2], valori[3], valori[4]
    locandina_path = valori[5] if len(valori) > 5 else ""

    finestra_dettagli = tk.Toplevel(root)
    finestra_dettagli.title(f"Gestione: {nome}")
    finestra_dettagli.geometry("850x520")
    finestra_dettagli.configure(bg="#34495e")

    frame_testi = tk.Frame(finestra_dettagli, bg="#34495e")
    frame_testi.pack(side="left", fill="both", expand=True, padx=20, pady=10)

    tk.Label(frame_testi, text=nome, font=("Arial", 13, "bold"), fg="#e67e22", bg="#34495e", wraplength=350, justify="left").pack(anchor="w", pady=10)
    tk.Label(frame_testi, text=f"📅 Data: {data}", font=("Arial", 10, "bold"), fg="white", bg="#34495e").pack(anchor="w", pady=3)
    tk.Label(frame_testi, text=f"🗺️ Regione: {regione}", font=("Arial", 10, "bold"), fg="white", bg="#34495e").pack(anchor="w", pady=3)
    tk.Label(frame_testi, text=f"📍 Luogo: {luogo}", font=("Arial", 10, "bold"), fg="white", bg="#34495e").pack(anchor="w", pady=3)
    
    tk.Label(frame_testi, text="📝 Note e Programma Completo:", font=("Arial", 10, "underline"), fg="white", bg="#34495e").pack(anchor="w", pady=10)
    testo_note = tk.Text(frame_testi, font=("Arial", 10), wrap="word", bg="#2c3e50", fg="white", bd=0, padx=10, pady=10)
    testo_note.insert("1.0", note)
    testo_note.configure(state="disabled")
    testo_note.pack(fill="both", expand=True, pady=10)

    frame_foto_container = tk.Frame(finestra_dettagli, bg="#34495e")
    frame_foto_container.pack(side="right", fill="both", padx=20, pady=10)

    btn_carica_foto = tk.Button(
        frame_foto_container, text="🖼️ Aggiungi / Cambia Locandina", 
        command=lambda: associa_foto_a_evento(nome, frame_visualizza_foto, finestra_dettagli),
        font=("Arial", 9, "bold"), bg="#3498db", fg="white", activebackground="#2980b9"
    )
    btn_carica_foto.pack(fill="x", pady=5)

    frame_visualizza_foto = tk.Frame(frame_foto_container, bg="#2c3e50", width=320, height=420)
    frame_visualizza_foto.pack(fill="both", expand=True, pady=5)
    frame_visualizza_foto.pack_propagate(False)

    loc_str = str(locandina_path)
    if locandina_path and os.path.exists(loc_str) and loc_str != "nan":
        try:
            img = Image.open(locandina_path)
            img = img.resize((300, 400), Image.Resampling.LANCZOS)
            img_tk = ImageTk.PhotoImage(img)
            lbl_immagine = tk.Label(frame_visualizza_foto, image=img_tk, bg="#2c3e50")
            lbl_immagine.image = img_tk
            lbl_immagine.pack(expand=True)
        except Exception:
            tk.Label(frame_visualizza_foto, text="Errore foto", fg="red", bg="#2c3e50").pack(expand=True)
    else:
        tk.Label(frame_visualizza_foto, text="Nessuna Locandina", font=("Arial", 11, "italic"), fg="grey", bg="#2c3e50").pack(expand=True)

# --- INTERFACCIA ---
root = tk.Tk()
root.title("Judaz Biker Agenda v4.6")
root.geometry("1000x720")
root.configure(bg="#2c3e50")

frame_top = tk.Frame(root, bg="#2c3e50")
frame_top.pack(fill="x", padx=15, pady=12)

lbl_cerca = tk.Label(frame_top, text="🔍 Cerca Raduno:", font=("Arial", 10, "bold"), fg="white", bg="#2c3e50")
lbl_cerca.pack(side="left", padx=5)
entry_ricerca = tk.Entry(frame_top, font=("Arial", 11), width=22)
entry_ricerca.pack(side="left", padx=5)
entry_ricerca.bind("<KeyRelease>", cerca_testo_libero)

lbl_reg = tk.Label(frame_top, text="🗺️ Filtra Regione:", font=("Arial", 10, "bold"), fg="white", bg="#2c3e50")
lbl_reg.pack(side="left", padx=15)
combo_regione = ttk.Combobox(frame_top, values=LISTA_REGIONI, font=("Arial", 10), state="readonly", width=18)
combo_regione.set("Tutta Italia")
combo_regione.pack(side="left", padx=5)
combo_regione.bind("<<ComboboxSelected>>", filtra_per_regione)

btn_apri = tk.Button(frame_top, text="📂 Apri Excel", command=apri_excel, font=("Arial", 10, "bold"), bg="#e67e22", fg="white")
btn_apri.pack(side="right", padx=5)

frame_tab = tk.Frame(root)
frame_tab.pack(fill="both", expand=True, padx=15, pady=5)

colonne = ("Data", "Regione", "Nome Evento", "Luogo", "Note_Hidden", "Locandina_Hidden")
tabella = ttk.Treeview(frame_tab, columns=colonne, show="headings")
tabella.heading("Data", text="DATA")
tabella.heading("Regione", text="REGIONE")
tabella.heading("Nome Evento", text="NOME EVENTO / RADUNO")
tabella.heading("Luogo", text="LUOGO")
tabella.column("Data", width=150, anchor="center")
tabella.column("Regione", width=150, anchor="center")
tabella.column("Nome Evento", width=350, anchor="w")
tabella.column("Luogo", width=250, anchor="w")
tabella.column("Note_Hidden", width=0, stretch=tk.NO)
tabella.column("Locandina_Hidden", width=0, stretch=tk.NO)
tabella.bind("<Double-1>", mostra_dettagli_completi)

scrollbar = ttk.Scrollbar(frame_tab, orient="vertical", command=tabella.yview)
tabella.configure(yscrollcommand=scrollbar.set)
tabella.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

frame_form = tk.LabelFrame(root, text="➕ Aggiungi Nuovo Raduno", font=("Arial", 11, "bold"), fg="white", bg="#34495e", padx=15, pady=10)
frame_form.pack(fill="x", padx=15, pady=15)

lbl_data = tk.Label(frame_form, text="Data:", fg="white", bg="#34495e", font=("Arial", 10))
lbl_data.grid(row=0, column=0, sticky="w", padx=5, pady=5)
entry_data = tk.Entry(frame_form, font=("Arial", 10), width=25)
entry_data.grid(row=0, column=1, padx=5, pady=5)

lbl_nome = tk.Label(frame_form, text="Nome Evento / Raduno:", fg="white", bg="#34495e", font=("Arial", 10))
lbl_nome.grid(row=0, column=2, sticky="w", padx=5, pady=5)
entry_nome = tk.Entry(frame_form, font=("Arial", 10), width=35)
entry_nome.grid(row=0, column=3, padx=5, pady=5)

lbl_luogo = tk.Label(frame_form, text="Luogo (Città e Prov):", fg="white", bg="#34495e", font=("Arial", 10))
lbl_luogo.grid(row=1, column=0, sticky="w", padx=5, pady=5)
entry_luogo = tk.Entry(frame_form, font=("Arial", 10), width=25)
entry_luogo.grid(row=1, column=1, padx=5, pady=5)

lbl_reg_form = tk.Label(frame_form, text="Seleziona Regione:", fg="white", bg="#34495e", font=("Arial", 10))
lbl_reg_form.grid(row=1, column=2, sticky="w", padx=5, pady=5)
combo_regione_form = ttk.Combobox(frame_form, values=LISTA_REGIONI[1:], font=("Arial", 10), state="readonly", width=32)
combo_regione_form.set("Veneto")
combo_regione_form.grid(row=1, column=3, padx=5, pady=5)

lbl_note = tk.Label(frame_form, text="Dettagli / Note:", fg="white", bg="#34495e", font=("Arial", 10))
lbl_note.grid(row=2, column=0, sticky="w", padx=5, pady=5)
entry_note = tk.Entry(frame_form, font=("Arial", 10), width=80)
entry_note.grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky="w")

btn_carica_foto_form = tk.Button(frame_form, text="🖼️ Allega Locandina Subito", command=seleziona_locandina_form, font=("Arial", 9, "bold"), bg="#9b59b6", fg="white")
btn_carica_foto_form.grid(row=3, column=0, pady=5, sticky="w", padx=5)

lbl_stato_foto_form = tk.Label(frame_form, text="Nessuna immagine", fg="white", bg="#34495e", font=("Arial", 9, "italic"))
lbl_stato_foto_form.grid(row=3, column=1, columnspan=3, pady=5, sticky="w", padx=5)

btn_salva = tk.Button(frame_form, text="➕ Salva Raduno Completo", command=aggiungi_nuovo_evento, font=("Arial", 11, "bold"), bg="#2ecc71", fg="white", activebackground="#27ae60", padx=15)
btn_salva.grid(row=4, column=0, columnspan=4, pady=8)

df_iniziale = carica_dati()
if not df_iniziale.empty:
    aggiorna_tabella(df_iniziale)

root.mainloop()