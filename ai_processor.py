"""
ai_processor.py — Groq AI (Llama 3.3 70B) ilə xəbərləri kateqoriyalara ayır
                   və Azerbaycancaya çevir.

API qənaəti strategiyası:
  - Bütün xəbərlər BİR sorğuya yığılır (batch processing)
  - Hər taramada cəmi 1–2 API çağırışı olur
  - Groq pulsuz: gündə 6000 sorğu, dəqiqədə 30 sorğu
"""

import json
import logging
import re
import time

from groq import Groq

from config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    CATEGORIES,
    MIN_IMPORTANCE_SCORE,
)

logger = logging.getLogger(__name__)

_client = Groq(api_key=GROQ_API_KEY)

# Batch ölçüsü — bir sorğuda neçə xəbər göndərilsin
_BATCH_SIZE = 20


# ─── Sistem promptu ───────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """Sən texnologiya xəbərlərini Azerbaycancaya çevirən və kateqoriyalara ayıran AI köməkçisisən.

Sənə İngilis dilinde texnologiya xəbərlərinin siyahısı veriləcək.
Hər xəbər üçün aşağıdakıları Azerbaycanca ver:

1. category — aşağıdakılardan birini seç:
   həftənin_hadisəsi  → qlobal miqyasda çox böyük, şok hadisə (hər taramada max 1-2 ədəd)
   süni_intellekt     → AI, ML, LLM, ChatGPT, Gemini, Claude, Copilot, robotlar
   təhlükəsizlik      → kiberhücum, zəiflik, hack, virus, ransomware, CVE, exploit
   məxfilik           → data sızması, izləmə, şifrələmə, VPN, GDPR, surveillance
   avadanlıq          → prosessor, GPU, telefon, laptop, çip, hardware, batareya
   açıq_mənbə         → Linux, open source, GPL, GitHub layihəsi, kernel
   oyun               → video oyun, konsol, Steam, gaming, esports
   qeyd_etməyə_dəyər  → texnologiya ilə əlaqəli digər maraqlı xəbərlər

2. title_az — başlığı Azerbaycancaya çevir (10-12 söz, təbii axıcı dillə)

3. summary_az — 1-2 cümlə Azerbaycanca xülasə (sadə, anlaşıqlı)

4. importance — 1-10 əhəmiyyət balı:
   9-10 → Texnologiya dünyasını silkələyən hadisə
   7-8  → Geniş auditoriyaya təsir edən mühüm xəbər  
   5-6  → Orta maraq, həvəskarlara maraqlı
   1-4  → Az əhəmiyyətli, spesifik xəbər

CAVAB FORMATІ — yalnız düzgün JSON array, heç bir izah əlavə etmə:
[
  {"index": 0, "category": "...", "title_az": "...", "summary_az": "...", "importance": 7},
  {"index": 1, "category": "...", "title_az": "...", "summary_az": "...", "importance": 5}
]"""


# ─── Batch emal ───────────────────────────────────────────────────────────────

def _build_user_message(articles: list[dict]) -> str:
    lines = ["Aşağıdakı xəbərləri emal et:\n"]
    for i, art in enumerate(articles):
        lines.append(f"[{i}] BAŞLIQ: {art['title']}")
        if art.get("description"):
            lines.append(f"    AÇIQLAMA: {art['description'][:250]}")
        lines.append(f"    MƏNBƏ: {art['source']}")
        if art.get("hint"):
            lines.append(f"    İPUCU: {art['hint']}")
        lines.append("")
    return "\n".join(lines)


def _call_groq(articles: list[dict], attempt: int = 0) -> list[dict]:
    """Groq-a bir batch göndər, JSON cavab al."""
    user_msg = _build_user_message(articles)

    try:
        response = _client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            temperature=0.2,
            max_tokens=4096,
        )
        raw = response.choices[0].message.content.strip()

        # JSON hissəsini çıxar (markdown code block-u kənar et)
        json_match = re.search(r"\[.*\]", raw, re.DOTALL)
        if not json_match:
            raise ValueError(f"JSON tapılmadı. Cavab: {raw[:200]}")

        results = json.loads(json_match.group())
        return results

    except Exception as exc:
        logger.error("Groq xəta (cəhd %d): %s", attempt + 1, exc)
        if attempt < 2:
            wait = 15 * (attempt + 1)
            logger.info("%ds gözlənilir, yenidən cəhd edilir...", wait)
            time.sleep(wait)
            return _call_groq(articles, attempt + 1)
        return []


# ─── Əsas funksiya ────────────────────────────────────────────────────────────

def process_articles(articles: list[dict]) -> list[dict]:
    """
    Bütün xəbərləri batch ilə Groq-a göndər,
    kateqoriyalanmış + Azerbaycanca xəbərlər siyahısı qaytar.
    """
    if not articles:
        return []

    processed: list[dict] = []

    for batch_start in range(0, len(articles), _BATCH_SIZE):
        batch = articles[batch_start: batch_start + _BATCH_SIZE]
        logger.info(
            "Groq batch göndərilir: %d xəbər (indeks %d-%d)",
            len(batch), batch_start, batch_start + len(batch) - 1,
        )

        ai_results = _call_groq(batch)

        for res in ai_results:
            idx = res.get("index", -1)
            if not (0 <= idx < len(batch)):
                continue

            importance = int(res.get("importance", 0))
            if importance < MIN_IMPORTANCE_SCORE:
                continue

            category_key = res.get("category", "qeyd_etməyə_dəyər")
            if category_key not in CATEGORIES:
                category_key = "qeyd_etməyə_dəyər"

            emoji, label = CATEGORIES[category_key]
            original = batch[idx]

            processed.append({
                "title_az":       res.get("title_az", original["title"]),
                "summary_az":     res.get("summary_az", ""),
                "category":       category_key,
                "category_label": label,
                "emoji":          emoji,
                "importance":     importance,
                "link":           original["link"],
                "source":         original["source"],
                "published":      original.get("published"),
            })

        # Batch-lər arası gözlə (rate limit: dəqiqədə 30 sorğu)
        if batch_start + _BATCH_SIZE < len(articles):
            logger.debug("Növbəti batch üçün 3s gözlənilir...")
            time.sleep(3)

    processed.sort(key=lambda x: x["importance"], reverse=True)

    logger.info(
        "AI emalı tamamlandı: %d/%d xəbər filtrdən keçdi",
        len(processed), len(articles),
    )
    return processed


def group_by_category(articles: list[dict]) -> dict[str, list[dict]]:
    """Xəbərləri kateqoriya açarına görə qruplaşdır (sabit sıra ilə)."""
    grouped: dict[str, list[dict]] = {key: [] for key in CATEGORIES}
    for art in articles:
        key = art["category"]
        grouped.setdefault(key, []).append(art)
    return grouped
