from fastapi import FastAPI, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import models
from .database import engine, get_db

# Hier sagen wir SQLAlchemy: "Guck in models.py und erstelle alle Tabellen in der DB, falls sie noch nicht existieren"
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Commander Deck Organizer")

# Hier binden wir unsere statischen Dateien (CSS/JS) und HTML-Templates an FastAPI an
# Wichtig: Da wir uns im Ordner 'src' befinden, reicht der direkte Pfadname
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# --- ROUTEN ---

# 1. Startseite (Das Dashboard mit der Tabelle)
@app.get("/", response_class=HTMLResponse)
def read_dashboard(request: Request, db: Session = Depends(get_db)):
    # Wir holen alle Decks aus der Datenbank heraus
    raw_decks = db.query(models.Deck).all()
    
    # JETZT NEU: Wir wandeln jedes SQLAlchemy-Objekt in ein normales Python-Dict um
    # '__dict__' wirft die internen SQLAlchemy-Sachen raus und behält nur die echten Daten fields
    decks = []
    for d in raw_decks:
        deck_dict = {key: value for key, value in d.__dict__.items() if not key.startswith('_')}
        decks.append(deck_dict)
    
    # Wir übergeben die sauberen Dictionaries an unser HTML-Template
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "decks": decks}
    )

# 2. Formular-Seite um ein neues Deck hinzuzufügen
@app.get("/add", response_class=HTMLResponse)
def add_deck_form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})


# Route zum Entgegennehmen des Formular-Submissions
@app.post("/add")
def create_deck(
    commander_name: str = Form(...),
    color_identity: str = Form(...),
    image_url: str = Form(...),
    archetype: str = Form(None),
    bracket: str = Form(None),
    powerlevel: int = Form(None),
    status: str = Form(...),
    moxfield_link: str = Form(None),
    db: Session = Depends(get_db)
):
    # Wir erstellen eine neue Instanz unseres Datenbank-Modells
    new_deck = models.Deck(
        commander_name=commander_name,
        color_identity=color_identity,
        image_url=image_url,
        archetype=archetype,
        bracket=bracket,
        powerlevel=powerlevel,
        status=status,
        moxfield_link=moxfield_link
    )
    
    # In die DB schreiben
    db.add(new_deck)
    db.commit()
    db.refresh(new_deck)
    
    # Nach dem Speichern leiten wir den Nutzer direkt zurück zum Dashboard
    return RedirectResponse(url="/", status_code=303)