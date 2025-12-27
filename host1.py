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
ADMIN_ID = [7460535883, 2118176057]
CHANNEL = '@N1_ORGANIZATION_1'

MAX_RAM_PER_BOT_MB = 40000
CHECK_INTERVAL = 5
AUTO_RESTART = True

BASE_DIR = 'HOSTING_SYSTEM'
BOTS_DIR = os.path.join(BASE_DIR, 'bots')
DATA_DIR = os.path.join(BASE_DIR, 'data')

os.makedirs(BOTS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

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
# ⚙️ BOT INSTANCE MANAGER (Process Isolation)
# ==========================================
class BotInstance:
    def __init__(self, chat_id: int, file_name: str, folder_path: str, main_script: str):
        self.chat_id = chat_id
        self.name = file_name
        self.folder_path = folder_path
        self.main_script = main_script
        self.process = None
        self.venv_path = os.path.join(folder_path, '.venv')
        self.log_file_path = os.path.join(folder_path, 'runtime.log')
        self.start_time = None
        self.restart_count = 0
        self.is_running = False

    def _get_pip_executable(self):
        if os.name == 'nt':
            return os.path.join(self.venv_path, 'Scripts', 'pip.exe')
        return os.path.join(self.venv_path, 'bin', 'pip')

    def ensure_venv(self):
        if not os.path.exists(self.venv_path):
            logger.info(f"[{self.name}] Creating Virtual Environment...")
            subprocess.check_call([sys.executable, '-m', 'venv', self.venv_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True

    def install_package(self, package_name: str, bot_instance, chat_id):
        """تثبيت مكتبة وإرسال النتيجة للمستخدم"""
        try:
            self.ensure_venv()
            pip_exe = self._get_pip_executable()
            
            # إرسال رسالة جاري التثبيت
            msg = bot_instance.send_message(chat_id, f"🔄 جاري تثبيت `{package_name}`...", parse_mode="Markdown")
            
            subprocess.check_call([pip_exe, 'install', package_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            bot_instance.edit_message_text(f"✅ تم تثبيت `{package_name}` بنجاح.", chat_id, msg.message_id, parse_mode="Markdown")
            return True
        except subprocess.CalledProcessError:
            bot_instance.edit_message_text(f"❌ فشل تثبيت `{package_name}`. تأكد من الاسم.", chat_id, msg.message_id, parse_mode="Markdown")
            return False
        except Exception as e:
            bot_instance.edit_message_text(f"❌ خطأ: {str(e)}", chat_id, msg.message_id)
            return False

    def start(self, bot_instance, chat_id):
        if os.path.exists(self.log_file_path):
            os.remove(self.log_file_path)

        self.ensure_venv()
        
        python_exe = os.path.join(self.venv_path, 'bin', 'python') if os.name != 'nt' else os.path.join(self.venv_path, 'Scripts', 'python.exe')
        script_path = os.path.join(self.folder_path, self.main_script)
        
        log_f = open(self.log_file_path, 'w', encoding='utf-8')
        
        self.process = subprocess.Popen(
            [python_exe, script_path],
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
        self.active_bots = {}

    def run_bot(self, chat_id, file_name, folder_path, main_script, bot_instance):
        if chat_id in self.active_bots:
            self.stop_bot(chat_id)
        
        bot_obj = BotInstance(chat_id, file_name, folder_path, main_script)
        bot_obj.start(bot_instance, chat_id)
        self.active_bots[chat_id] = bot_obj
        return bot_obj

    def stop_bot(self, chat_id) -> bool:
        if chat_id in self.active_bots:
            return self.active_bots[chat_id].stop()
        return False

    def delete_bot(self, chat_id) -> bool:
        if chat_id in self.active_bots:
            bot = self.active_bots[chat_id]
            self.stop_bot(chat_id)
            success = bot.delete_files()
            if success:
                del self.active_bots[chat_id]
            return success
        return False

manager = HostingManager()

# ==========================================
# 🤖 TELEGRAM BOT (SYNC VERSION)
# ==========================================
import telebot
from telebot import types

bot = telebot.TeleBot(TOKEN)

def get_control_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_status = types.InlineKeyboardButton('📊 حالة البوت', callback_data='status')
    btn_install = types.InlineKeyboardButton('📦 تثبيت مكتبة', callback_data='install_libs')
    btn_logs = types.InlineKeyboardButton('📜 اللوجات (Logs)', callback_data='logs')
    
    btn_stop = types.InlineKeyboardButton('🔴 إيقاف مؤقت', callback_data='stop')
    btn_delete = types.InlineKeyboardButton('🗑️ حذف وإلغاء', callback_data='delete')
    
    markup.add(btn_status, btn_install)
    markup.add(btn_logs)
    markup.add(btn_stop, btn_delete)
    return markup

def send_main_menu(chat_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('📤 رفع بوت جديد', callback_data='upload'))
    bot.send_message(chat_id, "👇 اختر إجراء:", reply_markup=markup)

# --- Handlers ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"

    if not access_manager.is_approved(user_id):
        is_new = access_manager.add_to_waiting(user_id, username)
        text = "🚫 **خاص - نظام الاستضافة**\n\n"
        if is_new:
            text += "✅ تم رفع طلبك للإدارة."
            for admin in ADMIN_ID:
                try: bot.send_message(admin, f"🔔 طلب جديد: {user_id} (@{username})")
                except: pass
        else:
            text += "📌 أنت في قائمة الانتظار."
        bot.send_message(message.chat.id, text, parse_mode="Markdown")
        return

    send_main_menu(message.chat.id)

# --- File Upload ---
@bot.message_handler(content_types=['document'])
def handle_file(message):
    user_id = message.from_user.id
    if not access_manager.is_approved(user_id):
        return

    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
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
            return bot.reply_to(message, "❌ لم يتم العثور على ملف تشغيل (run.py/bot.py)")

        manager.run_bot(user_id, file_name, bot_folder, main_script, bot)
        bot.send_message(message.chat.id, "🎉 **تم تشغيل البوت!**\nاستخدم لوحة التحكم:", reply_markup=get_control_markup())

    except Exception as e:
        logger.error(f"Upload Error: {e}")
        bot.reply_to(message, f"❌ حدث خطأ: {str(e)}")

# --- Interactive Lib Install Handler ---
def process_lib_install(message):
    chat_id = message.chat.id
    lib_name = message.text
    
    # التحقق من أن المستخدم لديه بوت نشط
    if chat_id not in manager.active_bots:
        bot.send_message(chat_id, "⚠️ لا يوجد بوت نشط حالياً لتثبيت المكتبات له.")
        send_main_menu(chat_id)
        return
    
    # تنفيذ التثبيت
    manager.active_bots[chat_id].install_package(lib_name, bot, chat_id)

# --- Callbacks ---
@bot.callback_query_handler(func=lambda call: call.data == 'upload')
def ask_upload(call):
    bot.send_message(call.message.chat.id, "📂 أرسل ملف البوت الآن (.py أو .zip)")

@bot.callback_query_handler(func=lambda call: call.data == 'install_libs')
def ask_library_name(call):
    if call.message.chat.id not in manager.active_bots:
        return bot.answer(call, "لا يوجد بوت نشط.")
    
    msg = bot.send_message(call.message.chat.id, "✍️ **أرسل اسم المكتبة الآن**\nمثال: `requests`, `telebot`", parse_mode="Markdown")
    # تسجيل الخطوة التالية
    bot.register_next_step_handler(msg, process_lib_install)
    bot.answer(call)

@bot.callback_query_handler(func=lambda call: call.data == 'stop')
def stop_user_bot(call):
    success = manager.stop_bot(call.message.chat.id)
    if success:
        bot.send_message(call.message.chat.id, "🔴 تم إيقاف البوت مؤقتاً.")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    else:
        bot.answer(call, "لا يوجد بوت يعمل.")

@bot.callback_query_handler(func=lambda call: call.data == 'delete')
def delete_user_bot(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ نعم، احذف كل شيء", callback_data='confirm_delete'))
    markup.add(types.InlineKeyboardButton("❌ إلغاء", callback_data='cancel_delete'))
    bot.send_message(call.message.chat.id, "⚠️ هل أنت متأكد من حذف البوت والملفات واللوجات نهائياً؟", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'confirm_delete')
def confirm_delete(call):
    success = manager.delete_bot(call.message.chat.id)
    if success:
        bot.send_message(call.message.chat.id, "🗑️ تم حذف البوت وملفاته بنجاح.")
        send_main_menu(call.message.chat.id)
    else:
        bot.send_message(call.message.chat.id, "❌ فشل الحذف.")

@bot.callback_query_handler(func=lambda call: call.data == 'cancel_delete')
def cancel_delete(call):
    bot.answer(call, "تم إلغاء العملية.")

@bot.callback_query_handler(func=lambda call: call.data == 'status')
def status_user_bot(call):
    bot_inst = manager.active_bots.get(call.message.chat.id)
    if bot_inst and bot_inst.is_running:
        ram = bot_inst.get_memory_usage()
        uptime = int(time.time() - bot_inst.start_time)
        text = f"🟢 **البوت يعمل**\n\n💾 الرام: {ram:.2f} MB\n⏳ التشغيل: {uptime} ثانية"
    elif bot_inst and not bot_inst.is_running:
        text = "🔴 **البوت متوقف**"
    else:
        text = "⚪ لا يوجد بوت نشط."
    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == 'logs')
def show_logs(call):
    bot_inst = manager.active_bots.get(call.message.chat.id)
    if not bot_inst:
        return bot.answer(call, "لا يوجد بوت لعرض لوجاته.")
    
    log_path = bot_inst.log_file_path
    if not os.path.exists(log_path):
        return bot.answer(call, "لا توجد لوجات.")
    
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            logs = f.read()
    except:
        logs = "خطأ في القراءة"

    if len(logs) > 4000:
        logs = logs[-4000:] + "\n... (تم الاقتطاع)"
    
    if not logs.strip():
        logs = "الملف فارغ."
    
    bot.send_message(call.message.chat.id, f"📜 **أحدث اللوجات:**\n\n```{logs}```", parse_mode="Markdown")

# ==========================================
# 🚀 MAIN ENTRY POINT
# ==========================================
if __name__ == '__main__':
    import threading
    
    def monitor_resources():
        while True:
            for chat_id, bot_obj in list(manager.active_bots.items()):
                if bot_obj.process.poll() is not None and bot_obj.is_running:
                    logger.warning(f"[{bot_obj.name}] Crashed detected.")
                    bot_obj.is_running = False
                    if AUTO_RESTART and bot_obj.restart_count < 3:
                        bot_obj.restart_count += 1
                        bot_obj.start(bot, chat_id)
                
                ram_usage = bot_obj.get_memory_usage()
                if ram_usage > MAX_RAM_PER_BOT_MB:
                    logger.warning(f"[{bot_obj.name}] Exceeded RAM limit ({ram_usage:.2f}MB). Killing...")
                    manager.stop_bot(chat_id)
            time.sleep(CHECK_INTERVAL)

    monitor_thread = threading.Thread(target=monitor_resources, daemon=True)
    monitor_thread.start()
    
    logger.info("Host Bot (Sync) Started on Python 3.8")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)