# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Boho Bloom is a marketing/landing website for a luxury unisex salon in Hanamkonda, Warangal. It is a single-page FastAPI app that renders one HTML template and serves static assets — there is no database, no auth, and no API beyond the landing page route.

## Common commands

Run from the project root with the existing virtualenv active (`venv/`).

```bash
# Install dependencies
pip install -r requirements.txt

# Run the dev server (auto-reload, http://0.0.0.0:8000)
python main.py
# or:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

There is no test suite, linter, or formatter configured. `test/` is an empty directory. If you add tests, install pytest yourself and place them there.

## Architecture

```
main.py                  # FastAPI app entry point
templates/index.html     # Single landing page (all sections live here)
static/
  css/style.css          # Full stylesheet for the page
  js/script.js           # Navbar toggle + scroll-reveal behavior
  images/                # Hero + about images
  fonts/                 # Currently empty
database/                # Empty placeholder; no DB in use
test/                    # Empty; reserved for future tests
```

`main.py` is intentionally tiny:
- mounts `static/` at `/static`
- creates a single `Jinja2Templates` pointing at `templates/`
- exposes one route `GET /` that renders `index.html` via `TemplateResponse(request, ...)` (note the request-first signature, not the older `name=` keyword)
- runs uvicorn on `0.0.0.0:8000` with reload when invoked as `__main__`

All page content (hero, about/services cards, gallery, contact form, footer) lives inline in `templates/index.html`. There is no templating logic — `{{ }}` blocks are not used; the template is a static document served as-is.

`static/js/script.js` handles two things: the mobile navbar toggle (`.navbar-toggle`) and IntersectionObserver-driven `reveal` class animations on elements marked `class="reveal"`. The CSS in `static/css/style.css` defines the corresponding `.reveal`/`.reveal-delay-1/2` initial states and transitions.

The contact form in `index.html` is markup-only — it has no `action`, no handler, and does not POST anywhere. If you wire it up, you'll need to add a FastAPI route and likely bring in an email library (the active branch is `feature/email`).

## Conventions and gotchas

- The page is SEO-tuned: canonical URL, JSON-LD `BeautySalon` schema, and brand copy are all in `templates/index.html`. Update those in place when business details (address, phone, hours) change — they are duplicated in the visible contact section.
- Brand color, typography, and layout are entirely driven by `static/css/style.css`. There is no Tailwind, no preprocessor, no build step — edit CSS directly.
- Image references in the template use absolute paths starting with `/static/...`. Keep this prefix when adding new assets.
- `requirements.txt` is UTF-16 encoded (it shows as garbled text in editors that default to UTF-8). Preserve that encoding if you regenerate it.
- `database/` and `static/fonts/` exist but are empty — they are placeholders, not dead code.
- The `.gitignore` excludes `venv/` and `__pycache__/`. Do not commit compiled `.pyc` files.
- `__pycache__/main.cpython-311.pyc` is currently tracked in the working tree despite the ignore rule; clean it up with `git rm --cached __pycache__/main.cpython-311.pyc` if you intend to keep the ignore.
