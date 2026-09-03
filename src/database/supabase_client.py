"""
OSINT Syria - Supabase Database Client
Stores and retrieves OSINT events from Supabase PostgreSQL cloud database.

The live table is named `events` (not `osint_events`). This client maps
between the `events` column schema and the internal `OSINTEvent` model.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any

from supabase import create_client, Client

from config.settings import config
from src.models import OSINTEvent

logger = logging.getLogger("osint.database")

# The actual table name in Supabase.
TABLE_NAME = "events"

# === SQL to create/verify the events table (run in Supabase SQL Editor) ===
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    title TEXT,
    title_arabic TEXT,
    threat_level TEXT DEFAULT 'low',
    category TEXT DEFAULT 'unknown',
    location_name TEXT,
    location_name_arabic TEXT,
    governorate TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    timestamp_utc TIMESTAMPTZ DEFAULT NOW(),
    confidence_score FLOAT DEFAULT 0.0,
    source_reliability TEXT DEFAULT 'B+',
    threat_score FLOAT DEFAULT 0.0,
    impact TEXT,
    urgency TEXT,
    source_platform TEXT,
    source_channel TEXT,
    raw_excerpt_arabic TEXT,
    raw_excerpt_english TEXT,
    full_narrative TEXT,
    has_arabic BOOLEAN DEFAULT TRUE,
    is_acknowledged BOOLEAN DEFAULT FALSE,
    is_escalated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp_utc DESC);
CREATE INDEX IF NOT EXISTS idx_events_threat ON events(threat_level);
CREATE INDEX IF NOT EXISTS idx_events_category ON events(category);
CREATE INDEX IF NOT EXISTS idx_events_governorate ON events(governorate);
CREATE INDEX IF NOT EXISTS idx_events_coords ON events(latitude, longitude);
"""

# category (DB store) <-> event_type (Arabic label used across the app)
CATEGORY_TO_ARABIC = {
    "security": "أمني",
    "infrastructure": "اقتصادي",
    "civilian": "إنساني",
    "digital_threats": "تضليل",
    "protests": "احتجاجات",
}
ARABIC_TO_CATEGORY = {v: k for k, v in CATEGORY_TO_ARABIC.items()}


def _parse_ts(value) -> Optional[datetime]:
    """Parse a timestamp into an aware datetime (UTC)."""
    if not value:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def to_db_row(event: OSINTEvent) -> Dict[str, Any]:
    """Convert an OSINTEvent model to an `events` table row."""
    category = ARABIC_TO_CATEGORY.get(event.event_type, event.event_type)
    summary_en = event.summary_en or ""
    return {
        "title": summary_en[:120] or None,
        "title_arabic": event.summary_ar or None,
        "threat_level": event.threat_level,
        "category": category or "unknown",
        "location_name": event.location_name or None,
        "location_name_arabic": event.location_name or None,
        "governorate": event.governorate or None,
        "latitude": event.latitude,
        "longitude": event.longitude,
        "timestamp_utc": event.timestamp.isoformat() if event.timestamp else None,
        "confidence_score": (event.confidence or 0.0) * 100,
        "source_reliability": "B+",
        "source_platform": "telegram",
        "source_channel": event.source_channel,
        "raw_excerpt_arabic": event.raw_text or None,
        "raw_excerpt_english": summary_en or None,
        "full_narrative": event.summary_ar or event.raw_text or None,
        "has_arabic": bool(event.raw_text),
    }


def _row_as_model_dict(row: Dict[str, Any]) -> Dict[str, Any]:
    """Convert an `events` DB row into the flat dict shape used by the API.

    Returns model field names so `OSINTEvent(**e)` works in api.py.
    """
    category = row.get("category")
    event_type = CATEGORY_TO_ARABIC.get(category, category) if category else "unknown"

    return {
        "id": row.get("id"),
        "raw_text": row.get("raw_excerpt_arabic") or "",
        "source_channel": row.get("source_channel") or "",
        "timestamp": _parse_ts(row.get("timestamp_utc") or row.get("created_at")) or datetime.now(timezone.utc),
        "event_type": event_type,
        "summary_ar": row.get("title_arabic") or row.get("full_narrative") or "",
        "summary_en": row.get("raw_excerpt_english") or row.get("title") or "",
        "threat_level": row.get("threat_level") or "low",
        "confidence": (row.get("confidence_score") or 0.0) / 100.0,
        "location_name": row.get("location_name") or "",
        "latitude": row.get("latitude"),
        "longitude": row.get("longitude"),
        "governorate": row.get("governorate") or "",
        "city": row.get("location_name") or "",
        "media_urls": [],
        "source_message_id": None,
        "raw_entities": None,
    }


