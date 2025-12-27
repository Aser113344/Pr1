import os
import logging
import zipfile
import subprocess
import signal
import psutil
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from database_manager import DatabaseManager

# الإعدادات الجديدة بالمسار الثابت
BASE_DIR = "/root/Pr1"
TOKEN = "8517733708:AAHhVV1wImoisoab23QRzoREca2FZQ5CzzQ"
ADMIN_ID = [123456789, 7460535883, 2118176057]
USERS_DIR = os.path.join(BASE_DIR, "users_data")
DB_PATH = os.path.join(BASE_DIR, "database/hosting.db")

# التأكد من وجود المجلدات الأساسية
os.makedirs(USERS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# تهيئة قاعدة البيانات
db = DatabaseManager(DB_PATH)

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    db.add_user(user.id, user.username, is_admin=(user.id == ADMIN_ID))
    
    if db.is_blocked(user.id):
        update.message.reply_text("❌ أنت محظور من استخدام هذا البوت.")
        return

    keyboard = [
        [InlineKeyboardButton("▶ تشغيل البوت", callback_query_data='run_bot'),
         InlineKeyboardButton("⏹ إيقاف البوت", callback_query_data='stop_bot')],
        [InlineKeyboardButton("📦 تحميل مكتبة", callback_query_data='install_lib')],
        [InlineKeyboardButton("📊 حالة البوت", callback_query_data='bot_status')]
    ]
    
    if db.is_admin(user.id):
        keyboard.append([InlineKeyboardButton("⚙ لوحة الأدمن", callback_query_data='admin_panel')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        f"👋 أهلاً بك {user.first_name} في بوت الاستضافة!\n\n"
        f"📍 المسار الحالي: `{BASE_DIR}`\n"
        "🚀 يمكنك رفع ملفات .py أو .zip لتشغيل بوتك الخاص.\n"
        "📂 تأكد أن ملف الـ zip يحتوي على main.py.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

def handle_document(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if db.is_blocked(user_id): return

    doc = update.message.document
    file_name = doc.file_name
    user_path = os.path.join(USERS_DIR, str(user_id))
    os.makedirs(user_path, exist_ok=True)

    file_path = os.path.join(user_path, file_name)
    new_file = context.bot.get_file(doc.file_id)
    new_file.download(file_path)

    if file_name.endswith('.zip'):
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(user_path)
            
            if os.path.exists(os.path.join(user_path, 'main.py')):
                update.message.reply_text("✅ تم فك الضغط بنجاح. تم العثور على main.py.")
                run_bot_logic(user_id, update)
            else:
                update.message.reply_text("❌ خطأ: لم يتم العثور على ملف main.py داخل الـ zip.")
        except Exception as e:
            update.message.reply_text(f"❌ حدث خطأ أثناء فك الضغط: {str(e)}")

    elif file_name.endswith('.py'):
        target_path = os.path.join(user_path, 'main.py')
        if os.path.exists(target_path): os.remove(target_path)
        os.rename(file_path, target_path)
        update.message.reply_text("✅ تم رفع ملف البوت بنجاح.")
        run_bot_logic(user_id, update)
    else:
        update.message.reply_text("⚠️ يرجى رفع ملفات .py أو .zip فقط.")

def run_bot_logic(user_id, update_or_context):
    user_path = os.path.join(USERS_DIR, str(user_id))
    main_file = os.path.join(user_path, 'main.py')
    
    if not os.path.exists(main_file):
        message = "❌ لا يوجد ملف main.py لتشغيله."
        if isinstance(update_or_context, Update): update_or_context.message.reply_text(message)
        else: update_or_context.bot.send_message(chat_id=user_id, text=message)
        return

    stop_bot_logic(user_id)

    try:
        process = subprocess.Popen(
            ['python3.8', 'main.py'],
            cwd=user_path,
            stdout=open(os.path.join(user_path, 'bot.log'), 'a'),
            stderr=subprocess.STDOUT
        )
        db.update_bot_status(user_id, process.pid, 'main.py', 'running')
        
        message = f"🚀 تم تشغيل البوت بنجاح! (PID: {process.pid})"
        if isinstance(update_or_context, Update): update_or_context.message.reply_text(message)
        else: update_or_context.bot.send_message(chat_id=user_id, text=message)
    except Exception as e:
        message = f"❌ فشل تشغيل البوت: {str(e)}"
        if isinstance(update_or_context, Update): update_or_context.message.reply_text(message)
        else: update_or_context.bot.send_message(chat_id=user_id, text=message)

def stop_bot_logic(user_id):
    bot_info = db.get_bot_info(user_id)
    if bot_info and bot_info[2] == 'running':
        pid = bot_info[0]
        try:
            parent = psutil.Process(pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
            db.update_bot_status(user_id, None, bot_info[1], 'stopped')
            return True
        except:
            db.update_bot_status(user_id, None, bot_info[1], 'stopped')
            return False
    return False

def admin_panel(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("👥 قائمة المستخدمين", callback_query_data='admin_list_users')],
        [InlineKeyboardButton("📢 رسالة جماعية", callback_query_data='admin_broadcast')],
        [InlineKeyboardButton("🚫 حظر مستخدم", callback_query_data='admin_block_user'),
         InlineKeyboardButton("✅ إلغاء حظر", callback_query_data='admin_unblock_user')],
        [InlineKeyboardButton("🔙 العودة", callback_query_data='back_to_main')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"⚙ لوحة تحكم الأدمن\n\nعدد المستخدمين: {len(db.get_all_users())}"
    if update.callback_query:
        update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        update.message.reply_text(text, reply_markup=reply_markup)

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()

    if db.is_blocked(user_id): return

    if query.data == 'run_bot':
        run_bot_logic(user_id, context)
    elif query.data == 'stop_bot':
        if stop_bot_logic(user_id):
            query.edit_message_text("⏹ تم إيقاف البوت بنجاح.")
        else:
            query.edit_message_text("⚠️ البوت ليس قيد التشغيل حالياً.")
    elif query.data == 'bot_status':
        bot_info = db.get_bot_info(user_id)
        status = bot_info[2] if bot_info else "غير موجود"
        query.edit_message_text(f"📊 حالة بوتك: {status}")
    elif query.data == 'install_lib':
        query.edit_message_text("📦 أرسل اسم المكتبة التي تريد تحميلها (مثال: requests):")
        context.user_data['awaiting_lib'] = True
    elif query.data == 'admin_panel' and db.is_admin(user_id):
        admin_panel(update, context)
    elif query.data == 'admin_list_users' and db.is_admin(user_id):
        users = db.get_all_users()
        text = "👥 قائمة المستخدمين:\n\n"
        for uid, uname in users:
            text += f"ID: `{uid}` | @{uname}\n"
        query.edit_message_text(text, parse_mode='Markdown')
    elif query.data == 'admin_block_user' and db.is_admin(user_id):
        query.edit_message_text("🚫 أرسل ID المستخدم لحظره:")
        context.user_data['admin_action'] = 'block'
    elif query.data == 'admin_unblock_user' and db.is_admin(user_id):
        query.edit_message_text("✅ أرسل ID المستخدم لإلغاء حظره:")
        context.user_data['admin_action'] = 'unblock'
    elif query.data == 'admin_broadcast' and db.is_admin(user_id):
        query.edit_message_text("📢 أرسل الرسالة التي تريد إرسالها للجميع:")
        context.user_data['admin_action'] = 'broadcast'
    elif query.data == 'back_to_main':
        start(update, context)

def handle_text(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if db.is_blocked(user_id): return

    if context.user_data.get('awaiting_lib'):
        lib_name = update.message.text.strip()
        if not all(c.isalnum() or c in '-_' for c in lib_name):
            update.message.reply_text("❌ اسم مكتبة غير صالح.")
            return
        
        update.message.reply_text(f"⏳ جاري تحميل المكتبة: {lib_name}...")
        try:
            result = subprocess.run(['pip3', 'install', lib_name], capture_output=True, text=True)
            if result.returncode == 0:
                update.message.reply_text(f"✅ تم تحميل {lib_name} بنجاح!")
            else:
                update.message.reply_text(f"❌ فشل التحميل:\n{result.stderr}")
        except Exception as e:
            update.message.reply_text(f"❌ حدث خطأ: {str(e)}")
        context.user_data['awaiting_lib'] = False
        return

    if db.is_admin(user_id) and 'admin_action' in context.user_data:
        action = context.user_data['admin_action']
        text = update.message.text.strip()

        if action == 'block':
            try:
                target_id = int(text)
                db.update_block_status(target_id, True)
                stop_bot_logic(target_id)
                update.message.reply_text(f"🚫 تم حظر المستخدم {target_id} وإيقاف بوتاته.")
            except: update.message.reply_text("❌ ID غير صالح.")
        
        elif action == 'unblock':
            try:
                target_id = int(text)
                db.update_block_status(target_id, False)
                update.message.reply_text(f"✅ تم إلغاء حظر المستخدم {target_id}.")
            except: update.message.reply_text("❌ ID غير صالح.")
        
        elif action == 'broadcast':
            users = db.get_all_users()
            count = 0
            for uid, _ in users:
                try:
                    context.bot.send_message(chat_id=uid, text=f"📢 رسالة من الإدارة:\n\n{text}")
                    count += 1
                except: pass
            update.message.reply_text(f"✅ تم إرسال الرسالة إلى {count} مستخدم.")
        
        del context.user_data['admin_action']
        return

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_document))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
