import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from app.auth import router as auth_router, get_current_user
from app.database import init_db

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


@asynccontextmanager
async def lifespan(application: FastAPI):
    init_db()
    yield


app = FastAPI(title="Boho-Bloom Luxury Salon", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(auth_router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    user = get_current_user(request)
    return templates.TemplateResponse(request, "index.html", {"user": user})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/")
    return templates.TemplateResponse(request, "auth/login.html")


@app.get("/profile/setup", response_class=HTMLResponse)
async def profile_setup_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(
        request, "auth/profile_setup.html", {"user": user}
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
