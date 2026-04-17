import json
import os
import logging

STATS_FILE = "api_usage.json"
logger = logging.getLogger(__name__)

def update_stats(provider: str, headers: dict):
    """API cavablarından limit məlumatlarını çıxarır və saxlayır."""
    stats = load_stats()
    
    if provider == "groq":
        # Groq headers: x-ratelimit-remaining-requests, x-ratelimit-remaining-tokens, x-ratelimit-reset-requests
        stats["groq"] = {
            "remaining_req": headers.get("x-ratelimit-remaining-requests", "N/A"),
            "remaining_tokens": headers.get("x-ratelimit-remaining-tokens", "N/A"),
            "reset_in": headers.get("x-ratelimit-reset-requests", "N/A"),
            "last_update": headers.get("date", "N/A")
        }
    elif provider == "openrouter":
        # OpenRouter genis melumat vermir free tier-de, ancaq ugurlu call sayir
        stats["openrouter"] = {
            "status": "Aktiv (Son call uğurlu)",
            "last_update": headers.get("date", "N/A")
        }
        
    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2)
    except Exception as e:
        logger.error(f"Limit stats yazıla bilmədi: {e}")

def load_stats() -> dict:
    """Yaddaşdan statistikaları yükləyir."""
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "groq": {"remaining_req": "N/A", "remaining_tokens": "N/A", "reset_in": "N/A", "last_update": "N/A"},
        "openrouter": {"status": "Məlumat yoxdur", "last_update": "N/A"}
    }
