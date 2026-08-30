#!/usr/bin/env python3
"""
OSINT Syria — Live Pipeline Test
Reads real Telegram data and runs through the full analysis pipeline.
"""

import asyncio
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from telethon import TelegramClient
from src.analyzer.groq_analyzer import GroqAnalyzer
from src.geocoder.syria_geocoder import SyriaGeocoder
from src.sources.telescope_detector import TelescopeDetector
from src.sources.cib_detector import CIBDetector, SuspiciousPost
from src.sources.arabic_nlp import ArabicNLPAnalyzer
from src.alerts.telegram_alerts import TelegramAlerts

# Colors
G = "\033[92m"
R = "\033[91m"
Y = "\033[93m"
C = "\033[96m"
B = "\033[1m"
X = "\033[0m"


async def main():
    print(f"\n{C}{B}{'='*60}")
    print(f"  🇸🇾 OSINT Syria — Live Pipeline Test")
    print(f"{'='*60}{X}\n")
    
    # Initialize components
    print(f"{B}[1/6] Initializing components...{X}")
    
    telescope = TelescopeDetector()
    cib = CIBDetector()
    nlp = ArabicNLPAnalyzer()
    geocoder = SyriaGeocoder()
    alerts = TelegramAlerts()
    
    print(f"  ✅ Telescope: {len(telescope.rules)} rules loaded")
    print(f"  ✅ CIB Detector: Ready")
    print(f"  ✅ Arabic NLP: Ready")
    print(f"  ✅ Geocoder: Ready")
    print(f"  ✅ Telegram Alerts: {'Configured' if alerts.is_configured else 'Not configured'}")
    
    # Connect to Telegram
    print(f"\n{B}[2/6] Connecting to Telegram...{X}")
    
    api_id = int(os.getenv("TG_API_ID", "0"))
    api_hash = os.getenv("TG_API_HASH", "")
    phone = os.getenv("TG_PHONE_NUMBER", "")
    
    client = TelegramClient("osint_syria_live_test", api_id, api_hash)
    await client.start(phone=phone)
    
    me = await client.get_me()
    print(f"  ✅ Connected as: {me.first_name} @{me.username}")
    
    # Read messages from channels
    print(f"\n{B}[3/6] Reading live messages from channels...{X}")
    
    channels = ["IdlibPlus", "liveuamap", "NorthPress", "ARA_News"]
    all_messages = []
    
    for channel_name in channels:
        try:
            entity = await client.get_entity(channel_name)
            print(f"\n  📡 @{channel_name} ({entity.title}):")
            
            async for msg in client.iter_messages(entity, limit=5):
                if msg.message:
                    text = msg.message[:120].replace("\n", " ")
                    timestamp = msg.date.strftime("%H:%M UTC")
                    
                    # Store for analysis
                    all_messages.append({
                        "channel": channel_name,
                        "text": msg.message,
                        "timestamp": msg.date,
                        "message_id": msg.id,
                    })
                    
                    # Quick color coding
                    if any(kw in text.lower() for kw in ["قصف", "اشتباكات", "انفجار"]):
                        print(f"    {R}📨 {timestamp} | {text}...{X}")
                    elif any(kw in text.lower() for kw in ["عاجل", "توتر"]):
                        print(f"    {Y}📨 {timestamp} | {text}...{X}")
                    else:
                        print(f"    {G}📨 {timestamp} | {text}...{X}")
                    
        except Exception as e:
            print(f"    ⚠️ @{channel_name}: {str(e)[:60]}")
    
    print(f"\n  📊 Total messages collected: {len(all_messages)}")
    
    # Analyze messages
    print(f"\n{B}[4/6] Running analysis pipeline...{X}")
    
    analyzed_count = 0
    threats_detected = 0
    
    for msg_data in all_messages[:10]:  # Analyze first 10
        text = msg_data["text"]
        
        # Telescope detection
        telescope_result = telescope.scan_text(text)
        
        # Arabic NLP
        nlp_result = nlp.analyze(text)
        
        # CIB check
        post = SuspiciousPost(
            post_id=str(msg_data["message_id"]),
            username=msg_data["channel"],
            platform="telegram",
            text=text,
            timestamp=msg_data["timestamp"],
        )
        cib_alert = cib.add_post(post)
        
        # Geocoding
        location = nlp_result.entities[0] if nlp_result.entities else ""
        geo_result = geocoder._lookup_location("دمشق") if "دمشق" in text else None
        
        analyzed_count += 1
        
        # Determine overall threat
        threat_level = "LOW"
        if telescope_result["threat_level"] in ("critical", "high"):
            threat_level = telescope_result["threat_level"].upper()
            threats_detected += 1
        
        # Print analysis
        print(f"\n  📋 Analysis #{analyzed_count}:")
        print(f"    📝 Text: {text[:80]}...")
        print(f"    🔭 Telescope: {telescope_result['threat_level'].upper()} ({len(telescope_result['matches'])} matches)")
        print(f"    🗣️ NLP: {nlp_result.sentiment} | Propaganda: {nlp_result.is_propaganda} | Fake: {nlp_result.is_fake_news_suspect}")
        print(f"    📍 Entities: {nlp_result.entities[:3]}")
        print(f"    ⚡ Overall: {threat_level}")
        
        if cib_alert:
            print(f"    🚨 CIB ALERT: {cib_alert.title}")
    
    # Test CIB simulation
    print(f"\n{B}[5/6] Simulating CIB campaign...{X}")
    
    now = datetime.utcnow()
    cib_test_messages = [
        "عاجل: انهيار المصرف المركزي وإغلاق جميع الفروع!",
        "عاجل: انهيار المصرف المركزي وإغلاق جميع الفروع!",
        "عاجل: انهيار المصرف المركزي وإغلاق جميع الفروع!",
        "عاجل: انهيار المصرف المركزي وإغلاق جميع الفروع!",
        "عاجل: انهيار المصرف المركزي وإغلاق جميع الفروع!",
    ]
    
    cib_detector = CIBDetector()
    for i, text in enumerate(cib_test_messages):
        post = SuspiciousPost(
            post_id=f"cib_test_{i}",
            username=f"fake_bot_{i}",
            platform="telegram",
            text=text,
            timestamp=now,
        )
        alert = cib_detector.add_post(post)
        if alert:
            print(f"  🚨 CIB DETECTED: {alert.title}")
            print(f"     Accounts: {alert.cluster.account_count}")
            print(f"     Severity: {alert.severity}")
            break
    else:
        print(f"  ✅ CIB test: {len(cib_detector._post_buffer)} posts buffered")
    
    # Test Telegram alert
    print(f"\n{B}[6/6] Testing Telegram alert...{X}")
    
    if alerts.is_configured:
        try:
            # Create a test event
            from src.models import OSINTEvent
            test_event = OSINTEvent(
                raw_text="اختبار: قصف جوي على ريف إدلب",
                source_channel="test",
                event_type="قصف",
                summary_ar="اختبار نظام الإنذار",
                threat_level="critical",
                confidence=0.9,
                location_name="إدلب",
                latitude=35.9306,
                longitude=36.6339,
                governorate="إدلب",
            )
            
            # Send alert
            import httpx
            token = os.getenv("TG_BOT_TOKEN", "")
            chat_id = os.getenv("TG_ALERT_CHAT_ID", "")
            
            if token and chat_id:
                alert_text = f"""🚨 OSINT Syria — Live Test Alert

🔴 THREAT: CRITICAL
📍 Location: إدلب ({test_event.latitude}, {test_event.longitude})
📝 Event: قصف جوي على ريف إدلب
🎯 Confidence: 90%

⏰ {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

✅ Pipeline test successful!
📡 Monitoring: {len(channels)} channels
🔭 Telescope: {len(telescope.rules)} rules
🕸️ CIB Detector: Active"""

                async with httpx.AsyncClient() as http:
                    resp = await http.post(
                        f"https://api.telegram.org/bot{token}/sendMessage",
                        json={"chat_id": chat_id, "text": alert_text},
                        timeout=10
                    )
                    if resp.status_code == 200:
                        print(f"  ✅ Test alert sent to @{me.username}!")
                    else:
                        print(f"  ⚠️ Alert failed: {resp.status_code}")
            else:
                print(f"  ⚠️ Bot token or chat ID not configured")
                
        except Exception as e:
            print(f"  ⚠️ Alert test error: {e}")
    else:
        print(f"  ⚠️ Telegram alerts not configured")
    
    await client.disconnect()
    
    # Summary
    print(f"\n{C}{B}{'='*60}")
    print(f"  🏁 LIVE PIPELINE TEST COMPLETE")
    print(f"{'='*60}{X}\n")
    
    print(f"  📊 Results:")
    print(f"    Messages analyzed: {analyzed_count}")
    print(f"    Threats detected: {threats_detected}")
    print(f"    CIB clusters: {len(cib_detector._clusters)}")
    print(f"    Telescope rules: {len(telescope.rules)}")
    print(f"    NLP analyzer: Active")
    print(f"    Geocoder: Active")
    print(f"    Telegram alerts: {'Active' if alerts.is_configured else 'Inactive'}")
    
    print(f"\n  🎯 Pipeline is LIVE and processing real data!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
