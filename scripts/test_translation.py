#!/usr/bin/env python3
"""Test: Read from Telegram, translate both ways, store, alert."""
import asyncio, os, sys, json, httpx

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv('.env')

from telethon import TelegramClient
from groq import Groq
from supabase import create_client

API_ID = int(os.getenv('TG_API_ID'))
API_HASH = os.getenv('TG_API_HASH')
GROQ_KEY = os.getenv('GROQ_API_KEY')
SB_URL = os.getenv('SUPABASE_URL')
SB_KEY = os.getenv('SUPABASE_KEY')
BOT = os.getenv('TG_BOT_TOKEN')
CHAT = os.getenv('TG_CHAT_ID')

PROMPT = """Analyze this OSINT text and return JSON ONLY:
{
    "threat": "critical/high/medium/low",
    "loc": "location name",
    "en": "brief English summary (1 sentence)",
    "ar": "ملخص مختصر بالعربي (جملة واحدة)",
    "type": "event type",
    "source_lang": "arabic or english"
}
Be factual. Text: """


async def main():
    print('🚀 OSINT PIPELINE — WITH TRANSLATION\n')

    c = TelegramClient('osint_trans_test', API_ID, API_HASH)
    await c.start()
    me = await c.get_me()
    print(f'✅ Telegram: {me.first_name}\n')

    msgs = []
    for ch in ['IdlibPlus', 'liveuamap', 'NorthPress', 'SyriaMonitor']:
        try:
            ent = await c.get_entity(ch)
            async for m in c.iter_messages(ent, limit=2):
                if m.text and len(m.text) > 20:
                    msgs.append({'ch': ch, 'text': m.text, 'date': m.date})
            print(f'  ✅ @{ch}')
        except:
            pass

    print(f'\n📨 {len(msgs)} messages\n')

    groq = Groq(api_key=GROQ_KEY)
    analyzed = []

    for m in msgs[:4]:
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
                lang = '🇸🇦' if a.get('source_lang') == 'arabic' else '🇬🇧'
                t = a.get('threat', '?').upper()
                print(f'  {lang} [{t}] @{m["ch"]}')
                print(f'     🇬🇧 EN: {a.get("en", "")[:90]}')
                print(f'     🇸🇦 AR: {a.get("ar", "")[:90]}')
                print()
        except Exception as ex:
            print(f'  ⚠️ {str(ex)[:50]}')

    # Store
    sb = create_client(SB_URL, SB_KEY)
    n = 0
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
            n += 1
        except:
            pass

    print(f'💾 {n} events stored\n')

    # Alert with translations
    lines = ['🚨 OSINT SYRIA — LIVE INTELLIGENCE BRIEF\n']
    for m in analyzed[:4]:
        a = m.get('a', {})
        t = a.get('threat', '?').upper()
        i = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}.get(t, '⚪')
        lang = '🇸🇦' if a.get('source_lang') == 'arabic' else '🇬🇧'
        lines.append(f'{i} [{t}] {lang} @{m["ch"]}')
        lines.append(f'🇬🇧 {a.get("en", "")[:100]}')
        lines.append(f'🇸🇦 {a.get("ar", "")[:100]}')
        lines.append(f'📍 {a.get("loc", "?")}')
        lines.append('')

    resp = httpx.post(f'https://api.telegram.org/bot{BOT}/sendMessage',
                      json={'chat_id': CHAT, 'text': '\n'.join(lines)}, timeout=10)
    print(f'🚨 Alert sent! Status: {resp.status_code}')

    await c.disconnect()
    print('\n🎉 DONE!')

asyncio.run(main())
