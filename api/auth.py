from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import JWT_EXPIRE_MINUTES, JWT_SECRET

JWT_ALGORITHM = "HS256"

# auto_error=False so every failure mode (missing header, malformed, expired,
# bad signature) comes back through the same 401 shape below, instead of
# FastAPI's default HTTPBearer error text.
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        # bcrypt's hard limit — counts UTF-8 bytes, not characters, so a
        # password with accented characters can be <=72 chars but >72 bytes.
        raise ValueError("Password is too long (max 72 bytes)")
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # Oversized password, or a malformed/non-bcrypt hash — treat as
        # "wrong password" instead of letting this 500.
        return False


def create_access_token(*, email: str, hotel_slug: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": email,
        "email": email,
        "hotel_slug": hotel_slug,
        "iat": now,
        "exp": now + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


@dataclass
class CurrentUser:
    email: str
    hotel_slug: str


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated",
                             headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired",
                             headers={"WWW-Authenticate": "Bearer"})
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token",
                             headers={"WWW-Authenticate": "Bearer"})

    email, hotel_slug = payload.get("email"), payload.get("hotel_slug")
    if not email or not hotel_slug:
        raise HTTPException(status_code=401, detail="Invalid token",
                             headers={"WWW-Authenticate": "Bearer"})
    return CurrentUser(email=email, hotel_slug=hotel_slug)
