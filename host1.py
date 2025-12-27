# -*- coding: utf-8 -*-
import subprocess
import os
import sys
import zipfile
import shutil
import requests
import re
import logging
import time
import json
import psutil
from typing import Dict, List, Optional, Any
from datetime import datetime

# إعدادات اللوجينج
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("host_system.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==========================================
# 🔧 CONFIGURATION
# ==========================================
TOKEN = '8517733708:AAHhVV1wImoisoab23QRzoREca2FZQ5CzzQ'
ADMIN_ID: List[int] = [7460535883, 2118176057]
CHANNEL = '@N1_ORGANIZATION_1'

MAX_RAM_PER_BOT_MB = 500
CHECK_INTERVAL = 5
AUTO_RESTART = True

BASE_DIR = 'HOSTING_SYSTEM'
BOTS_DIR = os.path.join(BASE_DIR, 'bots')
DATA_DIR = os.path.join(BASE_DIR, 'data')

os.makedirs(BOTS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# متغير لتخزين حالات المستخدمين (مثلاً: ينتظر كتابة اسم مكتبة)
user_input_states: Dict[int, str] = {}

# ==========================================
# 🛡️ ACCESS CONTROL SYSTEM
# ==========================================
class AccessManager:
    def __init__(self):
        self.approved_file = os.path.join(DATA_DIR, 'approved_users.json')
        self.waiting_file = os.path.join(DATA_DIR, 'waiting_list.json')
        self._load_data()

    def _load_data(self):
        try:
            if os.path.exists(self.approved_file):
                with open(self.approved_file, 'r') as f:
                    self.approved = set(json.load(f))
            else:
                self.approved = set(ADMIN_ID)
            
            if os.path.exists(self.waiting_file):
                with open(self.waiting_file, 'r') as f:
                    self.waiting = json.load(f)
            else:
                self.waiting = {}
        except Exception as e:
            logger.error(f"Error loading access data: {e}")
            self.approved = set(ADMIN_ID)
            self.waiting = {}

    def _save_data(self):
        try:
            with open(self.approved_file, 'w') as f:
                json.dump(list(self.approved), f)
            with open(self.waiting_file, 'w') as f:
                json.dump(self.waiting, f)
        except Exception as e:
            logger.error(f"Error saving access data: {e}")

    def is_approved(self, user_id: int) -> bool:
        return user_id in self.approved

    def add_to_waiting(self, user_id: int, username: str):
        if user_id not in self.approved and user_id not in self.waiting:
            self.waiting[str(user_id)] = {
                'username': username,
                'time': datetime.now().isoformat()
            }
            self._save_data()
            return True
        return False

access_manager = AccessManager()

# ==========================================
# ⚙️ BOT INSTANCE MANAGER
# ==========================================
class BotInstance:
    def __init__(self, chat_id: int, file_name: str, folder_path: str, main_script: str):
        self.chat_id = chat_id
        self.name = file_name
        self.folder_path = folder_path
        self.main_script = main_script
        self.process: Optional[subprocess.Popen] = None
        self.venv_path = os.path.join(folder_path, '.venv')
        self.log_file_path = os.path.join(folder_path, 'runtime.log')
        self.start_time = None
        self.restart_count = 0
        self.is_running = False

    def _get_pip_executable(self):
        return os.path.join(self.venv_path, 'bin', 'pip') if os.name != 'nt' else os.path.join(self.venv_path, 'Scripts', 'pip.exe')

    def ensure_venv(self):
        if not os.path.exists(self.venv_path):
            logger.info(f"[{self.name}] Creating Virtual Environment...")
            subprocess.check_call([sys.executable, '-m', 'venv', self.venv_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True

    def install_package(self, package_name: str) -> tuple:
        """تثبيت مكتبة واحدة محددة"""
        try:
            self.ensure_venv()
            pip_exe = self._get_pip_executable()
            # تشغيل أمر التثبيت
            subprocess.check_call([pip_exe, 'install', package_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True, f"✅ تم تثبيت المكتبة `{package_name}` بنجاح."
        except subprocess.CalledProcessError as e:
            return False, f"❌ فشل تثبيت `{package_name}`. تأكد من الاسم الصحيح في PyPI."
        except Exception as e:
            return False, f"❌ حدث خطأ غير متوقع: {str(e)}"

    def start(self):
        if os.path.exists(self.log_file_path):
            os.remove(self.log_file_path)

        self.ensure_venv()
        
        python_executable = os.path.join(self.venv_path, 'bin', 'python') if os.name != 'nt' else os.path.join(self.venv_path, 'Scripts', 'python.exe')
        script_path = os.path.join(self.folder_path, self.main_script)
        
        log_f = open(self.log_file_path, 'w', encoding='utf-8')
        
        self.process = subprocess.Popen(
            [python_executable, script_path],
            stdout=log_f,
            stderr=log_f,
            cwd=self.folder_path
        )
        self.start_time = time.time()
        self.is_running = True
        logger.info(f"[{self.name}] Started PID: {self.process.pid}")

    def stop(self):
        if not self.process: return False
        try:
            parent = psutil.Process(self.process.pid)
            children = parent.children(recursive=True)
            for child in children:
                child.kill()
            parent.kill()
            self.is_running = False
            return True
        except psutil.NoSuchProcess:
            self.is_running = False
            return False
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
            return False

    def get_logs(self, lines=50):
        if not os.path.exists(self.log_file_path):
            return "📂 لا توجد لوجات حالياً."
        try:
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                all_lines = f.readlines()
                if len(all_lines) > lines:
                    return ''.join(all_lines[-lines:])
                return ''.join(all_lines)
        except Exception as e:
            return f"❌ خطأ في قراءة اللوجات: {e}"

    def delete_files(self):
        if os.path.exists(self.folder_path):
            try:
                shutil.rmtree(self.folder_path)
                return True
            except Exception as e:
                logger.error(f"Failed to delete folder: {e}")
                return False
        return False

    def get_memory_usage(self) -> float:
        if not self.process or not self.is_running:
            return 0.0
        try:
            proc = psutil.Process(self.process.pid)
            return proc.memory_info().rss / (1024 * 1024)
        except psutil.NoSuchProcess:
            return 0.0

class HostingManager:
    def __init__(self):
        self.active_bots: Dict[int, BotInstance] = {}

    def run_bot(self, chat_id: int, file_name: str, folder_path: str, main_script: str):
        if chat_id in self.active_bots:
            self.stop_bot(chat_id)
        
        bot_instance = BotInstance(chat_id, file_name, folder_path, main_script)
        bot_instance.start()
        self.active_bots[chat_id] = bot_instance
        return bot_instance

    def stop_bot(self, chat_id: int) -> bool:
        if chat_id in self.active_bots:
            success = self.active_bots[chat_id].stop()
            return success
        return False

    def delete_bot(self, chat_id: int) -> bool:
        if chat_id in self.active_bots:
            bot = self.active_bots[chat_id]
            self.stop_bot(chat_id)
            success = bot.delete_files()
            if success:
                del self.active_bots[chat_id]
            return success
        return False
    
    def install_lib_for_bot(self, chat_id: int, lib_name: str) -> tuple:
        if chat_id in self.active_bots:
            return self.active_bots[chat_id].install_package(lib_name)
        return False, "لا يوجد بوت نشط لتثبيت المكتبات له."

manager = HostingManager()

# ==========================================
# 🤖 ASYNC TELEGRAM BOT UI
# ==========================================
try:
    import telebot.async_telebot as telebot
except ImportError:
    logger.critical("Please install: pip install pyTelegramBotAPI")
    sys.exit(1)

bot = telebot.TeleBot(TOKEN)

def get_control_markup():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    btn_status = telebot.types.InlineKeyboardButton('📊 حالة البوت', callback_data='status')
    btn_logs = telebot.types.InlineKeyboardButton('📜 اللوجات (Logs)', callback_data='logs')
    btn_install = telebot.types.InlineKeyboardButton('📦 تثبيت مكتبة', callback_data='install_libs') # الزر الجديد
    
    btn_stop = telebot.types.InlineKeyboardButton('🔴 إيقاف مؤقت', callback_data='stop')
    btn_delete = telebot.types.InlineKeyboardButton('🗑️ حذف وإلغاء', callback_data='delete')
    
    markup.add(btn_status, btn_install)
    markup.add(btn_logs)
    markup.add(btn_stop, btn_delete)
    return markup

async def send_main_menu(chat_id):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton('📤 رفع بوت جديد', callback_data='upload'))
    await bot.send_message(chat_id, "👇 اختر إجراء:", reply_markup=markup)

# --- Handlers ---
@bot.message_handler(commands=['start'])
async def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"

    if not access_manager.is_approved(user_id):
        is_new = access_manager.add_to_waiting(user_id, username)
        text = "🚫 **خاص - نظام الاستضافة**\n\n"
        if is_new:
            text += "✅ تم رفع طلبك للإدارة."
            for admin in ADMIN_ID:
                try: await bot.send_message(admin, f"🔔 طلب جديد: {user_id} (@{username})")
                except: pass
        else:
            text += "📌 أنت في قائمة الانتظار."
        await bot.send_message(message.chat.id, text, parse_mode="Markdown")
        return

    await send_main_menu(message.chat.id)

# --- معالج النصوص (للتثبيت التفاعلي) ---
@bot.message_handler(content_types=['text'])
async def handle_text_message(message):
    user_id = message.from_user.id
    text = message.text
    
    # التحقق مما إذا كان المستخدم في حالة انتظار لاسم مكتبة
    if user_id in user_input_states and user_input_states[user_id] == 'WAITING_LIB_NAME':
        # المستخدم يريد تثبيت مكتبة
        del user_input_states[user_id] # مسح الحالة
        
        if message.chat.id not in manager.active_bots:
            await bot.reply_to(message, "⚠️ لا يوجد بوت نشط حالياً لتثبيت المكتبات له.")
            return

        # إرسال رسالة جاري التثبيت
        status_msg = await bot.reply_to(message, f"🔄 جاري تثبيت المكتبة: `{text}`...", parse_mode="Markdown")
        
        # تنفيذ التثبيت
        success, result_msg = manager.install_lib_for_bot(message.chat.id, text)
        
        # تحديث الرسالة بالنتيجة
        await bot.edit_message_text(result_msg, status_msg.chat.id, status_msg.message_id, parse_mode="Markdown")
        return

    # إذا لم يكن في حالة تثبيت، يمكننا التعامل مع الأمر كنص عادي (اختياري)
    # حالياً نتجاهل النصوص العادية غير المرتبطة بحالة

# --- File Upload ---
@bot.message_handler(content_types=['document'])
async def handle_file(message):
    user_id = message.from_user.id
    if not access_manager.is_approved(user_id):
        return

    file_info = await bot.get_file(message.document.file_id)
    downloaded_file = await bot.download_file(file_info.file_path)
    file_name = message.document.file_name

    bot_id = f"{user_id}_{int(time.time())}"
    bot_folder = os.path.join(BOTS_DIR, bot_id)
    os.makedirs(bot_folder)

    main_script = None

    try:
        if file_name.endswith('.zip'):
            zip_path = os.path.join(bot_folder, file_name)
            with open(zip_path, 'wb') as f: f.write(downloaded_file)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref: zip_ref.extractall(bot_folder)
            
            for name in ['run.py', 'bot.py', 'main.py', 'app.py', 'index.py']:
                if os.path.exists(os.path.join(bot_folder, name)):
                    main_script = name
                    break
            if not main_script:
                pys = [f for f in os.listdir(bot_folder) if f.endswith('.py')]
                if pys: main_script = pys[0]
        elif file_name.endswith('.py'):
            main_script = file_name
            with open(os.path.join(bot_folder, file_name), 'wb') as f: f.write(downloaded_file)
        
        if not main_script:
            return await bot.reply_to(message, "❌ لم يتم العثور على ملف تشغيل (run.py/bot.py)")

        # التثبيت التلقائي لـ requirements.txt إذا وجد (اختياري، للحفاظ على كفاءة الرفع)
        req_path = os.path.join(bot_folder, 'requirements.txt')
        if os.path.exists(req_path):
            # نقوم بتجهيز venv فقط لسرعة الرفع، التثبيت الكامل يمكن أن يتم يدوياً أو هنا
            # هنا سنعمل venv فقط
            subprocess.check_call([sys.executable, '-m', 'venv', os.path.join(bot_folder, '.venv')], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            msg = await bot.send_message(message.chat.id, "📦 تم العثور على requirements.txt. يمكنك استخدام زر التثبيت لتثبيتها يدوياً أو تأكد من صحة الملف.")
        else:
            msg = await bot.send_message(message.chat.id, f"⚙️ جاري تشغيل {main_script}...")

        manager.run_bot(user_id, file_name, bot_folder, main_script)
        await bot.send_message(message.chat.id, "🎉 **تم تشغيل البوت!**\nاستخدم لوحة التحكم:", reply_markup=get_control_markup())

    except Exception as e:
        logger.error(f"Upload Error: {e}")
        await bot.reply_to(message, f"❌ حدث خطأ: {str(e)}")

# --- Callbacks ---
@bot.callback_query_handler(func=lambda call: call.data == 'upload')
async def ask_upload(call):
    await bot.send_message(call.message.chat.id, "📂 أرسل ملف البوت الآن (.py أو .zip)")

@bot.callback_query_handler(func=lambda call: call.data == 'install_libs')
async def ask_library_name(call):
    """عند الضغط على زر تثبيت المكتبة"""
    user_id = call.message.chat.id
    if user_id not in manager.active_bots:
        return await bot.answer(call, "لا يوجد بوت نشط.")
    
    # تسجيل الحالة بانتظار اسم المكتبة
    user_input_states[user_id] = 'WAITING_LIB_NAME'
    
    # إرسال رسالة للمستخدم
    await bot.send_message(user_id, "✍️ **أرسل اسم المكتبة الآن**\nمثال: `requests`, `telebot`, `pyrogram`", parse_mode="Markdown")
    await bot.answer(call)

@bot.callback_query_handler(func=lambda call: call.data == 'stop')
async def stop_user_bot(call):
    success = manager.stop_bot(call.message.chat.id)
    if success:
        await bot.send_message(call.message.chat.id, "🔴 تم إيقاف البوت مؤقتاً.")
        await bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    else:
        await bot.answer(call, "لا يوجد بوت يعمل.")

@bot.callback_query_handler(func=lambda call: call.data == 'delete')
async def delete_user_bot(call):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("✅ نعم، احذف كل شيء", callback_data='confirm_delete'))
    markup.add(telebot.types.InlineKeyboardButton("❌ إلغاء", callback_data='cancel_delete'))
    await bot.send_message(call.message.chat.id, "⚠️ هل أنت متأكد من حذف البوت والملفات واللوجات نهائياً؟", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'confirm_delete')
async def confirm_delete(call):
    success = manager.delete_bot(call.message.chat.id)
    if success:
        await bot.send_message(call.message.chat.id, "🗑️ تم حذف البوت وملفاته بنجاح.")
        await send_main_menu(call.message.chat.id)
    else:
        await bot.send_message(call.message.chat.id, "❌ فشل الحذف.")

@bot.callback_query_handler(func=lambda call: call.data == 'cancel_delete')
async def cancel_delete(call):
    await bot.answer(call, "تم إلغاء العملية.")

@bot.callback_query_handler(func=lambda call: call.data == 'status')
async def status_user_bot(call):
    bot_inst = manager.active_bots.get(call.message.chat.id)
    if bot_inst and bot_inst.is_running:
        ram = bot_inst.get_memory_usage()
        uptime = int(time.time() - bot_inst.start_time)
        text = f"🟢 **البوت يعمل**\n\n💾 الرام: {ram:.2f} MB\n⏳ التشغيل: {uptime} ثانية\n🔄 إعادة التشغيل: {bot_inst.restart_count}"
    elif bot_inst and not bot_inst.is_running:
        text = "🔴 **البوت متوقف**"
    else:
        text = "⚪ لا يوجد بوت نشط."
    
    await bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == 'logs')
async def show_logs(call):
    bot_inst = manager.active_bots.get(call.message.chat.id)
    if not bot_inst:
        return await bot.answer(call, "لا يوجد بوت لعرض لوجاته.")
    
    logs = bot_inst.get_logs(lines=100)
    if len(logs) > 4000:
        logs = logs[-4000:] + "\n... (تم اقتطاع الباقي)"
    
    if not logs.strip():
        logs = "الملف فارغ."
    
    await bot.send_message(call.message.chat.id, f"📜 **أحدث اللوجات:**\n\n```{logs}```", parse_mode="Markdown")

# ==========================================
# 🚀 MAIN ENTRY POINT
# ==========================================
if __name__ == '__main__':
    import threading
    
    def monitor_resources():
        while True:
            for chat_id, bot in list(manager.active_bots.items()):
                if bot.process.poll() is not None and bot.is_running:
                    logger.warning(f"[{bot.name}] Crashed detected.")
                    bot.is_running = False
                    if AUTO_RESTART and bot.restart_count < 3:
                        bot.restart_count += 1
                        bot.start()
                
                ram_usage = bot.get_memory_usage()
                if ram_usage > MAX_RAM_PER_BOT_MB:
                    logger.warning(f"[{bot.name}] Exceeded RAM limit ({ram_usage:.2f}MB). Killing...")
                    manager.stop_bot(chat_id)
            time.sleep(CHECK_INTERVAL)

    monitor_thread = threading.Thread(target=monitor_resources, daemon=True)
    monitor_thread.start()
    logger.info("Host Bot V3 Started (Interactive Install).")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)