#!/usr/bin/env python3
import asyncio, os, json, httpx, sys

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv('.env')

API_ID = int(os.getenv('TG_API_ID'))
API_HASH = os.getenv('TG_API_HASH')
GROQ_KEY = os.getenv('GROQ_API_KEY')
SB_URL = os.getenv('SUPABASE_URL')
SB_KEY = os.getenv('SUPABASE_KEY')
BOT = os.getenv('TG_BOT_TOKEN')
CHAT = os.getenv('TG_CHAT_ID')

async def main():
    print('🚀 OSINT PIPELINE — START\n')

    from telethon import TelegramClient
    c = TelegramClient('osint_pipe2', API_ID, API_HASH)
    await c.start()
    me = await c.get_me()
    print(f'✅ Telegram: {me.first_name}')

    msgs = []
    for ch in ['IdlibPlus', 'liveuamap', 'NorthPress']:
        try:
            ent = await c.get_entity(ch)
            async for m in c.iter_messages(ent, limit=3):
                if m.text and len(m.text) > 20:
                    msgs.append({'ch': ch, 'text': m.text, 'date': m.date})
            print(f'  ✅ @{ch}')
        except Exception as e:
            print(f'  ⚠️ @{ch}: {str(e)[:50]}')
    print(f'\n📨 {len(msgs)} messages collected\n')

    from groq import Groq
    groq = Groq(api_key=GROQ_KEY)
    analyzed = []
    for m in msgs[:5]:
        try:
            r = groq.chat.completions.create(
                messages=[{'role':'user','content':f'Return JSON: {{"threat":"critical/high/medium/low","loc":"location","en":"brief summary"}} Text: {m["text"][:300]}'}],
                model='openai/gpt-oss-20b', max_tokens=400, temperature=0.1
            )
            raw = r.choices[0].message.content
            s, e = raw.find('{'), raw.rfind('}')+1
            if s >= 0:
                a = json.loads(raw[s:e])
                m['a'] = a
                analyzed.append(m)
                t = a.get('threat','?').upper()
                print(f'  ✅ [{t}] {a.get("en","")[:70]}')
        except Exception as ex:
            print(f'  ⚠️ {str(ex)[:50]}')
    print(f'\n🤖 {len(analyzed)} analyzed\n')

    from supabase import create_client
    sb = create_client(SB_URL, SB_KEY)
    n = 0
    for m in analyzed:
        a = m.get('a', {})
        try:
            sb.table('events').insert({
                'id': f'SYR-{m["date"].strftime("%Y%m%d")}-{hash(m["text"])%100000:06d}',
                'title': a.get('en',''), 'title_arabic': '',
                'threat_level': a.get('threat','low'), 'category': 'security',
                'location_name': a.get('loc','Unknown'), 'location_name_arabic': '',
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
        except Exception as ex:
            print(f'  ⚠️ DB: {str(ex)[:60]}')
    print(f'💾 {n} events stored\n')

    lines = ['🇸🇾 OSINT SYRIA — LIVE BRIEF\n',
             f'📨 {len(msgs)} msgs | 🤖 {len(analyzed)} analyzed | 💾 {n} stored\n']
    for m in analyzed[:4]:
        a = m.get('a',{})
        t = a.get('threat','low').upper()
        i = {'CRITICAL':'🔴','HIGH':'🟠','MEDIUM':'🟡','LOW':'🟢'}.get(t,'⚪')
        lines.append(f'{i} [{t}] {a.get("en","")[:80]}')
        lines.append(f'📍 {a.get("loc","?")}\n')
    lines.append('🔗 osint-syria.onrender.com')

    resp = httpx.post(f'https://api.telegram.org/bot{BOT}/sendMessage',
                      json={'chat_id':CHAT, 'text':'\n'.join(lines)}, timeout=10)
    print(f'🚨 Alert sent! Status: {resp.status_code}')

    await c.disconnect()
    print('\n🎉 PIPELINE COMPLETE!')

asyncio.run(main())
