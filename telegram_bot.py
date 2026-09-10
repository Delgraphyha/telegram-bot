import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import yt_dlp

# دریافت توکن از متغیرهای محیطی رندر
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_USERNAME = "@delgraphyha"

# بررسی عضویت کاربر در کانال
async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['member', 'creator', 'administrator']:
            return True
    except Exception as e:
        print(f"Error checking subscription: {e}")
    return False

# دستور /start
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_member = await check_subscription(user_id, context)

    if not is_member:
        keyboard = [
            [InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}y")],
            [InlineKeyboardButton("✅ عضو شدم، بررسی کن", callback_data="check_sub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "سلام! برای استفاده از ربات، لطفاً ابتدا در کانال ما عضو شوید:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("خوش آمدید! نام آهنگ یا خواننده را بفرستید تا برایتان دانلود کنم.")

# مدیریت دکمه شیشه‌ای بررسی عضویت
async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    is_member = await check_subscription(user_id, context)

    if is_member:
        await query.edit_message_text("✅ عضویت شما تایید شد! حالا می‌توانید نام آهنگ مورد نظر خود را بفرستید.")
    else:
        await query.answer("❌ شما هنوز در کانال عضو نشده‌اید!", show_alert=True)

# پردازش پیام‌ها و دانلود موزیک
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if update.message.chat.type not in ['group', 'supergroup']:
        is_member = await check_subscription(user_id, context)
        if not is_member:
            await update.message.reply_text("⚠️ لطفاً ابتدا در کانال @delgraphyha عضو شوید تا بتوانید از ربات استفاده کنید.")
            return
        
    query_text = update.message.text
    processing_msg = await update.message.reply_text("🔍 در حال جستجوی موزیک...")

    try:
        cookies_content = os.getenv("YOUTUBE_COOKIES")
        if cookies_content:
            with open("cookies.txt", "w", encoding="utf-8") as f:
                f.write(cookies_content)

        ydl_opts = {
            'format': 'bestaudio/best',
            'default_search': 'auto',
            'noplaylist': True,
            'ignoreerrors': True,
            'outtmpl': 'song.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query_text, download=True)
            if info and 'entries' in info:
                entries = info.get('entries')
                if entries:
                    info = entries[0]
            
            if not info:
                await update.message.reply_text("❌ متأسفانه فایلی پیدا نشد.")
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=processing_msg.message_id)
                return

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

    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CallbackQueryHandler(button_callback_handler, pattern="^check_sub$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    PORT = int(os.environ.get("PORT", 10000))
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
    
    if RENDER_URL:
        webhook_url = f"{RENDER_URL.rstrip('/')}/{TOKEN}"
        print(f"Starting webhook on {webhook_url}")
        
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=webhook_url
        )
    else:
        print("Starting polling...")
        application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
