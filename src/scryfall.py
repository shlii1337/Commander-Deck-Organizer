import requests

SCRYFALL_NAMED_URL = "https://api.scryfall.com/cards/named"

# Scryfall rejects requests with the default `requests` User-Agent.
HEADERS = {"User-Agent": "CommanderDeckOrganizer/1.0", "Accept": "application/json"}


def get_card_info(name: str) -> dict:
    """Fetch a card's color identity and image URL from Scryfall by exact name."""
    response = requests.get(SCRYFALL_NAMED_URL, params={"exact": name}, headers=HEADERS, timeout=10)
    response.raise_for_status()
    data = response.json()

    if "image_uris" in data:
        image_url = data["image_uris"]["normal"]
    else:
        image_url = data["card_faces"][0]["image_uris"]["normal"]

    return {
        "name": data["name"],
        "color_identity": data["color_identity"],
        "image_url": image_url,
    }
