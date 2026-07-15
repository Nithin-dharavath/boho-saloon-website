import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from app.config import GMAIL_USER, GMAIL_APP_PASSWORD, SALON_EMAIL
from app.database import get_db

logger = logging.getLogger(__name__)

template_env = Environment(loader=FileSystemLoader("templates/emails"))


def send_template_email(
    to_email: str,
    subject: str,
    template_name: str,
    context: dict,
    idempotency_key: str,
    user_id: int = None,
) -> bool:
    db = get_db()
    try:
        existing = db.execute(
            "SELECT id FROM automation_logs WHERE idempotency_key = ?",
            (idempotency_key,),
        ).fetchone()
        if existing:
            logger.info("Skipping duplicate send for key=%s", idempotency_key)
            return True

        template = template_env.get_template(template_name)
        html_body = template.render(**context)

        text = f"Please view this email in an HTML-compatible client.\n\n— {context.get('business_name', 'Boho Bloom Luxury Salon')}"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SALON_EMAIL
        msg["To"] = to_email
        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        if GMAIL_USER and GMAIL_APP_PASSWORD:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
                server.sendmail(SALON_EMAIL, to_email, msg.as_string())
            logger.info("Email sent to %s (key=%s)", to_email, idempotency_key)
        else:
            print(f"\n[DEV] Email to {to_email}: {subject}")
            print(f"    Template: {template_name}")
            print(f"    Key: {idempotency_key}\n")

        db.execute(
            """INSERT INTO automation_logs
               (user_id, email_type, recipient, status, idempotency_key)
               VALUES (?, ?, ?, 'sent', ?)""",
            (user_id, context.get("email_type", "generic"), to_email, idempotency_key),
        )
        db.commit()
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("Gmail auth failed — check GMAIL_USER and GMAIL_APP_PASSWORD")
        db.execute(
            """INSERT INTO automation_logs
               (user_id, email_type, recipient, status, error, idempotency_key)
               VALUES (?, ?, ?, 'failed', ?, ?)""",
            (user_id, context.get("email_type", "generic"), to_email, "Gmail auth failed", idempotency_key),
        )
        db.commit()
        return False
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to_email, e)
        db.execute(
            """INSERT INTO automation_logs
               (user_id, email_type, recipient, status, error, idempotency_key)
               VALUES (?, ?, ?, 'failed', ?, ?)""",
            (user_id, context.get("email_type", "generic"), to_email, str(e), idempotency_key),
        )
        db.commit()
        return False
    finally:
        db.close()
