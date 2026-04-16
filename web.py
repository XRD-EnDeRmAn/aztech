"""
web.py — Render.com üçün giriş nöqtəsi və Telegram Webhooku

Bura Telegram-dan mesaj gəldikdə, onu oxuyub cavab verəcək.
İstifadəçi `/tarama` yazarsa -> dərhal axtarışa başlayıb Telegram-a atacaq.
"""

import os
import sys
import threading
import logging
import requests

from flask import Flask, request, jsonify
from config import TELEGRAM_BOT_TOKEN

# Windows terminalında UTF-8 məcburi et
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

_is_scanning = False

def _do_scan():
    """Arxa planda tarama aparır."""
    global _is_scanning
    _is_scanning = True
    try:
        from scheduler import run_scan
        run_scan()
    except Exception as e:
        logger.error("Tarama xətası: %s", e)
    finally:
        _is_scanning = False

def _trigger_scan(chat_id=None):
    """Tarama artıq gedirmi yoxlayır, getmirsə başladır."""
    global _is_scanning
    
    if chat_id:
        from telegram_bot import _send_message
        # Daxili funksiyanı birbaşa chat daxil olmaqla modifikasiya edən sadə versiya
        if _is_scanning:
            _send_message("⏳ Tarama artıq gedir, bir az gözləyin...")
            return False
        else:
            _send_message("🚀 Bot oyandı! Tarama başladı. Təxminən 2-3 dəqiqəyə xəbərlər gələcək...")

    t = threading.Thread(target=_do_scan, daemon=True)
    t.start()
    return True

@app.route("/")
def home():
    """Render daxil olduqda (Wake up url)"""
    return "Bot oyaqdır və Webhook dinləyir!", 200

@app.route("/scan")
def scan():
    """Url üzərindən tarama başlat (Seçim 1)"""
    started = _trigger_scan()
    if started:
        return jsonify({"status": "started", "message": "Tarama başladı!"})
    return jsonify({"status": "already_running"}), 200

@app.route("/webhook", methods=["POST"])
def webhook():
    """Telegram buraya mesajları göndərəcək (Seçim 2)"""
    update = request.get_json()
    if update and "message" in update and "text" in update["message"]:
        text = update["message"]["text"].lower()
        chat_id = update["message"]["chat"]["id"]
        
        if text in ["/start", "/tarama"]:
            logger.info("Telegram-dan /tarama əmri gəldi!")
            _trigger_scan(chat_id=chat_id)
            
    return "ok", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # Localda işləyir
    logger.info("Flask server başladı -> port %d", port)
    app.run(host="0.0.0.0", port=port, debug=False)
