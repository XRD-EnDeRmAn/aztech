"""
web.py — Render.com üçün giriş nöqtəsi və Telegram Webhooku

Bura Telegram-dan mesaj gəldikdə, onu oxuyub cavab verəcək.
İstifadəçi `/tarama` yazarsa -> dərhal axtarışa başlayıb Telegram-a atacaq.
`/script 1`, `/m 1`, `/short 1`, `/deep 1`, `/limit` komandaları
"""

import os
import sys
import threading
import logging
import requests

from flask import Flask, request, jsonify
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from news_memory import load_news_map
from ai_content_generator import process_command

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
        if _is_scanning:
            _send_message("⏳ Tarama artıq gedir, bir az gözləyin...")
            return False
        else:
            _send_message("🚀 Bot oyandı! Tarama başladı. Təxminən 2-3 dəqiqəyə xəbərlər gələcək...")

    t = threading.Thread(target=_do_scan, daemon=True)
    t.start()
    return True

def handle_article_command(command: str, args: list, chat_id: int):
    from telegram_bot import _send_message
    
    if not args:
        _send_message("❌ Zəhmət olmasa xəbər ID-ni qeyd edin. Məsələn: `/m 1`")
        return
        
    article_id = args[0]
    extra_args = args[1] if len(args) > 1 else ""
    
    news_map = load_news_map()
    if article_id not in news_map:
        _send_message(f"❌ Təəssüf ki, [{article_id}] nömrəli xəbər yaddaşdan silinib və ya mövcud deyil. Zəhmət olmasa yeni /tarama edin.")
        return
        
    article_info = news_map[article_id]
    _send_message(f"⏳ [{article_id}] nömrəli xəbər üçün məzmun yaradılır, lütfən bir qədər gözləyin...")
    
    # AI Process uzun cəkə bilər deyə background thread-də işlədək ki, Webhook timeout olmasın
    def process_and_send():
        result = process_command(command, article_info, extra_args)
        # Mesaj uzun ola bilər, əgər 4000 limitini aşarsa
        if len(result) > 4000:
            for i in range(0, len(result), 4000):
                _send_message(result[i:i+4000])
        else:
            _send_message(result)
            
    threading.Thread(target=process_and_send, daemon=True).start()

def handle_limit_command():
    from telegram_bot import _send_message
    # Qeyd: Groq API-nin dəqiq balansı üçün API requestlərini tutub oxumaq lazımdır, amma asan üsul ümumi məlumat verməkdir.
    text = """📊 <b>Süni İntellekt API Limitləri</b>

<b>Groq AI (Pulsuz Təbəqə)</b>
- Hesablanmış Limit: Dəqiqədə ~30 Sorğu
- Günlük Limit: 14,400 Sorğu / 500,000 Token
- Status: Aktiv 🟢

<i>* Əgər xəbər detalı /script və ya digər spesifik müraciətlərdə yuxarıdakı hədlər aşılsa ("Rate Limit") sistem avtomatik olaraq OpenRouter API istifadə edəcək.</i>
"""
    _send_message(text)

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
        
        # Təhlükəsizlik: TELEGRAM_CHAT_ID-dən gəlməyən mesajları məhəl qoyma
        if str(chat_id) != str(TELEGRAM_CHAT_ID):
            logger.warning(f"İcazəsiz giriş cəhdi (Chat ID: {chat_id}): {text}")
            return "ok", 200
            
        parts = text.split()
        command = parts[0]
        args = parts[1:]
        
        if command in ["/start", "/tarama"]:
            logger.info("Telegram-dan /tarama əmri gəldi!")
            _trigger_scan(chat_id=chat_id)
            
        elif command in ["/m", "/script", "/short", "/deep"]:
            # URL format `/m` komandasını `script` kimi emal etdirək
            cmd_type = "script" if command == "/m" else command[1:] 
            handle_article_command(cmd_type, args, chat_id)
            
        elif command == "/limit":
            handle_limit_command()
            
    return "ok", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info("Flask server başladı -> port %d", port)
    app.run(host="0.0.0.0", port=port, debug=False)
