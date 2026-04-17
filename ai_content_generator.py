import logging
import requests
from bs4 import BeautifulSoup
from groq import Groq

from config import GROQ_API_KEY, GROQ_MODEL, OPENROUTER_API_KEY

logger = logging.getLogger(__name__)

# Müştərilər
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

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

def generate_with_fallback(system_prompt: str, user_prompt: str) -> str:
    """Groq ilə mətni yaradır, alınmazsa (Məsələn Rate Limit) OpenRouter ilə yoxlayır."""
    
    # 1. Groq sınağı
    if groq_client:
        try:
            response = groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=4096,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Groq xətası (Fallback aktivləşdirilir...): {e}")
            
    # 2. OpenRouter sınağı
    if OPENROUTER_API_KEY:
        try:
            logger.info("OpenRouter istifadə olunur...")
            resp = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "google/gemini-2.5-pro", # Yaxud openrouter-dəki istədiyiniz model
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                },
                timeout=30
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"OpenRouter xətası: {e}")
            return "❌ Həm Groq, həm də OpenRouter limitləri aşıldı və ya xəta baş verdi."
            
    return "❌ Groq API xəta verdi və OpenRouter API Key daxil edilməyib."

def process_command(command_type: str, article_info: dict, extra_args: str = "") -> str:
    """Müxtəlif əmrləri (/script, /short, /deep, /m) emal edir."""
    
    url = article_info["link"]
    title = article_info["title"]
    
    content = fetch_article_text(url)
    if not content:
        return f"❌ Məqaləni oxumaq mümkün olmadı: {url}"
        
    user_prompt = f"Başlıq: {title}\n\nMəzmun:\n{content}"
    
    if command_type in ["script", "m"]:
        # Saniyə arqumentini çıxarmaq
        seconds = "60-120"
        if extra_args.isdigit():
            seconds = extra_args
            
        system_prompt = f"""Sən peşəkar video məzmun yaradıcısan. Bu xəbər əsasında Youtube/TikTok vizual videosu üçün {seconds} saniyəlik Azərbaycan dilində cəlbedici danışıq mətni hazırla. 
Format:
- 📌 Əsas hadisənin qısa izahı
- 💡 Vacib faktlar və detallar
- 🎙️ Videoda istifadə üçün hazır danışıq mətni (Mətn hissələrə bölünmüş olsun, yəni [Səhnə 1], [Səhnə 2] kimi qur).
Nəticə qısa və səlis Azərbaycan dilində olmalıdır.
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
        
    result = generate_with_fallback(system_prompt, user_prompt)
    return result
