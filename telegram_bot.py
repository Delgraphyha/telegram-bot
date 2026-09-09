import os
import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp

TOKEN = os.getenv("TELEGRAM_TOKEN")
PORT = int(os.environ.get("PORT", "10000"))
CHANNEL_USERNAME = "@delgraphyha"

app = Flask(__name__)
telegram_app = None

async def check_subscription(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception as e:
        print(f"Error checking sub: {e}")
    return False

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_member = await check_subscription(user_id, context)
    
    if not is_member:
        keyboard = [
            [InlineKeyboardButton("📢 عضویت در کانال دلگرافیها", url="https://t.me/delgraphyha")],
            [InlineKeyboardButton("✅ عضو شدم، بررسی مجدد", callback_data="check_sub")]
        ]
        await update.message.reply_text(
            "🎵 برای استفاده از ربات و دریافت موزیک‌های فارسی و خارجی، لطفاً ابتدا در کانال ما عضو شوید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text("🎧 عضویت شما تایید شد!\nحالا نام آهنگ فارسی یا خارجی مورد نظر خود را بفرستید تا نمونه کوتاه یا فایل آن را دریافت کنید:")

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == "check_sub":
        is_member = await check_subscription(user_id, context)
        if is_member:
            await query.message.edit_text("✅ عضویت شما تایید شد! اکنون می‌توانید نام آهنگ خود را ارسال کنید.")
        else:
            await query.answer("❌ شما هنوز در کانال عضو نشده‌اید.", show_alert=True)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_member = await check_subscription(user_id, context)
    
    if not is_member:
        await update.message.reply_text("⚠️ لطفاً ابتدا در کانال @delgraphyha عضو شوید تا بتوانید از ربات استفاده کنید.")
        return
        
    query_text = update.message.text
    processing_msg = await update.message.reply_text("🔍 در حال جستجوی آهنگ فارسی/خارجی مورد نظر...")

    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'default_search': 'ytsearch1',
            'noplaylist': True,
            'outtmpl': 'song.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query_text, download=True)
            if 'entries' in info:
                info = info['entries'][0]
            
            title = info.get('title', 'Unknown')
            file_path = "song.mp3"

            if os.path.exists(file_path):
                # ارسال نمونه ۱۵ ثانیه‌ای یا خود فایل
                await update.message.reply_audio(
                    audio=open(file_path, 'rb'),
                    title=title,
                    caption=f"🎵 {title}\n🔗 دریافت شده از ربات دلگرافیها"
                )
                os.remove(file_path)
            else:
                await update.message.reply_text("❌ متأسفانه فایلی پیدا نشد.")
        
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=processing_msg.message_id)

    except Exception as e:
        print(f"Error downloading music: {e}")
        await update.message.reply_text("❌ در پردازش درخواست شما خطایی رخ داد. لطفاً دوباره تلاش کنید.")

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    asyncio_run(telegram_app.process_update(update))
    return "ok", 200

@app.route("/")
def index():
    return "Bot is running!", 200

def asyncio_run(coro):
    import asyncio
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)

def main():
    global telegram_app
    if not TOKEN:
        print("❌ Error: TELEGRAM_TOKEN not set!")
        return

    telegram_app = ApplicationBuilder().token(TOKEN].build()
    
    telegram_app.add_handler(MessageHandler(filters.COMMAND & filters.Regex("^/start"), start_handler))
    telegram_app.add_handler(CallbackQueryHandler(button_callback_handler, pattern="^check_sub$"))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    asyncio_run(telegram_app.initialize())
    
    RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
    if RENDER_EXTERNAL_URL:
        webhook_url = f"{RENDER_EXTERNAL_URL}/{TOKEN}"
        asyncio_run(telegram_app.bot.set_webhook(webhook_url))
        print(f"Webhook set to: {webhook_url}")

    app.run(host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    main()
