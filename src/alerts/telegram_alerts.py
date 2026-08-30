"""
OSINT Syria - Telegram Alert System
Sends instant alerts to the operator for high-threat events.
"""

import logging
import httpx
from datetime import datetime
from typing import Optional

from config.settings import config
from src.models import OSINTEvent, AlertMessage

logger = logging.getLogger("osint.alerts")

# === Alert message templates ===
ALERT_TEMPLATES = {
    "critical": "🚨 *إنذار عاجل — حدث عالي الخطورة* 🚨",
    "high": "⚠️ *تنبيه — حدث مهم* ⚠️",
    "medium": "📌 *تقرير — حدث متوسط الخطورة*",
    "low": "📋 *تقرير — حدث rutinary*",
}

THREAT_EMOJI = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🟢",
}


class TelegramAlerts:
    """
    Sends alerts via Telegram Bot API.
    Free tier: 30 messages/sec to different users (more than enough).
    """

    API_BASE = "https://api.telegram.org"

    def __init__(self):
        self.bot_token = config.telegram.bot_token
        self.chat_id = config.telegram.alert_chat_id
        self._client = httpx.AsyncClient(timeout=10.0)

    @property
    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    async def send_alert(self, event: OSINTEvent) -> bool:
        """Send an alert for a high-threat event."""
        if not self.is_configured:
            logger.warning("⚠️ Telegram alerts not configured — skipping")
            return False

        if event.threat_level not in ("critical", "high"):
            return False

        message = self._format_message(event)

        try:
            url = f"{self.API_BASE}/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            }

            response = await self._client.post(url, json=payload)

            if response.status_code == 200:
                logger.info(f"🚨 Alert sent for event: {event.summary_ar[:40]}")
                return True
            else:
                logger.error(f"❌ Alert API error: {response.status_code} — {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to send alert: {e}")
            return False

    def _format_message(self, event: OSINTEvent) -> str:
        """Format the alert message in Arabic with Markdown."""
        emoji = THREAT_EMOJI.get(event.threat_level, "⚪")
        header = ALERT_TEMPLATES.get(event.threat_level, "📋 *تقرير*")

        location_line = ""
        if event.latitude and event.longitude:
            location_line = f"📍 *الموقع:* {event.location_name} ({event.latitude:.4f}, {event.longitude:.4f})"
        elif event.location_name:
            location_line = f"📍 *الموقع:* {event.location_name}"

        map_link = ""
        if event.latitude and event.longitude:
            map_link = f"🗺 [عرض على الخريطة](https://www.google.com/maps?q={event.latitude},{event.longitude})"

        message = f"""{header}

{emoji} *نوع الحدث:* {event.event_type}
📅 *التاريخ:* {event.timestamp.strftime('%Y-%m-%d %H:%M UTC')}
📢 *المصدر:* @{event.source_channel}

📝 *الملخص:*
{event.summary_ar}

{location_line}
🏛 *المحافظة:* {event.governorate or 'غير محدد'}
🏙 *المدينة:* {event.city or 'غير محدد'}

📊 *مستوى الخطورة:* {event.threat_level.upper()}
🎯 *الثقة:* {event.confidence:.0%}

{map_link}
━━━━━━━━━━━━━━━
🤖 OSINT Syria — Early Warning System"""

        return message

    async def send_startup_message(self):
        """Send a message confirming the system is online."""
        if not self.is_configured:
            return

        message = """✅ *نظام OSINT Syria — تم التشغيل بنجاح* ✅

🕐 *وقت التشغيل:* {time}
📡 *قنوات المراقبة:* {channels}

🔄 النظام يعمل الآن ويراقب القنوات بشكل لحظي.
⚡ سيتم إرسال تنبيهات فورية عند رصد أي أحداث عالية الخطورة.

━━━━━━━━━━━━━━━
🤖 OSINT Syria — Early Warning System"""

        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
        channels_count = len(config.monitored_channels)

        url = f"{self.API_BASE}/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message.format(time=now, channels=channels_count),
            "parse_mode": "Markdown",
        }

        try:
            await self._client.post(url, json=payload)
        except Exception as e:
            logger.error(f"Failed to send startup message: {e}")

    async def send_status_update(self, events_count: int, high_threats: int):
        """Send periodic status update."""
        if not self.is_configured:
            return

        message = """📊 *تقرير الحالة — OSINT Syria*

🕐 *الوقت:* {time}
📨 *أحداث مراقبة:* {total}
🔴 *عالية الخطورة:* {high}

━━━━━━━━━━━━━━━
🤖 OSINT Syria"""

        url = f"{self.API_BASE}/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message.format(
                time=datetime.utcnow().strftime('%H:%M UTC'),
                total=events_count,
                high=high_threats,
            ),
            "parse_mode": "Markdown",
        }

        try:
            await self._client.post(url, json=payload)
        except Exception as e:
            logger.error(f"Failed to send status update: {e}")

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
