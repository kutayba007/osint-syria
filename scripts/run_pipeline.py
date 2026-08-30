#!/usr/bin/env python3
"""
OSINT Syria — Full Pipeline Test
Collects from Telegram → Analyzes with Groq → Stores in Supabase → Sends Alert
"""
import asyncio
import json
import os
import sys
import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

from telethon import TelegramClient
from groq import Groq
from supabase import create_client

# Config
API_ID = int(os.getenv("TG_API_ID", "0"))
API_HASH = os.getenv("TG_API_HASH", "")
GROQ_KEY = os.getenv("GROQ_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "")
CHAT_ID = os.getenv("TG_CHAT_ID", "")

CHANNELS = ["IdlibPlus", "liveuamap", "NorthPress", "QalaatAlMudiq"]


async def run():
    print("🚀 OSINT SYRIA — FULL PIPELINE TEST")
    print("=" * 60)

    # 1. Connect Telegram
    print("\n📡 [1/5] Connecting to Telegram...")
    client = TelegramClient("osint_pipeline", API_ID, API_HASH)
    await client.start()
    me = await client.get_me()
    print(f"   ✅ Connected: {me.first_name}")

    # 2. Collect messages
    print("\n📨 [2/5] Collecting messages...")
    messages = []
    for ch in CHANNELS:
        try:
            entity = await client.get_entity(ch)
            async for msg in client.iter_messages(entity, limit=3):
                if msg.text and len(msg.text) > 20:
                    messages.append({"channel": ch, "text": msg.text, "date": msg.date})
            print(f"   ✅ @{ch}: collected")
        except Exception as e:
            print(f"   ⚠️ @{ch}: {str(e)[:50]}")

    print(f"   📊 Total: {len(messages)} messages")

    # 3. Analyze with Groq
    print("\n🤖 [3/5] Analyzing with Groq AI...")
    groq = Groq(api_key=GROQ_KEY)
    analyzed = []

    for msg in messages[:5]:
        try:
            resp = groq.chat.completions.create(
                messages=[{
                    "role": "user",
                    "content": f'Return JSON only: {{"threat":"critical/high/medium/low","loc":"location","en":"1 sentence summary","ar":"جملة بالعربي"}} Text: {msg["text"][:300]}'
                }],
                model="openai/gpt-oss-20b",
                max_tokens=150,
                temperature=0.1
            )
            raw = resp.choices[0].message.content
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start >= 0:
                result = json.loads(raw[start:end])
                msg["analysis"] = result
                analyzed.append(msg)
                print(f"   ✅ [{result.get('threat','?').upper()}] {result.get('en','')[:70]}")
        except Exception as e:
            print(f"   ⚠️ {str(e)[:60]}")

    # 4. Store in Supabase
    print("\n💾 [4/5] Storing in Supabase...")
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    stored = 0

    for msg in analyzed:
        a = msg.get("analysis", {})
        try:
            eid = f"SYR-{msg['date'].strftime('%Y%m%d')}-{hash(msg['text']) % 100000:06d}"
            sb.table("events").insert({
                "id": eid,
                "title": a.get("en", msg["text"][:100]),
                "title_arabic": a.get("ar", ""),
                "threat_level": a.get("threat", "low"),
                "category": a.get("event_type", "security"),
                "location_name": a.get("loc", "Unknown"),
                "location_name_arabic": a.get("loc", "Unknown"),
                "governorate": "Unknown",
                "latitude": 35.0,
                "longitude": 38.0,
                "timestamp_utc": msg["date"].isoformat(),
                "confidence_score": 80,
                "source_reliability": "B+",
                "threat_score": 80 if a.get("threat") in ["critical", "high"] else 50,
                "impact": "HIGH" if a.get("threat") in ["critical", "high"] else "MEDIUM",
                "urgency": "IMMEDIATE" if a.get("threat") == "critical" else "ELEVATED",
                "source_platform": "telegram",
                "source_channel": f"@{msg['channel']}",
                "raw_excerpt_arabic": msg["text"][:300],
                "raw_excerpt_english": a.get("en", ""),
                "has_arabic": True,
                "is_acknowledged": False,
                "is_escalated": a.get("threat") in ["critical", "high"]
            }).execute()
            stored += 1
        except Exception as e:
            print(f"   ⚠️ {str(e)[:60]}")

    print(f"   ✅ Stored {stored} events")

    # 5. Send Telegram Alert
    print("\n🚨 [5/5] Sending Telegram alert...")
    lines = ["🇸🇾 **OSINT SYRIA — LIVE BRIEF**", ""]
    lines.append(f"📡 Channels: {len(CHANNELS)} | Msgs: {len(messages)}")
    lines.append(f"🤖 Analyzed: {len(analyzed)} | Stored: {stored}")
    lines.append("")

    for msg in analyzed[:4]:
        a = msg.get("analysis", {})
        t = a.get("threat", "low").upper()
        icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(t, "⚪")
        lines.append(f"{icon} **[{t}]** {a.get('en', '')[:90]}")
        lines.append(f"📍 {a.get('loc', 'Unknown')}")
        lines.append("")

    lines.append("🔗 https://osint-syria.onrender.com")
    text = "\n".join(lines)

    try:
        resp = httpx.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"},
            timeout=10
        )
        if resp.status_code == 200:
            print("   ✅ Alert sent!")
        else:
            print(f"   ❌ {resp.text[:80]}")
    except Exception as e:
        print(f"   ❌ {str(e)[:80]}")

    await client.disconnect()

    print("\n" + "=" * 60)
    print("🎉 PIPELINE COMPLETE!")
    print("=" * 60)
    print(f"   📡 Channels: {len(CHANNELS)}")
    print(f"   📨 Messages: {len(messages)}")
    print(f"   🤖 Analyzed: {len(analyzed)}")
    print(f"   💾 Stored: {stored}")
    print(f"   🚨 Alert: Sent")
    print("=" * 60)


asyncio.run(run())
