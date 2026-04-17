"""
config.py — Mərkəzi konfiqurasiya faylı
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ─── Telegram ───────────────────────────────────────────────
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str   = os.getenv("TELEGRAM_CHAT_ID", "")

# ─── Groq və OpenRouter AI ──────────────────────────────────────
GROQ_API_KEY: str  = os.getenv("GROQ_API_KEY", "")
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
# llama-3.3-70b-versatile: güclü, pulsuz, qlobal
GROQ_MODEL: str    = "llama-3.3-70b-versatile"

# ─── Scheduler ───────────────────────────────────────────────
SCAN_INTERVAL_HOURS: int = int(os.getenv("SCAN_INTERVAL_HOURS", "6"))

# ─── Filtr ───────────────────────────────────────────────────
MIN_IMPORTANCE_SCORE: int = int(os.getenv("MIN_IMPORTANCE_SCORE", "6"))
MAX_ARTICLES_PER_RUN: int = int(os.getenv("MAX_ARTICLES_PER_RUN", "100"))

# ─── Kateqoriyalar (Azerbaycanca) ───────────────────────────
CATEGORIES = {
    "həftənin_hadisəsi":   ("🔥", "Həftənin Hadisəsi"),
    "süni_intellekt":      ("🤖", "Süni İntellekt"),
    "təhlükəsizlik":       ("🔒", "Təhlükəsizlik"),
    "məxfilik":            ("🕵️", "Məxfilik"),
    "avadanlıq":           ("💻", "Avadanlıq"),
    "açıq_mənbə":          ("🐧", "Açıq Mənbə"),
    "oyun":                ("🎮", "Oyun"),
    "qeyd_etməyə_dəyər":   ("📰", "Qeyd Etməyə Dəyər Xəbərlər"),
}

CATEGORY_NAMES_FOR_AI = list(CATEGORIES.keys())

# ─── Fayl yolları ────────────────────────────────────────────
SEEN_NEWS_FILE: str = os.path.join(os.path.dirname(__file__), "seen_news.json")
NEWS_MAP_FILE: str  = os.path.join(os.path.dirname(__file__), "news_map.json")
LOG_FILE: str       = os.path.join(os.path.dirname(__file__), "bot.log")
