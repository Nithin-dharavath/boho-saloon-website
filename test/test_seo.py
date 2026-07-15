from httpx import AsyncClient, ASGITransport
import pytest

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
async def test_login_page_has_noindex(client):
    async with client as ac:
        resp = await ac.get("/login")
    assert 'content="noindex, follow"' in resp.text


@pytest.mark.asyncio
async def test_sitemap_xml(client):
    async with client as ac:
        resp = await ac.get("/sitemap.xml")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "text/plain; charset=utf-8"
    assert "bohobloomsalon.com" in resp.text
    assert "<urlset" in resp.text


@pytest.mark.asyncio
async def test_robots_txt(client):
    async with client as ac:
        resp = await ac.get("/robots.txt")
    assert resp.status_code == 200
    assert "Disallow: /auth/" in resp.text
    assert "Disallow: /admin/" in resp.text
    assert "Sitemap:" in resp.text
