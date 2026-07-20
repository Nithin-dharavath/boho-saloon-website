# Google Sign-In via Identity Services (GIS) — Design Spec

**Date**: 2026-07-21
**Project**: Boho Bloom Luxury Salon
**Status**: Approved for implementation

---

## 1. Overview

Add Google Sign-In to Boho Bloom using Google Identity Services (GIS). Eligible signed-out users may be offered Google One Tap or the browser's FedCM-mediated sign-in UI — showing their Google account for one-click sign-in. A **"Continue with Google" button** on the login page provides the same flow. This coexists with the existing email + OTP authentication.

---

## 2. Architecture

| Layer | Component | Role |
|---|---|---|
| Frontend | GIS `accounts.js` library | Handles OAuth credential retrieval; returns signed ID token |
| Frontend | `templates/base.html` | Loads GIS library, initializes GIS once with both One Tap and button support, defines credential callback |
| Frontend | `templates/auth/login.html` | Container for Google button rendered via GIS `renderButton()` |
| Backend | `app/auth.py` — `POST /auth/google` | Verifies Google ID token server-side, validates `email_verified`, upserts user (stores `google_sub`), sets session cookie |
| Config | `app/config.py` | Reads `GOOGLE_CLIENT_ID` from environment |
| DB | `users` table | Add `google_sub` column for stable Google account identifier |
| External | Google Cloud Console | OAuth 2.0 Client ID configuration |

---

## 3. Configuration

### 3.1 New environment variable

```
GOOGLE_CLIENT_ID=<your-google-oauth-client-id>
```

Added to:
- `.env.example`
- `app/config.py`

### 3.2 New dependency

```
google-auth
```

For server-side verification of Google ID tokens via `google.oauth2.id_token.verify_oauth2_token()`.

---

## 4. Database — Schema Change

Add `google_sub` column to the `users` table:

```sql
ALTER TABLE users ADD COLUMN google_sub TEXT UNIQUE;
```

This stores Google's stable account identifier (`sub` claim) for identity linking that is resilient to email changes.

---

## 5. Backend — `POST /auth/google`

**Route**: `/auth/google` (method: POST)
**Prefix**: Added to existing `auth_router` (full path: `/auth/google`)
**Request body**:
```json
{ "credential": "<google_id_token>" }
```

**Flow**:
1. Verify the ID token server-side:
   ```python
   from google.oauth2 import id_token
   from google.auth.transport import requests

   info = id_token.verify_oauth2_token(
       credential, requests.Request(), GOOGLE_CLIENT_ID
   )
   ```
2. Extract claims from verified payload: `email`, `name`, `sub`, `email_verified`
3. **Reject if**:
   - `email_verified` is not `True` → return `{ "ok": false, "error": "Google email not verified" }`
   - Token's `aud` does not match `GOOGLE_CLIENT_ID` (built into verify)
4. Look up user by `google_sub` or `email`:
   - **Match by `google_sub`** → log them in
   - **Match by `email` only** (OTP user) → link their account: update `google_sub` → log them in
   - **No match** → `INSERT INTO users (email, name, google_sub) VALUES (?, ?, ?)`
5. Set name only if user's current name is null/empty (don't overwrite profile-setup name)
6. Issue JWT session cookie using existing `create_jwt()` and `response.set_cookie()`
7. Determine `needs_profile`:
   ```python
   needs_profile = not user.name or not user.phone
   ```
   (User must have both name and phone to skip profile setup)
8. Return:
   ```json
   { "ok": true, "is_new": true|false, "needs_profile": true|false }
   ```

**Error responses**:
- Invalid/expired token → `{ "ok": false, "error": "Invalid Google token" }`
- Missing `GOOGLE_CLIENT_ID` config → `{ "ok": false, "error": "Google sign-in not configured" }`
- Unverified Google email → `{ "ok": false, "error": "Google email not verified" }`

