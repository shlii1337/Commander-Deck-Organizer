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
    document.getElementById('edit_powerlevel').value = deck.powerlevel ?? 0;
    document.getElementById('edit_powerlevel_display').value = deck.powerlevel ? `${deck.powerlevel} / 10` : '–';
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

    // Baut den Tooltip-Text für die Powerlevel-Berechnung aus der Score-Aufschlüsselung
    function buildPowerlevelTooltip(data) {
        const b = data.breakdown || {};
        const pts = (factor) => (b[factor] && b[factor].points !== undefined) ? b[factor].points : 0;
        return [
            `Score: ${data.score}/100 → Bracket ${data.bracket}`,
            `Game Changer: +${pts('game_changers')}`,
            `Tutoren: +${pts('tutors')}`,
            `Fast Mana: +${pts('fast_mana')}`,
            `Manabasis: +${pts('mana_base')}`,
            `Strategie & Tempo: +${pts('strategy_execution')}`,
            `Synergie/Theme: +${pts('cohesion')}`,
            `Grundgerüst: +${pts('backbone')}`,
        ].join('\n');
    }

    // Scannt einen Moxfield-Link und befüllt Commander, Farben & Artwork
    function setupMoxfieldScan(linkId, scanBtnId, statusId, detectedId, commanderNameId, colorId, imageId, previewId, submitBtnId, bracketId, powerlevelId, archetypeId, powerlevelInfoId) {
        const linkInput = document.getElementById(linkId);
        const scanBtn = document.getElementById(scanBtnId);
        const status = document.getElementById(statusId);
        const detected = document.getElementById(detectedId);
        const commanderInput = document.getElementById(commanderNameId);
        const colorInput = document.getElementById(colorId);
        const imageInput = document.getElementById(imageId);
        const preview = document.getElementById(previewId);
        const submitBtn = document.getElementById(submitBtnId);
        const bracketInput = document.getElementById(bracketId);
        const powerlevelInput = document.getElementById(powerlevelId);
        const powerlevelDisplay = document.getElementById(`${powerlevelId}_display`);
        const archetypeInput = document.getElementById(archetypeId);
        const powerlevelInfo = document.getElementById(powerlevelInfoId);

        if (!scanBtn) return;

        scanBtn.addEventListener('click', function () {
            const url = linkInput.value.trim();
            if (!url) {
                status.innerText = "Bitte zuerst einen Moxfield-Link einfügen.";
                return;
            }

            status.innerText = "Scanne Deck & berechne Powerlevel... ⏳";

            fetch(`/api/scan-moxfield?url=${encodeURIComponent(url)}`)
                .then(res => res.json().then(data => ({ ok: res.ok, data })))
                .then(({ ok, data }) => {
                    if (!ok) {
                        status.innerHTML = `❌ ${data.error || "Unbekannter Fehler beim Scannen."}`;
                        detected.innerText = "";
                        if (submitBtn) submitBtn.disabled = true;
                        return;
                    }

                    detected.innerText = `Commander: ${data.commander_name}`;
                    commanderInput.value = data.commander_name;
                    colorInput.value = data.color_identity;
                    imageInput.value = data.image_url;
                    preview.innerHTML = `<img src="${data.image_url}" style="width: 200px; border-radius: 12px;">`;
                    if (bracketInput && data.bracket) bracketInput.value = data.bracket;
                    if (powerlevelInput && data.powerlevel !== undefined) powerlevelInput.value = data.powerlevel;
                    if (powerlevelDisplay && data.powerlevel !== undefined) powerlevelDisplay.value = `${data.powerlevel} / 10`;
                    if (archetypeInput && data.archetype) archetypeInput.value = data.archetype;
                    if (powerlevelInfo && data.breakdown) powerlevelInfo.setAttribute('data-tooltip', buildPowerlevelTooltip(data));
                    if (submitBtn) submitBtn.disabled = false;

                    status.innerHTML = `✅ Deck gescannt – Powerlevel ${data.powerlevel}/10 (Bracket ${data.bracket})`;
                })
                .catch(() => {
                    status.innerText = "❌ Fehler beim Scannen. Bitte später erneut versuchen.";
                    if (submitBtn) submitBtn.disabled = true;
                });
        });
    }

    // Moxfield-Scan auf beide Modals anwenden
    setupMoxfieldScan('moxfield_link', 'scanBtn', 'search-status', 'detected-commander', 'commander_name', 'color_identity', 'image_url', 'card-preview', 'submitBtn', 'bracket', 'powerlevel', 'archetype', 'powerlevel_info');
    setupMoxfieldScan('edit_moxfield_link', 'editScanBtn', 'edit-search-status', 'edit-detected-commander', 'edit_commander_name', 'edit_color_identity', 'edit_image_url', 'edit-card-preview', 'editSubmitBtn', 'edit_bracket', 'edit_powerlevel', 'edit_archetype', 'edit_powerlevel_info');

    // --- Dashboard: Filter, Sortierung & Suche für die Karten-Ansicht ---
    const deckGrid = document.getElementById('deck-grid');
    if (deckGrid) {
        const cards = Array.from(deckGrid.querySelectorAll('.deck-card'));
        const statusFilters = Array.from(document.querySelectorAll('.status-filter'));
        const colorPips = Array.from(document.querySelectorAll('.color-filter-pip'));
        const searchInput = document.getElementById('deck-search');
        const sortSelect = document.getElementById('deck-sort');
        const noResults = document.getElementById('no-results-message');

        function applyFilters() {
            const activeStatuses = new Set(
                statusFilters.filter(cb => cb.checked).map(cb => cb.value)
            );
            const activeColors = colorPips.filter(p => p.classList.contains('active')).map(p => p.dataset.color);
            const colorFilterActive = activeColors.length > 0 && activeColors.length < colorPips.length;
            const searchTerm = (searchInput?.value || '').trim().toLowerCase();

            let visibleCount = 0;

            cards.forEach(card => {
                const colors = card.dataset.colors === 'C' ? [] : card.dataset.colors.split(',');
                let visible = activeStatuses.has(card.dataset.status);

                if (visible && colorFilterActive) {
                    visible = activeColors.every(color => colors.includes(color));
                }

                if (visible && searchTerm) {
                    visible = card.dataset.name.includes(searchTerm);
                }

                card.style.display = visible ? '' : 'none';
                if (visible) visibleCount++;
            });

            if (noResults) {
                noResults.style.display = visibleCount === 0 ? '' : 'none';
            }
        }

        function applySort() {
            const value = sortSelect ? sortSelect.value : 'name_asc';
            const sorted = [...cards].sort((a, b) => {
                switch (value) {
                    case 'name_desc':
                        return b.dataset.name.localeCompare(a.dataset.name);
                    case 'powerlevel_desc':
                        return parseFloat(b.dataset.powerlevel) - parseFloat(a.dataset.powerlevel);
                    case 'powerlevel_asc':
                        return parseFloat(a.dataset.powerlevel) - parseFloat(b.dataset.powerlevel);
                    case 'bracket_desc':
                        return parseFloat(b.dataset.bracket) - parseFloat(a.dataset.bracket);
                    case 'bracket_asc':
                        return parseFloat(a.dataset.bracket) - parseFloat(b.dataset.bracket);
                    case 'status':
                        return a.dataset.status.localeCompare(b.dataset.status);
                    case 'name_asc':
                    default:
                        return a.dataset.name.localeCompare(b.dataset.name);
                }
            });

            sorted.forEach(card => deckGrid.appendChild(card));
        }

        statusFilters.forEach(cb => cb.addEventListener('change', applyFilters));
        colorPips.forEach(pip => pip.addEventListener('click', () => {
            pip.classList.toggle('active');
            applyFilters();
        }));
        if (searchInput) searchInput.addEventListener('input', applyFilters);
        if (sortSelect) sortSelect.addEventListener('change', applySort);

        applySort();
        applyFilters();
    }
});
