# Profile Page Design — Boho Bloom (Corrected)

## Overview

Add a `/profile` page showing the logged-in user's details (name, email, Member ID, age) with inline editing, plus a "Recent Appointments" section with demo booking data. The page uses a **liquid glass morphism** aesthetic with the existing warm earth-tone palette, rich CSS animations, and a **salon-touch** feel (elegant typography, soft curves, warm glow).

## Routes

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| GET | `/profile` | Render profile.html with user data | Yes (redirect to /login if unauthenticated) |
| POST | `/profile/update` | Accept JSON `{name, date_of_birth}`, update DB, return JSON `{ok, name, date_of_birth, age}` | Yes (Origin/Referer validated) |

## Backend Changes

### `main.py`
- Add `GET /profile` handler:
  - Calls `get_current_user()`, redirects to `/login` if unauthenticated
  - Fetches full user row from DB: `id, email, name, date_of_birth, created_at`
  - Computes `age` server-side (correct birthday-aware calculation)
  - Generates Member ID: `BB-{id:06d}` (display-only, no DB change)
  - Passes demo bookings (conditionally — only in dev mode OR labeled "Sample Appointments")
  - Renders `profile.html` with `noindex, nofollow` robots meta
- Add `POST /profile/update` handler:
  - Authenticates via `get_current_user()`
  - Validates Origin/Referer header for CSRF defense
  - Parses JSON body as `ProfileUpdate` (dedicated model, not `ProfileSetup`)
  - Updates `name` and `date_of_birth` only for `WHERE id = current_user["id"]` (never from body)
  - Computes and returns `age` in response so frontend has one authoritative value
  - Returns `{ok: true, name, date_of_birth, age}` or `422` on validation failure

### Pydantic Model — `ProfileUpdate`

Add to `app/models.py`:

```python
class ProfileUpdate(BaseModel):
    name: str
    date_of_birth: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        v = v.strip()
        if len(v) < 1 or len(v) > 100:
            raise ValueError("Name must be between 1 and 100 characters")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v):
        if v is None:
            return v
        v = v.strip()
        try:
            parsed = date.fromisoformat(v)
        except ValueError:
            raise ValueError("Date of birth must be YYYY-MM-DD")
        if parsed > date.today():
            raise ValueError("Date of birth cannot be in the future")
        if parsed < date(1900, 1, 1):
            raise ValueError("Invalid date of birth")
        return v
```

### `app/auth.py` — Fix Google `needs_profile`
Line 242: `not user["name"] or not user["phone"]` → `not user["name"]`
Since phone is not required per current product scope, and no flow collects it, remove the phone check.

### Age Calculation (server-side utility)
```python
def compute_age(dob_str: str | None) -> int | None:
    if not dob_str:
        return None
    dob = date.fromisoformat(dob_str)
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
```

### CSRF Protection
- Minimum: validate `Origin` or `Referer` header matches the app's origin
- For future: the design envisions a reusable CSRF middleware if more mutation endpoints appear

### Demo Bookings
```python
DEMO_BOOKINGS = [
    {"service": "Hair Styling & Blow-Dry", "date": "21 Jul 2026", "price": "₹1,200", "status": "completed"},
    {"service": "Facial Treatment — Gold Radiance", "date": "14 Jul 2026", "price": "₹2,500", "status": "completed"},
    {"service": "Manicure & Pedicure Combo", "date": "05 Jul 2026", "price": "₹1,800", "status": "completed"},
]
```

Only shown in dev mode OR labeled clearly as "Sample Appointments — Preview". In production without a booking backend, show empty state: "No appointments yet."

## Template: `templates/profile.html`

Extends `base.html`. Structure:

1. **Liquid background blobs** — 3 absolutely-positioned `<div>` elements with animated `border-radius` and opacity, using `--sand`, `--tan`, `--bronze` at ~20% opacity
2. **Profile shell** — centered column, `padding-top: 120px` (below navbar)
3. **Avatar** — `div` with `border-radius: 50%`, gradient background (`--bronze` → `--tan`), user initials rendered as text. Handles edge cases (single name → first letter, empty/null → "U"). Rendered server-side so it works before JS.
4. **Profile glass card** with fields:
   - **Member ID**: `BB-000042` (formatted display)
   - **Name** (editable via inline input)
   - **Email** (view-only)
   - **Age** (computed server-side from DOB, editable via DOB input)
   - **Member since** (from `created_at`)
