"""
OSINT Syria — ACLED API Integration
Fetches official conflict event data from ACLED (Armed Conflict Location & Event Data).
Free tier: 1,000 requests/month with key, unlimited without key (limited data).
API: https://apidocs.acleddata.com/
"""

import logging
import httpx
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from src.models import OSINTEvent

logger = logging.getLogger("osint.sources.acled")

ACLED_API_BASE = "https://api.acleddata.com/acled/read"


class ACLEDSource:
    """
    ACLED conflict data integration.
    Provides verified, geocoded conflict events for Syria.
    
    Setup:
    1. Register at https://acleddata.com/data-terms/
    2. Get free API key (email-based)
    3. Add ACLED_KEY to .env
    """

    # ACLED event types mapped to our categories
    EVENT_TYPE_MAP = {
        "Battles": "اشتباكات",
        "Explosions/Remote violence": "انفجار",
        "Protests": "بZX",
        "Riots": "توتر",
        "Violence against civilians": "استهداف",
        "Strategic developments": "إعلان رسمي",
        "Mobility": "تحركات عسكرية",
    }

    # ACLED violence categories
    VIOLENCE_MAP = {
        "1": "low",
        "2": "medium",
        "3": "high",
    }

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)
        self._last_request_time = 0

    async def fetch_syria_events(
        self,
        days_back: int = 7,
        limit: int = 500,
        event_types: Optional[List[str]] = None,
    ) -> List[OSINTEvent]:
        """
        Fetch recent conflict events from ACLED for Syria.
        
        Args:
            days_back: How many days back to fetch
            limit: Max events to fetch
            event_types: Filter by ACLED event types
        """
        params = {
            "key": self.api_key,
            "email": "",  # Required but empty for key-based auth
            "country": "Syria",
            "fields": "event_date|event_type|sub_event_type|actor1|actor2|"
                      "admin1|admin2|admin3|location|latitude|longitude|"
                      "fatalities|notes|timestamp|event_id_cnty",
            "limit": min(limit, 1000),
            "from_date": (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d"),
            "to_date": datetime.utcnow().strftime("%Y-%m-%d"),
        }

        if event_types:
            params["event_type"] = "|".join(event_types)

        try:
            response = await self.client.get(ACLED_API_BASE, params=params)
            response.raise_for_status()
            data = response.json()

            if "data" not in data:
                logger.warning("No data in ACLED response")
                return []

            events = []
            for item in data["data"]:
                event = self._parse_acled_event(item)
                if event:
                    events.append(event)

            logger.info(f"📊 ACLED: Fetched {len(events)} Syria conflict events")
            return events

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ ACLED API error: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"❌ ACLED fetch failed: {e}")
            return []

    def _parse_acled_event(self, item: Dict[str, Any]) -> Optional[OSINTEvent]:
        """Convert ACLED event to our OSINTEvent model."""
        try:
            # Parse coordinates
            lat = float(item.get("latitude", 0) or 0)
            lon = float(item.get("longitude", 0) or 0)

            if lat == 0 and lon == 0:
                return None  # Skip events without coordinates

            # Map ACLED event type to our categories
            acled_type = item.get("event_type", "")
            event_type = self.EVENT_TYPE_MAP.get(acled_type, "غير محدد")

            # Determine threat level based on fatalities
            fatalities = int(item.get("fatalities", 0) or 0)
            if fatalities >= 10:
                threat_level = "critical"
            elif fatalities >= 3:
                threat_level = "high"
            elif fatalities >= 1:
                threat_level = "medium"
            else:
                threat_level = "low"

            # Build raw text from ACLED notes
            notes = item.get("notes", "") or ""
            actor1 = item.get("actor1", "") or ""
            actor2 = item.get("actor2", "") or ""
            location = item.get("location", "") or ""

            raw_text = f"{notes}" if notes else f"{acled_type}: {actor1} vs {actor2} in {location}"

            # Parse timestamp
            timestamp_str = item.get("timestamp", "")
            try:
                timestamp = datetime.utcfromtimestamp(int(timestamp_str))
            except (ValueError, TypeError):
                timestamp = datetime.utcnow()

            return OSINTEvent(
                raw_text=raw_text[:500],
                source_channel="ACLED",
                timestamp=timestamp,
                event_type=event_type,
                summary_ar=f"{acled_type}: {actor1} — {location}",
                summary_en=f"{acled_type}: {actor1} vs {actor2} in {location}. Fatalities: {fatalities}",
                threat_level=threat_level,
                confidence=0.95,  # ACLED is highly reliable
                location_name=location,
                latitude=lat,
                longitude=lon,
                governorate=item.get("admin1", ""),
                city=item.get("admin2", ""),
                source_message_id=None,
                raw_entities={
                    "acled_id": item.get("event_id_cnty"),
                    "actor1": actor1,
                    "actor2": actor2,
                    "fatalities": fatalities,
                    "sub_event_type": item.get("sub_event_type", ""),
                },
            )

        except Exception as e:
            logger.error(f"Failed to parse ACLED event: {e}")
            return None

    async def get_fatality_stats(self, days_back: int = 30) -> Dict[str, Any]:
        """Get aggregated fatality statistics from ACLED."""
        events = await self.fetch_syria_events(days_back=days_back, limit=1000)

        stats = {
            "total_events": len(events),
            "total_fatalities": 0,
            "by_type": {},
            "by_governorate": {},
            "daily_trend": {},
        }

        for event in events:
            fatalities = event.raw_entities.get("fatalities", 0) if event.raw_entities else 0
            stats["total_fatalities"] += fatalities

            # By type
            etype = event.event_type
            stats["by_type"][etype] = stats["by_type"].get(etype, 0) + 1

            # By governorate
            gov = event.governorate or "Unknown"
            stats["by_governorate"][gov] = stats["by_governorate"].get(gov, 0) + 1

            # Daily trend
            day = event.timestamp.strftime("%Y-%m-%d")
            if day not in stats["daily_trend"]:
                stats["daily_trend"][day] = {"events": 0, "fatalities": 0}
            stats["daily_trend"][day]["events"] += 1
            stats["daily_trend"][day]["fatalities"] += fatalities

        return stats

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
