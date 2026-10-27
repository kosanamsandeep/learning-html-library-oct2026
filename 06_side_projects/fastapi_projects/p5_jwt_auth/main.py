"""
P5 — JWT authentication with OAuth2 password flow.

Demonstrates:
  * Password hashing with passlib + bcrypt (NEVER store plain text).
  * Login endpoint that issues a short-lived JWT.
  * A `Depends(current_user)` dependency that decodes the JWT, loads the user,
    and rejects bad / expired tokens.
  * A simple role check dependency.

WARNING — this is a teaching example. For production:
  * Read JWT_SECRET from settings, never a constant.
  * Use refresh tokens (separate, longer-lived, stored revocably).
  * Lock the bcrypt rounds based on your hardware (passlib does this; tune CPU work).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# -------------------- Config (move to settings in real apps!) --------------------
JWT_SECRET = "change-me-in-prod-this-is-only-a-demo"
JWT_ALG = "HS256"
JWT_TTL_MIN = 30


pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# -------------------- Fake user "database" --------------------
class UserInDB(BaseModel):
    username: str
    full_name: str
    role: str
    hashed_password: str


# Passwords hashed once on import (in real life: from your DB)
USERS: dict[str, UserInDB] = {
    "alice": UserInDB(
        username="alice",
        full_name="Alice Admin",
        role="admin",
        hashed_password=pwd_ctx.hash("alice-pw"),
    ),
    "bob": UserInDB(
        username="bob",
        full_name="Bob User",
        role="user",
        hashed_password=pwd_ctx.hash("bob-pw"),
    ),
}


# -------------------- API models --------------------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    username: str
    full_name: str
    role: str


# -------------------- Helpers --------------------
def authenticate(username: str, password: str) -> UserInDB | None:
    user = USERS.get(username)
    if not user:
        return None
    if not pwd_ctx.verify(password, user.hashed_password):
        return None
    return user


def make_access_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_TTL_MIN),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserInDB:
    creds_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        username: str | None = payload.get("sub")
    except JWTError:
        raise creds_exc
    if not username:
        raise creds_exc
    user = USERS.get(username)
    if not user:
        raise creds_exc
    return user


def require_admin(user: Annotated[UserInDB, Depends(current_user)]) -> UserInDB:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="admin only")
    return user


# -------------------- App + routes --------------------
app = FastAPI(
    title="JWT Auth",
    version="1.0.0",
    description="OAuth2 password flow + JWT + role-based access via dependencies.",
)


@app.post("/auth/login", response_model=Token, tags=["auth"])
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    """Exchange username + password for a short-lived JWT.

    The OAuth2 password flow uses form-encoded fields, not JSON. The Swagger
    "Authorize" button knows how to use this endpoint.
    """
    user = authenticate(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=make_access_token(user.username))


@app.get("/me", response_model=UserOut, tags=["auth"])
def me(user: Annotated[UserInDB, Depends(current_user)]) -> UserOut:
    """Any authenticated user can call this."""
    return UserOut(**user.model_dump(exclude={"hashed_password"}))


@app.get("/admin/secret", tags=["admin"])
def admin_secret(_: Annotated[UserInDB, Depends(require_admin)]) -> dict[str, str]:
    """Only admins. The dependency does the check; the route stays clean."""
    return {"secret": "42 is the answer"}
