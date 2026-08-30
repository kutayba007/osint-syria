"""
OSINT Syria - Telegram Channel Scraper
Real-time monitoring of public Telegram channels using Telethon.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, AsyncGenerator

from telethon import TelegramClient, events
from telethon.tl.types import Message

from config.settings import config
from src.models import OSINTEvent

logger = logging.getLogger("osint.scraper")


class TelegramScraper:
    """
    Scrapes public Telegram channels in real-time.
    Uses Telethon's Event system to listen for new messages.
    """

    def __init__(self):
        self.client = TelegramClient(
            "osint_syria_session",
            config.telegram.api_id,
            config.telegram.api_hash
        )
        self._running = False
        self._seen_ids: set = set()
        self._message_queue: asyncio.Queue = asyncio.Queue()

    async def start(self):
        """Start the Telegram client and begin monitoring."""
        await self.client.start(phone=config.telegram.phone)
        self._running = True
        logger.info("✅ Telegram Scraper connected successfully")

        # Register event handlers for all monitored channels
        for channel_url in config.monitored_channels:
            username = channel_url.split("/")[-1]
            try:
                entity = await self.client.get_entity(username)
                self.client.add_event_handler(
                    self._handle_new_message,
                    events.NewMessage(chats=entity)
                )
                logger.info(f"📡 Monitoring: @{username}")
            except Exception as e:
                logger.warning(f"⚠️ Could not monitor @{username}: {e}")

        logger.info("🔄 Telegram Scraper is running — waiting for messages...")

    async def _handle_new_message(self, event: events.NewMessage.Event):
        """Handle incoming messages from monitored channels."""
        msg: Message = event.message
        if msg.id in self._seen_ids:
            return

        self._seen_ids.add(msg.id)

        # Extract media URLs
        media_urls = []
        if msg.media:
            if hasattr(msg.media, 'photo'):
                media_urls.append(f"photo_{msg.id}")
            elif hasattr(msg.media, 'document'):
                media_urls.append(f"doc_{msg.id}")

        # Build the event
        osint_event = OSINTEvent(
            raw_text=msg.message or "",
            source_channel=str(event.chat.username or event.chat.title),
            timestamp=msg.date,
            media_urls=media_urls,
            source_message_id=msg.id,
        )

        await self._message_queue.put(osint_event)
        logger.info(f"📩 New message from @{osint_event.source_channel}: {osint_event.raw_text[:80]}...")

    async def get_message(self) -> Optional[OSINTEvent]:
        """Get next message from the queue."""
        try:
            return await asyncio.wait_for(
                self._message_queue.get(),
                timeout=1.0
            )
        except asyncio.TimeoutError:
            return None

    async def fetch_history(self, channel_username: str, limit: int = 50) -> List[OSINTEvent]:
        """Fetch recent message history from a channel."""
        events_list = []
        try:
            async for msg in self.client.iter_messages(channel_username, limit=limit):
                if msg.message:  # Skip empty messages
                    events_list.append(OSINTEvent(
                        raw_text=msg.message,
                        source_channel=channel_username,
                        timestamp=msg.date,
                        source_message_id=msg.id,
                    ))
        except Exception as e:
            logger.error(f"❌ Error fetching history from @{channel_username}: {e}")

        return events_list

    async def stop(self):
        """Gracefully stop the scraper."""
        self._running = False
        await self.client.disconnect()
        logger.info("🛑 Telegram Scraper stopped")

    @property
    def is_running(self) -> bool:
        return self._running
