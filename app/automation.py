import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import BIRTHDAY_DAYS_BEFORE, BIRTHDAY_DISCOUNT, BIRTHDAY_OFFER_EXPIRY_DAYS, TIMEZONE
from app.database import get_db
from app.email_service import send_template_email

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone=TIMEZONE)


def start_scheduler():
    if scheduler.running:
        return
    scheduler.add_job(
        check_birthday_offers,
        "cron",
        hour=8,
        minute=0,
        id="birthday_check",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("APScheduler started with timezone=%s", TIMEZONE)


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")


async def check_birthday_offers():
    db = get_db()
    try:
        users = db.execute(
            """SELECT id, email, name, date_of_birth FROM users
               WHERE date_of_birth IS NOT NULL AND name IS NOT NULL""",
        ).fetchall()

        today = datetime.now()
        window_end = today + timedelta(days=BIRTHDAY_DAYS_BEFORE)
        today_md = today.strftime("%m-%d")
        window_end_md = window_end.strftime("%m-%d")

        sent_count = 0
        for user in users:
            dob_md = datetime.strptime(user["date_of_birth"], "%Y-%m-%d").strftime("%m-%d")

            if today_md <= dob_md <= window_end_md:
                year = today.year
                idempotency_key = f"birthday_{user['id']}_{year}"

                success = send_template_email(
                    to_email=user["email"],
                    subject="Happy Birthday! A special offer awaits you at Boho Bloom",
                    template_name="birthday_offer.html",
                    context={
                        "name": user["name"],
                        "offer": BIRTHDAY_DISCOUNT,
                        "expiry": str(BIRTHDAY_OFFER_EXPIRY_DAYS),
                        "business_name": "Boho Bloom Luxury Salon",
                        "email_type": "birthday_offer",
                    },
                    idempotency_key=idempotency_key,
                    user_id=user["id"],
                )
                if success:
                    sent_count += 1

        if sent_count:
            logger.info("Birthday check complete — %d offer(s) sent", sent_count)
        else:
            logger.info("Birthday check complete — no offers due today")

    except Exception as e:
        logger.error("Birthday check failed: %s", e)
    finally:
        db.close()
