import os
from dotenv import load_dotenv

load_dotenv()

# Bot credentials
API_ID = int(os.getenv("API_ID", 38889620))
API_HASH = os.getenv("API_HASH", "7dfadd71a3cb2c61aab10297f1176a22")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8533471163:AAFgeWSjCV6oDtA4upGoMg-UrlcIbU43Z4c")
OWNER_ID = int(os.getenv("OWNER_ID", 5807965902))

# Channels & groups
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/AboutKiyotaka")
GROUP_LINK = os.getenv("GROUP_LINK", "https://t.me/DevXChkrGC")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "AboutKiyotaka")   # for membership check
GROUP_USERNAME = os.getenv("GROUP_USERNAME", "DevXChkrGC")          # for membership check

BOT_USERNAME = os.getenv("BOT_USERNAME", "TGidFreeebot")
DEV_LINK = os.getenv("DEV_LINK", "https://t.me/SUNIOxRICH")
UPDATES_LINK = os.getenv("UPDATES_LINK", "https://t.me/AboutKiyotaka")

# Log groups
LOGS_CHANNEL_ID = int(os.getenv("LOGS_CHANNEL_ID", -1002554500064))   # replace with your log group ID
MONITOR_GROUP_ID = int(os.getenv("MONITOR_GROUP_ID", -1002554500064))
APPROVED_GROUP_ID = int(os.getenv("APPROVED_GROUP_ID", -1002554500064))

# Files (for fallback and legacy)
PREMIUM_FILE = "premium.txt"
SITES_FILE = "sites.txt"
PROXY_FILE = "proxy.txt"
USER_SITES_FILE = "user_sites.json"
DAILY_USAGE_FILE = "daily_usage.json"
CONFIG_FILE = "config.json"
ADMINS_FILE = "admins.txt"
BANNED_FILE = "banned_users.txt"
GIFS_FILE = "gifs.json"
KEYS_FILE = "keys.txt"

# Shopify APIs (load balanced)
SHOPIFY_APIS = [
    "https://web-production-45515a.up.railway.app/shopify",
    "https://apixhello-production.up.railway.app/shopify",
    "https://leo4youhshopiiapi-production.up.railway.app/shopify",
]
RAZORPAY_API_BASE = "https://auto-razorpay-nano.vercel.app/hit"

# Premium emoji IDs (from original)
PREMIUM_EMOJI_IDS = {
    "✅": "6298612102709909362",
    "❌": "6206110936789423908",
    "⚡": "6026367225466720832",
    "💠": "5971837723676249096",
    "⏸️": "6001440193058444284",
    "▶️": "6285315214673975495",
    "🛑": "5420323339723881652",
    "📊": "5971837723676249096",
    "📦": "6066395745139824604",
    "📋": "5974235702701853774",
    "🔄": "5971837723676249096",
    "⏳": "5971837723676249096",
    "🚀": "6282977077427702833",
    "⚠️": "5420323339723881652",
    "💎": "5462902520215002477",
    "🔥": "5267500801240092311",
    "💰": "6190336264940559752",
    "💵": "6206155797722830770",
    "✔️": "6206479140040743133",
    "⭐": "5267500801240092311",
    "💳": "5472250091332993630",
    "🏧": "4967738760021148319",
    "☄️": "5041992177563993101",
    "🫥": "5325731315004218660",
    "⏳": "5325583469344989152",
    "⚡️": "5042334757040423886",
    "👑": "5039727497143387500",
    "🎯": "5444197605947085469",
    "📌": "5420323339723881652"
}
