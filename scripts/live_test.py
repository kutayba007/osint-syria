#!/usr/bin/env python3
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

from telethon import TelegramClient
from src.sources.telescope_detector import TelescopeDetector
from src.sources.cib_detector import CIBDetector, SuspiciousPost
from src.sources.arabic_nlp import ArabicNLPAnalyzer
from src.geocoder.syria_geocoder import SyriaGeocoder
from datetime import datetime

async def main():
    api_id = int(os.getenv('TG_API_ID', '0'))
    api_hash = os.getenv('TG_API_HASH', '')
    
    client = TelegramClient('osint_syria_live_test', api_id, api_hash)
    await client.connect()
    
    if not await client.is_user_authorized():
        print('Not authorized')
        return
    
    me = await client.get_me()
    print(f'Connected: {me.first_name} @{me.username}')
    
    telescope = TelescopeDetector()
    cib = CIBDetector()
    nlp = ArabicNLPAnalyzer()
    geocoder = SyriaGeocoder()
    
    print('\n' + '='*60)
    print('  OSINT SYRIA - LIVE PIPELINE TEST')
    print('='*60 + '\n')
    
    channels = ['IdlibPlus', 'liveuamap', 'NorthPress']
    
    for ch in channels:
        try:
            entity = await client.get_entity(ch)
            print(f'CHANNEL: @{ch} ({entity.title})')
            
            async for msg in client.iter_messages(entity, limit=3):
                if msg.message:
                    text = msg.message[:100].replace('\n', ' ')
                    ts = msg.date.strftime('%H:%M')
                    
                    t_result = telescope.scan_text(msg.message)
                    nlp_result = nlp.analyze(msg.message)
                    
                    # Normalize timestamp for CIB comparison
                    ts_normalized = msg.date.replace(tzinfo=None) if msg.date.tzinfo else msg.date
                    post = SuspiciousPost(str(msg.id), ch, 'telegram', msg.message, ts_normalized)
                    cib.add_post(post)
                    
                    threat = t_result['threat_level'].upper()
                    if threat in ('CRITICAL','HIGH'):
                        icon = 'CRITICAL'
                    elif threat == 'MEDIUM':
                        icon = 'MEDIUM'
                    else:
                        icon = 'LOW'
                    
                    print(f'  [{icon}] {ts} | {nlp_result.sentiment}')
                    print(f'    Text: {text}...')
            print()
        except Exception as e:
            print(f'  Error: {str(e)[:60]}\n')
    
    print('CIB SIMULATION:')
    now = datetime.utcnow()
    for i in range(5):
        post = SuspiciousPost(f't{i}', f'bot_{i}', 'telegram', 'URGENT: Bank collapse!', now)
        alert = cib.add_post(post)
        if alert:
            print(f'  CIB ALERT: {alert.cluster.account_count} accounts coordinated!')
            break
    else:
        print(f'  {len(cib._post_buffer)} posts in buffer')
    
    print('\nGEOCODER TEST:')
    loc = geocoder._lookup_location('Damascus')
    if loc:
        print(f'  Damascus: {loc[0]:.4f}, {loc[1]:.4f}')
    loc = geocoder._lookup_location('Aleppo')
    if loc:
        print(f'  Aleppo: {loc[0]:.4f}, {loc[1]:.4f}')
    
    print('\n' + '='*60)
    print('  LIVE TEST COMPLETE!')
    print('='*60)
    
    await client.disconnect()

asyncio.run(main())