class SupabaseDB:
    """
    Supabase client for storing and querying OSINT events.
    Uses the free tier (500MB storage, 50K monthly active users).
    """

    def __init__(self):
        self.client: Optional[Client] = None
        self._connected = False

    def connect(self):
        """Establish connection to Supabase."""
        try:
            self.client = create_client(config.supabase.url, config.supabase.key)
            self._connected = True
            logger.info("✅ Connected to Supabase")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Supabase: {e}")
            self._connected = False

    def store_event(self, event: OSINTEvent) -> Optional[str]:
        """Store a single event in the database."""
        if not self._connected:
            self.connect()

        if not self._connected or not self.client:
            return None

        try:
            row = to_db_row(event)
            if not row.get("id"):
                row["id"] = f"SYR-{datetime.utcnow().strftime('%Y%m%d-%H%M%S%f')}"

            result = self.client.table(TABLE_NAME).insert(row).execute()

            if result.data:
                event_id = result.data[0].get("id")
                logger.info(f"💾 Stored event {event_id}")
                return event_id
            return None

        except Exception as e:
            logger.error(f"❌ Failed to store event: {e}")
            return None

    def store_events_batch(self, events: List[OSINTEvent]) -> int:
        """Store multiple events at once. Returns count of successful inserts."""
        count = 0
        for event in events:
            if self.store_event(event):
                count += 1
        logger.info(f"💾 Stored {count}/{len(events)} events")
        return count

    def get_recent_events(
        self,
        hours: int = 24,
        threat_level: Optional[str] = None,
        governorate: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recent events as model-shaped dicts with optional filters."""
        if not self._connected:
            self.connect()

        if not self._connected or not self.client:
            return []

        try:
            since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

            query = (
                self.client.table(TABLE_NAME)
                .select("*")
                .gte("timestamp_utc", since)
                .order("timestamp_utc", desc=True)
                .limit(limit)
            )

            if threat_level:
                query = query.eq("threat_level", threat_level)
            if governorate:
                query = query.eq("governorate", governorate)

            result = query.execute()
            rows = result.data or []
            return [_row_as_model_dict(r) for r in rows]

        except Exception as e:
            logger.error(f"❌ Failed to fetch events: {e}")
            return []

    def get_event_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get statistics for the dashboard."""
        rows = self.get_recent_events(hours=hours)

        stats = {
            "total_events": len(rows),
            "by_threat_level": {},
            "by_type": {},
            "by_governorate": {},
            "by_hour": {},
            "high_threat_count": 0,
        }

        for row in rows:
            level = row.get("threat_level", "unknown")
            stats["by_threat_level"][level] = stats["by_threat_level"].get(level, 0) + 1

            etype = row.get("event_type", "unknown")
            stats["by_type"][etype] = stats["by_type"].get(etype, 0) + 1

            gov = row.get("governorate", "غير محدد")
            stats["by_governorate"][gov] = stats["by_governorate"].get(gov, 0) + 1

            if level in ("critical", "high"):
                stats["high_threat_count"] += 1

        return stats

    def get_map_data(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get events with coordinates for the map layer."""
        rows = self.get_recent_events(hours=hours)
        return [
            r for r in rows
            if r.get("latitude") and r.get("longitude")
        ]

    def health_check(self) -> bool:
        """Check if the database is reachable."""
        if not self._connected:
            self.connect()
        if not self.client:
            return False
        try:
            self.client.table(TABLE_NAME).select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"❌ health_check failed: {e}")
            return False