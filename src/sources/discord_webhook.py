"""
OSINT Syria — Discord Integration
Sends alerts and reports to Discord channels via webhooks.
Free tier: 50 messages/second per webhook — more than enough.
"""

import logging
import httpx
from datetime import datetime
from typing import Optional, List, Dict

from src.models import OSINTEvent

logger = logging.getLogger("osint.sources.discord")

THREAT_COLORS = {
    "critical": 0xEF4444,  # Red
    "high": 0xF97316,      # Orange
    "medium": 0xF59E0B,    # Amber
    "low": 0x06B6D4,       # Cyan
    "disinfo": 0xA855F7,   # Purple
}

THREAT_EMOJI = {
    "critical": "🚨",
    "high": "⚠️",
    "medium": "📌",
    "low": "📋",
    "disinfo": "🕸️",
}


class DiscordWebhook:
    """
    Discord webhook integration for OSINT alerts.
    Free and easy to set up.
    
    Setup:
    1. Create Discord server (or use existing)
    2. Create channel #osint-alerts
    3. Edit Channel → Integrations → Webhooks → New Webhook
    4. Copy webhook URL to .env as DISCORD_WEBHOOK_URL
    """

    def __init__(self, webhook_url: str = ""):
        self.webhook_url = webhook_url
        self.client = httpx.AsyncClient(timeout=10.0)

    @property
    def is_configured(self) -> bool:
        return bool(self.webhook_url)

    async def send_alert(self, event: OSINTEvent) -> bool:
        """Send an incident alert to Discord."""
        if not self.is_configured:
            return False

        if event.threat_level not in ("critical", "high", "disinfo"):
            return False

        emoji = THREAT_EMOJI.get(event.threat_level, "📋")
        color = THREAT_COLORS.get(event.threat_level, 0x06B6D4)

        embed = {
            "title": f"{emoji} {event.summary_ar or event.summary_en[:100]}",
            "description": event.summary_en[:300] if event.summary_en else event.raw_text[:300],
            "color": color,
            "fields": [
                {"name": "📍 Location", "value": event.location_name or "Unknown", "inline": True},
                {"name": "🏛 Governorate", "value": event.governorate or "Unknown", "inline": True},
                {"name": "⚠️ Threat Level", "value": event.threat_level.upper(), "inline": True},
                {"name": "🎯 Confidence", "value": f"{event.confidence:.0%}", "inline": True},
                {"name": "📢 Source", "value": f"@{event.source_channel}", "inline": True},
                {"name": "🕐 Time (UTC)", "value": event.timestamp.strftime("%H:%M UTC"), "inline": True},
            ],
            "footer": {"text": "OSINT Syria — Early Warning System"},
            "timestamp": event.timestamp.isoformat(),
        }

        if event.latitude and event.longitude:
            embed["url"] = f"https://www.google.com/maps?q={event.latitude},{event.longitude}"

        payload = {"embeds": [embed]}

        try:
            response = await self.client.post(self.webhook_url, json=payload)
            if response.status_code in (200, 204):
                logger.info(f"📨 Discord alert sent: {event.summary_ar[:40]}")
                return True
            else:
                logger.warning(f"⚠️ Discord webhook error: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Discord alert failed: {e}")
            return False

    async def send_batch_alerts(self, events: List[OSINTEvent]) -> int:
        """Send multiple alerts. Returns count of successful sends."""
        count = 0
        for event in events:
            if await self.send_alert(event):
                count += 1
            # Rate limit: max 50/sec
            if count % 10 == 0:
                import asyncio
                await asyncio.sleep(0.1)
        return count

    async def send_daily_summary(self, stats: Dict) -> bool:
        """Send a daily summary report to Discord."""
        if not self.is_configured:
            return False

        embed = {
            "title": "📊 OSINT Syria — Daily Summary",
            "description": f"Report for {datetime.utcnow().strftime('%Y-%m-%d')}",
            "color": 0x06B6D4,
            "fields": [
                {"name": "📨 Total Events", "value": str(stats.get("total", 0)), "inline": True},
                {"name": "🔴 Critical", "value": str(stats.get("critical", 0)), "inline": True},
                {"name": "🟠 High", "value": str(stats.get("high", 0)), "inline": True},
                {"name": "🟡 Medium", "value": str(stats.get("medium", 0)), "inline": True},
                {"name": "🟢 Low", "value": str(stats.get("low", 0)), "inline": True},
                {"name": "🕸️ Disinfo", "value": str(stats.get("disinfo", 0)), "inline": True},
            ],
            "footer": {"text": "OSINT Syria — Automated Daily Report"},
        }

        payload = {"embeds": [embed]}

        try:
            response = await self.client.post(self.webhook_url, json=payload)
            return response.status_code in (200, 204)
        except Exception:
            return False

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
