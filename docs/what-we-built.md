# What We Built — Auth System

## Session Summary

Added email-based authentication (passwordless OTP) for client accounts.

### Auth Flow

1. User clicks **"Sign In"** in navbar → `/login`
2. Enters email → `POST /auth/request-otp` → 6-digit code sent via Gmail SMTP
3. Enters code → `POST /auth/verify-otp` → JWT stored in HTTP-only cookie
4. **New users** redirected to `/profile/setup` for name + date of birth
5. **Returning users** → homepage with name shown in navbar

### Files Created

| File | Purpose |
|---|---|
| `app/__init__.py` | Package init |
| `app/config.py` | Env var loader (Gmail creds, JWT, OTP settings) |
| `app/database.py` | SQLite setup + CRUD for users + otp_codes tables |
| `app/auth.py` | FastAPI auth router (`/auth/*` endpoints) |
| `app/email_utils.py` | Gmail SMTP sender with dev fallback (prints to console) |
| `app/models.py` | Pydantic request/response schemas |
| `templates/auth/login.html` | Two-step OTP form (email → code) |
| `templates/auth/profile_setup.html` | Name + DOB form (post-registration) |
| `.env` | Secrets config (gitignored) |
| `.env.example` | Template for other devs |

### Files Modified

| File | Changes |
|---|---|
| `main.py` | Mounted auth router, added `/login`, `/profile/setup` routes, startup DB init |
| `templates/index.html` | Added "Sign In" link / user name in navbar (conditional on auth state) |
| `static/css/style.css` | Auth page styles (card, form, error states) |
| `requirements.txt` | Added `python-jose[cryptography]`, `python-dotenv` |
| `.gitignore` | Added `.env` and `*.db` |

### Database (SQLite)

```sql
users (id, email, name, date_of_birth, created_at)
otp_codes (id, email, code, expires_at, attempts, used, created_at)
```

### Security

- OTP: SHA-256 hashed in DB, 5-min expiry, 3-attempt limit, 60s rate limit
- JWT: HS256, 24h expiry, type-claim validated
- Cookie: HttpOnly, SameSite=Lax, path-scoped
- All DB queries: parameterized (no SQL injection)
- All inputs: server-side Pydantic validation

### API Endpoints

| Method | Path | Auth Required |
|---|---|---|
| POST | `/auth/request-otp` | No |
| POST | `/auth/verify-otp` | No |
| POST | `/auth/profile-setup` | Yes |
| GET | `/auth/me` | No (returns auth state) |
| POST | `/auth/logout` | No |

### Dependencies Added

```
python-jose[cryptography]  # JWT
python-dotenv              # .env loading
```

### How to Test

```bash
uvicorn main:app --reload
# Open http://localhost:8000
# "Sign In" link in navbar → enter email → check console for OTP code
# Enter code → redirected to profile setup or homepage
```
