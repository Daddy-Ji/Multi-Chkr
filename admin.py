import asyncio
import os
import json
import sys
import random
from datetime import datetime
from telethon import events, Button
from utils import premium_emoji, load_sites, load_proxies, load_razorpay_sites, get_file_lines
from db import *
from gates import *
from config import OWNER_ID, PREMIUM_FILE, SITES_FILE, PROXY_FILE, GIFS_FILE, KEYS_FILE, BANNED_FILE, CONFIG_FILE
from checker import add_gif, remove_gif, get_random_gif, load_gifs

# ---- Admin helpers (from original code) ----
def load_admins():
    if not os.path.exists(ADMINS_FILE):
        return [OWNER_ID]
    with open(ADMINS_FILE, 'r') as f:
        return [int(line.strip()) for line in f if line.strip().isdigit()]

def save_admins(admins):
    with open(ADMINS_FILE, 'w') as f:
        for uid in admins:
            f.write(f"{uid}\n")

def is_admin(user_id):
    return user_id in load_admins() or user_id == OWNER_ID

def load_banned():
    if not os.path.exists(BANNED_FILE):
        return set()
    with open(BANNED_FILE, 'r') as f:
        return {int(line.strip()) for line in f if line.strip().isdigit()}

def save_banned(banned):
    with open(BANNED_FILE, 'w') as f:
        for uid in banned:
            f.write(f"{uid}\n")

def is_banned(user_id):
    return user_id in load_banned()

def ban_user(user_id):
    banned = load_banned()
    banned.add(user_id)
    save_banned(banned)

def unban_user(user_id):
    banned = load_banned()
    banned.discard(user_id)
    save_banned(banned)

def load_config():
    if not os.path.exists(CONFIG_FILE):
        default = {"maintenance_mode": False, "maintenance_message": "🔧 Bot is under maintenance. Back soon!"}
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default, f, indent=4)
        return default
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def is_maintenance_mode():
    return load_config().get('maintenance_mode', False)

def get_maintenance_message():
    return load_config().get('maintenance_message', "🔧 Bot is under maintenance. Back soon!")

def generate_key(days):
    key = f"SHAURYA-{random.randint(100000,999999)}-{days}D"
    with open(KEYS_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{key}|{days}\n")
    return key

def redeem_key(key, user_id):
    if not os.path.exists(KEYS_FILE):
        return "invalid"
    try:
        with open(KEYS_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        new_lines = []
        found = False
        for line in lines:
            line = line.strip()
            if not line: continue
            k, d = line.split("|", 1)
            if k.strip().upper() == key.strip().upper():
                found = True
                expiry_days = 99999 if is_admin(user_id) else int(d.strip())
                set_premium(user_id, expiry_days)
            else:
                new_lines.append(line + "\n")
        if not found:
            return "invalid"
        with open(KEYS_FILE, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return "success"
    except:
        return "invalid"

def load_premium_users():
    # from DB
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT user_id FROM users WHERE is_premium = 1')
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]

# ---- (Optional) Admin panel callback handler (can be placed in main.py) ----
# The main admin panel is defined in main.py; this file only provides helper functions.
# If you need an inline admin panel callback, you can define it here.
