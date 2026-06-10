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


def get_commanders_from_moxfield(deck_id: str) -> list[str]:
    """Fetch the commander card name(s) for a Moxfield deck."""
    response = requests.get(
        MOXFIELD_API_URL.format(deck_id=deck_id), headers=HEADERS, timeout=10
    )
    response.raise_for_status()
    data = response.json()

    commander_cards = data.get("boards", {}).get("commanders", {}).get("cards", {})
    return [entry["card"]["name"] for entry in commander_cards.values()]
