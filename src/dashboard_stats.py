from collections import Counter

from sqlalchemy.orm import Session

from . import models

# Anzeige-Labels für die gespeicherten Status-Werte (DB-Werte bleiben unverändert)
STATUS_LABELS = {
    "Idea": "Idee / Konzept",
    "Digital (Moxfield)": "Digital",
    "In Paper (Proxy)": "Paper (Proxy)",
    "In Paper (Finished)": "Paper (fertig)",
}

# Farbkombinationen (sortiert in WUBRG-Reihenfolge, wie Deck.color_identity gespeichert wird)
COLOR_COMBO_NAMES = {
    "C": "Farblos",
    "W": "Mono-Weiß",
    "U": "Mono-Blau",
    "B": "Mono-Schwarz",
    "R": "Mono-Rot",
    "G": "Mono-Grün",
    "W,U": "Azorius",
    "W,B": "Orzhov",
    "W,R": "Boros",
    "W,G": "Selesnya",
    "U,B": "Dimir",
    "U,R": "Izzet",
    "U,G": "Simic",
    "B,R": "Rakdos",
    "B,G": "Golgari",
    "R,G": "Gruul",
    "W,U,G": "Bant",
    "W,U,B": "Esper",
    "U,B,R": "Grixis",
    "B,R,G": "Jund",
    "W,R,G": "Naya",
    "W,B,G": "Abzan",
    "W,U,R": "Jeskai",
    "U,B,G": "Sultai",
    "W,B,R": "Mardu",
    "U,R,G": "Temur",
    "U,B,R,G": "4-Farben (ohne Weiß)",
    "W,B,R,G": "4-Farben (ohne Blau)",
    "W,U,R,G": "4-Farben (ohne Schwarz)",
    "W,U,B,G": "4-Farben (ohne Rot)",
    "W,U,B,R": "4-Farben (ohne Grün)",
    "W,U,B,R,G": "Fünffarbig",
}

# Standardländer, die bei "meistgenutztes Set" ausgeklammert werden
BASIC_LAND_NAMES = {
    "Plains", "Island", "Swamp", "Mountain", "Forest", "Wastes",
    "Snow-Covered Plains", "Snow-Covered Island", "Snow-Covered Swamp",
    "Snow-Covered Mountain", "Snow-Covered Forest", "Snow-Covered Wastes",
}


def color_combo_name(color_identity: str) -> str:
    return COLOR_COMBO_NAMES.get(color_identity, color_identity)


def compute_dashboard_stats(decks: list[dict], db: Session, user_id: int) -> dict:
    powerlevels = [d["powerlevel"] for d in decks if d.get("powerlevel") is not None]
    avg_powerlevel = round(sum(powerlevels) / len(powerlevels), 2) if powerlevels else None

    color_counter = Counter(d["color_identity"] for d in decks if d.get("color_identity"))
    top_color_combo = None
    if color_counter:
        combo, count = color_counter.most_common(1)[0]
        top_color_combo = {"combo": combo, "name": color_combo_name(combo), "count": count}

    bracket_counter = Counter(
        d["bracket"].replace("Bracket ", "") for d in decks if d.get("bracket")
    )
    top_bracket = None
    if bracket_counter:
        bracket, count = bracket_counter.most_common(1)[0]
        top_bracket = {"bracket": bracket, "count": count}

    top_set = None
    set_rows = (
        db.query(models.DeckCard.set_name)
        .join(models.Deck, models.DeckCard.deck_id == models.Deck.id)
        .filter(models.Deck.user_id == user_id)
        .filter(models.DeckCard.name.notin_(BASIC_LAND_NAMES))
        .filter(models.DeckCard.set_name.isnot(None))
        .filter(models.DeckCard.set_name != "")
        .all()
    )
    set_counter = Counter(row[0] for row in set_rows)
    if set_counter:
        set_name, count = set_counter.most_common(1)[0]
        top_set = {"name": set_name, "count": count}

    return {
        "avg_powerlevel": avg_powerlevel,
        "top_color_combo": top_color_combo,
        "top_bracket": top_bracket,
        "top_set": top_set,
    }
