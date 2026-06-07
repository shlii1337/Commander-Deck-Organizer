from passlib.context import CryptContext
from itsdangerous import Signer

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Ein geheimer Schlüssel, um die Cookies fälschungssicher zu machen
COOKIE_SECRET = "super-geheimes-commander-geheimnis-2026"
signer = Signer(COOKIE_SECRET)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Hilfsfunktionen für das Session-Cookie
def create_session_cookie(username: str) -> str:
    return signer.sign(username.encode()).decode()

def get_username_from_cookie(cookie_value: str) -> str | None:
    try:
        return signer.unsign(cookie_value.encode()).decode()
    except Exception:
        return None