"""
OSINT Syria — Verified Working Telegram Channels
Last verified: August 2026
"""

WORKING_CHANNELS = [
    # === Active Conflict & OSINT ===
    {"username": "IdlibPlus", "name": "IDLIB PLUS", "priority": "high", "region": "idlib"},
    {"username": "NorthPress", "name": "North Press", "priority": "high", "region": "aleppo"},
    {"username": "QalaatAlMudiq", "name": "Qalaat Al Mudiq", "priority": "high", "region": "hama"},
    {"username": "ARA_News", "name": "ARA News", "priority": "high", "region": "hasakah"},
    {"username": "KurdishQuestion", "name": "Kurdish Question", "priority": "medium", "region": "hasakah"},
    
    # === Live Maps & Intelligence ===
    {"username": "liveuamap", "name": "Liveuamap", "priority": "high", "region": "all"},
    {"username": "ISWNews", "name": "ISW News", "priority": "medium", "region": "all"},
    {"username": "WarMonitors", "name": "Global News Monitor", "priority": "medium", "region": "international"},
    
    # === Syria Monitoring & Analysis ===
    {"username": "SyriaMonitor", "name": "رصد وتحليل الأخبار السورية", "priority": "high", "region": "all"},
    {"username": "SyriaNewsLive", "name": " سوريا مباشر", "priority": "high", "region": "all"},
    {"username": "SyriaBreakingNews", "name": "Breaking News", "priority": "high", "region": "all"},
    {"username": "syriareport", "name": "Syria Report", "priority": "medium", "region": "general"},
    {"username": "SURYAA", "name": "SURYAA", "priority": "medium", "region": "general"},
    
    # === Regional Sources ===
    {"username": "Raqqa_Sl", "name": "الرقة تذبح بصمت", "priority": "high", "region": "raqqa"},
    {"username": "HasakaNow", "name": "الحسكة الآن", "priority": "high", "region": "hasakah"},
    {"username": "SyriaCivilDefense", "name": "الدفاع المدني السوري", "priority": "high", "region": "all"},
    
    # === Damascus ===
    {"username": "Damascus_Syria", "name": "دمشق", "priority": "low", "region": "damascus"},
    
    # === International OSINT ===
    {"username": "ELINTNews", "name": "ELINT News", "priority": "medium", "region": "international"},
    {"username": "HRN17", "name": "HRN17", "priority": "low", "region": "general"},
]

CHANNEL_USERNAMES = [ch["username"] for ch in WORKING_CHANNELS]

# Channel count for display
TOTAL_CHANNELS = len(WORKING_CHANNELS)
HIGH_PRIORITY = sum(1 for ch in WORKING_CHANNELS if ch["priority"] == "high")
