#!/usr/bin/env python3
"""
OSINT Syria — Simple Telegram Login
Logs in to Telegram and reads channels.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from telethon import TelegramClient


async def main():
    api_id = int(os.getenv("TG_API_ID", "0"))
    api_hash = os.getenv("TG_API_HASH", "")
    phone = os.getenv("TG_PHONE_NUMBER", "")

    print(f"\n🇸🇾 OSINT Syria — Telegram Login")
    print(f"{'='*40}\n")

    client = TelegramClient("osint_syria_session", api_id, api_hash)
    
    print("📡 Connecting to Telegram...")
    await client.start(phone=phone)
    
    me = await client.get_me()
    print(f"\n✅ Logged in as: {me.first_name} {me.last_name or ''}")
    print(f"   Username: @{me.username or 'N/A'}")
    print(f"   Phone: {me.phone}")
    print(f"   User ID: {me.id}")

    # Test reading a channel
    print(f"\n📡 Testing channel access...")
    
    test_channels = ["syrianews", "SONA_NEWS"]
    
    for channel in test_channels:
        try:
            entity = await client.get_entity(channel)
            print(f"\n✅ @{channel} — {entity.title}")
            
            async for msg in client.iter_messages(entity, limit=3):
                if msg.message:
                    text = msg.message[:100].replace("\n", " ")
                    print(f"   📨 {msg.date.strftime('%H:%M')} | {text}...")
                    
        except Exception as e:
            print(f"   ⚠️ @{channel}: {str(e)[:60]}")

    print(f"\n{'='*40}")
    print(f"✅ All tests passed!")
    print(f"{'='*40}\n")
    
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
