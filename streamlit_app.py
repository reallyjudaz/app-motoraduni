img_path = str(row.get('Locandina', '')).strip()
if img_path.startswith("http"):
    st.html(f"""
    <!-- Immagine di anteprima nella pagina -->
    <img src="{img_path}" class="locandina-cliccabile" alt="Locandina" onclick="ApriLightbox('{idx}')">
    <div class="testo-aiuto-zoom">🔍 Clicca sulla locandina per aprirla e fare Pinch-Zoom</div>
    
    <!-- Struttura del Lightbox (inizialmente nascosto via CSS) -->
    <div class="lightbox-target" id="lightbox_{idx}" style="display: none;">
        <div class="panzoom-wrapper">
            <img src="{img_path}" id="img_zoom_{idx}" class="zoomable" alt="Zoom Locandina">
        </div>
        <button class="lightbox-close-btn" onclick="ChiudiLightbox('{idx}')">← TORNA ALL'EVENTO</button>
    </div>

    <script>
    // Definiamo una variabile globale per mantenere l'istanza di panzoom di questa locandina
    window.pz_{idx} = null;

    function ApriLightbox(id) {{
        const box = document.getElementById('lightbox_' + id);
        const elem = document.getElementById('img_zoom_' + id);
        
        // 1. Mostriamo il contenitore prima di inizializzare Panzoom
        box.style.display = 'flex';
        setTimeout(() => {{ box.style.opacity = '1'; }}, 10);
        
        // 2. Inizializziamo Panzoom solo ora che l'immagine è visibile a schermo
        if (!window.pz_{id}) {{
            window.pz_{id} = Panzoom(elem, {{
                maxScale: 4,
                minScale: 1,
                contain: 'outside',
                startScale: 1,
                excludeClass: 'lightbox-close-btn'
            }});
            
            // Abilitiamo lo zoom anche con la rotella del mouse (per i test da PC)
            elem.parentElement.addEventListener('wheel', window.pz_{id}.zoomWithWheel);
        }}
    }}

    function ChiudiLightbox(id) {{
        const box = document.getElementById('lightbox_' + id);
        
        // Spegniamo l'effetto opacità
        box.style.opacity = '0';
        
        // resettiamo lo zoom per il prossimo click
        if (window.pz_{id}) {{
            window.pz_{id}.reset();
        }}
        
        // Nascondiamo completamente il blocco dopo l'animazione
        setTimeout(() => {{ box.style.display = 'none'; }}, 200);
    }}
    </script>
    """)
