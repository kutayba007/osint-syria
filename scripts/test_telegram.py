#!/usr/bin/env python3
"""
OSINT Syria — Telegram Connection Test
Tests Telegram API connection, channel access, and message reading.
Run: python3 scripts/test_telegram.py
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

# Colors for terminal output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def print_header(text):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}{Colors.RESET}\n")


def print_step(num, text):
    print(f"{Colors.BLUE}{Colors.BOLD}[{num}]{Colors.RESET} {text}")


def print_success(text):
    print(f"  {Colors.GREEN}✅ {text}{Colors.RESET}")


def print_error(text):
    print(f"  {Colors.RED}❌ {text}{Colors.RESET}")


def print_warning(text):
    print(f"  {Colors.YELLOW}⚠️  {text}{Colors.RESET}")


def print_info(text):
    print(f"  {Colors.DIM}ℹ️  {text}{Colors.RESET}")


async def test_telegram():
    """Full Telegram connection test."""
    
    print_header("🇸🇾 OSINT Syria — Telegram Connection Test")
    
    # ============================================
    # STEP 1: Check Environment Variables
    # ============================================
    print_step(1, "Checking environment variables...")
    
    api_id = os.getenv("TG_API_ID", "")
    api_hash = os.getenv("TG_API_HASH", "")
    phone = os.getenv("TG_PHONE_NUMBER", "")
    bot_token = os.getenv("TG_BOT_TOKEN", "")
    chat_id = os.getenv("TG_ALERT_CHAT_ID", "")
    
    if not api_id or api_id == "your_api_id_here":
        print_error("TG_API_ID not set!")
        print_info("Get it from: https://my.telegram.org → API Development Tools")
        print_info("Create a .env file with your credentials")
        print_info("Or export them: export TG_API_ID=your_id")
        return False
    else:
        print_success(f"TG_API_ID: {api_id[:4]}...{api_id[-2:]}")
    
    if not api_hash or api_hash == "your_api_hash_here":
        print_error("TG_API_HASH not set!")
        print_info("Get it from: https://my.telegram.org → API Development Tools")
        return False
    else:
        print_success(f"TG_API_HASH: {api_hash[:8]}...")
    
    if not phone or phone == "+963XXXXXXXXX":
        print_warning("TG_PHONE_NUMBER not set (optional for bot-only mode)")
    else:
        print_success(f"TG_PHONE_NUMBER: {phone[:6]}...")
    
    if not bot_token or bot_token == "your_bot_token_here":
        print_warning("TG_BOT_TOKEN not set (needed for alerts)")
        print_info("Create bot: Telegram → @BotFather → /newbot")
    else:
        print_success(f"TG_BOT_TOKEN: {bot_token[:10]}...")
    
    if not chat_id or chat_id == "your_chat_id_here":
        print_warning("TG_ALERT_CHAT_ID not set (needed for alerts)")
        print_info("Get it: Send message to bot → visit api.telegram.org/bot<TOKEN>/getUpdates")
    else:
        print_success(f"TG_ALERT_CHAT_ID: {chat_id}")
    
    # ============================================
    # STEP 2: Test Telegram Client Connection
    # ============================================
    print_step(2, "Connecting to Telegram API...")
    
    try:
        from telethon import TelegramClient
        
        client = TelegramClient(
            "osint_test_session",
            int(api_id),
            api_hash
        )
        
        await client.start(phone=phone)
        me = await client.get_me()
        
        print_success(f"Connected as: {me.first_name} {me.last_name or ''} (@{me.username or 'N/A'})")
        print_success(f"Phone: {me.phone}")
        print_success(f"User ID: {me.id}")
        
    except Exception as e:
        print_error(f"Failed to connect: {e}")
        print_info("Make sure your API credentials are correct")
        return False
    
    # ============================================
    # STEP 3: Test Channel Access
    # ============================================
    print_step(3, "Testing channel access...")
    
    test_channels = [
        "syrianews",
        "syriastories",
        "SONA_NEWS",
        "aborejnews",
    ]
    
    accessible_channels = []
    
    for channel_username in test_channels:
        try:
            entity = await client.get_entity(channel_username)
            accessible_channels.append(entity)
            
            # Get last message
            messages = await client.iter_messages(entity, limit=1).__anext__()
            
            print_success(f"@{channel_username}")
            print_info(f"  Title: {entity.title}")
            print_info(f"  ID: {entity.id}")
            print_info(f"  Last message: {messages.message[:80] if messages.message else 'N/A'}...")
            
        except Exception as e:
            print_warning(f"@{channel_username} — {str(e)[:60]}")
    
    print_info(f"\nAccessible channels: {len(accessible_channels)}/{len(test_channels)}")
    
    # ============================================
    # STEP 4: Test Message Reading
    # ============================================
    if accessible_channels:
        print_step(4, "Reading recent messages...")
        
        for entity in accessible_channels[:2]:  # Test first 2 channels
            print_info(f"\n{Colors.CYAN}Messages from @{entity.username or entity.title}:{Colors.RESET}")
            
            count = 0
            async for message in client.iter_messages(entity, limit=5):
                if message.message:
                    count += 1
                    timestamp = message.date.strftime("%Y-%m-%d %H:%M")
                    text_preview = message.message[:120].replace("\n", " ")
                    
                    # Color based on content
                    if any(kw in text_preview.lower() for kw in ["قصف", "اشتباكات", "انفجار", "استهداف"]):
                        color = Colors.RED
                    elif any(kw in text_preview.lower() for kw in ["عاجل", "توتر", "حركة"]):
                        color = Colors.YELLOW
                    else:
                        color = Colors.DIM
                    
                    print(f"  {Colors.DIM}{timestamp}{Colors.RESET} | {color}{text_preview}...{Colors.RESET}")
            
            if count == 0:
                print_warning("No readable messages found")
            else:
                print_success(f"Read {count} messages successfully")
    
    # ============================================
    # STEP 5: Test Bot API (if configured)
    # ============================================
    if bot_token and bot_token != "your_bot_token_here":
        print_step(5, "Testing Telegram Bot API...")
        
        import httpx
        
        try:
            async with httpx.AsyncClient() as http:
                # Test bot info
                response = await http.get(f"https://api.telegram.org/bot{bot_token}/getMe")
                data = response.json()
                
                if data.get("ok"):
                    bot_info = data["result"]
                    print_success(f"Bot: @{bot_info['username']}")
                    print_success(f"Name: {bot_info['first_name']}")
                    print_success(f"ID: {bot_info['id']}")
                    
                    # Test sending message
                    if chat_id and chat_id != "your_chat_id_here":
                        print_info("Sending test message...")
                        
                        test_msg = {
                            "chat_id": chat_id,
                            "text": f"🇸🇾 OSINT Syria Test\n\n✅ Telegram connection successful!\n🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n\nThis is a test message from the OSINT pipeline.",
                            "parse_mode": "HTML",
                        }
                        
                        send_response = await http.post(
                            f"https://api.telegram.org/bot{bot_token}/sendMessage",
                            json=test_msg
                        )
                        send_data = send_response.json()
                        
                        if send_data.get("ok"):
                            print_success("Test message sent successfully!")
                        else:
                            print_error(f"Failed to send: {send_data.get('description', 'Unknown error')}")
                    else:
                        print_warning("Chat ID not set — skipping message test")
                else:
                    print_error(f"Bot API error: {data.get('description', 'Unknown')}")
                    
        except Exception as e:
            print_error(f"Bot API test failed: {e}")
    else:
        print_step(5, "Bot API test (skipped — no token)")
        print_info("Set TG_BOT_TOKEN to enable bot testing")
    
    # ============================================
    # STEP 6: Disconnect
    # ============================================
    print_step(6, "Disconnecting...")
    await client.disconnect()
    print_success("Clean disconnect")
    
    # ============================================
    # SUMMARY
    # ============================================
    print_header("📊 TEST SUMMARY")
    print(f"  {Colors.GREEN}✅ Telegram API connection: WORKING{Colors.RESET}")
    print(f"  {Colors.GREEN}✅ Channel access: {len(accessible_channels)} channels{Colors.RESET}")
    if bot_token and bot_token != "your_bot_token_here":
        print(f"  {Colors.GREEN}✅ Bot API: CONFIGURED{Colors.RESET}")
    else:
        print(f"  {Colors.YELLOW}⚠️  Bot API: NOT CONFIGURED{Colors.RESET}")
    print(f"\n  {Colors.CYAN}Next steps:{Colors.RESET}")
    print(f"  1. Add credentials to .env file")
    print(f"  2. Run: python3 -m src.pipeline")
    print(f"  3. Run: streamlit run dashboard/app.py")
    print()
    
    return True


if __name__ == "__main__":
    try:
        asyncio.run(test_telegram())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test cancelled by user{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Test failed: {e}{Colors.RESET}")
        sys.exit(1)
