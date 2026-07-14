# Pre-Deployment Checklist

## 1. Gmail Setup (Required for Email Sending)

```bash
# Create salon Gmail account (e.g., bohobloom.salon@gmail.com)
# Enable 2FA → Google Account → Security → 2-Step Verification
# Generate App Password: Security → App passwords → Select "Mail" + "Windows Computer"
# Copy the 16-char password (spaces included, e.g., "xxxx xxxx xxxx xxxx")
```

## 2. Environment Configuration

Edit `.env`:

```ini
GMAIL_USER=bohobloom.salon@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
SALON_EMAIL=bohobloom.salon@gmail.com
DATABASE_URL=database/auth.db
JWT_EXPIRY_HOURS=24
OTP_EXPIRY_MINUTES=5
OTP_MAX_ATTEMPTS=3
OTP_RATE_LIMIT_SECONDS=60
```

## 3. Security Hardening

- [ ] **Change SECRET_KEY** in `.env` — generate via:
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
- [ ] **Set `secure=True`** on cookie in `app/auth.py:147` (requires HTTPS)
- [ ] **Verify `.env` is in `.gitignore`** (already done)
- [ ] **Check `.gitignore` excludes `*.db` files** (already done)

## 4. HTTPS Setup

- Use a reverse proxy (nginx, Caddy) or platform TLS (Railway, Render, etc.)
- The `secure=False` flag on the session cookie must become `secure=True`

## 5. Server Configuration

- [ ] Choose `JWT_EXPIRY_HOURS` (default 24h — lower is safer)
- [ ] Choose `OTP_EXPIRY_MINUTES` (default 5 min)
- [ ] Choose `OTP_MAX_ATTEMPTS` (default 3)
- [ ] Choose `OTP_RATE_LIMIT_SECONDS` (default 60)

## 6. Testing Checklist

- [ ] `uvicorn main:app` starts without errors
- [ ] `/login` page renders correctly
- [ ] `POST /auth/request-otp` returns `{"ok": true}`
- [ ] Email sent (check inbox or console in dev)
- [ ] `POST /auth/verify-otp` with valid code returns JWT cookie
- [ ] `POST /auth/profile-setup` saves name + DOB
- [ ] `GET /auth/me` returns authenticated user
- [ ] `POST /auth/logout` clears session
- [ ] Rate limiting works — second request within 60s is blocked
- [ ] Invalid code returns error (max 3 attempts)

## 7. Future: Resend Integration

The `date_of_birth` column is ready in the `users` table. When you integrate Resend:

1. Add `RESEND_API_KEY` to `.env`
2. Create a Resend sender function in `app/email_utils.py`
3. Write a scheduled job/script that queries users by DOB and sends birthday emails

## 8. Deployment Platforms

Recommended for zero-config HTTPS + env vars:
- **Railway** (simple, free tier)
- **Render** (free tier, auto HTTPS)
- **Fly.io** (cheap, edge)
- **VPS** (nginx + systemd + certbot)

## 9. Files to Exclude from Deployment

```
venv/
__pycache__/
*.pyc
.env
*.db
```
