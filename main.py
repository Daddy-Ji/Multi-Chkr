import asyncio
import aiohttp
import aiofiles
import os
import random
import time
import json
import sys
from datetime import datetime, timedelta
from telethon import TelegramClient, events, Button
from telethon.errors import FloodWaitError
from config import *
from db import init_db, add_user, get_user, is_premium, get_credits, deduct_credits, get_all_users, get_all_plans, get_plan
from gates import list_categories, create_category, remove_category, get_gates_for_category, get_gate_details, create_gate, remove_gate, get_all_gates_info
from payments import create_payment, check_payment
from checker import *
from admin import *
from utils import *

# Initialize database
init_db()

# Bot instance
bot = TelegramClient('TGidFreeebot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Active sessions for bulk checks
active_sessions = {}

# Helper to check if user joined channel
async def is_joined_channel(user_id):
    try:
        channel = await bot.get_entity(CHANNEL_USERNAME)
        await bot.get_permissions(channel, user_id)
        return True
    except:
        return False

# Maintenance wrapper
def maintenance_check(func):
    async def wrapper(event, *args, **kwargs):
        user_id = event.sender_id
        if is_admin(user_id):
            return await func(event, *args, **kwargs)
        if is_maintenance_mode():
            await event.reply(premium_emoji(f"""<b>🔧 MAINTENANCE MODE</b>
━━━━━━━━━━━━━━━━━━━━
{get_maintenance_message()}
━━━━━━━━━━━━━━━━━━━━
<b>👑 Contact:</b> <a href="tg://user?id={OWNER_ID}">@SUNIOxRICH</a>"""), parse_mode='html')
            return
        return await func(event, *args, **kwargs)
    return wrapper

# ---------- START ----------
@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    sender = await event.get_sender()
    first_name = sender.first_name or "Unknown"
    username = sender.username or ""
    add_user(user_id, first_name, username)
    
    if is_admin(user_id):
        plan = "👑 Admin"
        plan_emoji = "👑"
    elif is_premium(user_id):
        plan = "💎 Premium"
        plan_emoji = "💎"
    else:
        plan = "⭐ Free"
        plan_emoji = "⭐"
    
    total_sites = len(load_sites())
    total_proxies = len(load_proxies())
    
    if await is_joined_channel(user_id):
        welcome_msg = f"""<b>⚡ 𝙒𝙀𝙇𝘾𝙊𝙈𝙀 𝙏𝙊 𝘿𝙀𝙑 𝙓 𝙎𝙃𝙊𝙋𝙄𝙁𝙔 💎 ⚡</b>
━━━━━━━━━━━━━━━━━━━━
<b>👑 User:</b> <a href="tg://user?id={user_id}">{first_name}</a>
<b>✅ ID:</b> <code>{user_id}</code>
<b>{plan_emoji} Access:</b> {plan}
<b>✅ Joined:</b> Active
━━━━━━━━━━━━━━━━━━━━
<b>📊 BOT STATUS:</b>
<b>🌐 Sites Loaded:</b> <code>{total_sites}</code>
<b>📡 Proxies Loaded:</b> <code>{total_proxies}</code>
<b>⚡ Status:</b> <code>✅ ONLINE</code>
━━━━━━━━━━━━━━━━━━━━
<b>👑 Dev:</b> <a href="tg://user?id={OWNER_ID}">⏤͟͟✧┊𓆩Dɢ Sʜᴀᴜʀʏᴀ𓆪 𖤍</a>
━━━━━━━━━━━━━━━━━━━━
<b>👇 Select an option below:</b>"""
        main_buttons = [
            [Button.inline("🔍 𝘾𝙃𝙀𝘾𝙆𝙀𝙍", b"checker"), Button.inline("🦄 𝘽𝙐𝙔 𝙉𝙊𝙒", b"buy")],
            [Button.inline("🛠️ 𝙏𝙊𝙊𝙇𝙎", b"tools_menu"), Button.inline("🆘 𝙎𝙐𝙋𝙋𝙊𝙍𝙏", b"support_menu")],
            [Button.inline("📊 𝙈𝙔 𝙋𝙇𝘼𝙉", b"my_plan"), Button.inline("🎯 𝘿𝙐𝙈𝙋𝙎", b"dumps_menu")],
            [Button.url("📣 𝙐𝙋𝘿𝘼𝙏𝙀𝙎", UPDATES_LINK), Button.url("💭 𝙂𝙍𝙊𝙐𝙋", GROUP_LINK)],
            [Button.inline("👑 𝘼𝘿𝙈𝙄𝙉", b"admin_panel") if is_admin(user_id) else None],
        ]
        main_buttons = [row for row in main_buttons if row is not None]
        try:
            await bot.send_file(event.chat_id, file=PHOTO_URL, caption=premium_emoji(welcome_msg), buttons=main_buttons, parse_mode="html")
        except:
            await event.reply(premium_emoji(welcome_msg), buttons=main_buttons, parse_mode="html")
    else:
        join_msg = f"""<b>⚡ 𝙒𝙀𝙇𝘾𝙊𝙈𝙀 𝙏𝙊 𝘿𝙀𝙑 𝙓 𝙎𝙃𝙊𝙋𝙄𝙁𝙔 💎 ⚡</b>
━━━━━━━━━━━━━━━━━━━━
<b>👑 User:</b> <a href="tg://user?id={user_id}">{first_name}</a>
<b>✅ ID:</b> <code>{user_id}</code>
<b>{plan_emoji} Access:</b> {plan}
━━━━━━━━━━━━━━━━━━━━
<b>⚠️ Please join both channels then verify!</b>"""
        join_buttons = [
            [Button.url("💭 𝙂𝙍𝙊𝙐𝙋", GROUP_LINK)],
            [Button.url("📣 𝙐𝙋𝘿𝘼𝙏𝙀𝙎", UPDATES_LINK)],
            [Button.inline("✅ 𝙑𝙀𝙍𝙄𝙁𝙔", b"verify")],
        ]
        try:
            await bot.send_file(event.chat_id, file=PHOTO_URL, caption=premium_emoji(join_msg), buttons=join_buttons, parse_mode="html")
        except:
            await event.reply(premium_emoji(join_msg), buttons=join_buttons, parse_mode="html")

@bot.on(events.CallbackQuery(pattern=b"verify"))
async def verify_handler(event):
    user_id = event.sender_id
    joined_ch1 = await is_joined_channel(user_id)
    try:
        group = await bot.get_entity(GROUP_LINK)
        await bot.get_permissions(group, user_id)
        joined_ch2 = True
    except:
        joined_ch2 = False
    if joined_ch1 and joined_ch2:
        await event.edit(premium_emoji("✅ Verified Successfully!\nNow use /start to continue."), parse_mode="html")
    else:
        await event.answer("❌ Please join both channels first!", alert=True)

# ---------- CHECKER MENU ----------
@bot.on(events.CallbackQuery(data=b"checker"))
async def checker_menu(event):
    categories = list_categories()
    buttons = []
    for cat in categories:
        buttons.append([Button.inline(f"{cat['name']} ({len(get_gates_for_category(cat['id']))})", f"cat_{cat['id']}".encode())])
    buttons.append([Button.inline("🔙 𝘽𝘼𝘾𝙆", b"back_to_start")])
    await event.edit(premium_emoji("""<b>🔒 𝘾𝙃𝙀𝘾𝙆𝙀𝙍 𝙈𝙀𝙉𝙐 🔒</b>
━━━━━━━━━━━━━━━━━━━━
<b>👇 Select a Gate Category:</b>"""), buttons=buttons, parse_mode="html")

@bot.on(events.CallbackQuery(pattern=b"cat_(\\d+)"))
async def category_gates(event):
    cat_id = int(event.pattern_match.group(1))
    gates = get_gates_for_category(cat_id)
    if not gates:
        await event.answer("No gates in this category.", alert=True)
        return
    buttons = []
    for gate in gates:
        buttons.append([Button.inline(f"{gate['name']} ({gate['command']})", f"gate_{gate['id']}".encode())])
    buttons.append([Button.inline("🔙 𝘽𝘼𝘾𝙆", b"checker")])
    await event.edit(premium_emoji(f"<b>📋 Gates in Category</b>\nSelect a gate:"), buttons=buttons, parse_mode="html")

@bot.on(events.CallbackQuery(pattern=b"gate_(\\d+)"))
async def gate_details(event):
    gate_id = int(event.pattern_match.group(1))
    gate = get_gate_details_by_id(gate_id)  # we'll implement this helper
    if not gate:
        await event.answer("Gate not found.", alert=True)
        return
    msg = f"""<b>⚡ Gate Details</b>
━━━━━━━━━━━━━━━━━━━━
<b>Name:</b> {gate['name']}
<b>Command:</b> <code>{gate['command']}</code>
<b>Sites:</b> <code>{len(gate['sites'])}</code>
<b>Extra:</b> {gate['extra_info']}
━━━━━━━━━━━━━━━━━━━━
<b>Usage:</b>
Single: <code>{gate['command']} card|mm|yyyy|cvv</code>
Bulk: Reply to .txt file with <code>{gate['command']}</code>"""
    buttons = [[Button.inline("🔙 𝘽𝘼𝘾𝙆", f"cat_{gate['category_id']}".encode())]]
    await event.edit(premium_emoji(msg), buttons=buttons, parse_mode="html")

def get_gate_details_by_id(gate_id):
    # Implement in gates.py
    pass

# ---------- BUY & PAYMENTS ----------
@bot.on(events.CallbackQuery(data=b"buy"))
async def buy_menu(event):
    plans = get_all_plans()
    if not plans:
        await event.answer("No plans available.", alert=True)
        return
    buttons = []
    for plan in plans:
        buttons.append([Button.inline(f"{plan['name']} - ${plan['price']} ({plan['duration']} days)", f"plan_{plan['id']}".encode())])
    buttons.append([Button.inline("🔙 𝘽𝘼𝘾𝙆", b"back_to_start")])
    await event.edit(premium_emoji("""<b>💎 𝙎𝙀𝙇𝙀𝘾𝙏 𝘼 𝙋𝙇𝘼𝙉</b>
━━━━━━━━━━━━━━━━━━━━
<b>👇 Choose your plan:</b>"""), buttons=buttons, parse_mode="html")

@bot.on(events.CallbackQuery(pattern=b"plan_(\\d+)"))
async def plan_payment(event):
    plan_id = int(event.pattern_match.group(1))
    plan = get_plan(plan_id)
    if not plan:
        await event.answer("Plan not found.", alert=True)
        return
    # Show payment methods
    buttons = [
        [Button.inline("BEP20 (BSC)", f"pay_{plan_id}_BEP20".encode())],
        [Button.inline("TRX (Tron)", f"pay_{plan_id}_TRX".encode())],
        [Button.inline("POL (Polygon)", f"pay_{plan_id}_POL".encode())],
        [Button.inline("TON", f"pay_{plan_id}_TON".encode())],
        [Button.inline("LTC", f"pay_{plan_id}_LTC".encode())],
        [Button.inline("BTC", f"pay_{plan_id}_BTC".encode())],
        [Button.inline("SOL", f"pay_{plan_id}_SOL".encode())],
        [Button.inline("ETH", f"pay_{plan_id}_ETH".encode())],
        [Button.inline("🔙 𝘽𝘼𝘾𝙆", b"buy")]
    ]
    msg = f"""<b>💳 {plan['name']} Plan</b>
━━━━━━━━━━━━━━━━━━━━
<b>Price:</b> ${plan['price']}
<b>Duration:</b> {plan['duration']} days
<b>Description:</b> {plan['description']}
━━━━━━━━━━━━━━━━━━━━
<b>Select payment method:</b>"""
    await event.edit(premium_emoji(msg), buttons=buttons, parse_mode="html")

@bot.on(events.CallbackQuery(pattern=b"pay_(\\d+)_(\\w+)"))
async def payment_process(event):
    user_id = event.sender_id
    plan_id = int(event.pattern_match.group(1))
    currency = event.pattern_match.group(2).decode()
    plan = get_plan(plan_id)
    if not plan:
        await event.answer("Plan not found.", alert=True)
        return
    payment = await create_payment(user_id, plan_id, currency)
    if not payment:
        await event.answer("Payment creation failed.", alert=True)
        return
    msg = f"""<b>💰 Payment Details</b>
━━━━━━━━━━━━━━━━━━━━
<b>Plan:</b> {plan['name']}
<b>Amount:</b> {payment['amount']} {currency}
<b>Address:</b> <code>{payment['address']}</code>
<b>TX ID:</b> <code>{payment['tx_id']}</code>
<b>Expires in:</b> {payment['expires_in']} min
━━━━━━━━━━━━━━━━━━━━
<b>⚠️ Send exact amount to the address above.</b>
<b>⏳ After payment, click "Verify Payment".</b>"""
    buttons = [
        [Button.inline("✅ Verify Payment", f"verify_pay_{payment['tx_id']}".encode())],
        [Button.inline("🔙 𝘽𝘼𝘾𝙆", b"buy")]
    ]
    await event.edit(premium_emoji(msg), buttons=buttons, parse_mode="html")

@bot.on(events.CallbackQuery(pattern=b"verify_pay_(\\w+)"))
async def verify_payment(event):
    tx_id = event.pattern_match.group(1).decode()
    user_id = event.sender_id
    # Check payment status
    success = await check_payment(tx_id)
    if success:
        await event.edit(premium_emoji("✅ Payment verified! Premium activated."), parse_mode="html")
    else:
        await event.answer("Payment not confirmed yet. Please wait.", alert=True)

# ---------- GATE COMMAND HANDLER (dynamic) ----------
@bot.on(events.NewMessage)
@maintenance_check
async def dynamic_gate_command(event):
    if event.is_private and event.message.text and event.message.text.startswith('/'):
        cmd = event.message.text.split()[0].lower()
        # Check if command is a gate command
        gate = get_gate_details(cmd)
        if gate:
            await handle_gate_command(event, gate)

async def handle_gate_command(event, gate):
    user_id = event.sender_id
    if is_banned(user_id):
        await event.reply("🚫 You are banned!")
        return
    if not await is_joined_channel(user_id):
        await event.reply("🚫 Pehle channel join karke verify karo!")
        return
    # Check if premium or has credits
    if not is_premium(user_id) and not is_admin(user_id):
        credits = get_credits(user_id)
        if credits <= 0:
            await event.reply(premium_emoji("❌ Insufficient credits! Buy premium or get more credits."))
            return
        if not deduct_credits(user_id, 1):
            await event.reply(premium_emoji("❌ Failed to deduct credits."))
            return

    # Extract cards
    if event.reply_to_msg_id:
        reply_msg = await event.get_reply_message()
        if reply_msg and reply_msg.file and str(reply_msg.file.name).endswith('.txt'):
            file_path = await reply_msg.download_media()
            async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = await f.read()
            os.remove(file_path)
            cards = extract_cc(content)
            if not cards:
                await event.reply("❌ No valid cards found.")
                return
            # Bulk check
            await start_bulk_check(event, cards, gate)
            return
        else:
            await event.reply("❌ Reply to a .txt file for bulk check.")
            return
    else:
        # Single check
        parts = event.message.text.split(' ', 1)
        if len(parts) < 2:
            await event.reply(f"Usage: `{gate['command']} card|mm|yyyy|cvv`")
            return
        cc_input = parts[1].strip()
        cards = extract_cc(cc_input)
        if not cards:
            await event.reply("❌ Invalid CC format.")
            return
        await start_single_check(event, cards[0], gate)

async def start_single_check(event, card, gate):
    user_id = event.sender_id
    sender = await event.get_sender()
    first_name = sender.first_name or "User"
    sites = gate.get('sites', [])
    if not sites:
        sites = load_sites()
    proxies = load_proxies()
    if not sites or not proxies:
        await event.reply("❌ No sites/proxies available.")
        return
    status_msg = await event.reply(premium_emoji("<b>⚡ Checking...</b>"), parse_mode='html')
    result = await check_card_with_retry(card, sites, proxies, max_retries=8)
    if result['status'] == 'Site Error' and result.get('site') and is_admin(user_id):
        # Auto-remove dead site (admin only)
        current_sites = load_sites()
        if result['site'] in current_sites:
            new_sites = [s for s in current_sites if s != result['site']]
            async with aiofiles.open(SITES_FILE, 'w') as f:
                for site in new_sites:
                    await f.write(f"{site}\n")
            await bot.send_message(user_id, f"🗑️ Dead site auto-removed: `{result['site'][:50]}`")
    # Format result
    brand, bin_type, level, bank, country, flag = await get_bin_info(card.split('|')[0])
    gateway = result.get("gateway", "𝘼𝙪𝙩𝙤 𝙎𝙝𝙤𝙥𝙞𝙛𝙮")
    price = result.get("price", "-")
    response_msg = str(result.get('message', 'Unknown Response'))[:60]
    if result['status'] == 'Charged':
        status_emoji = "💎"
        status_text = "𝘾𝙃𝘼𝙍𝙂𝙀𝘿"
        top_line = "💎 𝘾𝙃𝘼𝙍𝙂𝙀𝘿"
    elif result['status'] == 'Approved':
        status_emoji = "🔥"
        status_text = "𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿"
        top_line = "🔥 𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿"
    else:
        status_emoji = "❌"
        status_text = "𝘿𝙀𝘾𝙇𝙄𝙉𝙀𝘿"
        top_line = "❌ 𝘿𝙀𝘾𝙇𝙄𝙉𝙀𝘿"
    current_time = get_indian_time()
    is_razorpay = "razorpay" in gateway.lower() or "rz" in gateway.lower()
    currency = "₹" if is_razorpay else "$"
    bin_display = f"{card[:6]} - {brand}" if brand != '-' else card[:6]
    final_resp = f"""{top_line}
━━━━━━━━━━━━━━━━━━━
⭐ 𝐆𝐚𝐭𝐞 ➜ {gateway}
✔️ 𝐂𝐂 ➜ <tg-spoiler><code>{result['card']}</code></tg-spoiler>
⚡️𝐒𝐭𝐚𝐭𝐮𝐬 ➜ {status_emoji} {status_text}
⭐ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ➜ {response_msg}
{currency} 𝐀𝐦𝐨𝐮𝐧𝐭 ➜ {currency}{price}
💳 𝐁𝐢𝐧 ➜ {bin_display}
🏧 𝐁𝐚𝐧𝐤 ➜ {bank}
☄️ 𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ➜ {country} {flag}
⏳ 𝐓𝐢𝐦𝐞 ➜ {current_time}
👑 𝐂𝐡𝐞𝐜𝐤𝐞𝐝 𝐁𝐲 ➜ <a href="tg://user?id={user_id}">{first_name}</a>
🦄 Bot By: <a href="tg://user?id={OWNER_ID}">⏤͟͟✧┊𓆩Dɢ Sʜᴀᴜʀʏᴀ𓆪 𖤍</a>"""
    buttons = [[Button.inline("📋 𝘾𝙊𝙋𝙔 𝘾𝘾", f"copycc_{result['card']}".encode())]]
    try:
        await status_msg.delete()
    except:
        pass
    await bot.send_message(event.chat_id, premium_emoji(final_resp), buttons=buttons, parse_mode="html")
    if result['status'] in ['Charged', 'Approved']:
        await log_hit_to_group(user_id, result, result['status'], first_name, bot)
        # Send GIF
        gif_type = "charged" if result['status'] == 'Charged' else "approved"
        gif_url = get_random_gif(gif_type)
        if gif_url:
            try:
                await bot.send_message(event.chat_id, gif_url)
            except:
                pass

async def start_bulk_check(event, cards, gate):
    # Similar to original bulk logic but with gate-specific sites
    user_id = event.sender_id
    sender = await event.get_sender()
    username = sender.username or f"user_{user_id}"
    sites = gate.get('sites', [])
    if not sites:
        sites = load_sites()
    proxies = load_proxies()
    if not sites or not proxies:
        await event.reply("❌ No sites/proxies available.")
        return
    total_cards = len(cards)
    if not is_admin(user_id) and not is_premium(user_id):
        if total_cards > 2000:
            cards = cards[:2000]
            await event.reply("⚠️ Free limit 2000 cards. Truncated.")
    status_msg = await event.reply(premium_emoji(f"🫆 Starting bulk check for {len(cards)} cards..."))
    session_key = f"{user_id}_{status_msg.id}"
    active_sessions[session_key] = {'paused': False}
    all_results = {'charged': [], 'approved': [], 'dead': [], 'error_cards': [], 'errors': 0, 'total': len(cards), 'checked': 0, 'start_time': time.time()}
    dead_sites_to_remove = set()
    try:
        queue = asyncio.Queue()
        for card in cards: queue.put_nowait(card)
        async def worker():
            while not queue.empty() and session_key in active_sessions:
                session_state = active_sessions.get(session_key)
                if not session_state: break
                while session_state.get('paused', False):
                    await asyncio.sleep(0.3)
                    session_state = active_sessions.get(session_key)
                    if not session_state: return
                try:
                    card = await asyncio.wait_for(queue.get(), timeout=0.5)
                except:
                    continue
                res = await check_card_with_retry(card, sites, proxies, max_retries=8)
                if res.get('site') and res.get('status') == 'Site Error':
                    dead_sites_to_remove.add(res['site'])
                all_results['checked'] += 1
                if res['status'] == 'Charged':
                    all_results['charged'].append(res)
                    asyncio.create_task(log_hit_to_group(user_id, res, 'Charged', username, bot))
                elif res['status'] == 'Approved':
                    all_results['approved'].append(res)
                    asyncio.create_task(log_hit_to_group(user_id, res, 'Approved', username, bot))
                else:
                    all_results['dead'].append(res)
                queue.task_done()
                if all_results['checked'] % 10 == 0 or all_results['checked'] == total_cards:
                    progress_text = await update_progress(user_id, status_msg.id, all_results, all_results['checked'], first_name=username)
                    try:
                        await status_msg.edit(premium_emoji(progress_text), buttons=[[Button.inline("🛑 𝙎𝙏𝙊𝙋", f"stop_{status_msg.id}".encode())]], parse_mode="html")
                    except:
                        pass
        workers = [asyncio.create_task(worker()) for _ in range(10)]
        while workers:
            if session_key not in active_sessions:
                for w in workers:
                    if not w.done(): w.cancel()
                break
            done, pending = await asyncio.wait(workers, timeout=1.0)
            workers = list(pending)
    except Exception as e:
        await bot.send_message(user_id, f"❌ Error: {str(e)[:100]}")
    finally:
        if dead_sites_to_remove and is_admin(user_id):
            current_sites = load_sites()
            new_sites = [s for s in current_sites if s not in dead_sites_to_remove]
            if len(new_sites) != len(current_sites):
                async with aiofiles.open(SITES_FILE, 'w') as f:
                    for site in new_sites:
                        await f.write(f"{site}\n")
                await bot.send_message(user_id, f"🗑️ {len(current_sites) - len(new_sites)} dead sites auto-removed from sites.txt!")
        if session_key in active_sessions: del active_sessions[session_key]
        try: await status_msg.delete()
        except: pass
        await send_final_results(user_id, all_results, bot)

# ---------- STOP CALLBACK ----------
@bot.on(events.CallbackQuery(pattern=b"stop_(\\d+)"))
async def stop_handler(event):
    user_id = event.sender_id
    msg_id = int(event.pattern_match.group(1))
    session_key = f"{user_id}_{msg_id}"
    if session_key in active_sessions:
        active_sessions[session_key]['paused'] = True
        await event.answer("🛑 Stopping...", alert=True)
        await asyncio.sleep(1)
        if session_key in active_sessions:
            del active_sessions[session_key]
        await event.edit(premium_emoji("🛑 Stopped!"))
    else:
        await event.answer("No active session!", alert=True)

# ---------- COPY CC ----------
@bot.on(events.CallbackQuery(pattern=b"copycc_"))
async def copy_cc_handler(event):
    try:
        data = event.data.decode('utf-8')
        cc = data.split("_", 1)[1]
        await event.answer(f"✅ CC Copied!\n\n{cc}", alert=True)
    except:
        await event.answer("❌ Copy failed", alert=True)

# ---------- OTHER MENU CALLBACKS ----------
@bot.on(events.CallbackQuery(data=b"back_to_start"))
async def back_to_start(event):
    await start(event)

@bot.on(events.CallbackQuery(data=b"support_menu"))
async def support_menu(event):
    msg = f"""<b>🆘 𝙎𝙐𝙋𝙋𝙊𝙍𝙏 𝙈𝙀𝙉𝙐 🆘</b>
━━━━━━━━━━━━━━━━━━━━
<b>💎 Plans:</b> 7 Days $2 | 30 Days $5
<b>🔑 Redeem:</b> /redeem KEY_HERE
<b>📞 Contact:</b> <a href="tg://user?id={OWNER_ID}">@SUNIOxRICH</a>"""
    buttons = [[Button.url("💎 𝘽𝙐𝙔", f"https://t.me/SUNIOxRICH"), Button.inline("🔙", b"back_to_start")]]
    await event.edit(premium_emoji(msg), buttons=buttons, parse_mode="html")

@bot.on(events.CallbackQuery(data=b"my_plan"))
async def my_plan_handler(event):
    user_id = event.sender_id
    user = get_user(user_id)
    if not user:
        await event.answer("User not found.", alert=True)
        return
    first_name = user["first_name"] or "Unknown"
    if is_admin(user_id):
        status_text = "👑 ADMIN - UNLIMITED"
        expiry = "∞ Lifetime"
        emoji = "👑"
        daily = "∞"
    elif is_premium(user_id):
        status_text = "💎 PREMIUM ACTIVE"
        emoji = "💎"
        daily = "∞"
        expiry = user["premium_expiry"] or "Active"
    else:
        status_text = "⭐ FREE USER"
        expiry = "N/A"
        emoji = "⭐"
        usage = get_daily_usage(user_id)
        daily = f"{usage['cc_count']}/150"  # we'll keep daily_usage file for now

    msg = f"""<b>{emoji} 𝙈𝙔 𝙋𝙇𝘼𝙉 {emoji}</b>
━━━━━━━━━━━━━━━━━━━━
<b>👤 User:</b> {first_name}
<b>🆔 ID:</b> <code>{user_id}</code>
<b>💠 Status:</b> {status_text}
<b>⏳ Expiry:</b> {expiry}
<b>📊 Credits:</b> {user['credits']}
━━━━━━━━━━━━━━━━━━━━
<b>🔑 Redeem:</b> /redeem KEY"""
    await event.edit(premium_emoji(msg), buttons=[[Button.inline("🔙", b"back_to_start")]], parse_mode="html")

@bot.on(events.CallbackQuery(data=b"tools_menu"))
async def tools_menu(event):
    buttons = [
        [Button.inline("🛒 𝙎𝙃𝙊𝙋𝙄𝙁𝙔", b"shopify_tools"), Button.inline("💎 𝙍𝘼𝙕𝙊𝙍𝙋𝘼𝙔", b"rz_tools")],
        [Button.inline("📡 𝙋𝙍𝙊𝙓𝙔", b"proxy_tools"), Button.inline("💳 𝘾𝘾 𝙏𝙊𝙊𝙇𝙎", b"cc_tools")],
        [Button.inline("🔑 𝙋𝙇𝘼𝙉", b"premium_tools"), Button.inline("🎯 𝘿𝙐𝙈𝙋𝙎", b"dumps_menu")],
        [Button.inline("🔙", b"back_to_start")]
    ]
    await event.edit(premium_emoji("🛠️ 𝙏𝙊𝙊𝙇𝙎 𝙈𝙀𝙉𝙐"), buttons=buttons, parse_mode="html")

@bot.on(events.CallbackQuery(data=b"shopify_tools"))
async def shopify_tools(event):
    msg = f"""<b>🛒 𝙎𝙃𝙊𝙋𝙄𝙁𝙔 𝙎𝙄𝙏𝙀𝙎</b>
<code>/site</code> - Check all sites
<code>/addsites url</code> - Add site
<code>/rmsites url</code> - Remove site
<code>/mysites</code> - View your sites
<code>/clearsites</code> - Clear your sites"""
    await event.edit(premium_emoji(msg), buttons=[[Button.inline("🔙", b"tools_menu")]], parse_mode="html")

@bot.on(events.CallbackQuery(data=b"rz_tools"))
async def rz_tools(event):
    msg = f"""<b>💎 𝙍𝘼𝙕𝙊𝙍𝙋𝘼𝙔 𝙎𝙄𝙏𝙀𝙎</b>
<code>/rzsites</code> - Check all RZ sites
<code>/addrzsites url</code> - Add RZ site
<code>/rmrzsites url</code> - Remove RZ site"""
    await event.edit(premium_emoji(msg), buttons=[[Button.inline("🔙", b"tools_menu")]], parse_mode="html")

@bot.on(events.CallbackQuery(data=b"proxy_tools"))
async def proxy_tools(event):
    msg = f"""<b>📡 𝙋𝙍𝙊𝙓𝙔 𝙏𝙊𝙊𝙇𝙎</b>
<code>/proxy</code> - Check all proxies
<code>/addproxy</code> - Add proxies
<code>/getproxy</code> - View proxies
<code>/rmproxy ip:port</code> - Remove proxy
<code>/clearproxy</code> - Clear all proxies"""
    await event.edit(premium_emoji(msg), buttons=[[Button.inline("🔙", b"tools_menu")]], parse_mode="html")

@bot.on(events.CallbackQuery(data=b"cc_tools"))
async def cc_tools(event):
    msg = f"""<b>💳 𝘾𝘾 𝙏𝙊𝙊𝙇𝙎</b>
<code>/gen BIN COUNT</code> - Generate CCs
<code>/scrape</code> - Clean CC file (reply .txt)
<code>/dumps count</code> - Generate dumps
<code>/bulkdumps count</code> - Bulk dumps"""
    await event.edit(premium_emoji(msg), buttons=[[Button.inline("🔙", b"tools_menu")]], parse_mode="html")

@bot.on(events.CallbackQuery(data=b"premium_tools"))
async def premium_tools(event):
    msg = f"""<b>🔑 𝙋𝙇𝘼𝙉 𝙄𝙉𝙁𝙊</b>
<code>/redeem KEY</code> - Activate premium
<code>/plan</code> - Check your plan
━━━━━━━━━━━━━━━━━━━━
<b>💎 Benefits:</b>
• Unlimited Checks
• Razorpay + Shopify
• No Daily Limit
• Priority Support
• 10,000 CC Dumps"""
    await event.edit(premium_emoji(msg), buttons=[[Button.inline("🔙", b"tools_menu")]], parse_mode="html")

@bot.on(events.CallbackQuery(data=b"dumps_menu"))
async def dumps_menu(event):
    user_id = event.sender_id
    if is_admin(user_id):
        limit = 100000
        label = "👑 ADMIN"
    elif is_premium(user_id):
        limit = 10000
        label = "💎 PREMIUM"
    else:
        limit = 500
        label = "⭐ FREE"
    msg = f"""<b>🎯 𝘿𝙐𝙈𝙋𝙎 𝙂𝙀𝙉𝙀𝙍𝘼𝙏𝙊𝙍 🎯</b>
━━━━━━━━━━━━━━━━━━━━
<b>💎 Plan:</b> {label}
<b>📦 Max CCs:</b> <code>{limit}</code>
━━━━━━━━━━━━━━━━━━━━
<b>Commands:</b>
<code>/dumps count</code>
<code>/dumps count BIN</code>
<code>/bulkdumps count</code>"""
    await event.edit(premium_emoji(msg), buttons=[[Button.inline("🔙", b"tools_menu")]], parse_mode="html")

# ---------- ADMIN PANEL ----------
@bot.on(events.CallbackQuery(data=b"admin_panel"))
async def admin_panel_callback(event):
    if not is_admin(event.sender_id):
        await event.answer("Access Denied.", alert=True)
        return
    await admin_panel_command(event)

@bot.on(events.NewMessage(pattern='/admin'))
async def admin_panel_command(event):
    if not is_admin(event.sender_id):
        await event.reply("❌ Access Denied.")
        return
    config = load_config()
    maintenance_status = "🟢 OFF" if not config.get('maintenance_mode', False) else "🔴 ON"
    total_users = len(get_all_users())
    total_sites = len(load_sites())
    total_proxies = len(load_proxies())
    premium_users = len(load_premium_users())
    panel_msg = f"""<b>👑 𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇</b>
━━━━━━━━━━━━━━━━━━━━
<b>📊 STATISTICS:</b>
<b>👥 Total Users:</b> <code>{total_users}</code>
<b>💎 Premium:</b> <code>{premium_users}</code>
<b>🌐 Sites:</b> <code>{total_sites}</code>
<b>📡 Proxies:</b> <code>{total_proxies}</code>
━━━━━━━━━━━━━━━━━━━━
<b>🛠 MAINTENANCE:</b> <b>{maintenance_status}</b>
━━━━━━━━━━━━━━━━━━━━
<b>📋 COMMANDS:</b>
<code>/ban</code> <code>/unban</code> <code>/users</code> <code>/stats</code>
<code>/genkey</code> <code>/addpremium</code> <code>/rmpremium</code>
<code>/addadmin</code> <code>/rmadmin</code> <code>/admins</code>
<code>/broadcast</code> <code>/addsite</code> <code>/rmsite</code> <code>/sites</code> <code>/checksites</code>
<code>/addproxy</code> <code>/rmproxy</code> <code>/proxies</code> <code>/checkproxies</code>
<code>/addvideo</code> <code>/rmvideo</code> <code>/videos</code>
<code>/addgif</code> <code>/rmgif</code> <code>/gifs</code>
<code>/setlog</code> <code>/checklog</code>
<code>/clearcache</code> <code>/restart</code>
<code>/addcategory</code> <code>/rmcategory</code> <code>/addgate</code> <code>/rmgate</code>
━━━━━━━━━━━━━━━━━━━━
<b>👑 Bot By:</b> ⏤͟͟✧┊𓆩Dɢ Sʜᴀᴜʀʏᴀ𓆪 𖤍"""
    await event.reply(premium_emoji(panel_msg), parse_mode="html")

# ---------- OTHER ADMIN COMMANDS (copied from original with minor changes) ----------
# For brevity, we include only essential commands; the rest are similar to original.
# Placeholder for full admin commands. They will be similar to the original, but using DB for some operations.

# We'll implement a few key ones:
@bot.on(events.NewMessage(pattern=r'^/addgate\s+(.+)\s+(.+)\s+(.+)$'))
async def add_gate_cmd(event):
    if not is_admin(event.sender_id):
        await event.reply("❌ Access Denied.")
        return
    parts = event.pattern_match.group(1).split()
    if len(parts) < 3:
        await event.reply("Usage: /addgate category_name gate_name command")
        return
    cat_name, gate_name, command = parts[0], parts[1], parts[2]
    cat_id = get_category_id_by_name(cat_name)
    if not cat_id:
        await event.reply("Category not found. Create it first with /addcategory.")
        return
    if get_gate_details(command):
        await event.reply("Gate with this command already exists.")
        return
    create_gate(cat_id, gate_name, command, sites=[], extra_info="")
    await event.reply(f"✅ Gate '{gate_name}' added under '{cat_name}' with command {command}.")

@bot.on(events.NewMessage(pattern=r'^/addcategory\s+(.+)$'))
async def add_category_cmd(event):
    if not is_admin(event.sender_id):
        await event.reply("❌ Access Denied.")
        return
    name = event.pattern_match.group(1)
    create_category(name)
    await event.reply(f"✅ Category '{name}' added.")

@bot.on(events.NewMessage(pattern=r'^/rmcategory\s+(\d+)$'))
async def rm_category_cmd(event):
    if not is_admin(event.sender_id):
        await event.reply("❌ Access Denied.")
        return
    cat_id = int(event.pattern_match.group(1))
    delete_category(cat_id)
    await event.reply("✅ Category removed.")

@bot.on(events.NewMessage(pattern=r'^/rmgate\s+(\d+)$'))
async def rm_gate_cmd(event):
    if not is_admin(event.sender_id):
        await event.reply("❌ Access Denied.")
        return
    gate_id = int(event.pattern_match.group(1))
    delete_gate(gate_id)
    await event.reply("✅ Gate removed.")

@bot.on(events.NewMessage(pattern=r'^/addgif\s+(\w+)\s+(.+)$'))
async def add_gif_cmd(event):
    if not is_admin(event.sender_id):
        await event.reply("❌ Access Denied.")
        return
    gif_type = event.pattern_match.group(1)
    url = event.pattern_match.group(2)
    if gif_type not in ['charged', 'approved']:
        await event.reply("Type must be 'charged' or 'approved'.")
        return
    if add_gif(gif_type, url):
        await event.reply(f"✅ GIF added for {gif_type}.")
    else:
        await event.reply("❌ Failed to add GIF.")

@bot.on(events.NewMessage(pattern=r'^/rmgif\s+(\w+)\s+(.+)$'))
async def rm_gif_cmd(event):
    if not is_admin(event.sender_id):
        await event.reply("❌ Access Denied.")
        return
    gif_type = event.pattern_match.group(1)
    url = event.pattern_match.group(2)
    if remove_gif(gif_type, url):
        await event.reply(f"✅ GIF removed from {gif_type}.")
    else:
        await event.reply("❌ GIF not found.")

@bot.on(events.NewMessage(pattern=r'^/gifs$'))
async def list_gifs_cmd(event):
    if not is_admin(event.sender_id):
        await event.reply("❌ Access Denied.")
        return
    gifs = load_gifs()
    msg = "🎞️ **GIFs:**\n"
    for gtype, urls in gifs.items():
        msg += f"\n**{gtype.upper()}** ({len(urls)}):\n"
        for u in urls[:10]:
            msg += f"• <code>{u}</code>\n"
        if len(urls) > 10:
            msg += f"... and {len(urls)-10} more\n"
    await event.reply(premium_emoji(msg), parse_mode="html")

# ---------- MAINTENANCE ----------
@bot.on(events.NewMessage(pattern=r'^/maintenance\s+(on|off)$'))
async def maintenance_cmd(event):
    if not is_admin(event.sender_id):
        await event.reply("❌ Access Denied.")
        return
    state = event.pattern_match.group(1)
    config = load_config()
    config['maintenance_mode'] = (state == 'on')
    save_config(config)
    await event.reply(f"✅ Maintenance mode turned {state}.")

# ---------- BROADCAST ----------
@bot.on(events.NewMessage(pattern=r'^/broadcast\s+(.+)$'))
async def broadcast_cmd(event):
    if not is_admin(event.sender_id):
        await event.reply("❌ Access Denied.")
        return
    msg = event.pattern_match.group(1)
    users = get_all_users()
    sent = 0
    for uid in users:
        try:
            await bot.send_message(uid, f"📢 **Broadcast:**\n{msg}")
            sent += 1
            await asyncio.sleep(0.1)
        except:
            pass
    await event.reply(f"✅ Broadcast sent to {sent} users.")

# ---------- RESTART ----------
@bot.on(events.NewMessage(pattern='/restart'))
async def restart_cmd(event):
    if not is_admin(event.sender_id):
        await event.reply("❌ Access Denied.")
        return
    await event.reply("🔄 Restarting...")
    os.execv(sys.executable, ['python'] + sys.argv)

# ---------- MAIN LOOP ----------
if __name__ == "__main__":
    print("🔥 DEV X SHOPIFY BOT STARTED 🔥")
    print(f"👑 Owner: @SUNIOxRICH")
    print(f"📡 Channel: {UPDATES_LINK}")
    print(f"💬 Group: {GROUP_LINK}")
    print(f"🌐 Sites Loaded: {len(load_sites())}")
    print(f"📡 Proxies Loaded: {len(load_proxies())}")
    bot.start()
    bot.run_until_disconnected()
