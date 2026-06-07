// Funktionen zum Öffnen und Schließen der Modals
function openAddModal() {
    document.getElementById('add-modal').open = true;
}

function openEditModal(deck) {
    const modal = document.getElementById('edit-modal');
    
    // Formular-Action dynamisch auf die richtige ID biegen
    document.getElementById('editForm').action = `/edit/${deck.id}`;
    
    // Felder mit den bestehenden Zeilendaten befüllen
    document.getElementById('edit_commander_name').value = deck.commander_name;
    document.getElementById('edit_color_identity').value = deck.color_identity;
    document.getElementById('edit_image_url').value = deck.image_url;
    document.getElementById('edit_archetype').value = deck.archetype || '';
    document.getElementById('edit_bracket').value = deck.bracket || '2';
    document.getElementById('edit_powerlevel').value = deck.powerlevel || 7;
    document.getElementById('edit_status').value = deck.status;
    document.getElementById('edit_moxfield_link').value = deck.moxfield_link || '';
    
    // Bild-Vorschau direkt anzeigen
    document.getElementById('edit-card-preview').innerHTML = `<img src="${deck.image_url}" style="width: 200px; border-radius: 12px;">`;
    
    modal.open = true;
}

function closeModal(modalId) {
    document.getElementById(modalId).open = false;
}

document.addEventListener('DOMContentLoaded', function () {
    console.log("Single-Page Modal Skript geladen! 🃏");

    // Funktion um Scryfall-Suche an ein Input-Feld zu binden
    function setupScryfallSearch(inputId, datalistId, statusId, colorId, imageId, previewId, submitBtnId) {
        let timeout = null;
        const input = document.getElementById(inputId);
        const dataList = document.getElementById(datalistId);
        const status = document.getElementById(statusId);
        const colorInput = document.getElementById(colorId);
        const imageInput = document.getElementById(imageId);
        const preview = document.getElementById(previewId);
        const submitBtn = document.getElementById(submitBtnId);

        if (!input) return;

        input.addEventListener('input', function () {
            clearTimeout(timeout);
            const query = input.value.trim();

            if (query.length < 3) {
                dataList.innerHTML = "";
                return;
            }

            timeout = setTimeout(() => {
                fetch(`https://api.scryfall.com/cards/autocomplete?q=${encodeURIComponent(query)}`)
                    .then(res => res.json())
                    .then(data => {
                        dataList.innerHTML = "";
                        if (data.data) {
                            data.data.forEach(name => {
                                const option = document.createElement('option');
                                option.value = name;
                                dataList.appendChild(option);
                            });
                            if (data.data.includes(query)) {
                                fetchDetails(query);
                            }
                        }
                    });
            }, 300);
        });

        function fetchDetails(cardName) {
            status.innerText = "Lade Details... ⏳";
            fetch(`https://api.scryfall.com/cards/named?exact=${encodeURIComponent(cardName)}`)
                .then(res => { if (!res.ok) throw new Error(); return res.json(); })
                .then(data => {
                    status.innerHTML = `✅ Gefunden: <span style="color: #10b981;">${data.name}</span>`;
                    colorInput.value = data.color_identity.join(',');
                    const imgUrl = data.image_uris ? data.image_uris.normal : data.card_faces[0].image_uris.normal;
                    imageInput.value = imgUrl;
                    preview.innerHTML = `<img src="${imgUrl}" style="width: 200px; border-radius: 12px;">`;
                    if(submitBtn) submitBtn.disabled = false;
                })
                .catch(() => { if(submitBtn) submitBtn.disabled = true; });
        }

        input.addEventListener('change', function() {
            if (input.value.trim().length >= 3) fetchDetails(input.value.trim());
        });
    }

    // Scryfall auf beide Modals anwenden
    setupScryfallSearch('commander_name', 'commander-list', 'search-status', 'color_identity', 'image_url', 'card-preview', 'submitBtn');
    setupScryfallSearch('edit_commander_name', 'edit-commander-list', 'edit-search-status', 'edit_color_identity', 'edit_image_url', 'edit-card-preview', 'editSubmitBtn');
});