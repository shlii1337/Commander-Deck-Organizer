from sqlalchemy import Column, Integer, String
from .database import Base


class Deck(Base):
    __tablename__ = "decks"

    # Automatisch hochzählende ID für jedes Deck (Primary Key)
    id = Column(Integer, primary_key=True, index=True)

    # Die Daten, die wir von Scryfall holen werden
    commander_name = Column(String, nullable=False)
    color_identity = Column(
        String, nullable=False
    )  # Speichern wir als String (z.B. "W,U,B")
    image_url = Column(String, nullable=True)

    # Deine manuellen Angaben aus dem Formular
    archetype = Column(String, nullable=True)  # z.B. Aristocrats, Tribal
    bracket = Column(String, nullable=True)  # z.B. "Bracket 2" oder "Precon"
    powerlevel = Column(Integer, nullable=True)  # Skala 1-10
    status = Column(String, nullable=False)  # z.B. "Paper (Finished)", "Idea"
    moxfield_link = Column(String, nullable=True)
    