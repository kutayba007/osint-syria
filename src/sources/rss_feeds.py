"""
OSINT Syria — RSS Feed Aggregator
Monitors RSS/Atom feeds from news agencies, humanitarian orgs, and OSINT sources.
All feeds are FREE and publicly available.
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import List, Optional, Dict
from html import unescape

import httpx

from src.models import OSINTEvent

logger = logging.getLogger("osint.sources.rss")

# ============================================
# === FREE RSS FEEDS FOR SYRIA MONITORING ===
# ============================================

RSS_FEEDS: List[Dict[str, str]] = [
    # === International News ===
    {
        "name": "Al Jazeera Arabic",
        "url": "https://www.aljazeera.com/xml/rss/all.xml",
        "language": "ar",
        "category": "news",
        "priority": "high",
    },
    {
        "name": "BBC Arabic",
        "url": "https://feeds.bbci.co.uk/arabic/rss.xml",
        "language": "ar",
        "category": "news",
        "priority": "high",
    },
    {
        "name": "Reuters Middle East",
        "url": "https://www.reutersagency.com/feed/?taxonomy=best-sectors&post_type=best",
        "language": "en",
        "category": "news",
        "priority": "high",
    },
    {
        "name": "Associated Press",
        "url": "https://rsshub.app/apf/MEast",
        "language": "en",
        "category": "news",
        "priority": "medium",
    },

    # === Humanitarian Organizations ===
    {
        "name": "OCHA Syria",
        "url": "https://reliefweb.int/updates/rss.xml?search=syria&format=rss",
        "language": "en",
        "category": "humanitarian",
        "priority": "high",
    },
    {
        "name": "ICRC Syria",
        "url": "https://www.icrc.org/en/rss-feeds",
        "language": "en",
        "category": "humanitarian",
        "priority": "medium",
    },
    {
        "name": "UNHCR Syria",
        "url": "https://www.unhcr.org/rss/syria",
        "language": "en",
        "category": "humanitarian",
        "priority": "medium",
    },

    # === OSINT & Conflict Monitoring ===
    {
        "name": "ACLED Conflict Data",
        "url": "https://acleddata.com/feed/",
        "language": "en",
        "category": "conflict",
        "priority": "high",
    },
    {
        "name": "Liveuamap",
        "url": "https://rss.liveuamap.com/en/world",
        "language": "en",
        "category": "conflict",
        "priority": "medium",
    },

    # === Arabic Regional Sources ===
    {
        "name": "SANA (Syrian News Agency)",
        "url": "https://sana.sy/en/rss",
        "language": "ar",
        "category": "official",
        "priority": "medium",
    },
    {
        "name": "Al Mayadeen",
        "url": "https://www.almayadeen.net/rss",
        "language": "ar",
        "category": "news",
        "priority": "medium",
    },

    # === Security & Military ===
    {
        "name": "Jane's Defence",
        "url": "https://www.janes.com/feeds/news",
        "language": "en",
        "category": "military",
        "priority": "medium",
    },
    {
        "name": "Middle East Eye",
        "url": "https://www.middleeasteye.net/rss",
        "language": "en",
        "category": "news",
        "priority": "medium",
    },
]


class RSSFeedAggregator:
    """
    Aggregates RSS feeds from multiple sources.
    Provides Syria-related content filtered and classified.
    """

    # Syria-related keywords for filtering
    SYRIA_KEYWORDS = [
        "syria", "syrian", "damascus", "aleppo", "homs", "hama",
        "idlib", "daraa", "raqqa", "deir ez-zor", "latakia", "tartus",
        "hasakah", "qamishli", "suwayda", "quneitra",
        "سوريا", "سوري", "دمشق", "حلب", "حمص", "حماة",
        "إدلب", "درعا", "الرقة", "دير الزور", "اللاذقية", "طرطوس",
        "الحسكة", "قامشلي", "السويداء", "القنيطرة",
        "assad", "hts", "sdf", "isis", "tahrir al-sham",
        "الجولان", "golan", "fertile crescent",
    ]

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=15.0,
            headers={"User-Agent": "OSINT-Syria/1.0 RSS Aggregator"},
            follow_redirects=True,
        )
        self._seen_urls: set = set()

    async def fetch_all_feeds(self) -> List[OSINTEvent]:
        """Fetch and parse all configured RSS feeds."""
        all_events = []

        for feed_config in RSS_FEEDS:
            try:
                events = await self._fetch_feed(feed_config)
                all_events.extend(events)
            except Exception as e:
                logger.warning(f"⚠️ Failed to fetch {feed_config['name']}: {e}")

        # Deduplicate by URL
        unique_events = []
        for event in all_events:
            if event.source_message_id and event.source_message_id not in self._seen_urls:
                self._seen_urls.add(event.source_message_id)
                unique_events.append(event)

        logger.info(f"📰 RSS: Fetched {len(unique_events)} unique events from {len(RSS_FEEDS)} feeds")
        return unique_events

    async def _fetch_feed(self, feed_config: Dict) -> List[OSINTEvent]:
        """Fetch a single RSS feed and parse entries."""
        events = []

        try:
            response = await self.client.get(feed_config["url"])
            response.raise_for_status()
            content = response.text

            # Simple XML parsing (no lxml dependency)
            items = re.findall(r'<item[^>]*>(.*?)</item>', content, re.DOTALL | re.IGNORECASE)

            for item_xml in items[:20]:  # Limit to 20 items per feed
                event = self._parse_rss_item(item_xml, feed_config)
                if event and self._is_syria_relevant(event.raw_text):
                    events.append(event)

        except httpx.HTTPStatusError as e:
            logger.debug(f"HTTP {e.response.status_code} from {feed_config['name']}")
        except Exception as e:
            logger.debug(f"Error fetching {feed_config['name']}: {e}")

        return events

    def _parse_rss_item(self, xml: str, feed_config: Dict) -> Optional[OSINTEvent]:
        """Parse a single RSS item XML."""
        try:
            title = self._extract_tag(xml, "title")
            description = self._extract_tag(xml, "description")
            link = self._extract_tag(xml, "link")
            pub_date = self._extract_tag(xml, "pubDate")

            if not title and not description:
                return None

            # Parse date
            timestamp = self._parse_date(pub_date) if pub_date else datetime.utcnow()

            # Combine title and description
            raw_text = f"{title}\n\n{description}" if description else title
            raw_text = unescape(raw_text)  # Decode HTML entities
            raw_text = re.sub(r'<[^>]+>', '', raw_text)  # Strip HTML tags

            return OSINTEvent(
                raw_text=raw_text[:500],
                source_channel=feed_config["name"],
                timestamp=timestamp,
                event_type="غير محدد",
                summary_ar=title or raw_text[:100],
                summary_en=raw_text[:200],
                threat_level="low",
                confidence=0.7,  # RSS is generally reliable
                location_name="",
                latitude=None,
                longitude=None,
                governorate="",
                city="",
                source_message_id=hash(link or title or ""),
                raw_entities={
                    "feed_name": feed_config["name"],
                    "feed_category": feed_config["category"],
                    "link": link,
                    "language": feed_config["language"],
                },
            )

        except Exception as e:
            logger.debug(f"Failed to parse RSS item: {e}")
            return None

    def _extract_tag(self, xml: str, tag: str) -> str:
        """Extract content from an XML tag."""
        pattern = rf"<{tag}[^>]*>(.*?)</{tag}>"
        match = re.search(pattern, xml, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def _parse_date(self, date_str: str) -> datetime:
        """Parse various RSS date formats."""
        formats = [
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S %Z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%a, %d %b %Y %H:%M:%S GMT",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        return datetime.utcnow()

    def _is_syria_relevant(self, text: str) -> bool:
        """Check if text is related to Syria."""
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in self.SYRIA_KEYWORDS)

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
