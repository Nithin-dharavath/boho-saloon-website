from httpx import AsyncClient, ASGITransport
import pytest
from fastapi import HTTPException

from main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="https://test")


@pytest.mark.asyncio
async def test_index_has_seo_meta(client):
    async with client as ac:
        resp = await ac.get("/")
    html = resp.text

    assert resp.status_code == 200
    assert '<meta name="description"' in html
    assert '<meta name="keywords"' in html
    assert '<meta name="robots"' in html
    assert '<link rel="canonical"' in html
    assert '<meta property="og:title"' in html
    assert '<meta property="og:description"' in html
    assert '<meta property="og:image"' in html
    assert '<meta property="og:url"' in html
    assert '<meta name="twitter:card"' in html
    assert '<meta name="geo.region"' in html
    assert "Boho Bloom Luxury Salon | Hanamkonda, Warangal" in html
    assert '<img src="/static/images/salon-hero.jpg"' in html


@pytest.mark.asyncio
async def test_index_has_json_ld(client):
    async with client as ac:
        resp = await ac.get("/")
    assert "application/ld+json" in resp.text
    assert "BeautySalon" in resp.text
    assert "makesOffer" in resp.text


@pytest.mark.asyncio
async def test_index_has_enhanced_schema(client):
    async with client as ac:
        resp = await ac.get("/")
    html = resp.text
    assert "sameAs" in html
    assert "BreadcrumbList" in html
    assert '"sameAs"' in html


@pytest.mark.asyncio
async def test_login_page_has_noindex(client):
    async with client as ac:
        resp = await ac.get("/login")
    assert 'content="noindex, follow"' in resp.text


@pytest.mark.asyncio
async def test_sitemap_xml(client):
    async with client as ac:
        resp = await ac.get("/sitemap.xml")
    assert resp.status_code == 200
    assert "bohobloomsalon.com" in resp.text
    assert "<urlset" in resp.text
    assert "<lastmod>" in resp.text
    assert "/login" not in resp.text


@pytest.mark.asyncio
async def test_robots_txt(client):
    async with client as ac:
        resp = await ac.get("/robots.txt")
    assert resp.status_code == 200
    assert "Disallow: /auth/" in resp.text
    assert "Disallow: /admin/" in resp.text
    assert "Sitemap:" in resp.text


@pytest.mark.asyncio
async def test_services_page_seo(client):
    async with client as ac:
        resp = await ac.get("/services")
    html = resp.text
    assert resp.status_code == 200
    assert "application/ld+json" in html
    assert "BreadcrumbList" in html
    assert "ItemList" in html
    assert '<main id="main-content">' in html


@pytest.mark.asyncio
async def test_privacy_page_has_breadcrumb(client):
    async with client as ac:
        resp = await ac.get("/privacy-policy")
    html = resp.text
    assert resp.status_code == 200
    assert "BreadcrumbList" in html
    assert '<main id="main-content">' in html


@pytest.mark.asyncio
async def test_terms_page_has_breadcrumb(client):
    async with client as ac:
        resp = await ac.get("/terms-conditions")
    html = resp.text
    assert resp.status_code == 200
    assert "BreadcrumbList" in html
    assert '<main id="main-content">' in html


@pytest.mark.asyncio
async def test_custom_404_page(client):
    async with client as ac:
        resp = await ac.get("/nonexistent-page", headers={"accept": "text/html"})
    assert resp.status_code == 404
    assert "Page Not Found" in resp.text


@pytest.mark.asyncio
async def test_theme_color_meta(client):
    async with client as ac:
        resp = await ac.get("/")
    assert '<meta name="theme-color"' in resp.text


@pytest.mark.asyncio
async def test_skip_link_present(client):
    async with client as ac:
        resp = await ac.get("/")
    assert 'class="skip-link"' in resp.text
    assert "Skip to main content" in resp.text


@pytest.mark.asyncio
async def test_main_landmark_present(client):
    async with client as ac:
        resp = await ac.get("/")
    assert '<main id="main-content">' in resp.text


@pytest.mark.asyncio
async def test_font_preconnect_present(client):
    async with client as ac:
        resp = await ac.get("/")
    html = resp.text
    assert 'rel="preconnect"' in html
    assert 'fonts.googleapis.com' in html
    assert 'fonts.gstatic.com' in html


@pytest.mark.asyncio
async def test_font_preload_present(client):
    async with client as ac:
        resp = await ac.get("/")
    html = resp.text
    assert 'rel="preload"' in html
    assert 'Cormorant+Garamond' in html or 'Manrope' in html


@pytest.mark.asyncio
async def test_booking_endpoint(client):
    async with client as ac:
        resp = await ac.post("/api/booking", json={
            "name": "Test User",
            "phone": "+911234567890",
            "service": "Hair Cut",
            "message": "Test booking"
        })
    assert resp.status_code == 200, f"Got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["ok"] is True