**Security**:
- Token verification is done server-side using Google's public keys (no client secret needed for ID token flow)
- `email_verified` must be `True` before linking any account by email
- Session cookie uses existing `httponly`, `samesite=lax` settings
- No OAuth scopes or access tokens are requested — GIS auth is for authentication only, not Google API access

---

## 6. Frontend

### 6.1 GIS library — loaded globally

In `templates/base.html` (before `</head>`):

```html
<script src="https://accounts.google.com/gsi/client" async defer></script>
```

### 6.2 Single GIS initialization — on every page (signed-out users)

A single `initGoogleIdentity()` function handles both One Tap and the Google button. Called once per page, guarded by `{% if not user %}`:

```javascript
function initGoogleIdentity() {
  if (typeof google === 'undefined' || !google.accounts) return;

  google.accounts.id.initialize({
    client_id: '{{ GOOGLE_CLIENT_ID }}',
    callback: handleGoogleCredential,
    auto_select: false,
    cancel_on_tap_outside: false,
  });

  var button = document.getElementById('google-signin-btn');
  if (button) {
    google.accounts.id.renderButton(button, {
      theme: 'outline',
      size: 'large',
      text: 'continue_with',
      width: 350,
    });
  }

  google.accounts.id.prompt();
}
```

Key decisions:
- **`auto_select: false`** — user must explicitly click the One Tap prompt or button; no silent auto-login
- **Single initialization** — `initialize()` is called once; `renderButton()` and `prompt()` share the same config
- **`width: 350`** (not `'100%'`) — fixed pixel width per GIS API; container should be styled responsively via CSS
- The button element on login page is identified by `id="google-signin-btn"` (already exists)

### 6.3 Shared credential callback

In `templates/base.html` (global scope, outside the `{% if not user %}` guard):

```javascript
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
```

---

## 7. Google Cloud Console Setup (manual)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Navigate to **APIs & Services → Credentials**
4. Click **Create Credentials → OAuth 2.0 Client ID**
5. Application type: **Web application**
6. Add to **Authorized JavaScript origins**:
   - `http://localhost:8000` (development)
   - `https://bohobloomsalon.com` (production)
7. No redirect URI needed — GIS JavaScript callback pattern is used instead of redirect flow
8. Copy **Client ID** to `.env` as `GOOGLE_CLIENT_ID`

---

## 8. Content Security Policy

If the site uses or will use CSP headers, the following allowances are required:

```
script-src https://accounts.google.com;
frame-src https://accounts.google.com;
connect-src https://accounts.google.com;
```

Without these, GIS library loading and One Tap rendering will be blocked. Test Google Sign-In after enabling any CSP/COOP headers.

---

## 9. Files Changed

| File | Change |
|---|---|
| `database/schema.sql` (or migration) | Add `google_sub TEXT UNIQUE` to `users` table |
| `app/auth.py` | Add `POST /auth/google` endpoint + import google-auth |
| `app/config.py` | Add `GOOGLE_CLIENT_ID` config |
| `templates/base.html` | Add GIS script, single `initGoogleIdentity()`, credential callback |
| `templates/auth/login.html` | Wire Google button container to GIS (id already exists) |
| `.env.example` | Add `GOOGLE_CLIENT_ID` entry |
| `requirements.txt` | Add `google-auth` |

---

## 10. Edge Cases

| Case | Behavior |
|---|---|
| User has no Google session | One Tap silently suppresses; no prompt shown |
| User dismisses One Tap prompt | Behavior depends on browser/FedCM; prompt may not reappear same session |
| Google token is expired/invalid | Backend verification fails → `{ ok: false }` |
| User exists in DB from OTP sign-in | Google sign-in links `google_sub` to existing account |
| Google email is unverified | Backend rejects with `"Google email not verified"` |
| New Google user missing required fields | `needs_profile: true` → redirected to `/profile/setup` |
| Google sign-in on login page while OTP flow is active | Either flow works independently |
| CSP/COOP headers active | Must allow `accounts.google.com` in script-src, frame-src, connect-src |
| Safari/Firefox One Tap | FedCM-mediated UX may differ from Chrome's classic One Tap UI |
