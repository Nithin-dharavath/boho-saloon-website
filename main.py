import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from datetime import date

from app.auth import router as auth_router, get_current_user
from app.automation import start_scheduler, stop_scheduler, check_birthday_offers
from app.database import init_db, get_db
from app.config import ADMIN_EMAILS, GOOGLE_SITE_VERIFICATION, GOOGLE_CLIENT_ID
from app.models import ProfileUpdate
from app.seo import INDEX_SEO, LOGIN_SEO, PROFILE_SETUP_SEO, ADMIN_LOGS_SEO, PRIVACY_SEO, TERMS_SEO, SERVICES_SEO
from app.services_data import SERVICES

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


@asynccontextmanager
async def lifespan(application: FastAPI):
    init_db()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="Boho-Bloom Luxury Salon", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
templates.env.globals["GOOGLE_CLIENT_ID"] = GOOGLE_CLIENT_ID

app.include_router(auth_router)


@app.get("/sitemap.xml", response_class=PlainTextResponse)
async def sitemap():
    return """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://bohobloomsalon.com/</loc>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://bohobloomsalon.com/login</loc>
    <changefreq>monthly</changefreq>
    <priority>0.3</priority>
  </url>
  <url>
    <loc>https://bohobloomsalon.com/services</loc>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://bohobloomsalon.com/privacy-policy</loc>
    <changefreq>monthly</changefreq>
    <priority>0.4</priority>
  </url>
  <url>
    <loc>https://bohobloomsalon.com/terms-conditions</loc>
    <changefreq>monthly</changefreq>
    <priority>0.4</priority>
  </url>
</urlset>
"""


@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots():
    return """User-agent: *
Allow: /
Disallow: /auth/
Disallow: /admin/

Sitemap: https://bohobloomsalon.com/sitemap.xml
"""


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    user = get_current_user(request)
    ctx = {"user": user, **INDEX_SEO.to_context()}
    if GOOGLE_SITE_VERIFICATION:
        ctx["GOOGLE_SITE_VERIFICATION"] = GOOGLE_SITE_VERIFICATION
    return templates.TemplateResponse(request, "index.html", ctx)


@app.get("/services", response_class=HTMLResponse)
async def services_page(request: Request):
    user = get_current_user(request)
    ctx = {"user": user, "services_data": SERVICES, **SERVICES_SEO.to_context()}
    if GOOGLE_SITE_VERIFICATION:
        ctx["GOOGLE_SITE_VERIFICATION"] = GOOGLE_SITE_VERIFICATION
    return templates.TemplateResponse(request, "services.html", ctx)


@app.get("/privacy-policy", response_class=HTMLResponse)
async def privacy_policy(request: Request):
    ctx = {**PRIVACY_SEO.to_context()}
    if GOOGLE_SITE_VERIFICATION:
        ctx["GOOGLE_SITE_VERIFICATION"] = GOOGLE_SITE_VERIFICATION
    return templates.TemplateResponse(request, "privacy-policy.html", ctx)


@app.get("/terms-conditions", response_class=HTMLResponse)
async def terms_conditions(request: Request):
    ctx = {**TERMS_SEO.to_context()}
    if GOOGLE_SITE_VERIFICATION:
        ctx["GOOGLE_SITE_VERIFICATION"] = GOOGLE_SITE_VERIFICATION
    return templates.TemplateResponse(request, "terms-conditions.html", ctx)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/")
    ctx = {**LOGIN_SEO.to_context()}
    if GOOGLE_SITE_VERIFICATION:
        ctx["GOOGLE_SITE_VERIFICATION"] = GOOGLE_SITE_VERIFICATION
    return templates.TemplateResponse(request, "auth/login.html", ctx)


@app.get("/profile/setup", response_class=HTMLResponse)
async def profile_setup_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")
    ctx = {"user": user, **PROFILE_SETUP_SEO.to_context()}
    if GOOGLE_SITE_VERIFICATION:
        ctx["GOOGLE_SITE_VERIFICATION"] = GOOGLE_SITE_VERIFICATION
    return templates.TemplateResponse(
        request, "auth/profile_setup.html", ctx
    )


