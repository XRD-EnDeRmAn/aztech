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

def add_news_to_map(article: dict) -> str:
    """Xəbərə nömrə (ID) təyin edir və yaddaşa əlavə edir. Qaytarır: ID"""
    news_map = load_news_map()
    
    # Yeni bir ardıcıl ID təyin edək
    last_id = 0
    if news_map:
        try:
            # Ən böyük integer ID-ni tapaq
            last_id = max([int(k) for k in news_map.keys() if k.isdigit()])
        except ValueError:
            pass

    new_id = str(last_id + 1)
    news_map[new_id] = {
        "title": article.get("title_az", article.get("title", "")),
        "link": article.get("link", ""),
        "source": article.get("source", "")
    }
    
    save_news_map(news_map)
    return new_id
