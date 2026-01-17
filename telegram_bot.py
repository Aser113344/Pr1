import os
import yt_dlp
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# ==================== الإعدادات ====================
TOKEN = "8077182668:AAFWrEvwYbZnAUx8NBgjw1lhJ-3uyNaWgSA"
DOWNLOAD_PATH = "downloads"

if not os.path.exists(DOWNLOAD_PATH):
    os.makedirs(DOWNLOAD_PATH)

# ==================== دوال التحميل ====================

async def get_video_info(url):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

async def download_video(url, format_id, output_path):
    ydl_opts = {
        'format': format_id,
        'outtmpl': output_path,
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

# ==================== معالجات البوت ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك! أرسل لي رابط فيديو من يوتيوب وسأقوم بتحميله لك.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("الرجاء إرسال رابط يوتيوب صحيح.")
        return

    msg = await update.message.reply_text("جاري جلب معلومات الفيديو... ⏳")
    
    try:
        info = await get_video_info(url)
        title = info.get('title', 'video')
        formats = info.get('formats', [])
        
        keyboard = []
        seen_resolutions = set()
        
        # تصفية الجودات المتاحة (فيديو مع صوت أو فيديو يحتاج دمج)
        for f in formats:
            height = f.get('height')
            if height and height not in seen_resolutions:
                if f.get('vcodec') != 'none':
                    res = f"{height}p"
                    size = f.get('filesize', 0) / (1024 * 1024) if f.get('filesize') else 0
                    label = f"{res} ({size:.1f} MB)" if size > 0 else res
                    keyboard.append([InlineKeyboardButton(label, callback_data=f"dl|{f['format_id']}|{url}")])
                    seen_resolutions.add(height)
        
        # ترتيب الجودات من الأعلى للأقل
        keyboard.sort(key=lambda x: int(x[0].text.split('p')[0]), reverse=True)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await msg.edit_text(f"🎬 *العنوان:* {title}\n\nاختر الجودة المطلوبة للتحميل:", reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        await msg.edit_text(f"حدث خطأ أثناء جلب المعلومات: {str(e)}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('|')
    if data[0] == "dl":
        format_id = data[1]
        url = data[2]
        
        await query.edit_message_text("جاري التحميل... قد يستغرق هذا بعض الوقت حسب حجم الفيديو. ⏳")
        
        try:
            # الحصول على معلومات الفيديو مرة أخرى للحصول على العنوان
            info = await get_video_info(url)
            title = "".join([c for c in info['title'] if c.isalnum() or c in (' ', '.', '_')]).strip()
            file_path = os.path.join(DOWNLOAD_PATH, f"{title}_{format_id}.mp4")
            
            # التحميل
            await download_video(url, format_id, file_path)
            
            # إرسال الملف
            await query.edit_message_text("تم التحميل بنجاح! جاري إرسال الفيديو... 📤")
            with open(file_path, 'rb') as video:
                await context.bot.send_video(chat_id=query.message.chat_id, video=video, caption=f"✅ تم التحميل: {info['title']}")
            
            # حذف الملف بعد الإرسال لتوفير المساحة
            os.remove(file_path)
            await query.delete_message()
            
        except Exception as e:
            await query.edit_message_text(f"حدث خطأ أثناء التحميل أو الإرسال: {str(e)}")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    print("البوت يعمل الآن...")
    application.run_polling()
