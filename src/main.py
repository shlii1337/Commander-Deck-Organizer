import requests
from fastapi import FastAPI, Request, Form, Depends, HTTPException, Cookie
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import models, auth, moxfield, scryfall, powerlevel
from .database import engine, get_db

# Reihenfolge der Farben für die Anzeige (WUBRG)
COLOR_ORDER = ["W", "U", "B", "R", "G"]


# Hilfsfunktion: Holt den eingeloggten User anhand des Cookies
def get_current_user(session_token: str = Cookie(None), db: Session = Depends(get_db)):
    if not session_token:
        return None
    username = auth.get_username_from_cookie(session_token)
    if not username:
        return None
    return db.query(models.User).filter(models.User.username == username).first()


# Hier sagen wir SQLAlchemy: "Guck in models.py und erstelle alle Tabellen in der DB, falls sie noch nicht existieren"
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Commander Deck Organizer")

# Hier binden wir unsere statischen Dateien (CSS/JS) und HTML-Templates an FastAPI an
# Wichtig: Da wir uns im Ordner 'src' befinden, reicht der direkte Pfadname
app.mount("/static", StaticFiles(directory="src/static"), name="static")
templates = Jinja2Templates(directory="src/templates")


# --- ROUTEN ---

# 1. Startseite (Das Dashboard mit der Tabelle)
@app.get("/", response_class=HTMLResponse)
def read_dashboard(request: Request, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Wenn nicht eingeloggt -> ab zum Login!
    if not current_user:
        return RedirectResponse(url="/login")

    # Wir holen NUR die Decks, die diesem User gehören!
    raw_decks = db.query(models.Deck).filter(models.Deck.user_id == current_user.id).all()

    decks = []
    for d in raw_decks:
        deck_dict = {key: value for key, value in d.__dict__.items() if not key.startswith('_')}
        decks.append(deck_dict)

    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "decks": decks, "user": current_user}
    )


# 2. Formular-Submission zum Hinzufügen eines neuen Decks
@app.post("/add")
def add_deck(
    commander_name: str = Form(...),
    color_identity: str = Form(...),
    image_url: str = Form(...),
    archetype: str = Form(None),
    bracket: str = Form(None),
    powerlevel: int = Form(None),
    status: str = Form(...),
    moxfield_link: str = Form(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    new_deck = models.Deck(
        commander_name=commander_name,
        color_identity=color_identity,
        image_url=image_url,
        archetype=archetype,
        bracket=bracket,
        powerlevel=powerlevel,
        status=status,
        moxfield_link=moxfield_link,
        user_id=current_user.id
    )
    db.add(new_deck)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


# 3. Bestehendes Deck bearbeiten
@app.post("/edit/{deck_id}")
def edit_deck(
    deck_id: int,
    commander_name: str = Form(...),
    color_identity: str = Form(...),
    image_url: str = Form(...),
    archetype: str = Form(None),
    bracket: str = Form(None),
    powerlevel: int = Form(None),
    status: str = Form(...),
    moxfield_link: str = Form(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    deck = db.query(models.Deck).filter(models.Deck.id == deck_id).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck nicht gefunden.")
    if deck.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Kein Zugriff auf dieses Deck.")

    deck.commander_name = commander_name
    deck.color_identity = color_identity
    deck.image_url = image_url
    deck.archetype = archetype
    deck.bracket = bracket
    deck.powerlevel = powerlevel
    deck.status = status
    deck.moxfield_link = moxfield_link
    db.commit()
    return RedirectResponse(url="/", status_code=303)


# 4. Deck löschen
@app.post("/delete/{deck_id}")
def delete_deck(
    deck_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    deck = db.query(models.Deck).filter(models.Deck.id == deck_id).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck nicht gefunden.")
    if deck.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Kein Zugriff auf dieses Deck.")

    db.delete(deck)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


# 5. Moxfield-Link scannen: Commander, Farben & Artwork ermitteln
@app.get("/api/scan-moxfield")
def scan_moxfield(url: str, current_user: models.User = Depends(get_current_user)):
    if not current_user:
        return JSONResponse(status_code=401, content={"error": "Nicht eingeloggt."})

    deck_id = moxfield.extract_deck_id(url)
    if not deck_id:
        return JSONResponse(status_code=400, content={"error": "Ungültiger Moxfield-Link."})

    try:
        decklist = moxfield.get_decklist_from_moxfield(deck_id)
    except requests.exceptions.HTTPError:
        return JSONResponse(status_code=404, content={"error": "Deck nicht gefunden oder privat."})
    except requests.exceptions.RequestException:
        return JSONResponse(status_code=502, content={"error": "Moxfield ist gerade nicht erreichbar."})

    commanders = decklist["commanders"]
    if not commanders:
        return JSONResponse(status_code=400, content={"error": "Kein Commander in diesem Deck gefunden."})

    commander_names = [card["name"] for card in commanders]

    color_identity = set()
    image_url = None
    try:
        for index, name in enumerate(commander_names):
            card = scryfall.get_card_info(name)
            color_identity.update(card["color_identity"])
            if index == 0:
                image_url = card["image_url"]
    except requests.exceptions.RequestException:
        return JSONResponse(status_code=502, content={"error": "Scryfall-Daten konnten nicht geladen werden."})

    sorted_colors = [color for color in COLOR_ORDER if color in color_identity]
    color_identity_str = ",".join(sorted_colors) if sorted_colors else "C"

    power = powerlevel.calculate_power_level(commanders, decklist["mainboard"], sorted_colors)

    return {
        "commander_name": " // ".join(commander_names),
        "color_identity": color_identity_str,
        "image_url": image_url,
        "bracket": str(power["bracket"]),
        "powerlevel": power["powerlevel"],
        "archetype": power["archetype"] or "",
    }


# --- AUTH-ROUTEN ---

# 1. Login-Seite anzeigen
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# 2. Registrierung verarbeiten
@app.post("/register")
def register_user(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    # Prüfen, ob der Name schon vergeben ist
    existing_user = db.query(models.User).filter(models.User.username == username).first()
    if existing_user:
        return templates.TemplateResponse("login.html", {"request": {}, "error": "Benutzername bereits vergeben!"})

    # Neuen User anlegen (Passwort hashen!)
    hashed_pw = auth.hash_password(password)
    new_user = models.User(username=username, hashed_password=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Direkt einloggen nach Registrierung via Cookie
    response = RedirectResponse(url="/", status_code=303)
    token = auth.create_session_cookie(username)
    response.set_cookie(key="session_token", value=token, httponly=True)
    return response


# 3. Login verarbeiten
@app.post("/login")
def login_user(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()

    # Passwort überprüfen
    if not user or not auth.verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {"request": {}, "error": "Ungültiger Name oder Passwort!"})

    # Cookie setzen und aufs Dashboard leiten
    response = RedirectResponse(url="/", status_code=303)
    token = auth.create_session_cookie(username)
    response.set_cookie(key="session_token", value=token, httponly=True)
    return response


# 4. Logout (Cookie löschen)
@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("session_token")
    return response
