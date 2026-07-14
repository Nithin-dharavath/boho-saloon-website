# Deploy Flow

Triggers: `/deploy-flow`

Runs the full pre-deployment readiness checklist for the Boho Bloom auth system.

## Steps

### 1. Check .env Configuration

Read `.env` and verify:
- `GMAIL_USER` is non-empty and not a placeholder
- `GMAIL_APP_PASSWORD` is non-empty and not a placeholder
- `SECRET_KEY` is non-empty and not `change-me-...`

**PASS**: All three values set. **FAIL** (non-fatal): warn but continue.

### 2. Check Cookie Secure Flag

Grep `app/auth.py` for `secure=` on the cookie line.

**PASS**: `secure=True`. **FAIL** (non-fatal): remind user to set before production HTTPS.

### 3. Start Server

Run `uvicorn main:app --host 127.0.0.1 --port 8000` and confirm startup.

**PASS**: Server starts. **FAIL**: Report error, stop.

### 4. Test Full Auth Flow

Run these sequentially using curl/Python, capturing responses:

```
POST /auth/request-otp     → {"ok": true}
POST /auth/verify-otp      → {"ok": true}
POST /auth/profile-setup    → {"ok": true}
GET  /auth/me               → {"authenticated": true}
POST /auth/logout           → {"ok": true}
GET  /auth/me               → {"authenticated": false}
```

**PASS**: All 6 pass. **FAIL**: Stop and report which step failed + the error.

### 5. Test Rate Limiting

Request OTP twice in rapid succession for the same email. The second should return an error.

**PASS**: Second request blocked. **FAIL**: Report.

### 6. Test Input Validation

Send `POST /auth/request-otp` with `{"email": "bad"}`. Expect 422 validation error.

**PASS**: 422 returned. **FAIL**: Report.

### 7. Cleanup

Delete the test user from SQLite DB.

### 8. Report

Print:
```
┌─────────────────────────────────────┐
│  Boho Bloom — Deploy Readiness      │
├─────────────────────────────────────┤
│  1. .env configured       ✅ / ❌   │
│  2. Cookie secure flag     ✅ / ⚠️   │
│  3. Server starts          ✅ / ❌   │
│  4. Auth flow              ✅ / ❌   │
│  5. Rate limiting          ✅ / ❌   │
│  6. Input validation       ✅ / ❌   │
└─────────────────────────────────────┘
```
