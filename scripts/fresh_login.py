#!/usr/bin/env python3
"""
OSINT Syria — Fresh Telegram Login
Requests a new code and verifies it.
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
    api_id = int(os.getenv("TG_API_ID", "0"))
    api_hash = os.getenv("TG_API_HASH", "")
    phone = os.getenv("TG_PHONE_NUMBER", "")

    print(f"\n🇸🇾 OSINT Syria — Fresh Login")
    print(f"{'='*40}\n")

    client = TelegramClient("osint_syria_session", api_id, api_hash)
    
    print("📡 Connecting...")
    await client.connect()
    
    if await client.is_user_authorized():
        me = await client.get_me()
        print(f"✅ Already logged in as: {me.first_name}")
        await client.disconnect()
        return
    
    print("📨 Requesting new verification code...")
    await client.send_code_request(phone)
    print(f"✅ Code sent to {phone}")
    print(f"\n💡 Check your Telegram for the code!\n")
    
    code = input("Enter the code you received: ").strip()
    
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

    # Test channels
    print(f"\n📡 Testing channel access...\n")
    
    for channel in ["syrianews", "SONA_NEWS", "aborejnews"]:
        try:
            entity = await client.get_entity(channel)
            print(f"✅ @{channel} — {entity.title}")
            async for msg in client.iter_messages(entity, limit=2):
                if msg.message:
                    print(f"   📨 {msg.date.strftime('%H:%M')} | {msg.message[:70]}...")
            print()
        except Exception as e:
            print(f"⚠️ @{channel}: {str(e)[:60]}\n")

    print(f"🎉 Telegram integration is WORKING!")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
