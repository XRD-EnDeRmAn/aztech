import json
import logging
import os
from config import NEWS_MAP_FILE

logger = logging.getLogger(__name__)

def load_news_map() -> dict:
    """Yaddaşdan ID -> Xəbər xəritəsini yükləyir."""
    try:
        if os.path.exists(NEWS_MAP_FILE):
            with open(NEWS_MAP_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"news_map.json oxunarkən xəta: {e}")
    return {}

def save_news_map(news_map: dict) -> None:
    """ID -> Xəbər xəritəsini yaddaşa yazır."""
    try:
        # Yaddaşın çox şişməməsi üçün sadəcə son 200 elementi saxlayaq.
        if len(news_map) > 200:
            keys_to_keep = list(news_map.keys())[-200:]
            news_map = {k: news_map[k] for k in keys_to_keep}
            
        with open(NEWS_MAP_FILE, "w", encoding="utf-8") as f:
            json.dump(news_map, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"news_map.json yazılarkən xəta: {e}")

def assign_batch_ids(articles: list[dict]) -> None:
    """Xəbərlərə 1-dən başlayaraq seqvential ID-lər təyin edir və yaddaşa yazır.
    İstifadəçi qarmaq (Hook) üçün 1 ID-sini istifadə edə bilər (Məs. /script 1)."""
    news_map = load_news_map()
    
    for idx, article in enumerate(articles):
        str_id = str(idx + 1)  # Artıq 0 əvəzinə 1-dən başlayırıq
        news_map[str_id] = {
            "title": article.get("title_az", article.get("title", "")),
            "link": article.get("link", ""),
            "source": article.get("source", "")
        }
        # Açar kimi xəbər obyektinin içinə də qoyaq ki telegram_bot rahat yazdırsın
        article["bot_id"] = str_id
        
    save_news_map(news_map)
