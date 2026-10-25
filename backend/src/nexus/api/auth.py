"""Password-based registration and signed bearer-token authentication."""

from datetime import datetime, timedelta, timezone
import logging
from typing import Annotated
from uuid import UUID

import jwt
from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from psycopg.errors import UniqueViolation

from nexus.core.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_AUDIENCE,
    JWT_ISSUER,
    JWT_SECRET_KEY,
)
from nexus.storage import postgres

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])
password_hasher = PasswordHasher(type=Type.ID)
bearer_scheme = HTTPBearer(auto_error=False)


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=12, max_length=256)

    @field_validator("full_name")
    @classmethod
    def trim_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("Full name is required.")
        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class PublicUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    app_id: UUID
    full_name: str
    email: EmailStr


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: PublicUser


def _signing_key() -> str:
    # A 32-byte random secret encodes to 43 URL-safe characters. Reject the
    # short placeholder in .env.example instead of accepting a predictable key.
    if len(JWT_SECRET_KEY) < 43 or JWT_SECRET_KEY.startswith(("REPLACE", "GENERATE")):
        raise RuntimeError("JWT signing key is not configured securely.")
    return JWT_SECRET_KEY


def _issue_token(user: dict) -> tuple[str, int]:
    lifetime = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    now = datetime.now(timezone.utc)
    claims = {
        "sub": str(user["app_id"]),
        "iat": now,
        "exp": now + timedelta(seconds=lifetime),
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
    }
    return jwt.encode(claims, _signing_key(), algorithm="HS256"), lifetime


def _auth_result(user: dict) -> AuthResponse:
    token, lifetime = _issue_token(user)
    return AuthResponse(
        access_token=token,
        expires_in=lifetime,
        user=PublicUser(
            app_id=user["app_id"],
            full_name=user["full_name"],
            email=user["email"],
        ),
    )


def _database_unavailable(exc: Exception) -> HTTPException:
    logger.error("Authentication database unavailable (%s)", type(exc).__name__)
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Authentication is temporarily unavailable. Check server configuration and try again.",
    )


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(payload: RegisterRequest):
    logger.info("Registration requested")
    try:
        _signing_key()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Authentication is not configured securely.") from exc
    try:
        row = postgres.create_user(
            payload.full_name,
            str(payload.email).lower(),
            password_hasher.hash(payload.password),
        )
    except UniqueViolation as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        ) from exc
    except RuntimeError as exc:
        raise _database_unavailable(exc) from exc
    except Exception as exc:
        if getattr(exc, "sqlstate", None) == "23505":
            raise HTTPException(status_code=409, detail="An account with this email already exists.") from exc
        raise _database_unavailable(exc) from exc
    try:
        return _auth_result(row)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Authentication is not configured securely.") from exc


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    logger.info("Sign-in requested")
    try:
        user = postgres.get_user_by_email(str(payload.email).lower())
    except Exception as exc:
        raise _database_unavailable(exc) from exc
    if not user:
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")
    try:
        password_hasher.verify(user["password_hash"], payload.password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")
    if not user.get("is_active"):
        raise HTTPException(status_code=403, detail="This account is inactive.")
    try:
        return _auth_result(user)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Authentication is not configured securely.") from exc


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authentication required.", headers={"WWW-Authenticate": "Bearer"})
    try:
        claims = jwt.decode(
            credentials.credentials,
            _signing_key(),
            algorithms=["HS256"],
            issuer=JWT_ISSUER,
            audience=JWT_AUDIENCE,
            options={"require": ["sub", "iat", "exp", "iss", "aud"]},
        )
        app_id = str(UUID(claims["sub"]))
    except (jwt.PyJWTError, ValueError, RuntimeError, KeyError):
        raise HTTPException(status_code=401, detail="Authentication required.", headers={"WWW-Authenticate": "Bearer"})

    try:
        user = postgres.get_user_by_app_id(app_id)
    except Exception as exc:
        raise _database_unavailable(exc) from exc
    if not user or not user.get("is_active"):
        raise HTTPException(status_code=401, detail="Authentication required.", headers={"WWW-Authenticate": "Bearer"})
    # Always use the PostgreSQL value, never a client-supplied owner identifier.
    user["app_id"] = str(user["app_id"])
    return user


@router.get("/me", response_model=PublicUser)
def read_current_user(user: Annotated[dict, Depends(get_current_user)]):
    return user
