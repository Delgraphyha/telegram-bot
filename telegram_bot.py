import os
import threading
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_USERNAME = "@delgraphyha"

# راه‌اندازی سرور Flask برای پاسخ به پورت رندر
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

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
            "🎵 برای استفاده از ربات و دریافت موزیک‌ها، لطفاً ابتدا در کانال ما عضو شوید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text("🎧 عضویت شما تایید شد!\nحالا نام آهنگ مورد نظر خود را بفرستید تا جستجو کنم:")

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
    
    if update.message.chat.type not in ['group', 'supergroup']:
        is_member = await check_subscription(user_id, context)
        if not is_member:
            await update.message.reply_text("⚠️ لطفاً ابتدا در کانال @delgraphyha عضو شوید تا بتوانید از ربات استفاده کنید.")
            return
        
    query_text = update.message.text
    processing_msg = await update.message.reply_text("🔍 در حال جستجوی موزیک...")

    cookies_content = os.getenv("YOUTUBE_COOKIES")
    if cookies_content:
        with open("cookies.txt", "w", encoding="utf-8") as f:
            f.write(cookies_content)

    ydl_opts = {
        'format': 'bestaudio/best',
        'default_search': 'ytsearch1',
        'noplaylist': True,
        'cookiefile': 'cookies.txt',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
        await update.message.reply_text("❌ در جستجوی موزیک خطایی رخ داد.")

def main():
    if not TOKEN:
        print("❌ Error: TELEGRAM_TOKEN not set!")
        return

    # اجرای سرور فلاسگ در یک ترد جداگانه برای باز نگه داشتن پورت رندر
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CallbackQueryHandler(button_callback_handler, pattern="^check_sub$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("Bot is starting via Polling with Flask server...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
