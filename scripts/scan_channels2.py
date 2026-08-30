#!/usr/bin/env python3
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()
from telethon import TelegramClient

async def main():
    api_id = int(os.getenv('TG_API_ID', '0'))
    api_hash = os.getenv('TG_API_HASH', '')
    
    client = TelegramClient('osint_syria_live_test', api_id, api_hash)
    await client.connect()
    
    if not await client.is_user_authorized():
        print('Not authorized')
        return
    
    me = await client.get_me()
    print(f'Connected: {me.first_name}\n')
    
    channels = [
        'senti_syr', 'sentry_syria', 'syr_defense', 'syria_news24',
        'syria_monitor', 'SyriaAlerts', 'SyriaLive', 'SyriaWar',
        'SyriaConflict24', 'SyriaOSINT24', 'syria_intel',
        'DamascusNow', 'AleppoNow', 'HomsNow', 'IdlibNow',
        'DaraaNow', 'DeirEzzorNow', 'HasakaNow', 'RaqqaNow',
        'SyriaBreaking', 'BreakingSyria', 'SyriaNewsLive',
        'SyriaDirect', 'SyriaReport', 'SyriaAnalysis',
        'SyriaMonitor', 'SyriaWatcher', 'SyriaObserver',
        'SyriaIntel', 'SyriaOSINT', 'SyriaTI',
        'SyriaConflict', 'SyriaWarNews', 'SyriaWarReport',
        'SyriaLiveMap', 'SyriaMap', 'SyriaTracker',
        'SyriaCrisis', 'SyriaEmergency', 'SyriaAlert',
        'SyriaBreakingNews', 'SyriaLatest', 'SyriaUpdate',
        'SyriaToday', 'SyriaNow24', 'SyriaNewsNow',
        'syrianews', 'syrianews24', 'syrianewsnow',
        'SyriaPress', 'SyriaMedia', 'SyriaTV',
        'SyriaRadio', 'SyriaBroadcast', 'SyriaChannel',
        'SyriaNetwork', 'SyriaFeed', 'SyriaStream',
    ]
    
    found = []
    for ch in channels:
        try:
            entity = await client.get_entity(ch)
            if hasattr(entity, 'title'):
                last_msg = ''
                async for msg in client.iter_messages(entity, limit=1):
                    if msg.message:
                        last_msg = msg.message[:60].replace('\n', ' ')
                
                print(f'✅ @{ch} — {entity.title}')
                if last_msg:
                    print(f'   Last: {last_msg}...')
                found.append({'username': ch, 'title': entity.title})
        except:
            pass
    
    print(f'\n📊 Found: {len(found)} accessible channels')
    await client.disconnect()

asyncio.run(main())
