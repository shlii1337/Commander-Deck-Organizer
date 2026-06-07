from fastapi import FastAPI, Request, Form, Depends, HTTPException, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

# Die neuen Imports für das User-System:
from . import models, auth
from .database import engine, get_db

# ... (deine App-Initialisierung und das Static-Mounting bleiben gleich)

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


# Route zum Entgegennehmen des Formular-Submissions@app.post("/add")
def add_deck(
    commander_name: str = Form(...),
    color_identity: str = Form(...),
    image_url: str = Form(...),
    archetype: str = Form(None),
    bracket: str = Form(None),
    powerlevel: int = Form(None),
    status: str = Form(...),
    moxfield_link: str = Form(None),
    current_user: models.User = Depends(get_current_user), # User injizieren
    db: Session = Depends(get_db)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    # user_id=current_user.id wird hier beim Erstellen mitgegeben!
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

# Hilfsfunktion: Holt den eingeloggten User anhand des Cookies
def get_current_user(session_token: str = Cookie(None), db: Session = Depends(get_db)):
    if not session_token:
        return None
    username = auth.get_username_from_cookie(session_token)
    if not username:
        return None
    return db.query(models.User).filter(models.User.username == username).first()

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

@app.get("/", response_class=HTMLResponse)
def read_dashboard(request: Request, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Wenn nicht eingeloggt -> ab zum Login!
    if not current_user:
        return RedirectResponse(url="/login")
        
    # JETZT NEU: Wir holen NUR die Decks, die diesem User gehören!
    raw_decks = db.query(models.Deck).filter(models.Deck.user_id == current_user.id).all()
    
    decks = []
    for d in raw_decks:
        deck_dict = {key: value for key, value in d.__dict__.items() if not key.startswith('_')}
        decks.append(deck_dict)
    
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "decks": decks, "user": current_user}
    )

