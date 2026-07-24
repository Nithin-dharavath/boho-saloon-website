import secrets
import hashlib
import logging
import asyncio
from datetime import datetime, timedelta

from fastapi import APIRouter, Request, Response, HTTPException
from jose import jwt

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from app.config import (
    SECRET_KEY,
    OTP_EXPIRY_MINUTES,
    OTP_MAX_ATTEMPTS,
    JWT_EXPIRY_HOURS,
    OTP_RATE_LIMIT_SECONDS,
    GOOGLE_CLIENT_ID,
)
from app.database import get_db
from app.email_utils import send_otp_email
from app.models import OTPRequest, OTPVerify, ProfileSetup

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


def create_jwt(user_id: int, email: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": datetime.utcnow(),
        "type": "access",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def decode_jwt(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "access":
            return None
        return payload
    except Exception:
        return None


def get_current_user(request: Request):
    token = request.cookies.get("session")
    if not token:
        return None
    payload = decode_jwt(token)
    if not payload:
        return None
    return {"id": int(payload["sub"]), "email": payload["email"]}


@router.post("/request-otp")
async def request_otp(body: OTPRequest):
    email = body.email

    db = get_db()

    db.execute("DELETE FROM otp_codes WHERE expires_at <= ?", (datetime.utcnow(),))
    db.commit()

    recent_otp = db.execute(
        """SELECT COUNT(*) as cnt FROM otp_codes
           WHERE email = ? AND created_at > ?""",
        (email, datetime.utcnow() - timedelta(seconds=OTP_RATE_LIMIT_SECONDS)),
    ).fetchone()

    if recent_otp and recent_otp["cnt"] >= 1:
        db.close()
        return {"ok": False, "error": "Please wait before requesting another code."}

    code = f"{secrets.randbelow(900000) + 100000:06d}"
    code_hash = hashlib.sha256(code.encode()).hexdigest()

    db.execute(
        "INSERT INTO otp_codes (email, code, expires_at) VALUES (?, ?, ?)",
        (email, code_hash, datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)),
    )
    db.commit()
    db.close()

    try:
        await asyncio.to_thread(send_otp_email, email, code)
    except Exception:
        return {"ok": False, "error": "Could not send email. Please try again later."}

    return {"ok": True, "message": "Code sent to your email."}


@router.post("/verify-otp")
async def verify_otp(body: OTPVerify, response: Response):
    email = body.email
    code = body.code

    db = get_db()

    otp = db.execute(
        """SELECT id, code, attempts FROM otp_codes
           WHERE email = ? AND used = 0 AND expires_at > ?
           ORDER BY created_at DESC LIMIT 1""",
        (email, datetime.utcnow()),
    ).fetchone()

    if not otp:
        db.close()
        return {"ok": False, "error": "No valid code found. Request a new one."}

    if otp["attempts"] >= OTP_MAX_ATTEMPTS:
        db.execute("UPDATE otp_codes SET used = 1 WHERE id = ?", (otp["id"],))
        db.commit()
        db.close()
        return {"ok": False, "error": "Too many incorrect attempts. Request a new code."}

    code_hash = hashlib.sha256(code.encode()).hexdigest()
    if code_hash != otp["code"]:
        db.execute("UPDATE otp_codes SET attempts = attempts + 1 WHERE id = ?", (otp["id"],))
        db.commit()
        remaining = OTP_MAX_ATTEMPTS - otp["attempts"] - 1
        db.close()
        if remaining <= 0:
            return {"ok": False, "error": "Too many incorrect attempts. Request a new code."}
        return {"ok": False, "error": f"Incorrect code. {remaining} attempt(s) remaining."}

    db.execute("UPDATE otp_codes SET used = 1 WHERE id = ?", (otp["id"],))

    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    is_new = False
    if not user:
        db.execute("INSERT INTO users (email) VALUES (?)", (email,))
        db.commit()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        is_new = True

    db.close()

    token = create_jwt(user["id"], user["email"])

    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=JWT_EXPIRY_HOURS * 3600,
        secure=True,
        path="/",
    )

    needs_profile = is_new or not user["name"]

    return {
        "ok": True,
        "is_new": is_new,
        "needs_profile": needs_profile,
        "user": {"id": user["id"], "email": user["email"], "name": user["name"]},
    }


@router.post("/google")
async def google_auth(body: dict, response: Response):
    credential = body.get("credential")
    if not credential:
        return {"ok": False, "error": "Missing credential"}

    if not GOOGLE_CLIENT_ID:
        return {"ok": False, "error": "Google sign-in not configured"}

    try:
        info = id_token.verify_oauth2_token(
            credential, google_requests.Request(), GOOGLE_CLIENT_ID
        )
    except ValueError:
        return {"ok": False, "error": "Invalid Google token"}

    email = info.get("email")
    google_sub = info.get("sub")
    google_name = info.get("name", "")
    email_verified = info.get("email_verified", False)

    if not email or not email_verified:
        return {"ok": False, "error": "Google email not verified"}

    db = get_db()

    user = db.execute(
        "SELECT * FROM users WHERE google_sub = ?", (google_sub,)
    ).fetchone()

    if not user:
        user = db.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        if user:
            db.execute(
                "UPDATE users SET google_sub = ? WHERE id = ?",
                (google_sub, user["id"]),
            )
            db.commit()

    is_new = False
    if not user:
        db.execute(
            "INSERT INTO users (email, name, google_sub) VALUES (?, ?, ?)",
            (email, google_name or None, google_sub),
        )
        db.commit()
        user = db.execute(
            "SELECT * FROM users WHERE google_sub = ?", (google_sub,)
        ).fetchone()
        is_new = True

    if user and google_name and not user["name"]:
        db.execute(
            "UPDATE users SET name = ? WHERE id = ?",
            (google_name, user["id"]),
        )
        db.commit()
        user = db.execute(
            "SELECT * FROM users WHERE id = ?", (user["id"],)
        ).fetchone()

    db.close()

    token = create_jwt(user["id"], user["email"])

    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=JWT_EXPIRY_HOURS * 3600,
        secure=True,
        path="/",
    )

    needs_profile = not user["name"]

    return {
        "ok": True,
        "is_new": is_new,
        "needs_profile": needs_profile,
        "user": {"id": user["id"], "email": user["email"], "name": user["name"]},
    }


@router.post("/profile-setup")
async def profile_setup(body: ProfileSetup, request: Request):
    current_user = get_current_user(request)
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db = get_db()
    db.execute(
        "UPDATE users SET name = ?, date_of_birth = ? WHERE id = ?",
        (body.name.strip(), body.date_of_birth, current_user["id"]),
    )
    db.commit()
    db.close()

    return {"ok": True}


@router.get("/me")
async def get_me(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return {"ok": True, "authenticated": False}

    db = get_db()
    user = db.execute(
        "SELECT id, email, name, date_of_birth, created_at FROM users WHERE id = ?",
        (current_user["id"],),
    ).fetchone()
    db.close()

    if not user:
        return {"ok": True, "authenticated": False}

    return {
        "ok": True,
        "authenticated": True,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "date_of_birth": user["date_of_birth"],
            "created_at": user["created_at"],
        },
    }


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("session", path="/", httponly=True, samesite="lax", secure=True)
    return {"ok": True}
