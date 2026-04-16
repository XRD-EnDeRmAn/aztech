"""
main.py — Giriş nöqtəsi

İstifadə:
  python main.py          → Normal işə sal (scheduler + dərhal tarama)
  python main.py --test   → Yalnız bir tarama et, sonra çıx
  python main.py --check  → Yalnız konfiqurasiyani yoxla (API bağlantısı)
"""

import argparse
import logging
import sys
import os

# Windows terminalında UTF-8 məcburi et (emoji problemini həll edir)
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    GROQ_API_KEY,
    GROQ_MODEL,
    SCAN_INTERVAL_HOURS,
    MIN_IMPORTANCE_SCORE,
    MAX_ARTICLES_PER_RUN,
    LOG_FILE,
)


# ─── Logging qur ──────────────────────────────────────────────────────────────

def _setup_logging() -> None:
    fmt = "%(asctime)s  %(levelname)-8s  %(name)s — %(message)s"
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ]
    logging.basicConfig(level=logging.INFO, format=fmt, handlers=handlers)
    # 3-cü tərəf kitabxanalarının verbose loglarını sustur
    for noisy in ("httpx", "httpcore", "urllib3", "feedparser"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


# ─── Konfiq yoxlaması ─────────────────────────────────────────────────────────

def _check_config() -> bool:
    ok = True
    print("\n📋 Konfiqurasiya yoxlanılır...\n")

    checks = [
        (TELEGRAM_BOT_TOKEN, "TELEGRAM_BOT_TOKEN"),
        (TELEGRAM_CHAT_ID,   "TELEGRAM_CHAT_ID"),
        (GROQ_API_KEY,       "GROQ_API_KEY"),
    ]
    for val, name in checks:
        if val:
            print(f"  ✅ {name} — mövcuddur")
        else:
            print(f"  ❌ {name} — TAPILMADI! .env faylını yoxla")
            ok = False

    print(f"\n  ⏱  Tarama intervalı  : hər {SCAN_INTERVAL_HOURS} saat")
    print(f"  ⭐  Min əhəmiyyət balı : {MIN_IMPORTANCE_SCORE}/10")
    print(f"  📦  Max xəbər/tarama  : {MAX_ARTICLES_PER_RUN}")

    if ok:
        # Telegram test mesajı
        print("\n📨 Telegram bağlantısı test edilir...")
        try:
            import requests
            r = requests.get(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe",
                timeout=10,
            )
            d = r.json()
            if d.get("ok"):
                bot_name = d["result"].get("username", "?")
                print(f"  ✅ Telegram bot qoşuldu: @{bot_name}")
            else:
                print(f"  ❌ Telegram xətası: {d}")
                ok = False
        except Exception as e:
            print(f"  ❌ Telegram bağlantı xətası: {e}")
            ok = False

        # Groq AI test
        print(f"\n🤖 Groq AI test edilir ({GROQ_MODEL})...")
        try:
            from groq import Groq
            client = Groq(api_key=GROQ_API_KEY)
            resp = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": "Salam! Yalnız 'OK' cavabını ver."}],
                max_tokens=10,
            )
            answer = resp.choices[0].message.content.strip()
            print(f"  ✅ Groq qoşuldu — model: {GROQ_MODEL} — cavab: {answer}")
        except Exception as e:
            print(f"  ❌ Groq xətası: {e}")
            ok = False

    print()
    return ok


# ─── Əsas ─────────────────────────────────────────────────────────────────────

def main() -> None:
    _setup_logging()
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(
        description="Azerbaycanca Texnologiya Xəbər Botu"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Yalnız bir tarama et və çıx",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Konfiqurasiyani yoxla (API bağlantısı)",
    )
    args = parser.parse_args()

    # ── --check modu ──────────────────────────────────────────────────────────
    if args.check:
        success = _check_config()
        sys.exit(0 if success else 1)

    # ── Konfiq minimal yoxlaması ──────────────────────────────────────────────
    missing = []
    if not TELEGRAM_BOT_TOKEN: missing.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHAT_ID:   missing.append("TELEGRAM_CHAT_ID")
    if not GROQ_API_KEY:       missing.append("GROQ_API_KEY")

    if missing:
        print(
            "❌ .env faylında aşağıdakı dəyişənlər tapılmadı:\n"
            + "\n".join(f"  • {m}" for m in missing)
            + "\n\n.env.example faylını kopyala → .env adlandır → dəyərləri doldur."
        )
        sys.exit(1)

    # ── --test modu ───────────────────────────────────────────────────────────
    if args.test:
        logger.info("TEST MODU — yalnız bir tarama.")
        from telegram_bot import send_startup_message
        send_startup_message()

        from scheduler import run_scan
        run_scan()

        logger.info("Test tamamlandı. Çıxılır.")
        sys.exit(0)

    # ── Normal işə salma ──────────────────────────────────────────────────────
    logger.info("Bot işə düşür | Interval: %d saat | Min bal: %d",
                SCAN_INTERVAL_HOURS, MIN_IMPORTANCE_SCORE)

    from telegram_bot import send_startup_message
    send_startup_message()

    # Dərhal ilk taramanı et, sonra scheduler-i başlat
    from scheduler import run_scan, start_scheduler
    run_scan()
    start_scheduler()   # Bu nöqtədən bloklanır


if __name__ == "__main__":
    main()
