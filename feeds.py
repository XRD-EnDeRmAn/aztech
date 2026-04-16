"""
feeds.py — Etibarlı xəbər mənbələri (RSS URL-ləri)
"""

RSS_FEEDS = [
    # ── Təhlükəsizlik ──────────────────────────────────────────────────────────
    {
        "url": "https://www.bleepingcomputer.com/feed/",
        "name": "BleepingComputer",
        "hint": "təhlükəsizlik",
    },
    {
        "url": "https://krebsonsecurity.com/feed/",
        "name": "Krebs on Security",
        "hint": "təhlükəsizlik",
    },
    {
        "url": "https://feeds.feedburner.com/TheHackersNews",
        "name": "The Hacker News",
        "hint": "təhlükəsizlik",
    },
    {
        "url": "https://www.darkreading.com/rss.xml",
        "name": "Dark Reading",
        "hint": "təhlükəsizlik",
    },
    {
        "url": "https://www.securityweek.com/feed",
        "name": "SecurityWeek",
        "hint": "təhlükəsizlik",
    },
    # ── Süni İntellekt & Ümumi Tech ──────────────────────────────────────────
    {
        "url": "https://feeds.arstechnica.com/arstechnica/index",
        "name": "Ars Technica",
        "hint": None,
    },
    {
        "url": "https://www.theverge.com/rss/index.xml",
        "name": "The Verge",
        "hint": None,
    },
    {
        "url": "https://www.wired.com/feed/rss",
        "name": "Wired",
        "hint": None,
    },
    {
        "url": "https://techcrunch.com/feed/",
        "name": "TechCrunch",
        "hint": None,
    },
    {
        "url": "https://www.technologyreview.com/feed/",
        "name": "MIT Technology Review",
        "hint": "süni_intellekt",
    },
    {
        "url": "https://venturebeat.com/feed/",
        "name": "VentureBeat",
        "hint": "süni_intellekt",
    },
    # ── Avadanlıq ──────────────────────────────────────────────────────────────
    {
        "url": "https://www.tomshardware.com/feeds/all",
        "name": "Tom's Hardware",
        "hint": "avadanlıq",
    },
    {
        "url": "https://www.engadget.com/rss.xml",
        "name": "Engadget",
        "hint": None,
    },
    # ── Açıq Mənbə & Linux ────────────────────────────────────────────────────
    {
        "url": "https://www.phoronix.com/rss.php",
        "name": "Phoronix",
        "hint": "açıq_mənbə",
    },
    {
        "url": "https://lwn.net/headlines/rss",
        "name": "LWN.net",
        "hint": "açıq_mənbə",
    },
    # ── Oyun ───────────────────────────────────────────────────────────────────
    {
        "url": "https://www.pcgamer.com/rss/",
        "name": "PC Gamer",
        "hint": "oyun",
    },
    # ── Apple & Mobil ──────────────────────────────────────────────────────────
    {
        "url": "https://9to5mac.com/feed/",
        "name": "9to5Mac",
        "hint": "avadanlıq",
    },
    {
        "url": "https://9to5google.com/feed/",
        "name": "9to5Google",
        "hint": "avadanlıq",
    },
]
