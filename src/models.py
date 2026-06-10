from sqlalchemy import Column, Integer, Float, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # Verknüpfung: Ein User kann viele Decks haben
    decks = relationship("Deck", back_populates="owner")

class Deck(Base):
    __tablename__ = "decks"

    id = Column(Integer, primary_key=True, index=True)
    commander_name = Column(String, index=True)
    color_identity = Column(String)
    image_url = Column(String)
    archetype = Column(String, nullable=True)
    bracket = Column(String, nullable=True)
    powerlevel = Column(Float, nullable=True)
    status = Column(String)
    moxfield_link = Column(String, nullable=True)

    # NEU: Jedes Deck gehört jetzt fest zu einem User
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="decks")

    cards = relationship("DeckCard", back_populates="deck", cascade="all, delete-orphan")


class DeckCard(Base):
    __tablename__ = "deck_cards"

    id = Column(Integer, primary_key=True, index=True)
    deck_id = Column(Integer, ForeignKey("decks.id"), nullable=False)
    name = Column(String, nullable=False)
    set_code = Column(String, nullable=True)
    set_name = Column(String, nullable=True)
    quantity = Column(Integer, default=1)
    is_commander = Column(Boolean, default=False)

    deck = relationship("Deck", back_populates="cards")