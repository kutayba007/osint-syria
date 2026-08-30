#!/usr/bin/env python3
import asyncio, os, sys

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv('.env')
from telethon import TelegramClient

API_ID = int(os.getenv('TG_API_ID'))
API_HASH = os.getenv('TG_API_HASH')

channels = [
    # Major Arabic News
    'AlJazeera', 'AlJazeeraArabic', 'aljazeera', 'ajplus', 'ajaborabic',
    'AlArabiya', 'alarabiya', 'AlArabiyah', 'AlArabiya_Eng',
    'BBCArabic', 'BBCBreaking', 'BBCNewsArabic',
    'SkyNewsArabia', 'SkyNewsArabiya', 'skynewsarabia',
    'RT_arabic', 'RTArabic', 'RT_Arabic', 'RusAFrance',
    'France24_ar', 'France24_FR', 'France24_en',
    'AlMayadeenNews', 'AlMayadeen', 'almayadeennetwork',
    'CNNArabic', 'caborabic',
    'AlHurra', 'AlHurraNews', 'alhurra',
    'DW_arabic', 'DWArabic', 'dwaboreabic',
    # Palestinian/Syrian
    'AlQudsNews', 'Alquds', 'AlQudsArabic', 'Alqudsaljadeed',
    'ShebabAgency', 'ShebabNews',
    'SOHR', 'syriahr', 'syrianobservatory',
    'EnabBaladi', 'Enab_Baladi', 'enaborabadi',
    'ZamanAlWasl', 'ZamanAlwasl',
    'StepNewsAgency', 'StepAgency', 'StepAgency2',
    'OrientNews', 'Orient_OG',
    'BaladiNews', 'Baladi_News',
    'ShaamNews', 'shaam_news',
    # Turkish
    'AnadoluAgency', 'AnadoluEN', 'AnadoluAjans', 'aa_arabic',
    # Russian
    'TASS', 'tass_arabic', 'Sputnik_arabic', 'SputnikArabic',
    # International
    'ReutersArabic', 'Reuters',
    'AP', 'APNews', 'AP_Arabic',
    'NDNews', 'ND_news', 'NDarabic',
    'NedaaSyria', 'Nedaa',
    'AlMadaArabic', 'AlmadaNews',
    'RFE_arabic', 'RadioFarda',
    'VOAarabic', 'VOANews',
]

async def main():
    c = TelegramClient('osint_scan2', API_ID, API_HASH)
    await c.start()
    me = await c.get_me()
    print(f'✅ Connected: {me.first_name}')
    print(f'🔍 Scanning {len(channels)} channels...\n')

    working = []
    for ch in channels:
        try:
            ent = await c.get_entity(ch)
            print(f'✅ @{ch} — {ent.title}')
            working.append({'username': ch, 'name': ent.title})
        except:
            pass

    await c.disconnect()

    print(f'\n{"=" * 50}')
    print(f'📊 Found {len(working)} working channels:')
    print(f'{"=" * 50}')
    for w in working:
        print(f'  ✅ @{w["username"]} — {w["name"]}')

asyncio.run(main())
