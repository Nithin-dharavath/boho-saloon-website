import os
from dotenv import load_dotenv

load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
SECRET_KEY = os.getenv("SECRET_KEY", "")
SALON_EMAIL = os.getenv("SALON_EMAIL", GMAIL_USER)

DATABASE_URL = os.getenv("DATABASE_URL", "database/auth.db")
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))
OTP_EXPIRY_MINUTES = int(os.getenv("OTP_EXPIRY_MINUTES", "5"))
OTP_MAX_ATTEMPTS = int(os.getenv("OTP_MAX_ATTEMPTS", "3"))
OTP_RATE_LIMIT_SECONDS = int(os.getenv("OTP_RATE_LIMIT_SECONDS", "60"))

# Email automation
BIRTHDAY_DAYS_BEFORE = int(os.getenv("BIRTHDAY_DAYS_BEFORE", "14"))
BIRTHDAY_DISCOUNT = os.getenv("BIRTHDAY_DISCOUNT", "20% off any service")
BIRTHDAY_OFFER_EXPIRY_DAYS = int(os.getenv("BIRTHDAY_OFFER_EXPIRY_DAYS", "7"))
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")
ADMIN_EMAILS = os.getenv("ADMIN_EMAILS", "").split(",") if os.getenv("ADMIN_EMAILS") else []
GOOGLE_SITE_VERIFICATION = os.getenv("GOOGLE_SITE_VERIFICATION", "")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
