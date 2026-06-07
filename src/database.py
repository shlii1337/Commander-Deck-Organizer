from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Wo soll die Datenbank-Datei liegen? Direkt im Hauptordner.
SQLALCHEMY_DATABASE_URL = "sqlite:///./commander_decks.db"

# Das Engine-Objekt steuert die eigentliche Verbindung zur SQLite-Datei.
# 'check_same_thread': False ist ein SQLite-Spezifikum, das FastAPI benötigt.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Jedes Mal, wenn wir mit der DB sprechen, holen wir uns eine Session aus diesem Sessionmaker:
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Davon werden unsere Modelle (Tabellen) später erben:
Base = declarative_base()


# Ein kleiner Helper (Dependency), den wir später in FastAPI nutzen,
# um DB-Verbindungen sauber zu öffnen und nach dem Request wieder zu schließen.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()