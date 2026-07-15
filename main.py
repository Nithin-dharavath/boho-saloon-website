import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from app.auth import router as auth_router, get_current_user
from app.automation import start_scheduler, stop_scheduler, check_birthday_offers
from app.database import init_db, get_db
from app.config import ADMIN_EMAILS, GOOGLE_SITE_VERIFICATION
from app.seo import INDEX_SEO, LOGIN_SEO, PROFILE_SETUP_SEO, ADMIN_LOGS_SEO

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


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
