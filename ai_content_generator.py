import logging
import requests
from bs4 import BeautifulSoup
from groq import Groq

from config import GROQ_API_KEY, GROQ_MODEL_1, GROQ_MODEL_3, OPENROUTER_API_KEY, OPENROUTER_MODEL_2
from usage_memory import update_stats

logger = logging.getLogger(__name__)

# Müştərilər
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Dil Qaydası (Promptlara yapışdırılacaq)
AZ_STRICT_RULE = "\nMÜHÜM: Mətn yalnız təmiz Azərbaycan dilində olmalıdır. Qətiyyən Türk dili (örnək: 'yama' yerinə 'yamaq'), İndoneziya dili (örnək: 'tidak') və ya digər dillərdən sözlər qarışdırma. Əgər texniki termin varsa, onu ən uyğun Azərbaycan qarşılığı ilə de və ya olduğu kimi saxla, amma başqa dildəki qrammatikanı istifadə etmə."

def fetch_article_text(url: str) -> str:
    """URL-dən mətn məzmununu çəkir."""
    try:
        resp = requests.get(
            url, 
            timeout=15, 
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        
        # Paragrafları yığırıq
        paragraphs = soup.find_all('p')
        text = "\n".join([p.get_text() for p in paragraphs])
        
        # Mətnin uzunluğunu məhdudlaşdırırıq ki, token limiti aşılmasın (maksimum 15000 simvol)
        return text[:15000]
    except Exception as e:
        logger.error(f"Failed to fetch article text from {url}: {e}")
        return ""

def _try_groq(model: str, system_prompt: str, user_prompt: str) -> str:
    """Daxili Groq müraciəti."""
    if not groq_client: return None
    try:
        completion = groq_client.chat.completions.with_raw_response.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=4096,
        )
        update_stats("groq", completion.headers)
        return completion.parse().choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"Groq ({model}) xətası: {e}")
        return None

def _try_openrouter(model: str, system_prompt: str, user_prompt: str) -> str:
    """Daxili OpenRouter müraciəti."""
    if not OPENROUTER_API_KEY: return None
    try:
        resp = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "X-Title": "AzTech Bot"
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            },
            timeout=45
        )
        if resp.status_code == 200:
            update_stats("openrouter", resp.headers)
            return resp.json()["choices"][0]["message"]["content"].strip()
        logger.warning(f"OpenRouter ({model}) xətası: {resp.status_code}")
        return None
    except Exception as e:
        logger.warning(f"OpenRouter istisna: {e}")
        return None

def generate_with_fallback(system_prompt: str, user_prompt: str, model_choice: int = 1) -> str:
    """Pilləli fallback mexanizmi (1 -> 2 -> 3)."""
    system_prompt += AZ_STRICT_RULE

    # İerarxiya: 
    # 1: GROQ_MODEL_1 (70B)
    # 2: OPENROUTER_MODEL_2 (12B)
    # 3: GROQ_MODEL_3 (8B)
    
    # Əgər seçim 1-dirsə (və ya yoxdursa) ardıcıllıqla yoxla
    if model_choice <= 1:
        res = _try_groq(GROQ_MODEL_1, system_prompt, user_prompt)
        if res: return res
        model_choice = 2 # Əgər alınmasa növbətiyə keç

    if model_choice == 2:
        res = _try_openrouter(OPENROUTER_MODEL_2, system_prompt, user_prompt)
        if res: return res
        model_choice = 3 # Əgər alınmasa növbətiyə keç

    if model_choice >= 3:
        res = _try_groq(GROQ_MODEL_3, system_prompt, user_prompt)
        if res: return res

    return "❌ Bütün API limitləri tükəndi. Lütfən bir qədər sonra yenidən yoxlayın."

