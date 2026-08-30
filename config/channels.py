"""
OSINT Syria — Verified Telegram Channels
Last verified: August 2026
Total: 47 channels across Syria + Major Arabic/International News
"""

WORKING_CHANNELS = [
    # ═══════════════════════════════════════════
    # 🇸🇾 SYRIAN CONFLICT MONITORING
    # ═══════════════════════════════════════════
    {"username": "IdlibPlus", "name": "IDLIB PLUS", "priority": "high", "region": "idlib"},
    {"username": "NorthPress", "name": "North Press", "priority": "high", "region": "aleppo"},
    {"username": "QalaatAlMudiq", "name": "Qalaat Al Mudiq", "priority": "high", "region": "hama"},
    {"username": "ARA_News", "name": "ARA News", "priority": "high", "region": "hasakah"},
    {"username": "KurdishQuestion", "name": "Kurdish Question", "priority": "medium", "region": "hasakah"},
    {"username": "liveuamap", "name": "Liveuamap", "priority": "high", "region": "all"},
    {"username": "ISWNews", "name": "ISW News", "priority": "medium", "region": "all"},
    {"username": "WarMonitors", "name": "Global News Monitor", "priority": "medium", "region": "international"},
    {"username": "SyriaMonitor", "name": "رصد وتحليل الأخبار السورية", "priority": "high", "region": "all"},
    {"username": "SyriaNewsLive", "name": " سوريا مباشر", "priority": "high", "region": "all"},
    {"username": "SyriaBreakingNews", "name": "Breaking News", "priority": "high", "region": "all"},
    {"username": "Raqqa_Sl", "name": "الرقة تذبح بصمت", "priority": "high", "region": "raqqa"},
    {"username": "HasakaNow", "name": "الحسكة الآن", "priority": "high", "region": "hasakah"},
    {"username": "SyriaCivilDefense", "name": "الدفاع المدني السوري", "priority": "high", "region": "all"},
    {"username": "Damascus_Syria", "name": "دمشق", "priority": "low", "region": "damascus"},
    {"username": "syriareport", "name": "Syria Report", "priority": "medium", "region": "general"},
    {"username": "SURYAA", "name": "SURYAA", "priority": "medium", "region": "general"},
    {"username": "ELINTNews", "name": "ELINT News", "priority": "medium", "region": "international"},
    {"username": "HRN17", "name": "HRN17", "priority": "low", "region": "general"},
    # Syrian Observatory
    {"username": "syrianobservatory", "name": "المرصد السوري للأخبار", "priority": "high", "region": "all"},
    {"username": "EnabBaladi", "name": "عنب بلدي", "priority": "high", "region": "all"},
    {"username": "BaladiNews", "name": "شبكة بلدي الاعلامية", "priority": "medium", "region": "all"},
    {"username": "shaam_news", "name": "Sham News", "priority": "medium", "region": "all"},
    {"username": "Nedaa", "name": "nedaa", "priority": "medium", "region": "all"},
    {"username": "AlmadaNews", "name": "وكالة المدى الأخبارية", "priority": "medium", "region": "all"},

    # ═══════════════════════════════════════════
    # 🌍 MAJOR ARABIC NEWS NETWORKS
    # ═══════════════════════════════════════════
    {"username": "AlJazeera", "name": "AL JAZEERA", "priority": "high", "region": "international"},
    {"username": "AlArabiya", "name": "العربية", "priority": "high", "region": "international"},
    {"username": "BBCArabic", "name": "BBC News عربي", "priority": "high", "region": "international"},
    {"username": "France24_ar", "name": "فرانس 24 عربي", "priority": "high", "region": "international"},
    {"username": "AlMayadeen", "name": "قناة الميادين", "priority": "high", "region": "international"},
    {"username": "DWArabic", "name": "DW عربية", "priority": "medium", "region": "international"},

    # ═══════════════════════════════════════════
    # 📰 INTERNATIONAL WIRE SERVICES
    # ═══════════════════════════════════════════
    {"username": "ReutersArabic", "name": "رويترز عربي", "priority": "high", "region": "international"},
    {"username": "APNews", "name": "Associated Press", "priority": "high", "region": "international"},
    {"username": "aa_arabic", "name": "وكالة الأناضول", "priority": "high", "region": "international"},
    {"username": "Sputnik_arabic", "name": "سبوتنيك عربي", "priority": "medium", "region": "international"},
    {"username": "RadioFarda", "name": "راديو فردا", "priority": "medium", "region": "international"},
    {"username": "VOAarabic", "name": "صوت أمريكا", "priority": "medium", "region": "international"},

    # ═══════════════════════════════════════════
    # 🇵🇸 PALESTINE / REGIONAL
    # ═══════════════════════════════════════════
    {"username": "Alquds", "name": "Palestine Updates", "priority": "high", "region": "palestine"},
    {"username": "BBCBreaking", "name": "BBC Breaking", "priority": "high", "region": "international"},
    {"username": "France24_en", "name": "FRANCE 24 English", "priority": "medium", "region": "international"},
    {"username": "France24_FR", "name": "FRANCE 24 French", "priority": "low", "region": "international"},
]

CHANNEL_USERNAMES = [ch["username"] for ch in WORKING_CHANNELS]
TOTAL_CHANNELS = len(WORKING_CHANNELS)
HIGH_PRIORITY = sum(1 for ch in WORKING_CHANNELS if ch["priority"] == "high")
MEDIUM_PRIORITY = sum(1 for ch in WORKING_CHANNELS if ch["priority"] == "medium")
LOW_PRIORITY = sum(1 for ch in WORKING_CHANNELS if ch["priority"] == "low")
