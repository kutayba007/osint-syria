#!/usr/bin/env python3
"""
OSINT Syria — Final Pipeline
47 Channels + Translation + Supabase + Telegram Alerts
"""
import asyncio, os, sys, json, time, httpx

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv('.env')

from telethon import TelegramClient
from groq import Groq
from supabase import create_client
from config.channels import CHANNEL_USERNAMES, HIGH_PRIORITY

API_ID = int(os.getenv('TG_API_ID'))
API_HASH = os.getenv('TG_API_HASH')
GROQ_KEY = os.getenv('GROQ_API_KEY')
SB_URL = os.getenv('SUPABASE_URL')
SB_KEY = os.getenv('SUPABASE_KEY')
BOT = os.getenv('TG_BOT_TOKEN')
CHAT = os.getenv('TG_CHAT_ID')

CHANNELS = CHANNEL_USERNAMES
POLL_INTERVAL = 30
seen_ids = set()

PROMPT = """Analyze this OSINT text and return JSON ONLY:
{
    "threat": "critical/high/medium/low",
    "loc": "location name",
    "en": "brief English summary (1 sentence)",
    "ar": "ملخص مختصر بالعربي (جملة واحدة)",
    "type": "event type"
}
Be factual. Text: """


def send_alert(alerts):
    if not alerts:
        return
    lines = ['🚨 **OSINT SYRIA — HIGH THREAT ALERT**\n']
    for m in alerts[:5]:
        a = m.get('a', {})
        t = a.get('threat', '?').upper()
        i = {'CRITICAL': '🔴', 'HIGH': '🟠'}.get(t, '⚪')
        lines.append(f'{i} **[{t}]** @{m["ch"]}')
        lines.append(f'🇬🇧 {a.get("en", "")[:100]}')
        lines.append(f'🇸🇦 {a.get("ar", "")[:100]}')
        lines.append(f'📍 {a.get("loc", "?")}\n')
    lines.append(f'📊 {len(alerts)} alerts | 🔗 osint-syria.onrender.com')
    try:
        httpx.post(f'https://api.telegram.org/bot{BOT}/sendMessage',
                   json={'chat_id': CHAT, 'text': '\n'.join(lines)}, timeout=10)
    except:
        pass


async def run_once(client, groq, sb):
    global seen_ids
    msgs, alerts = [], []

    for ch in CHANNELS:
        try:
            ent = await client.get_entity(ch)
            async for m in client.iter_messages(ent, limit=2):
                mid = f'{ch}_{m.id}'
                if m.text and len(m.text) > 20 and mid not in seen_ids:
                    seen_ids.add(mid)
                    msgs.append({'ch': ch, 'text': m.text, 'date': m.date})
        except:
            pass

    if not msgs:
        return 0, 0, []

    analyzed = []
    for m in msgs[:8]:
        try:
            r = groq.chat.completions.create(
                messages=[{'role': 'user', 'content': PROMPT + m['text'][:400]}],
                model='openai/gpt-oss-20b', max_tokens=500, temperature=0.1
            )
            raw = r.choices[0].message.content
            s, e = raw.find('{'), raw.rfind('}') + 1
            if s >= 0:
                a = json.loads(raw[s:e])
                m['a'] = a
                analyzed.append(m)
        except:
            pass

    stored = 0
    for m in analyzed:
        a = m.get('a', {})
        try:
            sb.table('events').insert({
                'id': f'SYR-{m["date"].strftime("%Y%m%d")}-{hash(m["text"])%100000:06d}',
                'title': a.get('en', ''), 'title_arabic': a.get('ar', ''),
                'threat_level': a.get('threat', 'low'), 'category': a.get('type', 'security'),
                'location_name': a.get('loc', 'Unknown'), 'location_name_arabic': a.get('loc', ''),
                'governorate': 'Unknown', 'latitude': 35.0, 'longitude': 38.0,
                'timestamp_utc': m['date'].isoformat(), 'confidence_score': 80,
                'source_reliability': 'B+', 'threat_score': 80,
                'impact': 'HIGH' if a.get('threat') in ['critical','high'] else 'MEDIUM',
                'urgency': 'IMMEDIATE' if a.get('threat')=='critical' else 'ELEVATED',
                'source_platform': 'telegram', 'source_channel': f'@{m["ch"]}',
                'raw_excerpt_arabic': m['text'][:300], 'raw_excerpt_english': a.get('en',''),
                'has_arabic': True, 'is_acknowledged': False,
                'is_escalated': a.get('threat') in ['critical','high']
            }).execute()
            stored += 1
        except:
            pass

    for m in analyzed:
        a = m.get('a', {})
        if a.get('threat') in ['critical', 'high']:
            alerts.append(m)

    return len(msgs), stored, alerts


async def main():
    print(f'🚀 OSINT SYRIA — FINAL PIPELINE')
    print(f'📡 {len(CHANNELS)} channels | ⏱️ every {POLL_INTERVAL}s')
    print('=' * 60)

    client = TelegramClient('osint_final', API_ID, API_HASH)
    await client.start()
    me = await client.get_me()
    print(f'✅ Connected: {me.first_name}\n')

    groq = Groq(api_key=GROQ_KEY)
    sb = create_client(SB_URL, SB_KEY)

    cycle = 0
    while True:
        cycle += 1
        try:
            n, stored, alerts = await run_once(client, groq, sb)
            ts = time.strftime('%H:%M:%S')
            if n > 0:
                a = f' | 🚨 {len(alerts)} ALERTS' if alerts else ''
                print(f'[{ts}] Cycle {cycle}: 📨 {n} | 💾 {stored}{a}')
                for m in alerts[:3]:
                    x = m.get('a', {})
                    print(f'  🇬🇧 {x.get("en","")[:70]}')
                    print(f'  🇸🇦 {x.get("ar","")[:70]}\n')
                send_alert(alerts)
            else:
                print(f'[{ts}] Cycle {cycle}: No new messages')
        except Exception as e:
            print(f'[{time.strftime("%H:%M:%S")}] Cycle {cycle}: ⚠️ {str(e)[:50]}')
        await asyncio.sleep(POLL_INTERVAL)

asyncio.run(main())
