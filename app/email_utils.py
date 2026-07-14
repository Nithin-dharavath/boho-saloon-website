import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import GMAIL_USER, GMAIL_APP_PASSWORD, SALON_EMAIL

logger = logging.getLogger(__name__)


def send_otp_email(to_email: str, otp_code: str) -> None:
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        logger.warning("GMAIL_USER or GMAIL_APP_PASSWORD not set — printing code to console")
        print(f"\n[DEV] OTP code for {to_email}: {otp_code}\n")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Your Boho Bloom login code"
    msg["From"] = SALON_EMAIL
    msg["To"] = to_email

    text = (
        f"Your Boho Bloom login code is: {otp_code}\n\n"
        f"This code expires in 5 minutes.\n\n"
        f"If you didn't request this, you can ignore this email.\n"
        f"— Boho Bloom Luxury Salon"
    )

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:32px;font-family:Georgia,serif;background:#f8f1e8;">
  <div style="max-width:480px;margin:0 auto;background:#fff;border-radius:20px;padding:36px;">
    <h1 style="font-size:1.6rem;color:#4b2f1f;margin:0 0 8px;">Boho Bloom</h1>
    <p style="color:#7b5738;font-size:0.85rem;margin:0 0 28px;">Luxury Salon — Hanamkonda, Warangal</p>
    <p style="color:#4b2f1f;font-size:0.95rem;">Your login code is:</p>
    <div style="margin:24px 0;text-align:center;">
      <span style="display:inline-block;padding:16px 32px;font-size:2rem;font-weight:700;
                   letter-spacing:10px;background:#f8f1e8;border-radius:14px;color:#4b2f1f;">
        {otp_code}
      </span>
    </div>
    <p style="color:#7b5738;font-size:0.85rem;">This code expires in <strong>5 minutes</strong>.</p>
    <hr style="border:none;border-top:1px solid #ead8c3;margin:28px 0 18px;">
    <p style="color:#b48860;font-size:0.78rem;">If you didn't request this code, you can safely ignore this email.</p>
  </div>
</body>
</html>"""

    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(SALON_EMAIL, to_email, msg.as_string())
        logger.info("OTP email sent to %s", to_email)
    except smtplib.SMTPAuthenticationError:
        logger.error("Gmail auth failed — check GMAIL_USER and GMAIL_APP_PASSWORD")
        print("\n[ERROR] Gmail authentication failed. Check your credentials.\n")
        raise
    except smtplib.SMTPException as e:
        logger.error("SMTP error sending to %s: %s", to_email, e)
        raise
