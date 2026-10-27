"""Password-based registration and signed bearer-token authentication."""

from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
import hashlib
import hmac
import logging
import secrets
import smtplib
import ssl
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
    PASSWORD_RESET_OTP_EXPIRE_MINUTES,
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES,
    SMTP_FROM_EMAIL,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USE_TLS,
    SMTP_USERNAME,
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
    confirm_password: str = Field(min_length=12, max_length=256)

    @field_validator("confirm_password")
    @classmethod
    def validate_password_confirmation(cls, value: str, info):
        password = info.data.get("password")
        if password is not None and value != password:
            raise ValueError("Passwords do not match.")
        return value

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


class PasswordResetRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class PasswordResetVerifyRequest(PasswordResetRequest):
    otp: str = Field(pattern=r"^\d{6}$")


class PasswordResetCompleteRequest(PasswordResetRequest):
    reset_token: str = Field(min_length=32, max_length=256)
    new_password: str = Field(min_length=12, max_length=256)
    confirm_password: str = Field(min_length=12, max_length=256)

    @field_validator("confirm_password")
    @classmethod
    def validate_password_confirmation(cls, value: str, info):
        password = info.data.get("new_password")
        if password is not None and value != password:
            raise ValueError("Passwords do not match.")
        return value


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


def _recovery_digest(value: str) -> str:
    return hmac.new(_signing_key().encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()


def _send_password_reset_email(email: str, code: str) -> None:
    if not all((SMTP_HOST, SMTP_FROM_EMAIL)):
        raise RuntimeError("Password recovery email is not configured.")
    message = EmailMessage()
    message["Subject"] = "Your NEXPLY password reset code"
    message["From"] = SMTP_FROM_EMAIL
    message["To"] = email
    message.set_content(
        f"Your NEXPLY password reset code is {code}. It expires in "
        f"{PASSWORD_RESET_OTP_EXPIRE_MINUTES} minutes. If you did not request this, ignore this email."
    )
    context = ssl.create_default_context()
    if SMTP_USE_TLS:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            if SMTP_USERNAME:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(message)
    else:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15, context=context) as server:
            if SMTP_USERNAME:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(message)


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


@router.post("/password-reset/request", status_code=202)
def request_password_reset(payload: PasswordResetRequest):
    """Send an expiring email OTP without confirming whether an account exists."""
    logger.info("Password recovery requested")
    try:
        _signing_key()
        if not all((SMTP_HOST, SMTP_FROM_EMAIL)):
            raise RuntimeError("Password recovery email is not configured.")
        user = postgres.get_user_by_email(str(payload.email).lower())
        if user and user.get("is_active"):
            code = f"{secrets.randbelow(1_000_000):06d}"
            postgres.store_password_reset_code(
                str(user["app_id"]),
                _recovery_digest(code),
                datetime.now(timezone.utc) + timedelta(minutes=PASSWORD_RESET_OTP_EXPIRE_MINUTES),
            )
            try:
                _send_password_reset_email(str(payload.email), code)
            except Exception as exc:
                logger.error("Password recovery email delivery failed (%s)", type(exc).__name__)
                raise HTTPException(status_code=503, detail="Password recovery email could not be sent. Try again later.") from exc
    except RuntimeError as exc:
        logger.error("Password recovery unavailable (%s)", type(exc).__name__)
        raise HTTPException(status_code=503, detail="Password recovery email is not configured. Contact your administrator.") from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise _database_unavailable(exc) from exc
    return {"detail": "If an active account exists for this email, a verification code has been sent."}


@router.post("/password-reset/verify")
def verify_password_reset_code(payload: PasswordResetVerifyRequest):
    logger.info("Password recovery code submitted")
    reset_token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    try:
        verified = postgres.set_reset_token_for_code(
            str(payload.email).lower(),
            _recovery_digest(payload.otp),
            _recovery_digest(reset_token),
            now,
            now + timedelta(minutes=PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
        )
    except Exception as exc:
        raise _database_unavailable(exc) from exc
    if not verified:
        raise HTTPException(status_code=400, detail="The code is invalid or expired. Request a new code and try again.")
    return {"reset_token": reset_token, "expires_in": PASSWORD_RESET_TOKEN_EXPIRE_MINUTES * 60}


@router.post("/password-reset/complete")
def complete_password_reset(payload: PasswordResetCompleteRequest):
    logger.info("Password recovery completion submitted")
    try:
        changed = postgres.replace_password_with_reset_token(
            str(payload.email).lower(),
            _recovery_digest(payload.reset_token),
            password_hasher.hash(payload.new_password),
            datetime.now(timezone.utc),
        )
    except Exception as exc:
        raise _database_unavailable(exc) from exc
    if not changed:
        raise HTTPException(status_code=400, detail="The password reset session is invalid or expired. Request a new code.")
    return {"detail": "Your password has been updated. Sign in with your new password."}
