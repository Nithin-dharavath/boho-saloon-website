# Google Sign-In Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Google Sign-In via GIS alongside existing OTP auth

**Architecture:** GIS JavaScript library on frontend → Google ID token → server-side verification via google-auth → upsert user with google_sub → existing JWT session cookie

**Tech Stack:** FastAPI, Jinja2, Google Identity Services, google-auth (PyPI)

## Global Constraints

- `GOOGLE_CLIENT_ID` env var required
- `google-auth` dependency added
- `users` table gets `google_sub TEXT UNIQUE` column
- `auto_select: false` — no silent auto-login
- `email_verified` must be True on backend
- `needs_profile` determined by `not user.name or not user.phone`

---

### Task 1: Database migration + Config + Dependencies

**Files:**
- Modify: `app/database.py`
- Modify: `app/config.py`
- Modify: `.env.example`
- Modify: `requirements.txt`

- [ ] **Add google_sub column + phone column to users table in `app/database.py`**

```python
# In init_db(), after CREATE TABLE IF NOT EXISTS users
# Add migration via ALTER TABLE (handles existing DBs)
# Also add phone column for needs_profile check
try:
    conn.execute("ALTER TABLE users ADD COLUMN google_sub TEXT UNIQUE")
except sqlite3.OperationalError:
    pass  # column already exists
try:
    conn.execute("ALTER TABLE users ADD COLUMN phone TEXT")
except sqlite3.OperationalError:
    pass  # column already exists
```

- [ ] **Add GOOGLE_CLIENT_ID to `app/config.py`**

```python
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
```

Add after `GOOGLE_SITE_VERIFICATION` line.

- [ ] **Add to `.env.example`**

```
GOOGLE_CLIENT_ID=
```

- [ ] **Add google-auth to `requirements.txt`**

Add `google-auth` to the file.

---

### Task 2: Backend — POST /auth/google endpoint

**Files:**
- Modify: `app/auth.py`

- [ ] **Add google-auth import and new endpoint**

Add to imports:
```python
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app.config import GOOGLE_CLIENT_ID
```

Add new endpoint `POST /auth/google`:

```python
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
    except ValueError as e:
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
        secure=False,
        path="/",
    )

    needs_profile = not user["name"] or not user["phone"]

    return {
        "ok": True,
        "is_new": is_new,
        "needs_profile": needs_profile,
        "user": {"id": user["id"], "email": user["email"], "name": user["name"]},
    }
```

---

### Task 3: Frontend — GIS integration in base.html

**Files:**
- Modify: `templates/base.html`

- [ ] **Add GIS library script and JS functions**

Add in `<head>`:
```html
<script src="https://accounts.google.com/gsi/client" async defer></script>
```

Add before `</body>` (or in block scripts):
```html
<script>
{% if not user %}
function initGoogleIdentity() {
  if (typeof google === 'undefined' || !google.accounts) return;
  google.accounts.id.initialize({
    client_id: '{{ GOOGLE_CLIENT_ID }}',
    callback: handleGoogleCredential,
    auto_select: false,
    cancel_on_tap_outside: false,
  });
  var btn = document.getElementById('google-signin-btn');
  if (btn) {
    google.accounts.id.renderButton(btn, {
      theme: 'outline', size: 'large', text: 'continue_with', width: 350,
    });
  }
  google.accounts.id.prompt();
}
window.onload = initGoogleIdentity;
{% endif %}

async function handleGoogleCredential(response) {
  try {
    const res = await fetch('/auth/google', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ credential: response.credential }),
    });
    const data = await res.json();
    if (data.ok) {
      if (data.needs_profile) {
        window.location.href = '/profile/setup';
      } else {
        window.location.href = window.location.pathname;
      }
    } else {
      console.error('Google sign-in error:', data.error);
    }
  } catch (err) {
    console.error('Google sign-in network error:', err);
  }
}
</script>
```

---

### Task 4: Frontend — Google button on login page

**Files:**
- Modify: `templates/auth/login.html`

- [ ] **Replace static Google button with GIS-rendered button**

The button div already exists with `id="google-signin-btn"`. Remove the inner HTML content (the icon wrapper and text) so it's an empty container for GIS to render into. Keep the button element itself.

Change:
```html
<button type="button" class="btn btn-google" id="google-signin-btn" aria-label="Sign in with Google">
  <div class="google-icon-wrapper">
    <img src="https://developers.google.com/identity/images/g-logo.png" alt="Google" class="google-icon">
  </div>
  <div class="google-button-text">Continue with Google</div>
</button>
```

To:
```html
<div id="google-signin-btn"></div>
```
