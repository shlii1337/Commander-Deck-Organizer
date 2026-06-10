import os
import secrets

import bcrypt
from itsdangerous import Signer

# Geheimer Schlüssel, um die Cookies fälschungssicher zu machen.
# Per Umgebungsvariable COOKIE_SECRET setzen, damit Sessions Neustarts überdauern.
COOKIE_SECRET = os.environ.get("COOKIE_SECRET") or secrets.token_urlsafe(32)
signer = Signer(COOKIE_SECRET)

def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode("utf-8")[:72]
    return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))

# Hilfsfunktionen für das Session-Cookie
def create_session_cookie(username: str) -> str:
    return signer.sign(username.encode()).decode()

def get_username_from_cookie(cookie_value: str) -> str | None:
    try:
        return signer.unsign(cookie_value.encode()).decode()
    except Exception:
        return None