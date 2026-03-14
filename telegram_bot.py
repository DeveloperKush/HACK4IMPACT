import os
import requests
import asyncio
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_BASE = os.getenv("API_BASE", "http://127.0.0.1:5000")

if not TOKEN:
    print("ERROR: TELEGRAM_BOT_TOKEN is missing in the environment or .env file.")
    exit(1)

# --- STATES ---
(
    CHOOSING_MAIN,
    CHOOSING_MENTAL,
    FACT_CHECK_STATE,
    TELEMEDICINE_STATE,
    THERAPIST_STATE,
    DIARY_STATE,
    PEER_CHAT_STATE,
) = range(7)

# --- KEYBOARDS ---
MAIN_MENU_KB = [
    ["Fact Checker", "Mental Health"],
    ["Telemedicine", "Cancel"]
]
MENTAL_HEALTH_KB = [
    ["Therapist", "Diary"],
    ["Peer Chat", "Back to Main"]
]
BACK_KB = [["Back"]]

# --- PEER CHAT MEMORY ---
peer_queue = []
active_peers = {} # user_id -> partner_user_id

# --- START & MENUS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear() # Reset any ongoing session
    reply_markup = ReplyKeyboardMarkup(MAIN_MENU_KB, resize_keyboard=True)
    await update.message.reply_text(
        "Welcome to Jan-Sahayak Telegram Bot!\n\n"
        "Please choose a service from the menu below:",
        reply_markup=reply_markup,
    )
    return CHOOSING_MAIN

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text

    if text == "Fact Checker":
        reply_markup = ReplyKeyboardMarkup(BACK_KB, resize_keyboard=True)
        await update.message.reply_text(
            "🔎 **Fact Checker**\n"
            "Send me a claim, or upload an image/screenshot of a news article to verify.",
            reply_markup=reply_markup, parse_mode="Markdown"
        )
        return FACT_CHECK_STATE

    elif text == "Telemedicine":
        reply_markup = ReplyKeyboardMarkup(BACK_KB, resize_keyboard=True)
        await update.message.reply_text(
            "🩺 **Telemedicine (Triage/First-Aid)**\n"
            "Please describe your symptoms or medical emergency.",
            reply_markup=reply_markup, parse_mode="Markdown"
        )
        return TELEMEDICINE_STATE

    elif text == "Mental Health":
        reply_markup = ReplyKeyboardMarkup(MENTAL_HEALTH_KB, resize_keyboard=True)
        await update.message.reply_text(
            "🧠 **Mental Health Services**\n"
            "Choose an option below:",
            reply_markup=reply_markup, parse_mode="Markdown"
        )
        return CHOOSING_MENTAL

    elif text == "Cancel":
        await update.message.reply_text("Session cancelled. Send /start to begin again.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    else:
        await update.message.reply_text("Please choose a valid option from the keyboard.")
        return CHOOSING_MAIN


async def handle_mental_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    user_id = update.message.chat_id

    if text == "Therapist":
        reply_markup = ReplyKeyboardMarkup(BACK_KB, resize_keyboard=True)
        # Call reset just in case
        try:
            requests.post(f"{API_BASE}/mental-health/reset", json={"session_id": str(user_id)}, timeout=5)
        except:
            pass
        await update.message.reply_text(
            "🛋️ **AI Therapist**\n"
            "Hello. I am here to listen. How are you feeling today?",
            reply_markup=reply_markup, parse_mode="Markdown"
        )
        return THERAPIST_STATE

    elif text == "Diary":
        reply_markup = ReplyKeyboardMarkup(BACK_KB, resize_keyboard=True)
        await update.message.reply_text(
            "📔 **Anonymous Diary**\n"
            "Write your entry below, and it will be saved safely. What's on your mind?",
            reply_markup=reply_markup, parse_mode="Markdown"
        )
        return DIARY_STATE

    elif text == "Peer Chat":
        reply_markup = ReplyKeyboardMarkup([["Leave Chat"]], resize_keyboard=True)
        if user_id in active_peers:
            await update.message.reply_text("You are already in a chat.", reply_markup=reply_markup)
            return PEER_CHAT_STATE
        
        if peer_queue and peer_queue[0] != user_id:
            partner_id = peer_queue.pop(0)
            active_peers[user_id] = partner_id
            active_peers[partner_id] = user_id
            
            await update.message.reply_text("💙 You are now connected with a peer! Say hi.", reply_markup=reply_markup)
            try:
                await context.bot.send_message(chat_id=partner_id, text="💙 You are now connected with a peer! Say hi.")
            except Exception as e:
                print(f"Failed to notify peer: {e}")
        else:
            if user_id not in peer_queue:
                peer_queue.append(user_id)
            await update.message.reply_text("⏳ Waiting for another peer to connect...", reply_markup=reply_markup)
            
        return PEER_CHAT_STATE

    elif text == "Back to Main":
        reply_markup = ReplyKeyboardMarkup(MAIN_MENU_KB, resize_keyboard=True)
        await update.message.reply_text("Returning to Main Menu.", reply_markup=reply_markup)
        return CHOOSING_MAIN

    else:
        await update.message.reply_text("Please choose a valid option.")
        return CHOOSING_MENTAL


# --- FEATURE HANDLERS ---

async def handle_fact_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text == "Back":
        reply_markup = ReplyKeyboardMarkup(MAIN_MENU_KB, resize_keyboard=True)
        await update.message.reply_text("Main Menu", reply_markup=reply_markup)
        return CHOOSING_MAIN

    if update.message.photo:
        await update.message.reply_text("🔎 Extracting text from image...")
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = bytes(await photo_file.download_as_bytearray())
        
        try:
            res = requests.post(
                f"{API_BASE}/fact-check/verify", 
                files={"image": ("photo.jpg", photo_bytes, "image/jpeg")}, 
                timeout=30
            )
            data = res.json()
        except requests.exceptions.RequestException:
            await update.message.reply_text("Sorry, the server is unreachable right now.")
            return FACT_CHECK_STATE
    else:
        await update.message.reply_text("🔎 Verifying claim...")
        try:
            res = requests.post(f"{API_BASE}/fact-check/verify", json={"text": text}, timeout=30)
            data = res.json()
        except requests.exceptions.RequestException:
            await update.message.reply_text("Sorry, the server is unreachable right now.")
            return FACT_CHECK_STATE

    if data:
        if "error" in data:
            await update.message.reply_text(f"Error: {data['error']}")
        else:
            msg = f"**Answer:** {data.get('answer', 'No answer found.')}\n"
            if data.get('sources'):
                msg += f"\n**Sources:** {len(data['sources'])} found."
            await update.message.reply_text(msg, parse_mode="Markdown")

    return FACT_CHECK_STATE


async def handle_telemedicine(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text == "Back":
        reply_markup = ReplyKeyboardMarkup(MAIN_MENU_KB, resize_keyboard=True)
        await update.message.reply_text("Main Menu", reply_markup=reply_markup)
        return CHOOSING_MAIN

    await update.message.reply_text("🩺 Analyzing symptoms...")
    try:
        res = requests.post(f"{API_BASE}/telemedicine/chat", json={"symptoms": text}, timeout=20)
        data = res.json()
        if "error" in data:
            await update.message.reply_text(f"Error: {data['error']}")
        else:
            results = data.get("results", [])
            disclaimer = data.get("disclaimer", "")
            transport = data.get("transport_advice", "")
            
            reply = f"_{disclaimer}_\n\n"
            if transport:
                reply += f"🚨 **{transport}**\n\n"
                
            if results:
                r = results[0]
                reply += f"**Identified:** {r['condition']} (Severity: {r['severity']})\n"
                reply += f"**First Aid:**\n"
                for step in r['first_aid']:
                    reply += f"• {step}\n"
                reply += f"\n**Action:** {r['action']}"
            else:
                reply += "No specific condition detected. Please visit a doctor."
                
            await update.message.reply_text(reply, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text("Sorry, the server is unreachable right now.")

    return TELEMEDICINE_STATE


async def handle_therapist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    user_id = str(update.message.chat_id)
    if text == "Back":
        reply_markup = ReplyKeyboardMarkup(MENTAL_HEALTH_KB, resize_keyboard=True)
        await update.message.reply_text("Mental Health Menu", reply_markup=reply_markup)
        return CHOOSING_MENTAL

    # Optional typing action
    await context.bot.send_chat_action(chat_id=user_id, action='typing')
    
    try:
        res = requests.post(f"{API_BASE}/mental-health/chat", json={"message": text, "session_id": user_id}, timeout=30)
        data = res.json()
        if "error" in data:
            await update.message.reply_text(f"Error: {data['error']}")
        else:
            await update.message.reply_text(data.get("response", "No response."))
    except Exception as e:
        await update.message.reply_text("Sorry, the AI Therapist is currently unreachable.")

    return THERAPIST_STATE


async def handle_diary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    user_id = str(update.message.chat_id)
    if text == "Back":
        reply_markup = ReplyKeyboardMarkup(MENTAL_HEALTH_KB, resize_keyboard=True)
        await update.message.reply_text("Mental Health Menu", reply_markup=reply_markup)
        return CHOOSING_MENTAL

    try:
        res = requests.post(f"{API_BASE}/diary/save", json={"entry": text, "uuid": user_id, "mood": "neutral"}, timeout=10)
        data = res.json()
        if "error" in data:
            await update.message.reply_text(f"Error: {data['error']}")
        else:
            await update.message.reply_text(f"✅ {data.get('message', 'Saved')} (Total: {data.get('total_entries', 0)} entries)")
    except Exception as e:
        await update.message.reply_text("Sorry, the server is unreachable right now.")

    return DIARY_STATE


async def handle_peer_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    user_id = update.message.chat_id

    if text == "Leave Chat":
        reply_markup = ReplyKeyboardMarkup(MENTAL_HEALTH_KB, resize_keyboard=True)
        if user_id in peer_queue:
            peer_queue.remove(user_id)
            await update.message.reply_text("Left the waiting queue.", reply_markup=reply_markup)
        elif user_id in active_peers:
            partner_id = active_peers[user_id]
            del active_peers[user_id]
            if partner_id in active_peers:
                del active_peers[partner_id]
            
            await update.message.reply_text("You disconnected from the peer chat.", reply_markup=reply_markup)
            try:
                await context.bot.send_message(chat_id=partner_id, text="Your peer disconnected.", reply_markup=reply_markup)
            except:
                pass
        else:
            await update.message.reply_text("You are not in a chat.", reply_markup=reply_markup)
            
        return CHOOSING_MENTAL

    # Attempt to route the message
    if user_id in active_peers:
        partner_id = active_peers[user_id]
        try:
            await context.bot.send_message(chat_id=partner_id, text=f"**Peer:** {text}", parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text("Failed to send message. Partner may have blocked the bot.")
            # Unpair them
            del active_peers[user_id]
            if partner_id in active_peers:
                del active_peers[partner_id]
            reply_markup = ReplyKeyboardMarkup(MENTAL_HEALTH_KB, resize_keyboard=True)
            await update.message.reply_text("You have been disconnected.", reply_markup=reply_markup)
            return CHOOSING_MENTAL
    else:
        await update.message.reply_text("⏳ You are still waiting in the queue. Send 'Leave Chat' to exit.")
        
    return PEER_CHAT_STATE

# --- MAIN ---

def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_MAIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu)],
            CHOOSING_MENTAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_mental_menu)],
            FACT_CHECK_STATE: [MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, handle_fact_check)],
            TELEMEDICINE_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_telemedicine)],
            THERAPIST_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_therapist)],
            DIARY_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_diary)],
            PEER_CHAT_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_peer_chat)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
