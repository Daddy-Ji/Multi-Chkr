import re
import json
import random
import os
import aiohttp
import pytz
from datetime import datetime
from config import PREMIUM_EMOJI_IDS, SITES_FILE, PROXY_FILE, RZ_SITES_FILE

def premium_emoji(text):
    if not text:
        return text
    placeholders = []
    result = text
    for i, (emoji, doc_id) in enumerate(PREMIUM_EMOJI_IDS.items()):
        placeholder = f"\x00PE{i:02d}\x00"
        placeholders.append((placeholder, doc_id, emoji))
        result = result.replace(emoji, placeholder)
    for placeholder, doc_id, emoji in placeholders:
        result = result.replace(placeholder, f'<tg-emoji emoji-id="{doc_id}">{emoji}</tg-emoji>')
    return result

def extract_cc(text):
    pattern = r'(\d{15,16})\|(\d{2})\|(\d{2,4})\|(\d{3,4})'
    matches = re.findall(pattern, text)
    cards = []
    for match in matches:
        card, month, year, cvv = match
        if len(year) == 2:
            year = '20' + year
        cards.append(f"{card}|{month}|{year}|{cvv}")
    return cards

async def get_bin_info(card_number):
    try:
        bin_num = card_number[:6]
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f'https://bins.antipublic.cc/bins/{bin_num}') as resp:
                if resp.status != 200:
                    return 'BIN Info Not Found', '-', '-', '-', '-', ''
                data = await resp.json()
                brand = data.get('brand', '-')
                bin_type = data.get('type', '-')
                level = data.get('level', '-')
                bank = data.get('bank', '-')
                country = data.get('country_name', '-')
                flag = data.get('country_flag', '')
                return brand, bin_type, level, bank, country, flag
    except:
        return '-', '-', '-', '-', '-', ''

def get_indian_time():
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    return now.strftime("%I:%M:%S %p IST")

def get_file_lines(filepath):
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return [line.strip() for line in f if line.strip()]
    except:
        return []

def load_sites():
    return get_file_lines(SITES_FILE)

def load_proxies():
    return get_file_lines(PROXY_FILE)

def load_razorpay_sites():
    return get_file_lines(RZ_SITES_FILE)

def generate_unique_ccs(count, bin_prefix=None):
    ccs = set()
    bins = ['400000', '411111', '414720', '424242', '450875', '491761',
            '511111', '555555', '601100', '650000', '401200', '438935',
            '455619', '453201', '491683', '492181', '525400', '527700',
            '530000', '540000', '552000', '558000', '421765', '431940']
    max_attempts = count * 5
    attempts = 0
    while len(ccs) < count and attempts < max_attempts:
        attempts += 1
        if not bin_prefix:
            bin_prefix = random.choice(bins)
        remaining = 16 - len(str(bin_prefix))
        card_num = str(bin_prefix) + ''.join(str(random.randint(0,9)) for _ in range(remaining))
        if len(card_num) > 16:
            card_num = card_num[:16]
        elif len(card_num) < 16:
            card_num = card_num + ''.join(str(random.randint(0,9)) for _ in range(16 - len(card_num)))
        month = random.randint(1, 12)
        year = random.randint(2026, 2035)
        cvv = random.randint(100, 999)
        cc = f"{card_num}|{month:02d}|{year}|{cvv:03d}"
        ccs.add(cc)
    return list(ccs)[:count]
