# Logout Functionality — Design Spec

**Date:** 2026-07-29
**Status:** Approved for implementation

## Overview

Add a "Sign Out" button to `/profile` that logs the user out via the existing `POST /auth/logout` endpoint, with a branded confirmation modal. The logout button must only appear on `profile.html`.

## Background

- `POST /auth/logout` already exists in `app/auth.py:298` — deletes the `session` cookie
- No logout UI exists anywhere on the site today
- Navbar (`templates/partials/navbar.html`) already conditionally renders "Sign In" vs user's name based on `{% if user and user.id %}`
- Profile page (`templates/profile.html`) is the only authenticated page and already has a sidebar card with user info and an "Edit Profile" button

## Requirements

1. Logout button visible **only** on `/profile`
2. Branded confirmation modal before logout
3. Redirect to `"/"` after logout
4. Navbar updates automatically on redirect (server-rendered based on cookie)

## Design

### 1. Button — Profile Sidebar

Placed in `templates/profile.html` inside the `.profile-card` div, directly after the Edit Profile button (line 45).

- Text: "Sign Out" with a logout icon (arrow + door SVG)
- Class: `.profile-signout-btn` — styled to match `.profile-edit-trigger` with a muted/neutral color (no red to keep the luxury aesthetic)
- Only rendered in the profile sidebar, never in navbar or other pages

### 2. Confirmation Modal

A centered glassmorphism overlay card matching the profile aesthetic:

- **Backdrop:** Semi-transparent dark overlay (`rgba(0,0,0,0.3)`), click dismisses
- **Card:** Same `.profile-glass` styling — `rgba(255,255,255,0.35)` background, blur, rounded corners
- **Content:** Lock icon, "Sign Out?" heading, "Are you sure you want to sign out of your account?" body text
- **Buttons:** "Cancel" (outline style) and "Sign Out" (dark/filled style)
- **Dismiss triggers:** Cancel button, backdrop click, Escape key

### 3. JavaScript Behavior

Added inline in the `<script>` block at the bottom of `profile.html` (no changes to `script.js`):

1. Click "Sign Out" → add `.visible` class to modal → modal fades in
2. Click "Sign Out" in modal → `fetch('/auth/logout', { method: 'POST' })` → `window.location.href = '/'`
3. Click "Cancel" / backdrop / Escape → remove `.visible` class → modal fades out

### 4. CSS

Added to `static/css/profile.css`:

- `.profile-signout-btn` — matches `.profile-edit-trigger` dimensions, slightly different color treatment to differentiate from "Edit"
- `.logout-modal-overlay` — fixed full-screen backdrop
- `.logout-modal` — centered glass card
- `.logout-modal.visible` — opacity/transform transition for entrance

## Files Changed

| File | Change |
|------|--------|
| `templates/profile.html` | Add Sign Out button + confirmation modal HTML + inline JS |
| `static/css/profile.css` | Add ~30 lines for button + modal styles |

## No Changes Needed

- `app/auth.py` — logout endpoint already complete
- `main.py` — no route changes
- `templates/partials/navbar.html` — updates on page reload via existing `{% if user %}` logic
- `static/js/script.js` — logout is profile-page-only behavior

## Edge Cases

- **Already logged out:** Button is only shown when authenticated (Jinja2 `{% if user %}` guard in the template)
- **Network failure:** If fetch fails, user stays on profile page; no destructive action taken
- **Rapid double-click:** Modal is already open on first click; confirm button can be disabled briefly to prevent duplicate requests