def process_command(command_type: str, article_info: dict, extra_args: str = "", article_id: str = "", model_choice: int = 1) -> str:
    """Müxtəlif əmrləri (/script, /short, /deep, /m) emal edir."""
    url = article_info["link"]
    title = article_info["title"]
    
    content = fetch_article_text(url)
    if not content:
        return f"❌ Məqaləni oxumaq mümkün olmadı: {url}"
        
    user_prompt = f"Başlıq: {title}\n\nMəzmun:\n{content}"
    system_prompt = ""
    
    if command_type in ["script", "m"]:
        seconds = "60-120"
        args_parts = extra_args.split()
        if args_parts and args_parts[0].isdigit():
            seconds = args_parts[0]

        if article_id == "0":
            system_prompt = f"""Sən texnoloji YouTube/TikTok kanalının təqdimatçısısan. 
Bu xəbər MÜTLƏQ HOOK (Videonun ilk diqqət çəkən qarmağı) olmalıdır ({seconds} saniyəlik).
ŞƏRTLƏR:
1. QƏTİYYƏN VƏ QƏTİYYƏN Salam vermə, "xoş gəldiniz" demə!
2. Videoya birbaşa ən şok edici xəbərlə partlayış edərək giriş et. Məsələn: "Təsəvvür edin ki..." və ya "Discord hacklendi, həm də..." kimi.
3. Çox sürətlə əsas məqamı vurğula, izləyicini həyəcanda saxla. Planda texniki terminləri sadələşdir.
4. Mətni rəsmi dildə (robot kimi) deyil, tamamilə küçə dilinə yaxın, səmimi Azərbaycan YouTube üslubunda (Məsələn: "Bəs indi nolacaq?") yaz.
Nəticədə 3-4 cümləlik çox axıcı, "wow" təsiri yaradan kəsintisiz danışıq mətnin olsun. Formal və sıxıcı başlıq falan yazma dərhal zombiləşdirici sözlər yaz.
"""
        else:
            system_prompt = f"""Sən texnoloji YouTube/TikTok kanalının təqdimatçısısan.
Bu, videonun ORTA hissəsindəki sıradakı {seconds} saniyəlik xəbərdir.
ŞƏRTLƏR:
1. QƏTİYYƏN Salam vermə, "xoş gəldiniz", "videomuza gəldiniz" demə! 
2. Birbaşa "İndi isə sıradakı xəbərimizə keçək..." və ya "Rəqabət dünyasında isə fərqli bir olay var..." kimi axıcı bir keçidlə xəbərə başla.
3. Detalları səmimi, sadə, dost məclisində danışırmışan kimi izah et ("bilməyənlər üçün xatırladım...").
4. Mətnin sonunda öz çox sərt / məntiqli, oxuyucunu düşündürən bir fikrini ("Mənə qalsa, bu işin axırı çox pis bitəcək...") bildir.
Format olaraq tam oxunmağa hazır, cəlbedici bir ssenari mətnini Azərbaycan dilində təqdim et. Heç bir "Səhnə" və ya "Qısa izah" kimi alt-teglərdən istifadə etmə, sadəcə danışıq mətnini kəsintisiz yaz. Yutuberlər mətnlərini belə oxuyur.
"""
    elif command_type == "short":
        system_prompt = """Sən sosial media menecerisən. Verilmiş xəbər üçün diqqət çəkən Instagram/Telegram postu hazırla. 
Mətn yalnız 1-3 cümlə olmalı və çox cəlbedici olmalıdır. Axırda bir uyğun emoji əlavə et. Uzun hekayələr yazma.
"""
    elif command_type == "deep":
        system_prompt = """Sən baş texnoloji analitiksən. Verilmiş xəbərin texnologiya, biznes və bəşəriyyət üçün nə anlama gəldiyini 
dərin analiz et. Səbəb-nəticə əlaqələri qur və izah et. Xülasə yox, ətraflı hesabat yaz. Dil: Azərbaycan dili.
"""
    else:
        return "❌ Naməlum komanda."
        
    return generate_with_fallback(system_prompt, user_prompt, model_choice)
