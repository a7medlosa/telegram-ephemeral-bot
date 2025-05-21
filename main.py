from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler
import asyncio
import json
import os
from flask import Flask
from threading import Thread
import pytz

# إعداد Flask
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "✅ Telegram bot is running."

def run_web():
    web_app.run(host='0.0.0.0', port=8080)

# إعدادات البوت
TOKEN = os.getenv("BOT_TOKEN")
SETTINGS_FILE = "settings.json"
DEFAULT_DELAY = 10

def load_delay():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f).get("delay", DEFAULT_DELAY)
    return DEFAULT_DELAY

def save_delay(value):
    with open(SETTINGS_FILE, "w") as f:
        json.dump({"delay": value}, f)

delete_delay = load_delay()

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if update.effective_chat.type == "private":
        return True
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
        status = getattr(member.status, "value", member.status)
        return status in ["administrator", "creator"]
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text("❌ هذا الأمر مسموح للمشرفين فقط.")

    await update.message.reply_text(
        f"👋 أهلاً! أنا بوت بحذف الرسائل تلقائيًا بعد {delete_delay} ثانية.\n"
        f"تقدر تغير الوقت بالأمر: /settime 15"
    )

async def settime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global delete_delay
    if not await is_admin(update, context):
        return await update.message.reply_text("❌ هذا الأمر مسموح للمشرفين فقط.")
    try:
        new_time = int(context.args[0])
        if not (1 <= new_time <= 300):
            return await update.message.reply_text("❌ من فضلك اختر رقم بين 1 و 300 ثانية.")
        delete_delay = new_time
        save_delay(delete_delay)
        await update.message.reply_text(f"⏱️ تم تغيير وقت الحذف إلى {delete_delay} ثانية.")
    except:
        await update.message.reply_text("❗ استخدم الأمر هكذا:\n/settime 15")

async def delete_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    await asyncio.sleep(delete_delay)
    try:
        await context.bot.delete_message(chat_id=message.chat_id, message_id=message.message_id)
    except Exception as e:
        print(f"⚠️ خطأ أثناء الحذف: {e}")

if __name__ == '__main__':
    Thread(target=run_web).start()

    app = ApplicationBuilder().token(TOKEN).timezone(pytz.utc).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("settime", settime))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO | filters.VIDEO, delete_user_message))

    print("✅ البوت يعمل على Railway...")
    app.run_polling()
