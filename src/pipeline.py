"""
OSINT Syria - Main Pipeline
End-to-end intelligence processing: Scrape → Analyze → Geocode → Store → Alert → Update
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import config
from src.scraper.telegram_scraper import TelegramScraper
from src.analyzer.groq_analyzer import GroqAnalyzer
from src.geocoder.syria_geocoder import SyriaGeocoder
from src.database.supabase_client import SupabaseDB
from src.alerts.telegram_alerts import TelegramAlerts
from src.media.drive_archiver import DriveArchiver
from src.sources.acled_source import ACLEDSource
from src.sources.telescope_detector import TelescopeDetector
from src.sources.rss_feeds import RSSFeedAggregator
from src.sources.discord_webhook import DiscordWebhook

# === Logging Configuration ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("osint_syria.log", encoding="utf-8"),
    ]
)
logger = logging.getLogger("osint.pipeline")


class OSINTPipeline:
    """
    The main intelligence pipeline.
    
    Flow:
    1. 📡 SCRAPE  — Monitor Telegram channels in real-time
    2. 🤖 ANALYZE — Classify events with Groq AI
    3. 📍 GEOCODE — Map locations to coordinates
    4. 💾 STORE   — Save to Supabase cloud database
    5. 🚨 ALERT   — Send immediate alerts for high threats
    6. 📤 ARCHIVE — Save media to Google Drive
    """

    def __init__(self):
        self.scraper = TelegramScraper()
        self.analyzer = GroqAnalyzer()
        self.geocoder = SyriaGeocoder()
        self.db = SupabaseDB()
        self.alerts = TelegramAlerts()
        self.archiver = DriveArchiver()

        # NEW: Additional data sources
        self.acled = ACLEDSource(api_key=os.getenv("ACLED_KEY", ""))
        self.telescope = TelescopeDetector()
        self.rss = RSSFeedAggregator()
        self.discord = DiscordWebhook(webhook_url=os.getenv("DISCORD_WEBHOOK_URL", ""))

        self._events_processed = 0
        self._high_threats_detected = 0
        self._running = False

    async def start(self):
        """Start the full pipeline with all sources."""
        logger.info("=" * 60)
        logger.info("🇸🇾  OSINT SYRIA — Early Warning System")
        logger.info("=" * 60)
        logger.info(f"📡 Telegram: {len(config.monitored_channels)} channels")
        logger.info(f"📊 ACLED: Conflict data integration")
        logger.info(f"🔭 Telescope: {len(self.telescope.rules)} threat detection rules")
        logger.info(f"📰 RSS: {len(RSS_FEEDS)} feed sources")
        logger.info(f"🤖 AI Engine: Groq ({config.groq.model})")
        logger.info(f"💾 Database: Supabase Cloud")
        logger.info(f"🚨 Telegram Alerts: {'✅' if self.alerts.is_configured else '❌'}")
        logger.info(f"💬 Discord Alerts: {'✅' if self.discord.is_configured else '❌'}")
        logger.info("=" * 60)

        # Initialize components
        self.db.connect()

        # Connect to Telegram
        await self.scraper.start()

        # Start background data collection tasks
        asyncio.create_task(self._acled_sync_loop())
        asyncio.create_task(self._rss_sync_loop())

        # Send startup notification
        await self.alerts.send_startup_message()
        if self.discord.is_configured:
            await self.discord.send_daily_summary({"total": 0})

        self._running = True
        logger.info("🔄 Pipeline is RUNNING — All sources active...\n")

        # Main processing loop
        await self._process_loop()

    async def _process_loop(self):
        """Main event processing loop."""
        status_counter = 0

        while self._running:
            try:
                # Get next message from the queue
                event = await self.scraper.get_message()

                if event is None:
                    continue

                # Process through the pipeline
                result = await self._process_event(event)

                if result:
                    self._events_processed += 1

                    # Send periodic status updates (every 50 events)
                    status_counter += 1
                    if status_counter >= 50:
                        await self.alerts.send_status_update(
                            self._events_processed,
                            self._high_threats_detected
                        )
                        status_counter = 0

            except KeyboardInterrupt:
                logger.info("🛑 Shutdown requested...")
                await self.stop()
                break
            except Exception as e:
                logger.error(f"❌ Pipeline error: {e}")
                await asyncio.sleep(5)  # Wait before retrying

    async def _process_event(self, event):
        """Process a single event through the full pipeline."""

        # Step 0: 🔭 Telescope rule-based detection (fast, before AI)
        event = self.telescope.enrich_event(event)

        # Step 1: 🤖 AI Analysis
        event = await self.analyzer.analyze_event(event)

        # Step 2: 📍 Geocoding
        event = self.geocoder.geocode_event(event)

        # Step 3: 💾 Store in database
        event_id = self.db.store_event(event)
        if event_id:
            event.id = event_id

        # Step 4: 🚨 Alert if high threat
        if event.threat_level in ("critical", "high"):
            self._high_threats_detected += 1
            await self.alerts.send_alert(event)
            await self.discord.send_alert(event)

            logger.warning(
                f"{'🚨' if event.threat_level == 'critical' else '⚠️'} "
                f"THREAT [{event.threat_level.upper()}]: "
                f"{event.event_type} — {event.summary_ar[:80]}"
            )

        # Step 5: Log all events
        logger.info(
            f"📨 [{event.threat_level.upper():8}] "
            f"{event.event_type:12} | "
            f"{event.governorate or 'N/A':12} | "
            f"{event.summary_ar[:60]}"
        )

        return event

    # ============================================
    # === BACKGROUND DATA COLLECTION LOOPS ===
    # ============================================

    async def _acled_sync_loop(self):
        """Periodically sync ACLED conflict data."""
        while self._running:
            try:
                logger.info("📊 ACLED: Fetching conflict data...")
                acled_events = await self.acled.fetch_syria_events(days_back=1, limit=100)
                for event in acled_events:
                    await self._process_event(event)
                logger.info(f"📊 ACLED: Processed {len(acled_events)} events")
            except Exception as e:
                logger.error(f"❌ ACLED sync error: {e}")

            # Sync every 6 hours
            await asyncio.sleep(6 * 3600)

    async def _rss_sync_loop(self):
        """Periodically sync RSS feeds."""
        while self._running:
            try:
                logger.info("📰 RSS: Fetching feeds...")
                rss_events = await self.rss.fetch_all_feeds()
                for event in rss_events:
                    await self._process_event(event)
                logger.info(f"📰 RSS: Processed {len(rss_events)} events")
            except Exception as e:
                logger.error(f"❌ RSS sync error: {e}")

            # Sync every 30 minutes
            await asyncio.sleep(30 * 60)

    async def stop(self):
        """Gracefully stop the pipeline."""
        logger.info("🛑 Stopping pipeline...")
        self._running = False

        await self.scraper.stop()
        await self.alerts.close()
        await self.acled.close()
        await self.rss.close()
        await self.discord.close()

        logger.info(
            f"\n📊 Pipeline Stats:\n"
            f"   Events processed: {self._events_processed}\n"
            f"   High threats detected: {self._high_threats_detected}\n"
            f"   Sources: Telegram + ACLED + RSS + Telescope\n"
        )


async def main():
    """Entry point for the pipeline."""
    pipeline = OSINTPipeline()
    await pipeline.start()


if __name__ == "__main__":
    asyncio.run(main())
