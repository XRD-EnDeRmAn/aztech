"""
rss_reader.py — RSS mənbələrindən yeni xəbərləri oxuyur.

Xüsusiyyətlər:
  - Artıq göndərilmiş xəbərlər seen_news.json-da saxlanılır (dublikat yoxdur)
  - Yalnız son HOURS_LOOKBACK saat içindəki xəbərlər götürülür
  - MAX_ARTICLES_PER_RUN həddinə görə ən yeni xəbərlər seçilir
"""

import json
import logging
import hashlib
import time
from datetime import datetime, timezone, timedelta
from typing import Any

import feedparser

from config import SEEN_NEWS_FILE, MAX_ARTICLES_PER_RUN, SCAN_INTERVAL_HOURS
from feeds import RSS_FEEDS

logger = logging.getLogger(__name__)

# Geri baxış pəncərəsi:
# İstifadəçi botu istədiyi vaxt (istərsə gündə 1 dəfə) işlətdiyi üçün 
# həmişə son 24 saata baxırıq. Onsuz da oxunanlar seen_news.json-da olacağından
# dublikat gəlməyəcək və heç bir vacib xəbər qaçırılmayacaq.
HOURS_LOOKBACK = 24


# ─── Seen news yüklə / saxla ──────────────────────────────────────────────────

def _load_seen() -> set[str]:
    try:
        with open(SEEN_NEWS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def _save_seen(seen: set[str]) -> None:
    # Maksimum 5000 entry saxla (köhnələri sil)
    seen_list = list(seen)[-5000:]
    with open(SEEN_NEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(seen_list, f)


def _make_id(entry: Any) -> str:
    """Xəbər üçün unikal ID yarat (URL və ya hash)."""
    raw = getattr(entry, "link", "") or getattr(entry, "id", "") or entry.get("title", "")
    return hashlib.md5(raw.encode()).hexdigest()


def _parse_date(entry: Any) -> datetime | None:
    """feedparser struct_time → datetime (UTC)."""
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


# ─── Əsas funksiya ────────────────────────────────────────────────────────────

def fetch_new_articles() -> list[dict]:
    """
    Bütün RSS mənbələrindən yeni xəbərləri yığır.
    Returns: [{"title", "description", "link", "source", "hint", "published"}]
    """
    seen = _load_seen()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_LOOKBACK)

    collected: list[dict] = []

    for feed_info in RSS_FEEDS:
        url  = feed_info["url"]
        name = feed_info["name"]
        hint = feed_info.get("hint")

        try:
            # feedparser bəzən bloklanır — timeout üçün requests istifadə et
            import requests
            resp = requests.get(url, timeout=15,
                                headers={"User-Agent": "Mozilla/5.0 (compatible; TechNewsBot/1.0)"})
            d = feedparser.parse(resp.text)
        except Exception as exc:
            logger.warning("RSS yüklənmədi: %s — %s", name, exc)
            continue

        for entry in d.entries:
            art_id = _make_id(entry)
            if art_id in seen:
                continue

            pub = _parse_date(entry)

            # Tarixi olmayan xəbərləri AT — köhnə ola bilər
            if pub is None:
                continue

            if pub < cutoff:
                continue          # köhnədir, atla

            title = getattr(entry, "title", "").strip()
            if not title:
                continue

            # Qısa açıqlama (HTML tagları olmadan)
            summary = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
            # Sadə HTML təmizliyi
            import re
            summary = re.sub(r"<[^>]+>", " ", summary).strip()
            summary = " ".join(summary.split())[:400]   # 400 simvolla kəs

            collected.append({
                "id":          art_id,
                "title":       title,
                "description": summary,
                "link":        getattr(entry, "link", url),
                "source":      name,
                "hint":        hint,
                "published":   pub.isoformat() if pub else None,
            })

        time.sleep(0.3)   # mənbələr arasında kiçik fasilə

    # Ən yenilərini öndə saxla, MAX_ARTICLES_PER_RUN ilə kəs
    collected.sort(key=lambda x: x["published"] or "", reverse=True)
    collected = collected[:MAX_ARTICLES_PER_RUN]

    logger.info("Yeni xəbər: %d (mənbə: %d)", len(collected), len(RSS_FEEDS))

    # Görülmüşlər siyahısını yenilə
    new_ids = {a["id"] for a in collected}
    seen.update(new_ids)
    _save_seen(seen)

    return collected
