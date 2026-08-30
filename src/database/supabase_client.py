"""
OSINT Syria - Supabase Database Client
Stores and retrieves OSINT events from Supabase PostgreSQL cloud database.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from supabase import create_client, Client

from config.settings import config
from src.models import OSINTEvent

logger = logging.getLogger("osint.database")

# === SQL to create the events table (run in Supabase SQL Editor) ===
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS osint_events (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    raw_text TEXT NOT NULL,
    source_channel TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),

    -- AI-extracted fields
    event_type TEXT DEFAULT 'unknown',
    summary_ar TEXT,
    summary_en TEXT,
    threat_level TEXT DEFAULT 'low',
    confidence FLOAT DEFAULT 0.0,

    -- Geocoding
    location_name TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    governorate TEXT,
    city TEXT,

    -- Metadata
    media_urls JSONB DEFAULT '[]'::JSONB,
    source_message_id INTEGER,
    raw_entities JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON osint_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_threat ON osint_events(threat_level);
CREATE INDEX IF NOT EXISTS idx_events_type ON osint_events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_governorate ON osint_events(governorate);
CREATE INDEX IF NOT EXISTS idx_events_coords ON osint_events(latitude, longitude);

-- Enable RLS (Row Level Security)
ALTER TABLE osint_events ENABLE ROW LEVEL SECURITY;

-- Allow public read access for the dashboard
CREATE POLICY "Public read access" ON osint_events
    FOR SELECT USING (true);

-- Allow authenticated insert
CREATE POLICY "Authenticated insert" ON osint_events
    FOR INSERT WITH CHECK (true);
"""


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

        try:
            data = {
                "raw_text": event.raw_text,
                "source_channel": event.source_channel,
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type,
                "summary_ar": event.summary_ar,
                "summary_en": event.summary_en,
                "threat_level": event.threat_level,
                "confidence": event.confidence,
                "location_name": event.location_name,
                "latitude": event.latitude,
                "longitude": event.longitude,
                "governorate": event.governorate,
                "city": event.city,
                "media_urls": event.media_urls,
                "source_message_id": event.source_message_id,
                "raw_entities": event.raw_entities,
            }

            result = self.client.table("osint_events").insert(data).execute()

            if result.data:
                event_id = result.data[0].get("id")
                logger.info(f"💾 Stored event {event_id}")
                return event_id

        except Exception as e:
            logger.error(f"❌ Failed to store event: {e}")
            return None

    def store_events_batch(self, events: List[OSINTEvent]) -> int:
        """Store multiple events at once. Returns count of successful inserts."""
        if not self._connected:
            self.connect()

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
        """Get recent events with optional filters."""
        if not self._connected:
            self.connect()

        try:
            since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

            query = (
                self.client.table("osint_events")
                .select("*")
                .gte("timestamp", since)
                .order("timestamp", desc=True)
                .limit(limit)
            )

            if threat_level:
                query = query.eq("threat_level", threat_level)
            if governorate:
                query = query.eq("governorate", governorate)

            result = query.execute()
            return result.data or []

        except Exception as e:
            logger.error(f"❌ Failed to fetch events: {e}")
            return []

    def get_event_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get statistics for the dashboard."""
        events = self.get_recent_events(hours=hours)

        stats = {
            "total_events": len(events),
            "by_threat_level": {},
            "by_type": {},
            "by_governorate": {},
            "by_hour": {},
            "high_threat_count": 0,
        }

        for event in events:
            # By threat level
            level = event.get("threat_level", "unknown")
            stats["by_threat_level"][level] = stats["by_threat_level"].get(level, 0) + 1

            # By event type
            etype = event.get("event_type", "unknown")
            stats["by_type"][etype] = stats["by_type"].get(etype, 0) + 1

            # By governorate
            gov = event.get("governorate", "غير محدد")
            stats["by_governorate"][gov] = stats["by_governorate"].get(gov, 0) + 1

            # Count high threats
            if level in ("critical", "high"):
                stats["high_threat_count"] += 1

        return stats

    def get_map_data(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get events with coordinates for the map layer."""
        events = self.get_recent_events(hours=hours)
        return [
            e for e in events
            if e.get("latitude") and e.get("longitude")
        ]

    def health_check(self) -> bool:
        """Check if the database is reachable."""
        try:
            self.client.table("osint_events").select("id").limit(1).execute()
            return True
        except Exception:
            return False
