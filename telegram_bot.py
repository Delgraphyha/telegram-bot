import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_USERNAME = "@delgraphyha"

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
            "🎵 برای استفاده از ربات و دریافت فایل‌ها، لطفاً ابتدا در کانال ما عضو شوید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text("🎧 عضویت شما تایید شد! حالا لینک یا نام آهنگ مورد نظر را بفرستید:")

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == "check_sub":
        is_member = await check_subscription(user_id, context)
        if is_member:
            await query.message.edit_text("✅ عضویت شما با موفقیت تایید شد! اکنون می‌توانید درخواست خود را ارسال کنید.")
        else:
            await query.answer("❌ شما هنوز در کانال عضو نشده‌اید. لطفاً ابتدا عضو شوید.", show_alert=True)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_member = await check_subscription(user_id, context)
    
    if not is_member:
        await update.message.reply_text("⚠️ لطفاً ابتدا در کانال @delgraphyha عضو شوید تا بتوانید از ربات استفاده کنید.")
        return
        
    text = update.message.text
    await update.message.reply_text(f"🔍 در حال پردازش درخواست شما برای: {text}")

def main():
    if not TOKEN:
        print("❌ Error: TELEGRAM_TOKEN environment variable not set!")
        return

    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex("^/start"), start_handler))
    app.add_handler(CallbackQueryHandler(button_callback_handler, pattern="^check_sub$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    print("🤖 ربات اینستاگرام و جوین اجباری روشن شد...")
    app.run_polling()

if __name__ == "__main__":
    main()
