// Funktionen zum Öffnen und Schließen der Modals
function openAddModal() {
    document.getElementById('add-modal').open = true;
}

function openEditModal(deck) {
    const modal = document.getElementById('edit-modal');

    // Formular-Action dynamisch auf die richtige ID biegen
    document.getElementById('editForm').action = `/edit/${deck.id}`;

    // Felder mit den bestehenden Zeilendaten befüllen
    document.getElementById('edit_moxfield_link').value = deck.moxfield_link || '';
    document.getElementById('edit_commander_name').value = deck.commander_name;
    document.getElementById('edit_color_identity').value = deck.color_identity;
    document.getElementById('edit_image_url').value = deck.image_url;
    document.getElementById('edit_archetype').value = deck.archetype || '';
    document.getElementById('edit_bracket').value = deck.bracket || '2';
    document.getElementById('edit_powerlevel').value = deck.powerlevel || 7;
    document.getElementById('edit_status').value = deck.status;

    // Erkannten Commander & Bild-Vorschau direkt anzeigen
    document.getElementById('edit-detected-commander').innerText = `Commander: ${deck.commander_name}`;
    document.getElementById('edit-search-status').innerText = 'Ändere den Link und klicke auf "Neu scannen", um Commander/Farben/Artwork zu aktualisieren.';
    document.getElementById('edit-card-preview').innerHTML = `<img src="${deck.image_url}" style="width: 200px; border-radius: 12px;">`;

    modal.open = true;
}

function closeModal(modalId) {
    document.getElementById(modalId).open = false;
}

document.addEventListener('DOMContentLoaded', function () {
    console.log("Single-Page Modal Skript geladen! 🃏");

    // Scannt einen Moxfield-Link und befüllt Commander, Farben & Artwork
    function setupMoxfieldScan(linkId, scanBtnId, statusId, detectedId, commanderNameId, colorId, imageId, previewId, submitBtnId) {
        const linkInput = document.getElementById(linkId);
        const scanBtn = document.getElementById(scanBtnId);
        const status = document.getElementById(statusId);
        const detected = document.getElementById(detectedId);
        const commanderInput = document.getElementById(commanderNameId);
        const colorInput = document.getElementById(colorId);
        const imageInput = document.getElementById(imageId);
        const preview = document.getElementById(previewId);
        const submitBtn = document.getElementById(submitBtnId);

        if (!scanBtn) return;

        scanBtn.addEventListener('click', function () {
            const url = linkInput.value.trim();
            if (!url) {
                status.innerText = "Bitte zuerst einen Moxfield-Link einfügen.";
                return;
            }

            status.innerText = "Scanne Deck... ⏳";

            fetch(`/api/scan-moxfield?url=${encodeURIComponent(url)}`)
                .then(res => res.json().then(data => ({ ok: res.ok, data })))
                .then(({ ok, data }) => {
                    if (!ok) {
                        status.innerHTML = `❌ ${data.error || "Unbekannter Fehler beim Scannen."}`;
                        detected.innerText = "";
                        if (submitBtn) submitBtn.disabled = true;
                        return;
                    }

                    status.innerHTML = `✅ Deck erfolgreich gescannt`;
                    detected.innerText = `Commander: ${data.commander_name}`;
                    commanderInput.value = data.commander_name;
                    colorInput.value = data.color_identity;
                    imageInput.value = data.image_url;
                    preview.innerHTML = `<img src="${data.image_url}" style="width: 200px; border-radius: 12px;">`;
                    if (submitBtn) submitBtn.disabled = false;
                })
                .catch(() => {
                    status.innerText = "❌ Fehler beim Scannen. Bitte später erneut versuchen.";
                    if (submitBtn) submitBtn.disabled = true;
                });
        });
    }

    // Moxfield-Scan auf beide Modals anwenden
    setupMoxfieldScan('moxfield_link', 'scanBtn', 'search-status', 'detected-commander', 'commander_name', 'color_identity', 'image_url', 'card-preview', 'submitBtn');
    setupMoxfieldScan('edit_moxfield_link', 'editScanBtn', 'edit-search-status', 'edit-detected-commander', 'edit_commander_name', 'edit_color_identity', 'edit_image_url', 'edit-card-preview', 'editSubmitBtn');
});
