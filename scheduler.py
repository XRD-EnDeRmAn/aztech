"""
scheduler.py — APScheduler ilə avtomatik tarama.
"""

import logging
import time

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import SCAN_INTERVAL_HOURS

logger = logging.getLogger(__name__)


def run_scan() -> None:
    """Bir tarama dövrü: RSS → AI → Telegram."""
    from rss_reader  import fetch_new_articles
    from ai_processor import process_articles
    from telegram_bot import send_news_digest, send_error_alert

    logger.info("═" * 50)
    logger.info("Tarama başladı...")

    try:
        # 1) Yeni xəbərləri yığ
        articles = fetch_new_articles()
        if not articles:
            logger.info("Yeni xəbər tapılmadı. Tarama tamamlandı.")
            return

        # 2) AI ilə emal et (kateqorizasiya + Azerbaycancaya çevir)
        processed = process_articles(articles)
        if not processed:
            logger.info("Filtrdən keçən xəbər yoxdur.")
            return

        # 3) Telegram-a göndər
        sent = send_news_digest(processed)
        logger.info("Tarama tamamlandı. Göndərilən mesaj: %d", sent)

    except Exception as exc:
        logger.exception("Tarama zamanı xəta: %s", exc)
        try:
            send_error_alert(str(exc))
        except Exception:
            pass

    logger.info("═" * 50)


def start_scheduler() -> None:
    """Scheduler-i işə sal — proqram burada bloklanır."""
    scheduler = BlockingScheduler(timezone="UTC")

    scheduler.add_job(
        func=run_scan,
        trigger=IntervalTrigger(hours=SCAN_INTERVAL_HOURS),
        id="news_scan",
        name="Tech Xəbər Taraması",
        max_instances=1,          # eyni anda 2 tarama olmasın
        misfire_grace_time=300,   # 5 dəq gecikmə qəbul edilsin
    )

    logger.info(
        "Scheduler başladı — hər %d saatdan bir tarama aparılacaq.",
        SCAN_INTERVAL_HOURS,
    )

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler dayandırıldı.")
        scheduler.shutdown()
