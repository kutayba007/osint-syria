"""
OSINT Syria - Data Models
Pydantic models for structured event data.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class OSINTEvent(BaseModel):
    """Core event model — represents a single intelligence event."""
    id: Optional[str] = None
    raw_text: str
    source_channel: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # AI-extracted fields
    event_type: str = "unknown"          # اشتباكات / قصف / إغلاق طريق / توتر / ...
    summary_ar: str = ""                 # ملخص بالعربي
    summary_en: str = ""                 # English summary
    threat_level: str = "low"            # critical / high / medium / low
    confidence: float = 0.0              # AI confidence score (0-1)

    # Geocoding
    location_name: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    governorate: str = ""                # محافظة
    city: str = ""                       # مدينة / بلدة

    # Metadata
    media_urls: List[str] = Field(default_factory=list)
    source_message_id: Optional[int] = None
    raw_entities: Optional[dict] = None

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class AlertMessage(BaseModel):
    """Telegram alert message."""
    event_id: str
    title: str
    body: str
    threat_level: str
    location: str
    coordinates: Optional[str] = None
    source_channel: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChannelConfig(BaseModel):
    """Configuration for a monitored channel."""
    username: str
    name: str
    priority: int = 1
    language: str = "ar"
    enabled: bool = True
