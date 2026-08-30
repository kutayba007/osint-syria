"""
OSINT Syria - Configuration Module
Loads environment variables and provides centralized config.
"""

import os
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv

load_dotenv()


@dataclass
class TelegramConfig:
    api_id: int = int(os.getenv("TG_API_ID", "0"))
    api_hash: str = os.getenv("TG_API_HASH", "")
    phone: str = os.getenv("TG_PHONE", "")
    bot_token: str = os.getenv("TG_BOT_TOKEN", "")
    alert_chat_id: str = os.getenv("TG_CHAT_ID", "")


@dataclass
class GroqConfig:
    api_key: str = os.getenv("GROQ_API_KEY", "")
    model: str = "openai/gpt-oss-20b"
    max_tokens: int = 1024
    temperature: float = 0.1


@dataclass
class SupabaseConfig:
    url: str = os.getenv("SUPABASE_URL", "")
    key: str = os.getenv("SUPABASE_KEY", "")


@dataclass
class GeoConfig:
    """Geocoding config — Nominatim (free, no key needed)"""
    user_agent: str = "osint-syria/1.0"
    timeout: int = 10


@dataclass
class AppConfig:
    """Global app configuration"""
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    groq: GroqConfig = field(default_factory=GroqConfig)
    supabase: SupabaseConfig = field(default_factory=SupabaseConfig)
    geo: GeoConfig = field(default_factory=GeoConfig)

    # === Syria monitoring channels — loaded from channels.py ===
    @property
    def monitored_channels(self) -> List[str]:
        from config.channels import CHANNEL_USERNAMES
        return CHANNEL_USERNAMES

    # === Event severity levels ===
    threat_levels: dict = field(default_factory=lambda: {
        "critical": "🔴 عالي جداً - إنذار فوري",
        "high": "🟠 عالي - تنبيه مهم",
        "medium": "🟡 متوسط - مراقبة",
        "low": "🟢 منخفض - تقرير عادي",
    })

    # === Syrian cities & regions for geocoding ===
    syrian_regions: List[str] = field(default_factory=lambda: [
        "دمشق", "حلب", "حمص", "حماة", "اللاذقية", "دير الزور",
        "الرقة", "درعا", "السويداء", "القنيطرة", "طرطوس",
        "إدلب", "الرقة", " Raqqa", "Damascus", "Aleppo", "Homs",
        "Hama", "Latakia", "Deir ez-Zor", "Daraa", "Idlib",
        "Tartus", "Quneitra", "Suwayda",
        "الشام", "بانياس", "صافيتا", "الhoot", "سك wa",
    ])

    # === Polling interval (seconds) ===
    poll_interval: int = 30


config = AppConfig()
