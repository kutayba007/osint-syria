#!/usr/bin/env python3
"""
OSINT Syria — Health Check Script
Verifies all system components are operational.
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

# Colors
G = "\033[92m"  # Green
R = "\033[91m"  # Red
Y = "\033[93m"  # Yellow
C = "\033[96m"  # Cyan
B = "\033[1m"   # Bold
X = "\033[0m"   # Reset


def check(name, func):
    """Run a check and print result."""
    try:
        result = func()
        if result:
            print(f"  {G}✅ {name}: {result}{X}")
        else:
            print(f"  {G}✅ {name}: OK{X}")
        return True
    except Exception as e:
        print(f"  {R}❌ {name}: {str(e)[:80]}{X}")
        return False


def main():
    print(f"\n{C}{B}{'='*60}")
    print(f"  🇸🇾 OSINT Syria — Health Check")
    print(f"{'='*60}{X}\n")
    
    results = {}
    
    # 1. Environment Variables
    print(f"{B}[1/7] Environment Variables{X}")
    results["env"] = check("TG_API_ID", lambda: os.getenv("TG_API_ID", "")[:4] + "...")
    check("TG_API_HASH", lambda: os.getenv("TG_API_HASH", "")[:8] + "...")
    check("TG_PHONE", lambda: os.getenv("TG_PHONE_NUMBER", "")[:6] + "...")
    check("TG_BOT_TOKEN", lambda: "Configured" if os.getenv("TG_BOT_TOKEN") else None)
    check("TG_CHAT_ID", lambda: os.getenv("TG_ALERT_CHAT_ID", ""))
    check("GROQ_API_KEY", lambda: "Configured" if os.getenv("GROQ_API_KEY") else "Not set (optional)")
    check("SUPABASE_URL", lambda: "Configured" if os.getenv("SUPABASE_URL") else "Not set (optional)")
    print()
    
    # 2. Python Packages
    print(f"{B}[2/7] Python Packages{X}")
    packages = ["telethon", "groq", "geopy", "supabase", "fastapi", "uvicorn", "pydantic", "httpx"]
    for pkg in packages:
        try:
            __import__(pkg)
            check(pkg, lambda: "Installed")
        except ImportError:
            check(pkg, lambda: (_ for _ in ()).throw(Exception("NOT INSTALLED")))
    print()
    
    # 3. Telegram Connection
    print(f"{B}[3/7] Telegram Connection{X}")
    try:
        import asyncio
        from telethon import TelegramClient
        
        async def test_telegram():
            api_id = int(os.getenv("TG_API_ID", "0"))
            api_hash = os.getenv("TG_API_HASH", "")
            phone = os.getenv("TG_PHONE_NUMBER", "")
            
            client = TelegramClient("osint_syria_health_check", api_id, api_hash)
            await client.start(phone=phone)
            me = await client.get_me()
            await client.disconnect()
            return f"{me.first_name} @{me.username} (ID: {me.id})"
        
        check("Telegram User API", lambda: asyncio.run(test_telegram()))
    except Exception as e:
        check("Telegram User API", lambda: (_ for _ in ()).throw(e))
    print()
    
    # 4. Telegram Bot
    print(f"{B}[4/7] Telegram Bot{X}")
    try:
        import httpx
        
        def test_bot():
            token = os.getenv("TG_BOT_TOKEN", "")
            if not token:
                raise Exception("Bot token not configured")
            
            resp = httpx.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
            data = resp.json()
            if data.get("ok"):
                return f"@{data['result']['username']}"
            raise Exception(data.get("description", "Unknown error"))
        
        check("Bot API", test_bot)
        
        # Test sending message
        def test_send():
            token = os.getenv("TG_BOT_TOKEN", "")
            chat_id = os.getenv("TG_ALERT_CHAT_ID", "")
            if not token or not chat_id:
                raise Exception("Bot token or chat ID not configured")
            
            resp = httpx.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": "🛰️ Health Check: System operational!"},
                timeout=10
            )
            data = resp.json()
            if data.get("ok"):
                return "Test message sent!"
            raise Exception(data.get("description", "Unknown error"))
        
        check("Bot Send Message", test_send)
    except Exception as e:
        check("Telegram Bot", lambda: (_ for _ in ()).throw(e))
    print()
    
    # 5. Geocoder
    print(f"{B}[5/7] Geocoder (Nominatim){X}")
    try:
        from geopy.geocoders import Nominatim
        
        def test_geocoder():
            geo = Nominatim(user_agent="osint_syria_health_check")
            loc = geo.geocode("دمشق, سوريا", timeout=10)
            if loc:
                return f"دمشق: {loc.latitude:.4f}, {loc.longitude:.4f}"
            raise Exception("Could not geocode Damascus")
        
        check("Nominatim Geocoder", test_geocoder)
    except Exception as e:
        check("Nominatim Geocoder", lambda: (_ for _ in ()).throw(e))
    print()
    
    # 6. Telescope Detector
    print(f"{B}[6/7] Telescope Threat Detector{X}")
    try:
        from src.sources.telescope_detector import TelescopeDetector
        
        def test_telescope():
            detector = TelescopeDetector()
            result = detector.scan_text("قصف جوي مكثف على ريف إدلب الغربي")
            return f"{len(result['matches'])} rules matched, threat: {result['threat_level']}"
        
        check("Telescope Rules", test_telescope)
    except Exception as e:
        check("Telescope Rules", lambda: (_ for _ in ()).throw(e))
    print()
    
    # 7. File Structure
    print(f"{B}[7/7] Project Structure{X}")
    required_files = [
        "config/settings.py",
        "src/pipeline.py",
        "src/api.py",
        "src/models.py",
        "src/scraper/telegram_scraper.py",
        "src/analyzer/groq_analyzer.py",
        "src/geocoder/syria_geocoder.py",
        "src/database/supabase_client.py",
        "src/alerts/telegram_alerts.py",
        "src/sources/acled_source.py",
        "src/sources/telescope_detector.py",
        "src/sources/rss_feeds.py",
        "src/sources/discord_webhook.py",
        "dashboard/app.py",
        ".env",
    ]
    
    missing = []
    for f in required_files:
        full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), f)
        if os.path.exists(full_path):
            check(f, lambda: "Exists")
        else:
            check(f, lambda: (_ for _ in ()).throw(Exception("MISSING")))
            missing.append(f)
    print()
    
    # Summary
    print(f"{C}{B}{'='*60}")
    print(f"  🏁 HEALTH CHECK COMPLETE")
    print(f"{'='*60}{X}\n")
    
    if not missing:
        print(f"  {G}✅ All systems operational!{X}")
    else:
        print(f"  {Y}⚠️  Missing files: {', '.join(missing)}{X}")
    
    print(f"\n  {C}Ready to launch: python3 -m src.pipeline{X}\n")


if __name__ == "__main__":
    main()
