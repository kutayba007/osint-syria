#!/usr/bin/env python3
"""
OSINT Syria — Verify Telegram Code
Usage: python3 scripts/verify_code.py 53833
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError


async def main():
    code = sys.argv[1] if len(sys.argv) > 1 else input("Enter verification code: ")
    
    api_id = int(os.getenv("TG_API_ID", "0"))
    api_hash = os.getenv("TG_API_HASH", "")
    phone = os.getenv("TG_PHONE_NUMBER", "")

    print(f"\n🇸🇾 OSINT Syria — Verifying Code: {code}")
    print(f"{'='*40}\n")

    client = TelegramClient("osint_syria_session", api_id, api_hash)
    
    print("📡 Connecting...")
    await client.connect()
    
    if not await client.is_user_authorized():
        print("📨 Sending code request...")
        await client.send_code_request(phone)
        
        print("🔑 Signing in...")
        try:
            await client.sign_in(phone, code)
        except SessionPasswordNeededError:
            password = input("Two-factor auth enabled. Enter password: ")
            await client.sign_in(password=password)
    
    me = await client.get_me()
    print(f"\n✅ SUCCESS! Logged in as:")
    print(f"   Name: {me.first_name} {me.last_name or ''}")
    print(f"   Username: @{me.username or 'N/A'}")
    print(f"   Phone: {me.phone}")
    print(f"   User ID: {me.id}")

    # Test reading channels
    print(f"\n📡 Testing channel access...\n")
    
    test_channels = ["syrianews", "SONA_NEWS", "aborejnews"]
    
    for channel in test_channels:
        try:
            entity = await client.get_entity(channel)
            print(f"✅ @{channel} — {entity.title}")
            
            async for msg in client.iter_messages(entity, limit=2):
                if msg.message:
                    text = msg.message[:80].replace("\n", " ")
                    print(f"   📨 {msg.date.strftime('%H:%M UTC')} | {text}...")
            print()
                    
        except Exception as e:
            print(f"⚠️ @{channel}: {str(e)[:60]}\n")

    print(f"{'='*40}")
    print(f"🎉 Telegram integration is WORKING!")
    print(f"{'='*40}\n")
    
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
