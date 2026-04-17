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

# Modellər ierarxiyası:
# 1) Llama 3.3 70B (Ən ağıllı, kiçik limit)
# 2) Gemma 3 12B (Orta ağıllı, OpenRouter)
# 3) Llama 3.1 8B (Sürətli, böyük limit)
# 4) Mistral 7B (Ehtiyat üçün pulsuz, OpenRouter)
GROQ_MODEL_1: str    = "llama-3.3-70b-versatile"
OPENROUTER_MODEL_2: str = "google/gemma-3-12b-it:free"
GROQ_MODEL_3: str    = "llama-3.1-8b-instant"
OPENROUTER_MODEL_4: str = "mistralai/mistral-7b-instruct:free"

# Default olaraq hansından başladılsın (1-ci model)
GROQ_MODEL: str = GROQ_MODEL_1

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
