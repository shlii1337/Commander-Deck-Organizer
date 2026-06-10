import re

import requests

MOXFIELD_API_URL = "https://api2.moxfield.com/v3/decks/all/{deck_id}"

# Moxfield blocks the default `requests` User-Agent, so pretend to be a browser.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

DECK_ID_PATTERN = re.compile(r"moxfield\.com/decks/([A-Za-z0-9_-]+)")


def extract_deck_id(url: str) -> str | None:
    """Extract the deck ID from a Moxfield deck URL."""
    match = DECK_ID_PATTERN.search(url)
    if not match:
        return None
    return match.group(1)


def _normalize_card(card: dict, quantity: int) -> dict:
    """Normalize a Moxfield card object for the power-level scoring engine.

    For double-faced cards Moxfield often leaves the top-level `oracle_text`
    and `type_line` empty/incomplete, with the real per-face data nested in
    `card_faces`. We merge those faces so downstream regex checks see the
    full text.
    """
    oracle_text = card.get("oracle_text") or ""
    type_line = card.get("type_line") or ""
    card_faces = card.get("card_faces") or []

    if not oracle_text and card_faces:
        oracle_text = "\n".join(face.get("oracle_text", "") for face in card_faces)
    if not type_line and card_faces:
        type_line = " // ".join(face.get("type_line", "") for face in card_faces)

    return {
        "name": card.get("name", ""),
        "quantity": quantity,
        "cmc": card.get("cmc") or 0,
        "type_line": type_line,
        "oracle_text": oracle_text,
        "color_identity": card.get("color_identity") or [],
        "set": card.get("set", ""),
        "set_name": card.get("set_name", ""),
    }


def get_decklist_from_moxfield(deck_id: str) -> dict:
    """Fetch a Moxfield deck's commanders and mainboard, normalized for scoring."""
    response = requests.get(
        MOXFIELD_API_URL.format(deck_id=deck_id), headers=HEADERS, timeout=10
    )
    response.raise_for_status()
    data = response.json()

    boards = data.get("boards", {})
    commander_cards = boards.get("commanders", {}).get("cards", {})
    mainboard_cards = boards.get("mainboard", {}).get("cards", {})

    return {
        "commanders": [
            _normalize_card(entry["card"], entry.get("quantity", 1))
            for entry in commander_cards.values()
        ],
        "mainboard": [
            _normalize_card(entry["card"], entry.get("quantity", 1))
            for entry in mainboard_cards.values()
        ],
    }
