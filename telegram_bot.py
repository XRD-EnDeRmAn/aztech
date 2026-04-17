"""
telegram_bot.py — Kateqoriyalanmış xəbərləri Telegram-a göndərir.

Mesaj formatı (örnek.md-ə uyğun):
──────────────────────────────────
🤖 Süni İntellekt

📌 OpenAI saniyədə 1000 token yaradan yeni modelini təqdim etdi
📝 OpenAI, GPT modelinin yeni versiyasını elan etdi — bu model əvvəlkilərdən...
🔗 techcrunch.com  •  ⭐ 9/10

📌 Anthropic 16 AI agenti ilə C kompilyatoru yazdırdı
📝 ...
──────────────────────────────────
"""

import logging
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, CATEGORIES
from ai_processor import group_by_category
from news_memory import add_news_to_map

logger = logging.getLogger(__name__)

_TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
_MAX_MSG_LEN  = 4000   # Telegram limiti 4096, ehtiyatlı ol


# ─── Köməkçi funksiyalar ──────────────────────────────────────────────────────

def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return url


def _escape(text: str) -> str:
    """Telegram MarkdownV2 üçün xüsusi simvolları escape et."""
    special = r"\_*[]()~`>#+-=|{}.!"
    for ch in special:
        text = text.replace(ch, f"\\{ch}")
    return text


def _send_message(text: str) -> bool:
    """Telegram-a bir mesaj göndər."""
    try:
        resp = requests.post(
            f"{_TELEGRAM_API}/sendMessage",
            json={
                "chat_id":    TELEGRAM_CHAT_ID,
                "text":       text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=20,
        )
        data = resp.json()
        if not data.get("ok"):
            logger.error("Telegram xəta: %s", data)
            return False
        return True
    except Exception as exc:
        logger.error("Telegram göndərmə xətası: %s", exc)
        return False


# ─── Mesaj formatı ────────────────────────────────────────────────────────────

def _format_category_block(category_key: str, articles: list[dict]) -> str:
    """Bir kateqoriya üçün Telegram mesaj bloku yarat."""
    emoji, label = CATEGORIES[category_key]
    lines = [f"<b>{emoji} {label}</b>", ""]

    for art in articles:
        importance = art.get("importance", 0)
        stars = "⭐" * min(importance // 3, 3)  # max 3 ulduz
        
        # ID yaradılır / götürülür
        art_id = add_news_to_map(art)

        lines.append(f"📌 <b>[{art_id}] {art['title_az']}</b>")
        if art.get("summary_az"):
            lines.append(f"📝 {art['summary_az']}")
        lines.append(
            f"🔗 <a href=\"{art['link']}\">{_domain(art['link'])}</a>"
            + (f"  {stars}" if stars else "")
        )
        lines.append("")   # boş sətir

    return "\n".join(lines)


def _chunk_messages(blocks: list[str]) -> list[str]:
    """Bloklardan Telegram limiti keçməyən mesajlar yarat."""
    messages: list[str] = []
    current = ""

    for block in blocks:
        candidate = (current + "\n\n" + block).strip() if current else block
        if len(candidate) > _MAX_MSG_LEN:
            if current:
                messages.append(current.strip())
            current = block
        else:
            current = candidate

    if current.strip():
        messages.append(current.strip())

    return messages


# ─── Əsas funksiyalar ─────────────────────────────────────────────────────────

def send_news_digest(articles: list[dict]) -> int:
    """
    Kateqoriyalanmış xəbərləri Telegram-a göndər.
    Returns: göndərilmiş mesaj sayı
    """
    if not articles:
        logger.info("Göndəriləcək xəbər yoxdur.")
        return 0

    grouped = group_by_category(articles)

    # Yalnız xəbər olan kateqoriyaları al
    blocks: list[str] = []
    for key in CATEGORIES:
        arts = grouped.get(key, [])
        if arts:
            blocks.append(_format_category_block(key, arts))

    if not blocks:
        return 0

    # Başlıq mesajı
    now = datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M UTC")
    header = (
        f"🗞 <b>Texnologiya Xəbərləri</b>\n"
        f"📅 {now}\n"
        f"📊 {len(articles)} xəbər — {len(blocks)} kateqoriya\n"
        f"{'─' * 30}"
    )

    messages = [header] + _chunk_messages(blocks)

    sent = 0
    for msg in messages:
        if _send_message(msg):
            sent += 1

    logger.info("Telegram-a %d mesaj göndərildi.", sent)
    return sent


def send_startup_message() -> None:
    """Bot işə düşəndə test mesajı göndər."""
    from config import SCAN_INTERVAL_HOURS, MIN_IMPORTANCE_SCORE
    text = (
        "🤖 <b>Texnologiya Xəbər Botu işə düşdü!</b>\n\n"
        f"⏱ Tarama intervalı: hər <b>{SCAN_INTERVAL_HOURS} saat</b>\n"
        f"⭐ Minimum əhəmiyyət balı: <b>{MIN_IMPORTANCE_SCORE}/10</b>\n\n"
        "İlk tarama indi başlayır... 🚀"
    )
    _send_message(text)


def send_error_alert(error_msg: str) -> None:
    """Kritik xəta baş verəndə xəbər ver."""
    text = f"⚠️ <b>Bot xətası:</b>\n<code>{error_msg[:500]}</code>"
    _send_message(text)