5. **Inline status region**: `<div id="profile-message" role="status" aria-live="polite"></div>`
6. **Edit mode**: click button → fields switch to `<input>`, store original values, show Save/Cancel
   - Cancel restores originals from JS
   - Save sends JSON POST, updates UI only on success
   - On error, shows message in status region, stays in edit mode
7. **Recent Appointments section** — header + grid of mini glass cards or empty state
8. **Robots meta**: `<meta name="robots" content="noindex, nofollow">` (no SEOMeta)
9. **Title**: `My Profile | Boho Bloom`

### Edit Flow (Vanilla JS)
```
Click Edit → store originals → show inputs
  ├── Save → fetch POST /profile/update (JSON)
  │         ├── 200 → update UI, exit edit mode, show success
  │         └── 422 → show error in status region, stay in edit mode
  └── Cancel → restore originals from stored values, exit edit mode
```

## CSS: `static/css/style.css`

New section (~250 lines) at the end.

### Liquid Glass Foundation
```css
.profile-glass {
    background: rgba(255, 255, 255, 0.35);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: var(--radius-xl);
    box-shadow: var(--shadow-soft);
}
```

### Accessibility Fallbacks
```css
@supports not (backdrop-filter: blur(24px)) {
    .profile-glass { background: rgba(255, 255, 255, 0.92); }
}

@media (prefers-reduced-motion: reduce) {
    .profile-blob,
    .profile-avatar,
    .reveal,
    .profile-field view→edit transition {
        animation: none !important;
        transition: none !important;
    }
}
```

### Animated Background Blobs
```css
@keyframes morph {
    0%   { border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%; }
    50%  { border-radius: 30% 60% 70% 40% / 50% 60% 30% 60%; }
    100% { border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%; }
}
.profile-blob { animation: morph 12s ease infinite; }
```

### Profile-specific Components
- `.profile-shell` — centered wrapper (max-width 600px)
- `.profile-avatar` — initials circle with gradient
- `.profile-card` — glass container with padding
- `.profile-field` — label + value/input row
- `.profile-member-id` — styled monospace pill (`BB-000042`)
- `.profile-field-edit` — input styling (matches existing auth inputs)
- `.profile-actions` — save/cancel buttons row
- `.profile-message` — inline status region (success green / error red)
- `.profile-bookings` — grid of booking cards
- `.booking-card` — mini glass card with left accent border
- `.bookings-empty` — centered empty state text
- `.status-badge` — pill for completed/upcoming

### Animation Details
- `.reveal` + `.reveal-delay-1/2` for staggered entry
- Card enters with `translateY(20px)` → `translateY(0)`, opacity 0 → 1
- Avatar pulses gently on load (`@keyframes avatarGlow`)
- Edit/save buttons have hover lift + smooth color transitions
- Liquid blobs drift and morph continuously in background
- Field view→edit transition: `max-height` + `opacity` animation (0.3s ease)
- All animations respect `prefers-reduced-motion`

## JS: `static/js/script.js`

New function `initProfileEdit()`:
- Toggle edit mode on click — store original values in `data-original-*` attributes
- Serialize form data as JSON
- `fetch POST /profile/update` with `Content-Type: application/json`
- On 200: update displayed name, age, DOB; exit edit mode; show success message
- On error: show error in `#profile-message`, stay in edit mode
- Cancel: restore originals, exit edit mode
- Generate initials from name with edge-case handling:
  - `"Nithin Dharavathu"` → `ND`
  - `"Nithin"` → `N`
  - `""` / `null` → `U`

## Navbar Fix

`templates/partials/navbar.html`: Change `<a href="/auth/me">` → `<a href="/profile">`.
Keep `/auth/me` as a JSON API endpoint — it may be used by other frontend logic.

## Files Changed

| File | Type | Change |
|------|------|--------|
| `main.py` | Edit | Add GET /profile + POST /profile/update |
| `app/auth.py` | Edit | Fix needs_profile phone check |
| `app/models.py` | Edit | Add ProfileUpdate Pydantic model |
| `templates/profile.html` | **New** | Profile page template with noindex |
| `static/css/style.css` | Edit | Add ~250 lines profile/liquid glass CSS |
| `static/js/script.js` | Edit | Add initProfileEdit() |
| `templates/partials/navbar.html` | Edit | Account link → /profile |

## Out of Scope
- No DB migrations (all columns confirmed present)
- No new Python dependencies
- No booking backend (demo data / empty state)
- No profile image upload (initials avatar only)
- No CSRF token library (Origin/Referer validation for now; token middleware deferred)