@app.post("/admin/trigger/birthday-check")
async def trigger_birthday_check(request: Request):
    user = get_current_user(request)
    if not user or user["email"] not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")
    await check_birthday_offers()
    return {"ok": True, "message": "Birthday check complete"}


@app.get("/admin/automation-logs", response_class=HTMLResponse)
async def view_automation_logs(request: Request, email_type: str = ""):
    user = get_current_user(request)
    if not user or user["email"] not in ADMIN_EMAILS:
        return RedirectResponse(url="/login")

    db = get_db()
    try:
        if email_type:
            rows = db.execute(
                "SELECT * FROM automation_logs WHERE email_type = ? ORDER BY sent_at DESC LIMIT 100",
                (email_type,),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM automation_logs ORDER BY sent_at DESC LIMIT 100"
            ).fetchall()
    finally:
        db.close()

    ctx = {"logs": rows, "filter_type": email_type, **ADMIN_LOGS_SEO.to_context()}
    if GOOGLE_SITE_VERIFICATION:
        ctx["GOOGLE_SITE_VERIFICATION"] = GOOGLE_SITE_VERIFICATION
    return templates.TemplateResponse(
        request,
        "admin/automation_logs.html",
        ctx,
    )


DEMO_BOOKINGS = [
    {"service": "Hair Styling & Blow-Dry", "date": "21 Jul 2026", "price": "\u20b91,200", "status": "completed"},
    {"service": "Facial Treatment \u2014 Gold Radiance", "date": "14 Jul 2026", "price": "\u20b92,500", "status": "completed"},
    {"service": "Manicure & Pedicure Combo", "date": "05 Jul 2026", "price": "\u20b91,800", "status": "completed"},
]


def compute_age(dob_str: str | None) -> int | None:
    if not dob_str:
        return None
    dob = date.fromisoformat(dob_str)
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse(url="/login")

    db = get_db()
    user = db.execute(
        "SELECT id, email, name, date_of_birth, created_at FROM users WHERE id = ?",
        (current_user["id"],),
    ).fetchone()
    db.close()

    if not user:
        return RedirectResponse(url="/login")

    age = compute_age(user["date_of_birth"])
    member_id = f"BB-{user['id']:06d}"

    raw_name = (user["name"] or "").strip()
    if raw_name:
        parts = raw_name.split()
        if len(parts) >= 2:
            initials = (parts[0][0] + parts[-1][0]).upper()
        else:
            initials = parts[0][0].upper()
    else:
        initials = "U"

    ctx = {
        "user": {"id": user["id"], "email": user["email"], "name": user["name"]},
        "profile": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "date_of_birth": user["date_of_birth"],
            "age": age,
            "member_id": member_id,
            "created_at": user["created_at"],
            "initials": initials,
        },
        "bookings": DEMO_BOOKINGS,
    }
    if GOOGLE_SITE_VERIFICATION:
        ctx["GOOGLE_SITE_VERIFICATION"] = GOOGLE_SITE_VERIFICATION
    return templates.TemplateResponse(request, "profile.html", ctx)


@app.post("/profile/update")
async def profile_update(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    origin = request.headers.get("origin", "")
    referer = request.headers.get("referer", "")
    allowed = False
    for h in [origin, referer]:
        if h and ("bohobloomsalon.com" in h or "localhost" in h or "127.0.0.1" in h):
            allowed = True
            break
    if not allowed:
        raise HTTPException(status_code=403, detail="Forbidden")

    body = await request.json()
    data = ProfileUpdate(**body)

    db = get_db()
    db.execute(
        "UPDATE users SET name = ?, date_of_birth = ? WHERE id = ?",
        (data.name.strip(), data.date_of_birth, current_user["id"]),
    )
    db.commit()
    db.close()

    age = compute_age(data.date_of_birth)
    return JSONResponse({
        "ok": True,
        "name": data.name.strip(),
        "date_of_birth": data.date_of_birth,
        "age": age,
    })


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
