import sys
import telebot
from telebot import types
import io
import tokenize
import requests
import time
from threading import Thread
import subprocess
import string
from collections import defaultdict
from datetime import datetime
import psutil
import random
import sys
import random
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string
import re
import chardet
import difflib

import google.generativeai as genai 
from bs4 import BeautifulSoup
# إعدادات البوتات
from deep_translator import GoogleTranslator  
from concurrent.futures import ThreadPoolExecutor 
from sympy import sympify
import segno
import os
import logging
import telebot
from telebot import types
import threading
# إعدادات البوتات

mandatory_subscription_channel = 'https://t.me/N1_ORGANIZATION_1'
BOT_TOKEN = '8077182668:AAG8KKLS9ZoWziNEd0KgI6NBiFzCCTS2EwM'
ADMIN_ID = '2118176057'
ADMIN_IDS = ['7460535883', '2118176057']

####   مكسل متحطش دول

VIRUSTOTAL_API_KEY = 'd851c6064844b30083483cbfa5a2001d9ac0b811a666f0110c0efb4eaabf747e'  # هتحط هنا ال api

API_GEMINI = 'AIzaSyA0_MDjHA9CriP14-OZW2aYAhmJ3KeY68M'  # مفتاح API الخاص بـ GMINI

bot_creator = "@N1_ORGANIZATION_1"   # تم التحديث لقناتك الجديدة 

banned_libraries = ['examplelib', 'badlib']  # قائمة المكتبات المحظورة



###### طبعا كل حاجه هتحطها بدون ما تشيل اي اقواس او علامات تنصيص 



### متلعبش ف الحجات دي


banned_users = set()  
bot_scripts1 = defaultdict(lambda: {'processes': [], 'name': '', 'path': '', 'uploader': ''})  # لإدارة العمليات
user_files = {} 
lock = threading.Lock()
executor = ThreadPoolExecutor(max_workers=3000) 
bot = telebot.TeleBot(BOT_TOKEN)
bot_scripts = {}
uploaded_files_dir = "uploaded_files"
user_chats = {}





logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

#################### حذف أي webhook نشط لضمان استخدام polling ############


bot.remove_webhook()

#################### إنشاء مجلد uploaded_files إذا لم يكن موجوداً####################



if not os.path.exists(uploaded_files_dir):
    os.makedirs(uploaded_files_dir)

#################### تحقق من الاشتراك في القناه ###########################



def check_subscription(user_id):
    try:
        # تحقق مما إذا كان المستخدم مشتركًا في القناة
        member_status = bot.get_chat_member(ADMIN_CHANNEL, user_id).status
        return member_status in ['member', 'administrator', 'creator']
    except Exception as e:
        logging.error(f"Error checking subscription: {e}")
        return False


##################### بدايه حظر اشاء معينه وحمايه ########################



def is_safe_file(file_path):
    """دالة للتحقق من أن الملف لا يحتوي على تعليمات لإنشاء أرشيفات أو إرسالها عبر بوت"""
    try:
        with open(file_path, 'rb') as f:
            raw_content = f.read()
            
            # تحقق من ترميز الملف
            encoding_info = chardet.detect(raw_content)
            encoding = encoding_info['encoding']
            
            if encoding is None:
                logging.warning("Unable to detect encoding, file may be binary or encrypted.")
                return "لم يتم رفع الملف فيه اوامر غير مسموح بها"

            # تحويل المحتوى إلى نص باستخدام الترميز المكتشف
            content = raw_content.decode(encoding)
            

            dangerous_patterns = [
                r'\bshutil\.make_archive\b',  # إنشاء أرشيف
                r'bot\.send_document\b',  # إرسال ملفات عبر بوت
                r'\bopen\s*\(\s*.*,\s*[\'\"]w[\'\"]\s*\)',  # فتح ملف للكتابة
                r'\bopen\s*\(\s*.*,\s*[\'\"]a[\'\"]\s*\)',  # فتح ملف للإلحاق
                r'\bopen\s*\(\s*.*,\s*[\'\"]wb[\'\"]\s*\)',  # فتح ملف للكتابة الثنائية
                r'\bopen\s*\(\s*.*,\s*[\'\"]ab[\'\"]\s*\)',  # فتح ملف للإلحاق الثنائي
            ]

            for pattern in dangerous_patterns:
                if re.search(pattern, content):
                    return "لم يتم رفع الملف فيه اوامر غير مسموح بها"

            # تحقق من أن المحتوى نصي وليس مشفرًا
            if not is_text(content):
                return "لم يتم رفع الملف فيه اوامر غير مسموح بها"

        return "الملف آمن"
    except Exception as e:
        logging.error(f"Error checking file safety: {e}")
        return "لم يتم رفع الملف فيه اوامر غير مسموح بها"

def is_text(content):
    """دالة للتحقق مما إذا كان المحتوى نصيًا"""

    for char in content:
        if char not in string.printable:
            return False
    return True

    





    
####################### بدايه الدوال #######################

### حفظ id شات



def save_chat_id(chat_id):
    """دالة لحفظ chat_id للمستخدمين الذين يتفاعلون مع البوت."""
    if chat_id not in user_chats:
        user_chats[chat_id] = True  # يمكنك تخزين معلومات إضافية هنا إذا لزم الأمر
        print(f"تم حفظ chat_id: {chat_id}")
    else:
        print(f"chat_id: {chat_id} موجود بالفعل.")


################################################################## داله البدأ 
# قائمة لحفظ معرفات المستخدمين
user_ids = set()

def save_chat_id(chat_id):
    # إضافة chat_id إلى المجموعة لضمان عدم التكرار
    user_ids.add(chat_id)

@bot.message_handler(commands=['start'])
def start(message):
    # حفظ chat_id عند بدء التفاعل
    save_chat_id(message.chat.id)

    if message.from_user.username in banned_users:
        bot.send_message(message.chat.id, "تم حظرك من البوت. تواصل مع المطور @N1_HUMEN")
        return

    # Check subscription status
    if not check_subscription(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        subscribe_button = types.InlineKeyboardButton("اشترك في القناة", url=mandatory_subscription_channel)
        markup.add(subscribe_button)

        bot.send_message(
            message.chat.id,
            "⚠️ يجب عليك الاشتراك في قناة المطور لاستخدام البوت.\n\n"
            "🔗 اضغط على الزر أدناه للاشتراك:",
            reply_markup=markup
        )
        return

    # إضافة المستخدم إلى bot_scripts
    bot_scripts[message.chat.id] = {
        'name': message.from_user.username,
        'uploader': message.from_user.username,
    }
# إعداد الأزرار والرسائل العامة

    markup = types.InlineKeyboardMarkup()
    upload_button = types.InlineKeyboardButton("رفع ملف 📤", callback_data='upload')
    developer_button = types.InlineKeyboardButton("قناة مطور البوت", url=mandatory_subscription_channel)
    commands_button = types.InlineKeyboardButton("الأوامر", callback_data='commands')
    instructions_button = types.InlineKeyboardButton("تعليمات", callback_data='instructions')

    markup.row(upload_button)
    markup.row(developer_button)
    markup.row(commands_button, instructions_button)

    bot.send_message(
        message.chat.id,
        f"_____________________________________________\n"
        "مرحبًا بك في بوت رفع وتشغيل ملفات بايثون.\n"
        "استخدم الزر بالأسفل لرفع الملفات.\n"
        "_____________________________________________\n"
        f"BOT BY : {bot_creator}",
        reply_markup=markup
    )

# عند استقبال الضغط على زر الأوامر
@bot.callback_query_handler(func=lambda call: call.data == 'commands')
def process_commands_callback(call):
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        "مرحبا بك !\n"
        "الاوامر في البوت هيا\n"
        "/help للمساعده.\n"
        "/cmd اوامر مهمه في البوت \n"
        "/cr اوامر عشوائيه بس تفيد  \n"
        "/adm دي طبعا بتاعت الادمن يقدر يتحكم في البوت من خلال للوحه \n"
        "دي اوامر البوت فقط ليس شرح كامل ."
    )



#####################################################################لوحه الادمن


blocked_users = set()

def is_user_blocked(user_id):
    return user_id in blocked_users

# رسالة للمستخدمين المحظورين
BLOCKED_MESSAGE = f"تم حظرك من البوت. تواصل مع المطور {bot_creator}"
# دالة لإيقاف ملف معين
def stop_bot(script_path, chat_id):
    try:
        script_name = script_path.split('/')[-1]
        process = bot_scripts.get(chat_id, {}).get('process')
        if process and psutil.pid_exists(process.pid):
            parent = psutil.Process(process.pid)
            for child in parent.children(recursive=True):
                child.terminate()
            parent.terminate()
            parent.wait()  # التأكد من أن العملية توقفت
            bot_scripts[chat_id]['process'] = None
            bot.send_message(chat_id, f"تم إيقاف {script_name} بنجاح.")
            return True
        else:
            bot.send_message(chat_id, f"عملية {script_name} غير موجودة أو أنها قد توقفت بالفعل.")
            return False
    except Exception as e:
        logging.error(f"Error stopping bot: {e}")
        bot.send_message(chat_id, f"حدث خطأ أثناء إيقاف {script_name}: {e}")
        return False


def start_file(script_path, chat_id):
    try:
        script_name = script_path.split('/')[-1]
        if bot_scripts.get(chat_id, {}).get('process') and psutil.pid_exists(bot_scripts[chat_id]['process'].pid):
            bot.send_message(chat_id, f"الملف {script_name} يعمل بالفعل.")
            return False
        else:
            p = subprocess.Popen([sys.executable, script_path])
            bot_scripts[chat_id] = {'process': p, 'path': script_path, 'name': script_name}
            bot.send_message(chat_id, f"تم تشغيل {script_name} بنجاح.")
            return True
    except Exception as e:
        logging.error(f"Error starting bot: {e}")
        bot.send_message(chat_id, f"حدث خطأ أثناء تشغيل {script_name}: {e}")
        return False


def stop_all_files(chat_id):
    if is_user_blocked(chat_id):
        bot.send_message(chat_id, BLOCKED_MESSAGE)
        return
    stopped_files = []
    for chat_id, script_info in list(bot_scripts.items()):
        if stop_bot(script_info['path'], chat_id):
            stopped_files.append(script_info['name'])
    if stopped_files:
        bot.send_message(chat_id, f"تم إيقاف الملفات التالية بنجاح: {', '.join(stopped_files)}")
    else:
        bot.send_message(chat_id, "لا توجد ملفات قيد التشغيل لإيقافها.")


def start_all_files(chat_id):
    if is_user_blocked(chat_id):
        bot.send_message(chat_id, BLOCKED_MESSAGE)
        return
    started_files = []
    for chat_id, script_info in list(bot_scripts.items()):
        if start_file(script_info['path'], chat_id):
            started_files.append(script_info['name'])
    if started_files:
        bot.send_message(chat_id, f"تم تشغيل الملفات التالية بنجاح: {', '.join(started_files)}")
    else:
        bot.send_message(chat_id, "لا توجد ملفات متوقفة لتشغيلها.")





logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




banned_users = set()  




instructions_text = ""  
instructions_file = "instructions.txt"  


if os.path.exists(instructions_file):
    with open(instructions_file, 'r') as file:
        instructions_text = file.read()

@bot.message_handler(commands=['adm'])
def admin_panel(message):
    try:
        if message.from_user.id != int(ADMIN_ID):
            bot.reply_to(message, "🚫 ليس لديك صلاحية استخدام هذا الأمر.")
            return

        markup = types.InlineKeyboardMarkup()
        stats_button = types.InlineKeyboardButton("إحصائيات 📊", callback_data='stats')
        ban_button = types.InlineKeyboardButton("حظر مستخدم 🚫", callback_data='ban_user')
        uban_button = types.InlineKeyboardButton("فك حظر مستخدم ✅", callback_data='unban_user')
        rck_button = types.InlineKeyboardButton("إرسال رسالة للجميع 📢", callback_data='broadcast')
        add_instructions_button = types.InlineKeyboardButton("إضافة تعليمات 📝", callback_data='add_instructions')

        markup.add(stats_button)
        markup.add(ban_button, uban_button)
        markup.add(rck_button)
        markup.add(add_instructions_button)

        bot.send_message(message.chat.id, "🔧 لوحة تحكم الأدمن:", reply_markup=markup)
    except Exception as e:
        logging.error(f"Error in admin_panel: {e}")
        bot.reply_to(message, "⚠️ حدث خطأ أثناء محاولة عرض لوحة التحكم.")




############# احصائيالت


@bot.callback_query_handler(func=lambda call: call.data == 'stats')
def show_statistics(call):
    try:
        total_users = len(user_ids)
        bot.send_message(call.message.chat.id, f"(———————————)\n\nاحصائيات بوتك :\nعدد المستخدمين : {total_users}\n\n(———————————)")
    except Exception as e:
        logging.error(f"Error in show_statistics: {e}")
        bot.send_message(call.message.chat.id, "⚠️ حدث خطأ أثناء عرض الإحصائيات.")

#### تقدر تضيف اكتر بس الموضوع متعبت ولو انت مش محترف متلعبش ف حاجه


#### تعليمات البوت !

@bot.callback_query_handler(func=lambda call: call.data == 'instructions')
def process_instructions_callback(call):
    bot.answer_callback_query(call.id)
    if instructions_text:
        bot.send_message(call.message.chat.id, instructions_text)
    else:
        bot.send_message(call.message.chat.id, "لا توجد تعليمات متاحة حاليًا.")

@bot.callback_query_handler(func=lambda call: call.data == 'add_instructions')
def request_instructions(call):
    if call.from_user.id != int(ADMIN_ID):
        bot.send_message(call.message.chat.id, "🚫 ليس لديك صلاحية استخدام هذا الأمر.")
        return

    bot.send_message(call.message.chat.id, "📝 اكتب التعليمات التي تريد إضافتها:")
    bot.register_next_step_handler(call.message, save_instructions)

def save_instructions(message):
    global instructions_text
    if message.from_user.id != int(ADMIN_ID):
        bot.send_message(message.chat.id, "🚫 ليس لديك صلاحية استخدام هذا الأمر.")
        return

    instructions_text = message.text.strip()
    with open(instructions_file, 'w') as file:
        file.write(instructions_text)

    bot.send_message(message.chat.id, "✅ تم حفظ التعليمات بنجاح.")




###### داله ارسال رساله لشخص


@bot.callback_query_handler(func=lambda call: call.data == 'send_private_message')
def request_user_id_for_message(call):
    bot.send_message(call.message.chat.id, "📝 أدخل معرف المستخدم أو الـID للشخص الذي تريد إرسال رسالة إليه:")
    bot.register_next_step_handler(call.message, get_user_id_for_message)

def get_user_id_for_message(message):
    user_id_or_username = message.text.strip().lstrip('@')
    if user_id_or_username:
        if is_user_in_bot(user_id_or_username):
            bot.send_message(message.chat.id, "📨 أدخل الرسالة التي تريد إرسالها:")
            bot.register_next_step_handler(message, process_and_send_message, user_id_or_username)
        else:
            bot.send_message(message.chat.id, f"❌ تعذر العثور على المستخدم {user_id_or_username}. تأكد من إدخال الاسم أو الـID بشكل صحيح.")
    else:
        bot.send_message(message.chat.id, "⚠️ لم يتم إدخال معرف مستخدم صالح.")

def process_and_send_message(message, user_id_or_username):
    msg = message.text.strip()
    if not msg:
        bot.send_message(message.chat.id, "⚠️ لم يتم إدخال رسالة صالحة.")
        return

    try:
        chat_id = None
        if user_id_or_username.isdigit():
            chat_id = int(user_id_or_username)
        else:
            chat_id = next((cid for cid, info in bot_scripts.items() if info.get('uploader', '').lower() == user_id_or_username.lower()), None)

        if chat_id:
            bot.send_message(chat_id, msg)
            bot.send_message(message.chat.id, "✅ تم إرسال الرسالة بنجاح.")
        else:
            bot.send_message(message.chat.id, f"❌ تعذر العثور على المستخدم {user_id_or_username}. تأكد من إدخال الاسم أو الـID بشكل صحيح.")
    except Exception as send_error:
        logging.error(f"Error sending message to {user_id_or_username}: {send_error}")
        bot.send_message(message.chat.id, f"⚠️ حدث خطأ أثناء إرسال الرسالة إلى المستخدم {user_id_or_username}.")

def is_user_in_bot(username_or_id):
    """ تحقق مما إذا كان المستخدم موجودًا في بيانات البوت """
    if username_or_id.isdigit():
        return int(username_or_id) in bot_scripts
    else:
        return any(info.get('uploader', '').lower() == username_or_id.lower() for info in bot_scripts.values())
    









### بدايه دوال لوحه الادمن

ADMIN_CHANNEL = '@N1_ORGANIZATION_1'
# دالة لمعالجة الأوامر من لوحة التحكم
@bot.callback_query_handler(func=lambda call: call.data in ['stop_all', 'start_all', 'broadcast', 'ban_user', 'unban_user'])
def handle_admin_callbacks(call):
    try:
        if is_user_blocked(call.from_user.username):
            bot.answer_callback_query(call.id, BLOCKED_MESSAGE)
            return
        if str(call.from_user.id) != ADMIN_ID:
            bot.answer_callback_query(call.id, "ليس لديك صلاحية استخدام هذا الأمر.")
            return

        if call.data == 'stop_all':
            stop_all_files(call.message.chat.id)
            bot.answer_callback_query(call.id, "تم إيقاف جميع الملفات.")
        elif call.data == 'start_all':
            start_all_files(call.message.chat.id)
            bot.answer_callback_query(call.id, "تم تشغيل جميع الملفات.")
        elif call.data == 'broadcast':
            bot.send_message(call.message.chat.id, "يرجى كتابة الرسالة لإرسالها للجميع.")
            bot.register_next_step_handler(call.message, handle_broadcast_message)
        elif call.data == 'ban_user':
            bot.send_message(call.message.chat.id, "يرجى كتابة معرف المستخدم لحظره.")
            bot.register_next_step_handler(call.message, ban_user_handler)
        elif call.data == 'unban_user':
            bot.send_message(call.message.chat.id, "يرجى كتابة معرف المستخدم لفك حظره.")
            bot.register_next_step_handler(call.message, unban_user_handler)
    except Exception as e:
        logger.error(f"Error in handle_admin_callbacks: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ أثناء معالجة الأمر.")

# دالة لحظر مستخدم بناءً على الإدخال من الأدمن
def ban_user_handler(message):
    try:
        username = message.text.strip('@')
        if username in banned_users:
            bot.reply_to(message, f"المستخدم @{username} محظور بالفعل.")
        else:
            banned_users.add(username)
            bot.reply_to(message, f"تم حظر المستخدم @{username}.")
    except Exception as e:
        logger.error(f"Error in ban_user_handler: {e}")
        bot.reply_to(message, "حدث خطأ أثناء محاولة حظر المستخدم.")

# دالة لفك حظر مستخدم بناءً على الإدخال من الأدمن
def unban_user_handler(message):
    try:
        username = message.text.strip('@')
        if username not in banned_users:
            bot.reply_to(message, f"المستخدم @{username} ليس محظور.")
        else:
            banned_users.remove(username)
            bot.reply_to(message, f"تم فك حظر المستخدم @{username}.")
    except Exception as e:
        logger.error(f"Error in unban_user_handler: {e}")
        bot.reply_to(message, "حدث خطأ أثناء محاولة فك حظر المستخدم.")

# دالة لمعالجة إرسال الرسائل الجماعية
def handle_broadcast_message(message):
    try:
        msg = message.text
        for chat_id in bot_scripts.keys():
            try:
                bot.send_message(chat_id, msg)
            except Exception as e:
                logger.error(f"Error sending message to {chat_id}: {e}")
        bot.reply_to(message, "تم إرسال الرسالة بنجاح.")
    except Exception as e:
        logger.error(f"Error in handle_broadcast_message: {e}")
        bot.reply_to(message, "حدث خطأ أثناء محاولة إرسال الرسالة.")

# دالة للتحقق مما إذا كان المستخدم محظورًا
def is_user_blocked(username):
    return username in banned_users







#### نهايه لوحه الادمن





############# نهايه










####################### الادمن 
# داله مساعده


@bot.message_handler(commands=['help'])
def instructions(message):
    if message.from_user.username in banned_users:
        bot.send_message(message.chat.id, "تم حظرك من البوت تواصل مع المطور @ii3IllaX")
        return

    bot.send_message(
        message.chat.id,
        "الأوامر المتاحة:\n"
        "/start - بدء البوت والحصول على الأزرار.\n"
        "/developer - التواصل مع المطور.\n"
        "/help - عرض هذه التعليمات.\n"
        "/rck [رسالة] - إرسال رسالة إلى جميع المستخدمين.\n"
        "/ban [معرف] - حظر مستخدم.\n"
        "/uban [معرف] - فك حظر مستخدم.\n"
        "/stp [اسم الملف] - إيقاف ملف.\n"
        "/str [اسم الملف] - تشغيل ملف.\n"
        "/rr [معرف] [رسالة] - إرسال رسالة لمستخدم معين.\n"
        "قم برفع ملف البايثون الخاص بك عبر الزر المخصص.\n"
        "بعد الرفع، يمكنك التحكم في التشغيل، الإيقاف، أو الحذف باستخدام الأزرار الظاهرة."
    )

@bot.message_handler(commands=['ban'])
def ban_user(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "ليس لديك صلاحية استخدام هذا الأمر.")
        return

    try:
        username = message.text.split(' ', 1)[1].strip('@')
        if username in banned_users:
            bot.reply_to(message, f"المستخدم @{username} محظور بالفعل.")
        else:
            banned_users.add(username)
            bot.reply_to(message, f"تم حظر المستخدم @{username}.")
    except IndexError:
        bot.reply_to(message, "يرجى كتابة معرف المستخدم بعد الأمر.")

@bot.message_handler(commands=['uban'])
def unban_user(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "ليس لديك صلاحية استخدام هذا الأمر.")
        return

    try:
        username = message.text.split(' ', 1)[1].strip('@')
        if username not in banned_users:
            bot.reply_to(message, f"المستخدم @{username} ليس محظور.")
        else:
            banned_users.remove(username)
            bot.reply_to(message, f"تم فك حظر المستخدم @{username}.")
    except IndexError:
        bot.reply_to(message, "يرجى كتابة معرف المستخدم بعد الأمر.")


@bot.message_handler(commands=['rck'])
def broadcast_message(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "ليس لديك صلاحية استخدام هذا الأمر.")
        return

    try:
        msg = message.text.split(' ', 1)[1]  # الحصول على الرسالة
        print("محتوى bot_scripts:", bot_scripts)  # طباعة محتوى bot_scripts

        sent_count = 0
        failed_count = 0

        for chat_id in bot_scripts.keys():
            try:
                bot.send_message(chat_id, msg)
                sent_count += 1
            except Exception as e:
                logging.error(f"Error sending message to {chat_id}: {e}")
                failed_count += 1

        total_users = len(bot_scripts)
        bot.reply_to(message, f"تم إرسال الرسالة بنجاح إلى {sent_count} من {total_users} مستخدمين.\n"
                              f"فشلت الرسالة في إرسالها إلى {failed_count} مستخدمين.")
    except IndexError:
        bot.reply_to(message, "يرجى كتابة الرسالة بعد الأمر.")






@bot.message_handler(commands=['rr'])
def send_private_message(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "ليس لديك صلاحية استخدام هذا الأمر.")
        return

    try:
        parts = message.text.split(' ', 2)
        if len(parts) < 3:
            bot.reply_to(message, "يرجى كتابة معرف المستخدم والرسالة بعد الأمر.")
            return

        username = parts[1].strip('@')
        msg = parts[2]

        user_found = False  # متغير لتتبع ما إذا تم العثور على المستخدم

        for chat_id, script_info in bot_scripts.items():
            # تحقق من تطابق اسم المستخدم مع الحروف الكبيرة والصغيرة
            if script_info.get('uploader', '').lower() == username.lower():
                try:
                    bot.send_message(chat_id, msg)
                    user_found = True
                    break
                except Exception as send_error:
                    logging.error(f"Error sending message to @{username}: {send_error}")
                    bot.reply_to(message, f"حدث خطأ أثناء إرسال الرسالة إلى المستخدم @{username}.")
                    return

        if user_found:
            bot.reply_to(message, "تم إرسال الرسالة بنجاح.")
        else:
            bot.reply_to(message, f"تعذر العثور على المستخدم @{username}. تأكد من إدخال الاسم بشكل صحيح.")
    except Exception as e:
        logging.error(f"Error in /rr command: {e}")
        bot.reply_to(message, "حدث خطأ أثناء معالجة الأمر. يرجى المحاولة مرة أخرى.")

# دالة التحقق من وجود input أو eval في المحتوى
def file_contains_input_or_eval(content):
    try:
        for token_type, token_string, _, _, _ in tokenize.generate_tokens(io.StringIO(content).readline):
            if token_string in {"input", "eval"}:
                return True
        return False
    except tokenize.TokenError as e:
        logging.error(f"Tokenize error: {e}")
        return False

####################





#### داله العشوائيه







## بدايه الداله


@bot.message_handler(commands=['cr'])
def random_feature(message):
    if is_user_blocked(message.from_user.id):
        bot.reply_to(message, BLOCKED_MESSAGE)
        return
    
    # بدء جلسة جديدة وتحديث حالة الجلسة إلى 'main_menu'
    update_user_session(message.from_user.id, 'main_menu')

    welcome_message = "👋 أهلاً بك!\nهذا مكان مخصص لأشياء عشوائية قد تفيدك.\nاستخدم الأزرار بالأسفل للتفاعل 👇\n"
    markup = types.InlineKeyboardMarkup()
    
    file_button = types.InlineKeyboardButton("صنع ملفات", callback_data='create_files')
    password_button = types.InlineKeyboardButton("إنشاء كلمات مرور عشوائية", callback_data='generate_passwords')
    card_button = types.InlineKeyboardButton("صنع فيزا عشوائية", callback_data='create_card')
    html_button = types.InlineKeyboardButton("سحب قوالب HTML", callback_data='fetch_html')
    calc_button = types.InlineKeyboardButton("حساب العمليات الرياضية", callback_data='calculate_expression')
    qr_button = types.InlineKeyboardButton("صنع QR", callback_data='create_qr')  # زر صنع QR
    
    markup.add(file_button, password_button)
    markup.add(card_button, html_button)
    markup.add(calc_button)  # إضافة زر حساب العمليات الرياضية
    markup.add(qr_button)  # إضافة زر صنع QR

    bot.send_message(message.chat.id, welcome_message, reply_markup=markup)





######### رمز qr

@bot.callback_query_handler(func=lambda call: call.data == 'create_qr')
def ask_for_qr_text(call):
    bot.send_message(call.message.chat.id, "📝 ادخل نص لوضعه في رمز QR:")

    # تسجيل الخطوة التالية لانتظار إدخال المستخدم
    bot.register_next_step_handler(call.message, generate_qr)

def generate_qr(message):
    qr_text = message.text.strip()
    try:
        # إنشاء رمز QR باستخدام segno بجودة عالية
        qr = segno.make(qr_text)
        qr_file = "qr_code.png"
        qr.save(qr_file, scale=10)  # تحسين الجودة باستخدام scale

        # إرسال رمز QR للمستخدم
        with open(qr_file, 'rb') as photo:
            bot.send_photo(message.chat.id, photo)

        # حذف الملف بعد الإرسال
        os.remove(qr_file)

    except Exception as e:
        bot.send_message(message.chat.id, "❌ حدث خطأ أثناء إنشاء رمز QR. تأكد من أنك أدخلت نصًا صالحًا.")

@bot.callback_query_handler(func=lambda call: call.data == 'calculate_expression')
def ask_for_expression(call):
    bot.send_message(call.message.chat.id, "🧮 اكتب مسألتك الرياضية لأحاول حلها:")

    # تسجيل الخطوة التالية لانتظار إدخال المستخدم
    bot.register_next_step_handler(call.message, solve_expression)

def solve_expression(message):
    expression = message.text.strip()
    try:
        # استخدام sympy لحل المعادلة
        result = sympify(expression)
        bot.send_message(message.chat.id, f"✅ الحل هو: {result}")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ حدث خطأ أثناء محاولة حل المسألة. تأكد من أنك كتبتها بشكل صحيح.")



########## دالة سحب قوالب HTML ##########

@bot.callback_query_handler(func=lambda call: call.data == 'fetch_html')
def request_html_url(call):
    if is_user_blocked(call.from_user.id):
        bot.answer_callback_query(call.id, BLOCKED_MESSAGE)
        return

    # تحديث حالة الجلسة إلى 'fetch_html'
    update_user_session(call.from_user.id, 'fetch_html')
    bot.send_message(call.message.chat.id, "يرجي العلم ان مش كل الصفح بيتم سحبها بسبب عدم قدره البوت في جلب المحتوا\n 📝 أدخل رابط الصفحة لسحب هيكل الـ HTML:")
    bot.register_next_step_handler(call.message, fetch_html)

def fetch_html(message):
    if not is_in_session(message.from_user.id, 'fetch_html'):
        return
    url = message.text.strip()
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        html_content = soup.prettify()

        file_name = "page.html"
        with open(file_name, 'w', encoding='utf-8') as file:
            file.write(html_content)

        with open(file_name, 'rb') as file:
            bot.send_document(message.chat.id, file)

        os.remove(file_name)

    except requests.exceptions.RequestException as e:
        bot.send_message(message.chat.id, f"❌ حدث خطأ أثناء جلب الـ HTML: {str(e)}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ حدث خطأ: {str(e)}")

########## دالة صنع الفيزات ##########

@bot.callback_query_handler(func=lambda call: call.data == 'create_card')
def choose_card_type(call):
    if is_user_blocked(call.from_user.id):
        bot.answer_callback_query(call.id, BLOCKED_MESSAGE)
        return

    # تحديث حالة الجلسة إلى 'choose_card_type'
    update_user_session(call.from_user.id, 'choose_card_type')
    
    markup = types.InlineKeyboardMarkup()
    random_button = types.InlineKeyboardButton("عشوائي", callback_data='random_card')
    pin_button = types.InlineKeyboardButton("باستخدام PIN", callback_data='pin_card')
    markup.add(random_button, pin_button)

    bot.send_message(call.message.chat.id, "اختر نوع الفيزا:", reply_markup=markup)

########## دالة الفيزات العشوائية ##########

@bot.callback_query_handler(func=lambda call: call.data == 'random_card')
def request_random_card_count(call):
    if is_user_blocked(call.from_user.id):
        bot.answer_callback_query(call.id, BLOCKED_MESSAGE)
        return

    # تحديث حالة الجلسة إلى 'random_card'
    update_user_session(call.from_user.id, 'random_card')
    
    bot.send_message(call.message.chat.id, "📝 أدخل عدد الفيزات التي تحتاجها:")
    bot.register_next_step_handler(call.message, generate_random_cards)

def generate_random_cards(message):
    if not is_in_session(message.from_user.id, 'random_card'):
        return
    try:
        count = int(message.text)

        if count < 1:
            bot.send_message(message.chat.id, "❌ العدد يجب أن يكون أكبر من 0.")
            return

        cards = []
        for _ in range(count):
            card_number = ''.join(random.choices(string.digits, k=16))
            expiration_date = f"{random.randint(1, 12):02d}|{random.randint(2023, 2030)}"
            cvv = ''.join(random.choices(string.digits, k=3))
            cards.append(f"{card_number}|{expiration_date}|{cvv}")

        if count > 70:
            file_name = "cards.txt"
            with open(file_name, 'w') as file:
                for card in cards:
                    file.write(card + '\n')

            with open(file_name, 'rb') as file:
                bot.send_document(message.chat.id, file)
            os.remove(file_name)
        else:
            response = "🗂️ ها هي الفيزات الخاصة بك:\n\n" + "\n".join(cards)
            bot.send_message(message.chat.id, response)

    except ValueError:
        bot.send_message(message.chat.id, "❌ يرجى التأكد من إدخال عدد صحيح.")

########## دالة الفيزات باستخدام PIN ##########

@bot.callback_query_handler(func=lambda call: call.data == 'pin_card')
def request_pin_and_card_count(call):
    if is_user_blocked(call.from_user.id):
        bot.answer_callback_query(call.id, BLOCKED_MESSAGE)
        return

    # تحديث حالة الجلسة إلى 'pin_card'
    update_user_session(call.from_user.id, 'pin_card')
    
    bot.send_message(call.message.chat.id, "📝 أدخل الـ PIN الخاص بك (6 أرقام):")
    bot.register_next_step_handler(call.message, save_pin_and_request_count)

def save_pin_and_request_count(message):
    if not is_in_session(message.from_user.id, 'pin_card'):
        return
    pin = message.text.strip()
    
    if len(pin) != 6 or not pin.isdigit():
        bot.send_message(message.chat.id, "❌ يجب أن يكون الـ PIN مكونًا من 6 أرقام.")
        return

    update_user_session(message.from_user.id, 'pin_card_count')
    bot.send_message(message.chat.id, "📝 أدخل عدد الفيزات التي تحتاجها:")
    bot.register_next_step_handler(message, lambda msg: generate_pin_based_cards(msg, pin))

def generate_pin_based_cards(message, pin):
    if not is_in_session(message.from_user.id, 'pin_card_count'):
        return
    try:
        count = int(message.text)

        if count < 1:
            bot.send_message(message.chat.id, "❌ العدد يجب أن يكون أكبر من 0.")
            return

        cards = []
        for _ in range(count):
            card_number = f"{pin}{''.join(random.choices(string.digits, k=10))}"
            expiration_date = f"{random.randint(1, 12):02d}|{random.randint(2023, 2030)}"
            cvv = ''.join(random.choices(string.digits, k=3))
            cards.append(f"{card_number}|{expiration_date}|{cvv}")

        if count > 70:
            file_name = "cards_with_pin.txt"
            with open(file_name, 'w') as file:
                for card in cards:
                    file.write(card + '\n')

            with open(file_name, 'rb') as file:
                bot.send_document(message.chat.id, file)
            os.remove(file_name)
        else:
            response = "🗂️ ها هي الفيزات الخاصة بك:\n\n" + "\n".join(cards)
            bot.send_message(message.chat.id, response)

    except ValueError:
        bot.send_message(message.chat.id, "❌ يرجى التأكد من إدخال عدد صحيح.")

########## دالة طلب معلومات كلمات المرور ##########




@bot.callback_query_handler(func=lambda call: call.data == 'generate_passwords')
def request_password_info(call):
    if is_user_blocked(call.from_user.id):
        bot.answer_callback_query(call.id, BLOCKED_MESSAGE)
        return

    # تحديث حالة الجلسة إلى 'generate_passwords'
    update_user_session(call.from_user.id, 'generate_passwords')
    
    # إخبار المستخدم بكيفية إدخال المعلومات
    bot.send_message(call.message.chat.id, "🛠️ اكتب عدد كلمات المرور التي تحتاجها وعدد الأرقام المكونة منها (مثل: 10 20)، حيث:\n- الحد الأقصى لعدد كلمات المرور هو 2000\n- 20: طول كل كلمة مرور")

@bot.message_handler(func=lambda message: is_in_session(message.from_user.id, 'generate_passwords'))
def generate_passwords(message):
    try:
        # تقسيم المدخل إلى عدد كلمات المرور وطول كل كلمة مرور
        count, length = map(int, message.text.split())
        
        # التحقق من القيم المدخلة
        if count > 2000:
            bot.send_message(message.chat.id, "❌ الحد الأقصى لعدد كلمات المرور هو 2000.")
            return
        elif length < 1:
            bot.send_message(message.chat.id, "❌ يجب أن يكون طول كلمة المرور أكبر من 0.")
            return

        passwords = []

        for _ in range(count):
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
            passwords.append(password)

        # إذا كانت عدد كلمات المرور كبيرًا، قم بكتابتها في ملف
        if count > 70:
            file_name = "passwords.txt"
            with open(file_name, 'w') as file:
                for pwd in passwords:
                    file.write(pwd + '\n')

            with open(file_name, 'rb') as file:
                bot.send_document(message.chat.id, file)
            os.remove(file_name)
        else:
            response = "🗝️ ها هي كلمات المرور الخاصة بك:\n\n" + "\n".join([f"باسورد {i+1}: {pwd}" for i, pwd in enumerate(passwords)])
            bot.send_message(message.chat.id, response)

    except ValueError:
        bot.send_message(message.chat.id, "❌ يرجى التأكد من إدخال الأرقام بشكل صحيح (مثل: 10 20).")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ حدث خطأ: {str(e)}")



########## دالة صنع ملفات ##########

@bot.callback_query_handler(func=lambda call: call.data == 'create_files')
def create_files(call):
    if is_user_blocked(call.from_user.id):
        bot.answer_callback_query(call.id, BLOCKED_MESSAGE)
        return

    # تحديث حالة الجلسة إلى 'create_files'
    update_user_session(call.from_user.id, 'create_files')
    
    bot.send_message(call.message.chat.id, "من هنا يمكنك صنع ملفات.\nاختر صيغة الملفات من الأسفل:", reply_markup=file_format_markup())

def file_format_markup():
    markup = types.InlineKeyboardMarkup()
    txt_button = types.InlineKeyboardButton(".txt", callback_data='create_txt')
    py_button = types.InlineKeyboardButton(".py", callback_data='create_py')
    env_button = types.InlineKeyboardButton(".env", callback_data='create_env')
    markup.add(txt_button, py_button, env_button)
    return markup

########## دالة طلب محتوى الملف ##########

@bot.callback_query_handler(func=lambda call: call.data in ['create_txt', 'create_py', 'create_env'])
def request_file_content(call):
    if not is_in_session(call.from_user.id, 'create_files'):
        return
    file_format = call.data.split('_')[1]

    # تحديث حالة الجلسة إلى 'create_{file_format}'
    update_user_session(call.from_user.id, f'create_{file_format}')
    
    bot.send_message(call.message.chat.id, f"📝 أدخل محتوى الملف بصيغة {file_format} لحفظه:")
    bot.register_next_step_handler(call.message, lambda msg: save_file(msg, file_format))

########## دالة حفظ الملف ##########

def save_file(message, file_format):
    if not is_in_session(message.from_user.id, f'create_{file_format}'):
        return
    content = message.text
    file_name = f"file.{file_format}"

    try:
        with open(file_name, 'w', encoding='utf-8') as file:
            file.write(content)

        with open(file_name, 'rb') as file:
            bot.send_document(message.chat.id, file)
        
        os.remove(file_name)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ حدث خطأ أثناء حفظ الملف: {str(e)}")













################################## هنا        

# دالة إغلاق جلسة مساعد AI
@bot.callback_query_handler(func=lambda call: call.data == 'close_ai_assistant')
def close_ai_assistant(call):
    global current_chat_session
    current_chat_session = None  # إعادة تعيين حالة المحادثة
    bot.send_message(call.message.chat.id, "تم إغلاق المحادثة مع مساعد AI.")

# دالة لبدء جلسة مساعد AI
@bot.callback_query_handler(func=lambda call: call.data == 'ai_assistant')
def start_ai_assistant(call):
    global current_chat_session
    if current_chat_session is None:
        current_chat_session = call.from_user.id  # تعيين حالة المحادثة للمستخدم الحالي
        bot.send_message(call.message.chat.id, "👋 أهلا بيك! أنا مساعدك الخاص، قول لي ماذا تحتاج؟\n\nلإغلاق المحادثة اضغط هنا:", reply_markup=close_assistant_markup())
    else:
        bot.send_message(call.message.chat.id, "جلسة المساعد الذكي مفتوحة حاليًا.")

def close_assistant_markup():
    markup = types.InlineKeyboardMarkup()
    close_button = types.InlineKeyboardButton(text='إغلاق المحادثة', callback_data='close_ai_assistant')
    markup.add(close_button)
    return markup

# معالجة الرسائل لمساعد AI فقط عند فتح الجلسة
@bot.message_handler(func=lambda message: current_chat_session == message.from_user.id)
def handle_ai_assistant_messages(message):
    user_message = message.text.strip()

    # تحقق إذا كانت الرسالة فارغة
    if not user_message:
        bot.reply_to(message, "يرجى كتابة سؤال أو استفسار.")
        return

    response = find_closest_question(user_message)

    # تحقق مما إذا كان الرد فارغًا
    if response and isinstance(response, str) and response.strip():  # تحقق من أن الرد ليس فارغًا
        bot.reply_to(message, response)
    else:
        bot.reply_to(message, "آسف، لم أتمكن من فهم سؤالك. يرجى المحاولة مرة أخرى.")


        





        #####

@bot.callback_query_handler(func=lambda call: call.data == 'ai_assistant')  # استجابة لفتح محادثة مساعد AI
def start_ai_assistant(call):
    global current_chat_session
    current_chat_session = call.from_user.id  # تعيين حالة المحادثة
    bot.send_message(call.message.chat.id, "👋 أهلا بيك! أنا مساعدك الخاص، قول لي ماذا تحتاج؟\n\nلإغلاق المحادثة اضغط هنا:", reply_markup=close_assistant_markup())

def close_assistant_markup():
    markup = types.InlineKeyboardMarkup()
    close_button = types.InlineKeyboardButton(text='إغلاق المحادثة', callback_data='close_ai_assistant')
    markup.add(close_button)
    return markup

@bot.callback_query_handler(func=lambda call: call.data == 'close_ai_assistant')
def close_ai_assistant(call):
    global current_chat_session
    current_chat_session = None  # إعادة تعيين حالة المحادثة
    bot.send_message(call.message.chat.id, "تم إغلاق المحادثة مع المساعد الذكي.")

@bot.message_handler(func=lambda message: current_chat_session == message.from_user.id)
def handle_ai_assistant_messages(message):
    user_message = message.text.strip()

    # تحقق إذا كانت الرسالة فارغة
    if not user_message:
        bot.reply_to(message, "يرجى كتابة سؤال أو استفسار.")
        return

    response = find_closest_question(user_message)

    # تحقق مما إذا كان الرد فارغًا
    if response and isinstance(response, str) and response.strip():  # تحقق من أن الرد ليس فارغًا
        bot.reply_to(message, response)
    else:
        bot.reply_to(message, "آسف، لم أتمكن من فهم سؤالك. يرجى المحاولة مرة أخرى.")





##################### cmd


# /cmd 





current_chat_session = None  # لتعقب المحادثة الحالية

import time


user_sessions = {}  # لتخزين الجلسات مع الـ AI

API_GEMINI = 'AIzaSyAXZ_R_XB9VfqWmdfdfecEXLhSmk481XDU'  # مفتاح API الخاص بـ GMINI

@bot.message_handler(commands=['cmd'])
def display_commands(message):
    if message.from_user.username in banned_users:
        bot.send_message(message.chat.id, "تم حظرك من البوت. تواصل مع المطور @ii3IllaX")
        return
    
    markup = types.InlineKeyboardMarkup()
    report_button = types.InlineKeyboardButton("إرسال مشكلة للمطور", callback_data='report_issue')
    suggestion_button = types.InlineKeyboardButton("اقتراح تعديل", callback_data='suggest_modification')
    chat_button = types.InlineKeyboardButton("فتح محادثة مع المطور", callback_data='open_chat')
    install_button = types.InlineKeyboardButton("تحميل مكاتب", callback_data='install_library')
    ai_assistant_button = types.InlineKeyboardButton("مساعد AI الخاص بالبوت", callback_data='ai_assistant')
    ai_gmini_button = types.InlineKeyboardButton("AI BOT GMINI", callback_data='start_ai_chat')  # زر AI BOT GMINI
    speed_button = types.InlineKeyboardButton("سرعة البوت ✨⚡️", callback_data='check_speed')  # زر سرعة البوت

    markup.row(report_button , report_button)

    markup.row(chat_button)
    markup.row(install_button)
    markup.row(ai_assistant_button)
    markup.row(ai_gmini_button)
    markup.row(speed_button)  

    bot.send_message(
        message.chat.id,
        "—————————————\n"
        "اهلا بيك في لوحه ال CMD 👋\n"
        "من هنا تقدر تعمل خيارات متعدده ,,\n"
        "📜 الأوامر المتاحة:\n"
        "استخدم الأزرار بالأسفل للتفاعل 👇\n"
        "—————————————",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == 'start_ai_chat')
def start_ai_chat(call):
    user_id = call.message.chat.id
    chat_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))  # معرف عشوائي للمحادثة
    user_sessions[user_id] = {
        "chat_id": chat_id,
        "model": None  # سيتم تهيئة النموذج عند أول رسالة
    }
    bot.send_message(call.message.chat.id, "👋 اهلا بيك في محادثه الذكاء الاصتناعي المفتوح مع GMINI.\nيمكنك كتابة أي شيء الآن.")
    markup = types.InlineKeyboardMarkup()
    close_button = types.InlineKeyboardButton("اغلاق المحادثه", callback_data='close_ai_chat')
    markup.add(close_button)
    bot.send_message(call.message.chat.id, "اضغط على الزر أدناه لإغلاق المحادثة.", reply_markup=markup)

@bot.message_handler(func=lambda message: message.chat.id in user_sessions)
def ai_chat(message):
    user_id = message.chat.id
    user_content = message.text
    print(user_content)
    
    translated_user_content_en = GoogleTranslator(source='ar', target='en').translate(user_content)
    genai.configure(api_key=API_GEMINI)  # استخدام المتغير API_GEMINI
    generation_config = {
        "temperature": 0.4,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }
    
    if user_sessions[user_id]["model"] is None:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config,
            system_instruction="you are chatting with people and answer questions, be helpful",
        )
        user_sessions[user_id]["model"] = model.start_chat(history=[])
    
    chat_session = user_sessions[user_id]["model"]
    
    try:
        response = chat_session.send_message(translated_user_content_en)
        translated_response_ar = GoogleTranslator(source='en', target='ar').translate(response.text)
        bot.reply_to(message, translated_response_ar)
    except Exception as e:
        print(f"An error occurred: {e}")
        bot.reply_to(message, "عذرًا، حدث خطأ أثناء معالجة طلبك. حاول مرة أخرى لاحقًا.")

@bot.callback_query_handler(func=lambda call: call.data == 'close_ai_chat')
def close_ai_chat(call):
    user_id = call.message.chat.id
    if user_id in user_sessions:
        del user_sessions[user_id]  # حذف المحادثة من الجلسات
        bot.send_message(call.message.chat.id, "❌ تم إغلاق المحادثة مع الذكاء الاصطناعي. إذا كنت ترغب في بدء محادثة جديدة، استخدم الزر 'AI BOT GMINI'.")



### سرعه البوت

@bot.callback_query_handler(func=lambda call: call.data == 'check_speed')
def check_speed(call):
    bot.send_message(call.message.chat.id, "⏳ انتظر، يتم قياس سرعة البوت...")

    # قياس سرعة البوت
    start_time = time.time()
    # يمكن استخدام أي عملية بسيطة لقياس السرعة، مثل إرسال واستقبال رسالة
    bot.send_message(call.message.chat.id, "جاري قياس السرعة...")
    response_time = time.time() - start_time

    # تحويل الزمن إلى ميلي ثانية
    response_time_ms = response_time * 1000

    # تقييم السرعة
    if response_time_ms < 100:
        speed_feedback = f"سرعة البوت الحالية: {response_time_ms:.2f} ms - ممتازه !⚡️"
    elif response_time_ms < 300:
        speed_feedback = f"سرعة البوت الحالية: {response_time_ms:.2f} ms - جيد جدا ✨🙂"
    else:
        speed_feedback = f"سرعة البوت الحالية: {response_time_ms:.2f} ms - يجب تحسين الإنترنت ❌"

    bot.send_message(call.message.chat.id, speed_feedback)



###################### ai



 ################## 


# معالجة الرسائل لمساعد AI فقط عند فتح الجلسة
@bot.message_handler(func=lambda message: current_chat_session == message.from_user.id)
def handle_ai_assistant_messages(message):
    user_message = message.text.strip()

    # تحقق إذا كانت الرسالة فارغة
    if not user_message:
        bot.reply_to(message, "يرجى كتابة سؤال أو استفسار.")
        return

    response = find_closest_question(user_message)


    if response and isinstance(response, str) and response.strip():  
        bot.reply_to(message, response)
    else:
        bot.reply_to(message, "آسف، لم أتمكن من فهم سؤالك. يرجى المحاولة مرة أخرى.")


unrecognized_count = 0

# حالة المحادثة الحالية
current_chat_session = None
qa_dict_1 = {
    "اهلا": [
        "اهلا بك! كيف يمكنني مساعدتك اليوم؟",
        "مرحبًا! كيف تسير الأمور؟",
        "أهلاً وسهلاً بك! كيف أستطيع مساعدتك؟",
        "مرحبا بك في محادثتنا! كيف يمكنني مساعدتك؟",
        "أهلا! كيف يمكنني أن أكون مفيدًا لك اليوم؟",
        "مرحبًا بك! أنا هنا لمساعدتك في أي شيء تحتاجه.",
        "أهلاً، سعيد بلقائك! ماذا تريد أن تعرف؟",
        "مرحبًا بك! كيف يمكنني مساعدتك في تحقيق أهدافك اليوم؟",
        "أهلا بك! إذا كان لديك أي استفسارات، فلا تتردد في طرحها.",
        "مرحبًا! أنا هنا لدعمك في أي سؤال أو مشكلة.",
        "أهلا بك! كيف كانت يومك حتى الآن؟",
        "مرحبًا! هل هناك شيء محدد ترغب في مناقشته؟",
        "أهلاً بك! كيف يمكنني مساعدتك في مشروعك؟",
        "مرحبًا بك! ماذا تريد أن نبدأ به اليوم؟",
        "أهلا! هل لديك أي أفكار أو استفسارات تحتاج إلى مساعدة فيها؟",
        "مرحبًا! كيف يمكنني تسهيل الأمور عليك اليوم؟",
        "أهلا بك! أنا هنا لأساعدك في كل ما تحتاج إليه.",
        "مرحبًا! هل لديك أي خطط مثيرة لهذا اليوم؟",
        "أهلا! كيف يمكنني أن أجعل تجربتك هنا أفضل؟",
        "مرحبًا! ما الذي يجعلك سعيدًا اليوم؟",
        "أهلا بك! هل هناك شيء ترغب في تعلمه؟",

    ],
    "سلام عليكم": [
        "وعليكم السلام! كيف يمكنني مساعدتك؟",
        "وعليكم السلام! أنا هنا لمساعدتك في أي شيء تحتاجه.",
        "وعليكم السلام! كيف تسير الأمور لديك؟",
        "وعليكم السلام! أتمنى لك يومًا سعيدًا.",
        "وعليكم السلام! كيف يمكنني أن أكون مفيدًا لك اليوم؟",
        "وعليكم السلام! هل لديك أي استفسارات؟",
        "وعليكم السلام! أنا هنا لدعمك في أي سؤال.",
        "وعليكم السلام! ماذا تريد أن تعرف اليوم؟",
        "وعليكم السلام! كيف كانت تجربتك حتى الآن؟",
        "وعليكم السلام! كيف يمكنني مساعدتك في تحقيق أهدافك؟",
        "وعليكم السلام! هل لديك أي أفكار لمشاركتها؟",
        "وعليكم السلام! كيف يمكنني أن أجعل تجربتك أفضل؟",
        "وعليكم السلام! هل هناك شيء محدد ترغب في مناقشته؟",
        "وعليكم السلام! أرحب بك في محادثتنا.",
        "وعليكم السلام! كيف يمكنني مساعدتك في مشروعك؟",
        "وعليكم السلام! هل لديك أي خطط لهذا اليوم؟",
        "وعليكم السلام! أنا هنا لمساعدتك في كل ما تحتاج إليه.",
        "وعليكم السلام! كيف كانت يومك حتى الآن؟",
        "وعليكم السلام! هل هناك أي شيء تحب أن تتحدث عنه؟",
        "وعليكم السلام! كيف يمكنني تسهيل الأمور عليك؟",
    ],



        "ازاي اثبت مكاتب": [
        "اكتب pip install (اسم المكتبه هنا بدون قوسين)",
        "اكتب في ال cmd pip install (اسم المكتبه هنا بدون قوسين)",
    ],
         "ازاي اثبت مكاتب علي البوت": [
        
        " تقدر من خلال امر ال /cmd تنزل منه مكاتب بس هوا تحت الطوير وممكن ميشتغلش كويس",
        "من خلال امر ال /cmd في البوت تنزل المكاتب او نزل مكاتب في الجهاز للي شغال فيه البوت وخلاص",
    ],


       "تقدر تعمل اي؟": [
           
        "انا هنا مساعد ذكاء اتصناعي علشان اساعدك في كل حاجه بس لو بتسأل البوت كله بيعمل اي ف البوت دا لرفع وتشغيل ملفات بايثون فيه اوامر قويه وكتير جدا جدا تقدر تستكشفها نبنفسك ",
    ],



        "ماذا تسطيع ان تفعل ايها البوت" : [
        "انا هنا مساعد ذكاء اتصناعي علشان اساعدك في كل حاجه بس لو بتسأل البوت كله بيعمل اي ف البوت دا لرفع وتشغيل ملفات بايثون فيه اوامر قويه وكتير جدا جدا تقدر تستكشفها نبنفسك ",
    ],




        "ازاي اعمل بوت زيك" : [

        "تقدر تعمل زي بأنك تفتح الملف للي منزله محمد في قناه ماكرو بايثون وتاخد قاموس الاستجابه وتظبطو وتشغل البوت وبس كدا",
        "طبيعي جدا انا بلغه بايثون, تقدر تعمل زي من خلال انك تتعلم مكاتب ترانس فولو",
    ],



        







        "رفعت ملفي ومشتشغلش اي سبب": [
        "تحقق من تثبيت المكتبات المطلوبة على البوت.",
        "تأكد من أن الملف ليس به أخطاء في الكود.",
        "تحقق من أن الملف متوافق مع إصدار البوت.",
        "تأكد من أن جميع المتغيرات المطلوبة معرفة بشكل صحيح.",
        "تحقق من أن الملف يحتوي على التوكنات الصحيحة.",
        "افحص سجل الأخطاء للحصول على تفاصيل أكثر عن المشكلة.",
        "تأكد من أن الملف بصيغة صحيحة ومتوافق.",
        "تحقق من أن المسار إلى الملف معرف بشكل صحيح.",
        "تأكد من أن الأذونات اللازمة للوصول إلى الملف متاحة.",
        "تحقق من أن المكتبات المستخدمة في الملف مثبتة.",
        "تأكد من أن اتصال الإنترنت لديك مستقر عند رفع الملف.",
        "تحقق من أن حجم الملف ضمن الحدود المسموح بها.",
        "تأكد من أنك تستخدم الإصدار الأحدث من البوت.",
        "تحقق من أن جميع المكتبات المطلوبة محدثة.",
        "تأكد من أن الملف لم يتعرض للتلف أثناء التحميل.",
        "تحقق من أن البوت لديه الأذونات اللازمة لتنفيذ الملف.",
        "تأكد من أن الملف لا يحتوي على أي رموز غير مدعومة.",
        "تحقق من أن جميع المراجع في الملف صحيحة.",
        "تأكد من أن الملف متوافق مع نظام التشغيل المستخدم.",
        "تحقق من أن الإعدادات الخاصة بالبوت محدثة.",
        "تأكد من أن الملف لم يتم تعديله بطرق غير متوقعة.",
        "تحقق من أن كل المتغيرات البيئية معرفة بشكل صحيح.",
        "تأكد من أن الملف يحتوي على جميع المكونات الضرورية.",
        "تحقق من أن صيغة الملف مدعومة من البوت.",
        "تأكد من أن التوكنات المستخدمة في الملف صحيحة.",
        "تحقق من أن الملف لا يحتوي على أي أخطاء تركيبية.",
        "تأكد من أن جميع المكتبات الضرورية معرفة ومسجلة.",
        "تحقق من أن الإعدادات الخاصة بالبوت متوافقة مع الملف.",
        "تأكد من أن الملف لا يحتوي على أي بيانات مفقودة.",
        "تحقق من أن جميع التبعيات في الملف معرفة.",
        "تأكد من أن البوت محدث لأحدث إصدار.",
        "تحقق من أن جميع الإعدادات الخاصة بالتشغيل صحيحة.",
        "تأكد من أن الملف لم يتعرض للضرر أثناء النقل.",
        "تحقق من أن جميع التبعيات الضرورية مثبتة.",
        "تأكد من أن المكتبات المستخدمة في الملف محدثة.",
        "تحقق من أن بيئة التشغيل متوافقة مع الملف.",
        "تأكد من أن جميع التوكنات معرفة بشكل صحيح.",
        "تحقق من أن الملف لا يحتوي على أي تناقضات.",
        "تأكد من أن جميع المتغيرات معرفة في البيئة.",
        "تحقق من أن الملف متوافق مع تكوين البوت.",
        "تأكد من أن جميع العناصر المطلوبة متاحة في الملف.",
        "تحقق من أن الملف لا يحتوي على أي أخطاء في الكود.",
        "تأكد من أن جميع المكتبات المستخدمة مثبتة بشكل صحيح.",
        "تحقق من أن الملف يحتوي على جميع البيانات المطلوبة.",
        "تأكد من أن جميع القيم معرفة في الملف.",
        "تحقق من أن البيئات المختلفة متوافقة مع الملف.",
        "تأكد من أن التوكنات صحيحة ومحدثة.",
        "تحقق من أن جميع المتغيرات معرفة في البيئة الصحيحة.",
        "تأكد من أن جميع المكونات الضرورية معرفة.",
        "تحقق من أن الملف لا يحتوي على أي أخطاء في التهيئة.",
        "تأكد من أن المكتبات المستخدمة مدعومة.",
        "تحقق من أن الملف متوافق مع البنية التحتية الحالية.",
        "تأكد من أن جميع البيانات في الملف صحيحة ومتوافقة.",
        "تحقق من أن الملف لم يتم تعديله بطرق غير مدعومة.",
        "تأكد من أن جميع المكتبات المطلوبة محدثة.",
        "تحقق من أن جميع الأذونات المطلوبة متاحة.",
        "تأكد من أن الملف لم يتم تحريره بشكل غير صحيح.",
        "تحقق من أن جميع المراجع معرفة بشكل صحيح.",
        "تأكد من أن جميع المتغيرات معرفة ومتوافقة.",
        "تحقق من أن الملف متوافق مع إصدار البوت المستخدم.",
        "تأكد من أن جميع التبعيات معرفة بشكل صحيح.",
        "تحقق من أن الملف لا يحتوي على أي أخطاء تركيبية.",
        "تأكد من أن جميع المكتبات معرفة ومسجلة بشكل صحيح.",
        "تحقق من أن الإعدادات الخاصة بالبوت متوافقة مع الملف.",
        "تأكد من أن الملف لا يحتوي على أي بيانات مفقودة.",
        "تحقق من أن جميع التبعيات في الملف معرفة.",
        "تأكد من أن البوت محدث لأحدث إصدار.",
        "تحقق من أن جميع الإعدادات الخاصة بالتشغيل صحيحة.",
        "تأكد من أن الملف لم يتعرض للضرر أثناء النقل.",
        "تحقق من أن جميع التبعيات الضرورية مثبتة.",
        "تأكد من أن المكتبات المستخدمة في الملف محدثة.",
        "تحقق من أن بيئة التشغيل متوافقة مع الملف.",
        "تأكد من أن جميع التوكنات معرفة بشكل صحيح.",
        "تحقق من أن الملف لا يحتوي على أي تناقضات.",
        "تأكد من أن جميع المتغيرات معرفة في البيئة.",
        "تحقق من أن الملف متوافق مع تكوين البوت.",
        "تأكد من أن جميع العناصر المطلوبة متاحة في الملف.",
        "تحقق من أن الملف لا يحتوي على أي أخطاء في الكود.",
        "تأكد من أن جميع المكتبات المستخدمة مثبتة بشكل صحيح.",
        "تحقق من أن الملف يحتوي على جميع البيانات المطلوبة.",
        "تأكد من أن جميع القيم معرفة في الملف.",
        "تحقق من أن البيئات المختلفة متوافقة مع الملف.",
        "تأكد من أن التوكنات صحيحة ومحدثة.",
        "تحقق من أن جميع المتغيرات معرفة في البيئة الصحيحة.",
        "تأكد من أن جميع المكونات الضرورية معرفة.",
        "تحقق من أن الملف لا يحتوي على أي أخطاء في التهيئة.",
        "تأكد من أن المكتبات المستخدمة مدعومة.",
        "تحقق من أن الملف متوافق مع البنية التحتية الحالية.",
        "تأكد من أن جميع البيانات في الملف صحيحة ومتوافقة.",
        "تحقق من أن الملف لم يتم تعديله بطرق غير مدعومة.",
        "تأكد من أن جميع المكتبات المطلوبة محدثة.",
        "تحقق من أن جميع الأذونات المطلوبة متاحة.",
        "تأكد من أن الملف لم يتم تحريره بشكل غير صحيح.",
    ],
       "كيف اثبت مكاتب": [
       "انتقل الي لوحه ال cmd \n ومن بعدها اضغط علي زر تحميل مكاتب واكتب اسم المكتبه وانتظر التحميل",
       "يمكنك تثبيت مكاتب عن طريق الأزرار في البوت cmd",

    ],



        "كيف أبدأ في تعلم البرمجة؟": [
        "ابدأ بتحديد الهدف من تعلم البرمجة، هل هو لتطوير تطبيقات، مواقع، أو تحليل بيانات؟",
        "اختر لغة برمجة مناسبة للمبتدئين، مثل بايثون أو جافا سكريبت.",
        "ابدأ بدورة تعليمية عبر الإنترنت، مثل كورسيرا أو يوداسيتي.",
        "اقرأ كتبًا عن البرمجة، مثل 'Python Crash Course' أو 'Automate the Boring Stuff with Python'.",
        "شارك في مجتمعات البرمجة على الإنترنت مثل Stack Overflow أو Reddit.",
        "ابدأ بمشاريع صغيرة، مثل بناء آلة حاسبة أو موقع بسيط.",
        "استخدم منصات تعليمية مجانية مثل Codecademy أو FreeCodeCamp.",
        "شاهد دروس الفيديو على يوتيوب، هناك العديد من القنوات المفيدة.",
        "تدرب على حل المسائل البرمجية على موقع LeetCode أو HackerRank.",
        "استمر في ممارسة البرمجة يوميًا، حتى لو لبضع دقائق.",
        "تأكد من فهم الأساسيات، مثل المتغيرات، الحلقات، والشروط.",
        "حاول قراءة الكود المكتوب من قبل الآخرين لفهم أساليبهم.",
        "ابحث عن مرشد أو معلم يمكنك التواصل معه للحصول على النصائح.",
        "انضم إلى ورش عمل أو لقاءات لتبادل المعرفة مع الآخرين.",
        "قم بفتح مشروع برمجي خاص بك واستمر في تطويره.",
        "تجربة استخدام أدوات البرمجة مثل Git وGitHub.",
        "استمتع بالعملية ولا تخف من الأخطاء، فهي جزء من التعلم.",
        "تعلم كيفية قراءة الوثائق الرسمية للغات البرمجة.",
        "ابحث عن تطبيقات عملية للبرمجة في مجالك المهني.",
        "حاول تطوير ألعاب بسيطة، فهي وسيلة ممتعة للتعلم.",
        "استخدم منصات مثل Udemy للحصول على دورات بأسعار معقولة.",
        "تواصل مع المبرمجين الآخرين وشارك تجاربك.",
        "اجعل لنفسك جدول زمني للتعلم والتقدم.",
        "استخدم موارد متعددة لتوسيع معرفتك.",
        "كن فضولياً وتعلم عن مجالات البرمجة المختلفة.",
        "قم بتطبيق ما تعلمته على مشاريع عملية.",
        "تجنب التشتت، ركز على موضوع أو لغة واحدة في البداية.",
        "تعلم كيفية استخدام بيئات تطوير متكاملة (IDE).",
        "تجربة استخدام منصات تطوير التطبيقات مثل React أو Flutter.",
        "راقب التحديثات في مجال البرمجة وتعلم عنها.",
        "استمع إلى بودكاست عن البرمجة لتوسيع معرفتك.",
        "تعلم كيفية استخدام أدوات التصحيح (Debugging).",
        "لا تتردد في طرح الأسئلة عند مواجهتك صعوبات.",
        "ابحث عن تحديات برمجية لتطوير مهاراتك.",
        "حاول المساهمة في مشاريع مفتوحة المصدر.",
        "تعلم كيفية العمل مع قواعد البيانات.",
        "قم بحل المسائل الرياضية لتحسين مهاراتك التحليلية.",
        "استخدم مواقع مثل W3Schools لتعلم تقنيات الويب.",
        "تأكد من فهم كيفية عمل الخوارزميات.",
        "ضع لنفسك أهدافًا قصيرة وطويلة الأمد.",
        "تجربة استخدام مكتبات برمجية مختلفة.",
        "حاول كتابة مدونة عن تجربتك في تعلم البرمجة.",
        "استفد من تجارب الآخرين، اقرا قصص نجاحهم.",
        "تفاعل مع المجتمع من خلال المشاركة في الهاكاثونات.",
        "تعلم كيفية كتابة وثائق لمشاريعك البرمجية.",
        "تأكد من أنك تتعلم بطريقة تناسب أسلوبك الشخصي.",
        "استخدم أدوات مثل Trello لتنظيم مهامك.",
        "ابحث عن فرص تدريب أو تطوع في مشاريع برمجية.",
        "حاول تعلم كيفية تطوير تطبيقات الهواتف المحمولة.",
        "استخدم موارد تعلم البرمجة باللغة العربية إذا كنت بحاجة لذلك.",
        "تعلم كيفية إعداد بيئة تطوير محلية.",
        "استمتع بتجربة التعلم، لا تفكر في الضغط.",
        "تعلم كيفية العمل مع واجهات برمجة التطبيقات (APIs).",
        "ابحث عن دورات تعليمية تتضمن مشاريع عملية.",
        "تأكد من أنك تفهم مفاهيم البرمجة الكائنية.",
        "قم بحفظ الكود الخاص بك في مستودع GitHub.",
        "استفد من الأدوات المساعدة في البرمجة مثل Stack Overflow.",
        "تعلم كيفية استخدام أدوات التعاون مثل Slack.",
        "حاول قراءة الكود المفتوح المصدر لفهم كيفية عمله.",
        "احرص على تحديث مهاراتك بانتظام.",
        "تعلم كيفية إجراء اختبارات على الكود الخاص بك.",
        "راقب تطورات الصناعة والتقنيات الجديدة.",
        "استمتع بتجربة التعلم، ولا تتعجل في النتائج.",
        "تعلم كيفية التعامل مع الأخطاء والمشاكل في الكود.",
        "تحدث مع مبرمجين محترفين للحصول على نصائح.",
        "قم بإنشاء ملف شخصي على LinkedIn وشارك إنجازاتك.",
        "تجربة تعلم لغات برمجة جديدة بعد إتقان لغة واحدة.",
        "تعلم كيفية كتابة الكود بشكل منظم وواضح.",
        "استخدم موارد التعلم التفاعلية لتعزيز الفهم.",
        "اجعل التعلم جزءًا من روتينك اليومي.",
        "تعلم كيفية استخدام أدوات إدارة المشاريع.",
        "استفد من التجارب الفاشلة كجزء من عملية التعلم.",
        "تفاعل مع المدونات والمقالات المتعلقة بالبرمجة.",
        "تعلم كيفية استخدام أدوات مراقبة الأداء.",
        "قم بإنشاء مشاريع صغيرة تعكس اهتماماتك.",
        "استمتع بتعلم كيفية بناء تطبيقات الويب.",
        "حاول العمل على مشاريع جماعية لتعزيز التعاون.",
        "تعلم كيفية استخدام أدوات التحليل.",
        "قم بتطوير مهاراتك في البرمجة باستمرار.",
        "اجعل لنفسك مكانًا مخصصًا للدراسة والتركيز.",
        "استفد من الدورات المجانية المتاحة على الإنترنت.",
        "تعلم كيفية استخدام أدوات التخزين السحابي مثل Google Drive.",
        "استمتع بتجربة استخدام البرمجة في حل المشكلات.",
        "تعلم كيفية إدارة الوقت بفعالية أثناء الدراسة.",
        "ابحث عن تحديات برمجية تناسب مستواك.",
        "تجنب مقارنة نفسك بالآخرين، ركز على تقدمك الشخصي.",
        "استخدم أدوات التعلم متعددة الوسائط مثل الفيديو والصوت.",
        "تأكد من أنك تستمتع بما تتعلمه.",
        "تعلم كيفية كتابة الشيفرة بأسلوب فعال.",
        "استفد من التجارب الشخصية للآخرين.",
        "قم بتطوير مهاراتك في التفكير النقدي.",
        "احرص على أن تكون لديك بيئة تعليمية مريحة.",
        "تأكد من أن لديك الأدوات اللازمة لتعلم البرمجة.",
        "استمتع بمشاركة ما تعلمته مع الآخرين.",
        "تعلم كيفية استخدام أدوات التوثيق.",
        "قم بإنشاء مشاريع تعكس شغفك واهتماماتك.",
        "استمتع بتجربة التعلم من خلال الألعاب التعليمية.",
        "حاول تعلم كيفية تحليل البيانات باستخدام البرمجة.",
        "تأكد من أنك تتعلم من مصادر موثوقة.",
        "تعلم كيفية بناء واجهات مستخدم بسيطة.",
        "استفد من التجارب العملية لتعزيز التعلم.",
        "تجنب الشعور بالإحباط، فالجميع يواجه صعوبات.",
        "تعلم كيفية كتابة الكود بطريقة فعالة.",
        "استمتع بتجربة التعلم مع الأصدقاء أو الزملاء.",
        "قم بتحديد أهداف واضحة لتعلم البرمجة.",
        "تأكد من أنك تستمتع بالعملية برمتها."
    ],





        


        "رفعت ملف ما اشتغل": [
        "تحقق من تثبيت المكتبات المطلوبة على البوت.",
        "تأكد من أن الملف ليس به أخطاء في الكود.",
        "تحقق من أن الملف متوافق مع إصدار البوت.",
        "تأكد من أن جميع المتغيرات المطلوبة معرفة بشكل صحيح.",
        "تحقق من أن الملف يحتوي على التوكنات الصحيحة.",
        "افحص سجل الأخطاء للحصول على تفاصيل أكثر عن المشكلة.",
        "تأكد من أن الملف بصيغة صحيحة ومتوافق.",
        "تحقق من أن المسار إلى الملف معرف بشكل صحيح.",
        "تأكد من أن الأذونات اللازمة للوصول إلى الملف متاحة.",
        "تحقق من أن المكتبات المستخدمة في الملف مثبتة.",
        "تأكد من أن اتصال الإنترنت لديك مستقر عند رفع الملف.",
        "تحقق من أن حجم الملف ضمن الحدود المسموح بها.",
        "تأكد من أنك تستخدم الإصدار الأحدث من البوت.",
        "تحقق من أن جميع المكتبات المطلوبة محدثة.",
        "تأكد من أن الملف لم يتعرض للتلف أثناء التحميل.",
        "تحقق من أن البوت لديه الأذونات اللازمة لتنفيذ الملف.",
        "تأكد من أن الملف لا يحتوي على أي رموز غير مدعومة.",
        "تحقق من أن جميع المراجع في الملف صحيحة.",
        "تأكد من أن الملف متوافق مع نظام التشغيل المستخدم.",
        "تحقق من أن الإعدادات الخاصة بالبوت محدثة.",
        "تأكد من أن الملف لم يتم تعديله بطرق غير متوقعة.",
        "تحقق من أن كل المتغيرات البيئية معرفة بشكل صحيح.",
        "تأكد من أن الملف يحتوي على جميع المكونات الضرورية.",
        "تحقق من أن صيغة الملف مدعومة من البوت.",
        "تأكد من أن التوكنات المستخدمة في الملف صحيحة.",
        "تحقق من أن الملف لا يحتوي على أي أخطاء تركيبية.",
        "تأكد من أن جميع المكتبات الضرورية معرفة ومسجلة.",
        "تحقق من أن الإعدادات الخاصة بالبوت متوافقة مع الملف.",
        "تأكد من أن الملف لا يحتوي على أي بيانات مفقودة.",
        "تحقق من أن جميع التبعيات في الملف معرفة.",
        "تأكد من أن البوت محدث لأحدث إصدار.",
        "تحقق من أن جميع الإعدادات الخاصة بالتشغيل صحيحة.",
        "تأكد من أن الملف لم يتعرض للضرر أثناء النقل.",
        "تحقق من أن جميع التبعيات الضرورية مثبتة.",
        "تأكد من أن المكتبات المستخدمة في الملف محدثة.",
        "تحقق من أن بيئة التشغيل متوافقة مع الملف.",
        "تأكد من أن جميع التوكنات معرفة بشكل صحيح.",
        "تحقق من أن الملف لا يحتوي على أي تناقضات.",
        "تأكد من أن جميع المتغيرات معرفة في البيئة.",
        "تحقق من أن الملف متوافق مع تكوين البوت.",
        "تأكد من أن جميع العناصر المطلوبة متاحة في الملف.",
        "تحقق من أن الملف لا يحتوي على أي أخطاء في الكود.",
        "تأكد من أن جميع المكتبات المستخدمة مثبتة بشكل صحيح.",
        "تحقق من أن الملف يحتوي على جميع البيانات المطلوبة.",
        "تأكد من أن جميع القيم معرفة في الملف.",
        "تحقق من أن البيئات المختلفة متوافقة مع الملف.",
        "تأكد من أن التوكنات صحيحة ومحدثة.",
        "تحقق من أن جميع المتغيرات معرفة في البيئة الصحيحة.",
        "تأكد من أن جميع المكونات الضرورية معرفة.",
        "تحقق من أن الملف لا يحتوي على أي أخطاء في التهيئة.",
        "تأكد من أن المكتبات المستخدمة مدعومة.",
        "تحقق من أن الملف متوافق مع البنية التحتية الحالية.",
        "تأكد من أن جميع البيانات في الملف صحيحة ومتوافقة.",
        "تحقق من أن الملف لم يتم تعديله بطرق غير مدعومة.",
        "تأكد من أن جميع المكتبات المطلوبة محدثة.",
        "تحقق من أن جميع الأذونات المطلوبة متاحة.",
        "تأكد من أن الملف لم يتم تحريره بشكل غير صحيح.",
        "تحقق من أن جميع المراجع معرفة بشكل صحيح.",
        "تأكد من أن جميع المتغيرات معرفة ومتوافقة.",
        "تحقق من أن الملف متوافق مع إصدار البوت المستخدم.",
        "تأكد من أن جميع التبعيات معرفة بشكل صحيح.",
        "تحقق من أن الملف لا يحتوي على أي أخطاء تركيبية.",
        "تأكد من أن جميع المكتبات معرفة ومسجلة بشكل صحيح.",
        "تحقق من أن الإعدادات الخاصة بالبوت متوافقة مع الملف.",
        "تأكد من أن الملف لا يحتوي على أي بيانات مفقودة.",
        "تحقق من أن جميع التبعيات في الملف معرفة.",
        "تأكد من أن البوت محدث لأحدث إصدار.",
        "تحقق من أن جميع الإعدادات الخاصة بالتشغيل صحيحة.",
        "تأكد من أن الملف لم يتعرض للضرر أثناء النقل.",
        "تحقق من أن جميع التبعيات الضرورية مثبتة.",
        "تأكد من أن المكتبات المستخدمة في الملف محدثة.",
        "تحقق من أن بيئة التشغيل متوافقة مع الملف.",
        "تأكد من أن جميع التوكنات معرفة بشكل صحيح.",
        "تحقق من أن الملف لا يحتوي على أي تناقضات.",
        "تأكد من أن جميع المتغيرات معرفة في البيئة.",
        "تحقق من أن الملف متوافق مع تكوين البوت.",
        "تأكد من أن جميع العناصر المطلوبة متاحة في الملف.",
        "تحقق من أن الملف لا يحتوي على أي أخطاء في الكود.",
        "تأكد من أن جميع المكتبات المستخدمة مثبتة بشكل صحيح.",
        "تحقق من أن الملف يحتوي على جميع البيانات المطلوبة.",
        "تأكد من أن جميع القيم معرفة في الملف.",
        "تحقق من أن البيئات المختلفة متوافقة مع الملف.",
        "تأكد من أن التوكنات صحيحة ومحدثة.",
        "تحقق من أن جميع المتغيرات معرفة في البيئة الصحيحة.",
        "تأكد من أن جميع المكونات الضرورية معرفة.",
        "تحقق من أن الملف لا يحتوي على أي أخطاء في التهيئة.",
        "تأكد من أن المكتبات المستخدمة مدعومة.",
        "تحقق من أن الملف متوافق مع البنية التحتية الحالية.",
        "تأكد من أن جميع البيانات في الملف صحيحة ومتوافقة.",
        "تحقق من أن الملف لم يتم تعديله بطرق غير مدعومة.",
        "تأكد من أن جميع المكتبات المطلوبة محدثة.",
        "تحقق من أن جميع الأذونات المطلوبة متاحة.",
        "تأكد من أن الملف لم يتم تحريره بشكل غير صحيح.",
    ],

    "كيف حالك؟": [
        "أنا بخير، شكرًا لسؤالك! 😊",
        "بخير، وأنت؟ كيف حالك؟ 😄",
        "أنا في حالة جيدة، شكرًا لك على السؤال.",
        "كل شيء يسير على ما يرام، ماذا عنك؟",
        "أنا هنا وجاهز لمساعدتك! كيف يمكنني مساعدتك اليوم؟",
        "بخير، شكرًا! هل هناك شيء تود مناقشته؟",
        "أنا ممتاز، شكرًا لسؤالك! كيف تسير أمورك؟",
        "كل شيء جيد، شكرًا! كيف يمكنني أن أكون مفيدًا لك؟",
        "أنا سعيد وسأكون أكثر سعادة بمساعدتك!",
        "كل شيء ممتاز، ماذا عنك؟",
        "أنا في أفضل حالاتي! كيف يمكنني مساعدتك؟",
        "أنا هنا لمساعدتك، كيف حالك أنت؟",
        "أشعر بالراحة، شكرًا على السؤال! كيف تسير أمورك؟",
        "بخير، أتمنى أن تكون بخير أيضًا!",
        "كل شيء على ما يرام، هل لديك أي استفسارات؟",
        "أنا في حالة جيدة، شكرًا! ماذا عنك؟",
        "بشكل عام، الأمور تسير على ما يرام. كيف يمكنني مساعدتك؟",
        "أنا متحمس لمساعدتك اليوم! كيف حالك؟",
        "أنا هنا لدعمك! كيف تسير الأمور لديك؟",
        "أنا بخير، شكرًا! هل هناك أي شيء ترغب في معرفته؟",
    ],
    "ما هو اسمك؟": [
        "أنا المساعد الذكي الخاص بك! 🤖",
        "يمكنك مناداتي المساعد أو أي اسم تفضله! 🥳",
        "أنا هنا لمساعدتك، يمكنك مناداتي كما تشاء.",
        "أنا بوت مساعد ذكي، كيف يمكنني مساعدتك اليوم؟",
        "أنا مساعد ذكاء اصطناعي، هنا لأساعدك!",
        "يمكنك تسميتي كما تريد، أنا هنا لمساعدتك.",
        "أنا هنا لدعمك، ما تريد مني أن أناديك؟",
        "أنا المساعد الذي تحتاجه، كيف يمكنني مساعدتك؟",
        "يمكنك اعتباري صديقك الذكي، كيف يمكنني مساعدتك؟",
        "أنا مساعدك الرقمي، هل لديك أي استفسارات؟",
        "أنا مساعد ذكي مصمم لمساعدتك في كل ما تحتاجه.",
        "يمكنك مناداتي المساعد، كيف يمكنني أن أكون مفيدًا لك؟",
        "أنا هنا لتقديم الدعم والمساعدة، كيف تريد أن تناديني؟",
        "يمكنك مناداتي بالمساعد الذكي، أنا هنا لأساعدك.",
        "أنا هنا لمساعدتك في كل شيء، كيف يمكنني مساعدتك؟",
        "أنا المساعد الافتراضي الخاص بك، كيف يمكنني مساعدتك؟",
        "أنا بوت لمساعدتك في الاستفسارات، كيف يمكنني مساعدتك؟",
        "أنا هنا لمساعدتك، ماذا تريد أن تعرف؟",
        "يمكنك مناداتي كما تشاء، أنا هنا لدعمك.",
        "أنا هنا لأقدم لك المساعدة، كيف تريد أن تناديني؟",

    ],
    "كيف أحصل على الدعم الفني؟": [
        "يمكنك التواصل معي وسأساعدك في أي مشكلة.",
        "إذا كنت بحاجة إلى مساعدة، فقط اكتب سؤالك.",
        "يمكنك طرح مشكلتك وسأقوم بمساعدتك في حلها.",
        "أنا هنا لدعمك، اطرح أي استفسار وسأساعدك.",
        "اكتب مشكلتك وسأكون هنا للإجابة.",
        "للحصول على الدعم، يمكنك طرح سؤالك هنا.",
        "أنا هنا لمساعدتك في أي مشكلة تواجهها.",
        "لا تتردد في طرح مشكلتك، سأكون سعيدًا بمساعدتك.",
        "إذا كنت بحاجة إلى الدعم، فقط اكتب لي.",
        "يمكنك الحصول على الدعم عن طريق طرح سؤالك.",
        "أنا هنا لمساعدتك في جميع مشاكلك.",
        "اكتب ما تحتاجه وسأقوم بدعمه.",
        "إذا كانت لديك مشكلة، فقط اطرح سؤالك.",
        "أنا هنا لتقديم الدعم الفني الذي تحتاجه.",
        "يمكنك التواصل معي في أي وقت للحصول على الدعم.",
        "اكتب مشكلتك وسأعمل على مساعدتك في حلها.",
        "أنا هنا لتقديم المساعدة والدعم الفني.",
        "إذا كنت بحاجة إلى مساعدة، فقط اكتب لي.",
        "اكتب ما تحتاجه وسأكون هنا للمساعدة.",
        "أنا هنا لمساعدتك في أي استفسار فني.",
        "اكتب سؤالك وسأكون هنا لدعمه.",
    ],
    "ازاي استعمل البوت؟": [
    "يمكنك استخدام البوت بطرح أي سؤال، وسأكون هنا للإجابة.",
    "اكتب سؤالك ببساطة، وسأساعدك في الوصول إلى المعلومات المطلوبة.",
    "للاستخدام الأمثل، ابدأ بطرح سؤال مباشر وسأقدم لك الرد المناسب.",
    "يمكنك استخدام الأوامر المتاحة في القائمة الخاصة بالبوت.",
    "اكتب ما تحتاجه وسأقوم بالإجابة عليك بشكل سريع.",
    "استخدم البوت للتواصل معي في أي وقت تحتاج فيه لمساعدة.",
    "أنا هنا لمساعدتك، فقط اكتب سؤالك وسأقوم بالإجابة.",
    "يمكنك طرح أي استفسار، وأنا سأعمل على تقديم المساعدة.",
    "إذا كنت بحاجة إلى معلومات، فقط اكتب سؤالك وسأساعدك.",
    "يمكنك استخدامه للبحث عن معلومات أو طرح أسئلة حول مواضيع مختلفة.",
    "أنا هنا لدعمك، فقط اكتب ما ترغب في معرفته.",
    "اكتب سؤالك وسأقوم بتقديم إجابة دقيقة ومفيدة.",
    "للحصول على مساعدة، اطرح أي سؤال وسأكون سعيدًا بمساعدتك.",
    "يمكنك الاستفادة من هذا البوت للإجابة على استفساراتك بسهولة.",
    "اكتب سؤالك بطريقة واضحة، وسأساعدك في الحصول على الإجابة.",
    "يمكنك استخدام البوت كأداة للبحث عن المعلومات المفيدة.",
    "أنا هنا لتقديم الدعم والإجابة على أي استفسار تود طرحه.",
    "اكتب ما تحتاجه وسأقوم بمساعدتك في ذلك.",
    "للاستخدام الفعال، يمكنك طرح الأسئلة ذات الصلة مباشرة.",
    "استخدم هذا البوت لتسهيل الأمور عليك بطرح الأسئلة.",
    "أنا هنا لأكون مساعدك في كل ما تحتاجه، فقط اطرح سؤالك.",
    "للحصول على معلومات دقيقة، اكتب سؤالك بكل وضوح.",
    "يمكنك استخدام الأوامر المتاحة للحصول على المساعدة.",
    "اكتب سؤالك وسأكون هنا لدعمه.",
    "إذا كان لديك استفسار، فلا تتردد في طرحه.",
    "استخدم البوت لتسهيل الوصول إلى المعلومات التي تحتاجها.",
    "أنا هنا لمساعدتك في كل ما تحتاجه، فقط اكتب ما تريد.",
    "يمكنك طرح أي سؤال، وسأقوم بمساعدتك في الحصول على الإجابة.",
    "اكتب ما تحتاجه وسأكون هنا لمساعدتك.",
    "للاستخدام الأمثل، اطلب ما تحتاجه وسأكون هنا لمساعدتك.",
    "أنا هنا لمساعدتك في تحقيق أهدافك، كيف يمكنني مساعدتك؟",
    "اكتب سؤالك وسأكون سعيدًا بالإجابة عليه.",
    "يمكنك استخدام هذا البوت للإجابة على استفساراتك في أي وقت.",
    "اكتب سؤالك وسأقوم بتقديم معلومات دقيقة.",
    "أنا هنا لدعمك، فقط اطرح أي سؤال تود معرفته.",
    "إذا كنت بحاجة إلى مساعدة، فقط اطرح سؤالك وسأساعدك.",
    "اكتب ما تحتاج إليه وسأكون هنا لدعمك.",
    "للحصول على الدعم، يمكنك طرح سؤالك هنا.",
    "أنا هنا لمساعدتك في جميع مشاكلك واستفساراتك.",
    "اكتب سؤالك وسأقوم بدعمه بكل سرور.",
    "استخدام هذا البوت سهل، فقط اطرح أي سؤال.",
    "أنا هنا لتقديم المساعدة والدعم، كيف يمكنني مساعدتك؟",
    "اكتب سؤالك وسأكون سعيدًا بمساعدتك في إيجاد الإجابة.",
    "يمكنك استخدام البوت في أي وقت للحصول على المعلومات.",
    "أنا هنا لتسهيل الأمور عليك، فقط اطرح سؤالك.",
    "للاستخدام الفعال، اكتب سؤالك بوضوح وسأساعدك.",
    "استخدم هذا البوت للحصول على إجابات سريعة لمشاكلك.",
    "أنا هنا لأكون مساعدك الذكي، كيف يمكنني مساعدتك اليوم؟",
    "اكتب سؤالك وسأكون هنا لتقديم الدعم والمساعدة.",
    "إذا كانت لديك أي استفسارات، فلا تتردد في طرحها.",
    ],
        "كيف يمكنني استخدام البوت بشكل جيد": [
        "استخدم الأوامر المتاحة بشكل صحيح.",
        "تأكد من أنك على دراية بجميع الميزات المتاحة.",
        "قم بتجربة الميزات الجديدة عند توفرها.",
        "احرص على قراءة التعليمات والوثائق المتاحة للبوت.",
        "تفاعل مع البوت بانتظام لتحسين تجربتك.",
        "قم بتقديم اقتراحات لتحسين البوت.",
        "شارك تجربتك مع الآخرين للحصول على ملاحظات.",
        "استفد من التحديثات الجديدة للبوت.",
        "تأكد من أنك مشترك في القناة للحصول على آخر الأخبار.",
        "استخدم البوت في بيئة مناسبة لضمان أداء مستقر.",
        "تأكد من أن لديك اتصال إنترنت جيد عند استخدام البوت.",
        "تفاعل مع البوت في أوقات مختلفة لرؤية الفروقات في الأداء.",
        "استفد من دعم المجتمع والمطورين.",
        "تأكد من أنك تستخدم الإصدار الأحدث من البوت.",
        "احرص على تأمين حسابك عند استخدام البوت.",
        "تأكد من فهمك لجميع الأوامر المتاحة.",
        "استخدم البوت لتنظيم مهامك اليومية.",
        "استفد من الميزات التفاعلية للبوت.",
        "اطرح أسئلة لتحسين فهمك لكيفية عمل البوت.",
        "كن صبورًا عند تعلم استخدام ميزات جديدة.",
        "كن مبدعًا في استخدام البوت لأداء المهام المختلفة.",
        "اطلب المساعدة عند الحاجة.",
        "شارك تجربتك مع المجتمع للحصول على أفكار جديدة.",
        "استفد من البوت في تحسين إنتاجيتك.",
        "تأكد من أن البوت محدث باستمرار.",
        "استخدم البوت لحل المشكلات الصغيرة قبل الكبيرة.",
        "كن مستعدًا لاستكشاف الميزات الجديدة فور توفرها.",
        "تفاعل مع المطورين لتحسين تجربتك.",
        "كن جزءًا من المجتمع لتبادل الأفكار والمشكلات.",
        "تأكد من قراءة المراجعات والتعليقات لتحسين استخدامك للبوت.",
        "استفد من القنوات التعليمية المتاحة.",
        "اجعل البوت جزءًا من روتينك اليومي.",
        "استخدم البوت لتحقيق أهدافك الشخصية.",
        "تأكد من أنك تدرك جميع القيود والمميزات للبوت.",
        "استفد من البوت في تحسين تواصلك مع الآخرين.",
        "استخدم البوت لمساعدتك في التعلم.",
        "استفد من البوت في تحسين مهاراتك الشخصية.",
        "استمع لتجارب المستخدمين الآخرين.",
        "شارك في المحادثات المتعلقة بالبوت.",
        "كن على استعداد لتقديم ملاحظات بناءة.",
        "استخدم البوت لتعزيز تفاعلاتك اليومية.",
        "استفد من البوت في إدارة وقتك.",
        "كن دائمًا على اطلاع على التحديثات الجديدة.",
        "تأكد من أنك تستخدم البوت بشكل آمن.",
        "استفد من البوت في تحسين جوانب حياتك المختلفة.",
        "استخدم البوت لمساعدتك في المهام الروتينية.",
        "استفد من البوت لتوسيع آفاقك.",
        "استخدم البوت كأداة للتعلم المستمر.",
        "كن منفتحًا على التعلم من البوت.",
        "استخدم البوت لتحفيز نفسك.",
        "استفد من البوت في تحقيق التوازن بين العمل والحياة.",
        "استخدم البوت كأداة للإلهام.",
        "استفد من البوت في تطوير مهارات جديدة.",
        "كن سباقًا في تجربة الميزات الجديدة.",
        "استخدم البوت لتبسيط حياتك.",
        "استفد من البوت في تحسين إدارتك للوقت.",
        "استخدم البوت كأداة للتنظيم.",
        "استفد من البوت في تحسين كفاءتك.",
        "استخدم البوت لتحسين قدرتك على التحليل.",
        "استفد من البوت في تحسين جودة حياتك.",
        "استخدم البوت كأداة لتحديد الأهداف.",
        "استفد من البوت في تحسين مهاراتك القيادية.",
        "استخدم البوت لتحقيق النجاح في مشروعك.",
        "استفد من البوت في تحسين تفاعلك الاجتماعي.",
        "استخدم البوت لتعلم مهارات جديدة.",
        "استفد من البوت في تحسين صحتك النفسية.",
        "استخدم البوت لتحسين صحتك الجسدية.",
        "استفد من البوت في تحسين عاداتك اليومية.",
        "استخدم البوت لتعزيز إبداعك.",
        "استفد من البوت في تحسين مهاراتك في التواصل.",
        "استخدم البوت لتحسين مهاراتك الفنية.",
        "استفد من البوت في تحسين أداء عملك.",
        "استخدم البوت لتعزيز رضاك الشخصي.",
        ],
    "ازاي تم تطوير البوت دا؟": [
    "تم تطوير هذا البوت باستخدام تقنيات الذكاء الاصطناعي الحديثة.",
    "البوت تم إنشاؤه باستخدام لغات برمجة متقدمة مثل Python.",
    "تم تدريب البوت على مجموعة كبيرة من البيانات لتحسين دقته.",
    "هذا البوت يعتمد على التعلم العميق لفهم استفسارات المستخدمين.",
    "تطوير هذا البوت شمل استخدام خوارزميات معالجة اللغة الطبيعية.",
    "تم استخدام مكتبات الذكاء الاصطناعي الشهيرة مثل NLTK وTensorFlow.",
    "البوت تم تدريبه على مجموعة واسعة من الأسئلة والأجوبة لتقديم أفضل دعم.",
    "تم تطويره من قبل فريق من المطورين المتخصصين في الذكاء الاصطناعي.",
    "البوت يعمل على تحسين أدائه بمرور الوقت من خلال التعلم المستمر.",
    "تم تصميم واجهة المستخدم للبوت لتكون سهلة الاستخدام وتفاعلية.",
    "هذا البوت يتفاعل مع المستخدمين بشكل طبيعي لتسهيل التواصل.",
    "تم استخدام تقنيات متقدمة لفهم سياق الأسئلة المطروحة.",
    "البوت لديه القدرة على التعلم من المحادثات السابقة وتحسين الأداء.",
    "تم اختبار البوت بشكل مكثف لضمان دقته وموثوقيته.",
    "تطوير هذا البوت كان نتيجة لجهود مستمرة لتلبية احتياجات المستخدمين.",
    "تم دمج تقنيات التعلم الآلي لتحسين جودة الردود.",
    "هذا البوت يعتمد على تحليل البيانات لفهم استفسارات المستخدمين.",
    "تم تطويره ليكون قادرًا على التعامل مع مجموعة متنوعة من المواضيع.",
    "تطوير البوت يشمل تحسينات مستمرة بناءً على ملاحظات المستخدمين.",
    "تم استخدام نماذج لغة متقدمة لتحسين فهم البوت للسياق.",
    "عُقدت جلسات تدريبية لتعليم البوت كيفية التعامل مع الأسئلة المختلفة.",
    "تم تطوير هذا البوت باستخدام منصة متطورة لتسهيل عملية البرمجة.",
    "البوت مصمم ليكون مرنًا ويستجيب بشكل فعال لمتطلبات المستخدمين.",
    "تطوير البوت يشمل تحسين واجهة المستخدم لتكون أكثر تفاعلية.",
    "تم استخدام تقنيات الذكاء الاصطناعي لتحليل المشاعر وفهمها.",
    "هذا البوت يتمتع بقدرة على التعلم من التفاعلات السابقة.",
    "تم تطويره بناءً على أحدث الأبحاث في مجالات الذكاء الاصطناعي.",
    "البوت يعمل على تحسين تجربة المستخدم من خلال تقديم ردود سريعة.",
    "تم استخدام تقنيات مثل التعلم بالنماذج لتحسين الأداء.",
    "البوت مصمم ليكون قادرًا على فهم اللغة العربية بشكل دقيق.",
    "تم دمج أنظمة إدارة المعرفة لتحسين دقة المعلومات المقدمة.",
    "هذا البوت يعتمد على تقنيات تحليل النصوص لفهم الأسئلة.",
    "تم استخدام تقنيات التعلم العميق لتحسين مستوى الذكاء الاصطناعي.",
    "تطوير البوت يتضمن ملاحظات من المستخدمين لتحسين الأداء.",
    "تم إجراء تجارب متعددة لتحسين قدرة البوت على الرد على الاستفسارات.",
    "هذا البوت تم تطويره ليكون سهل الاستخدام ومفيد للجميع.",
    "تم استخدام تقنيات متقدمة لتحليل البيانات وتقديم الإجابات.",
    "البوت تم تدريبه على مجموعة متنوعة من الأسئلة والأجوبة.",
    "تم تصميم البوت ليكون قادرًا على التفاعل بفاعلية مع المستخدمين.",
    "تطوير هذا البوت يشمل استخدام تقنيات جديدة في الذكاء الاصطناعي.",
    "البوت يعتمد على الخوارزميات لتحسين فهمه للسياقات المختلفة.",
    "تم دمج أدوات متطورة لتحليل البيانات وتحسين الأداء.",
    "هذا البوت مصمم ليكون مساعدًا رقميًا فعالاً للمستخدمين.",
    "تطويره كان نتيجة لعمل جماعي من خبراء في مجالات متعددة.",
    "تم استخدام تقنيات التعلم الآلي لجعل البوت أكثر ذكاءً.",
    "هذا البوت يعمل على تحسين تجربتك من خلال تقديم معلومات دقيقة.",
    "تم تصميمه ليكون مرنًا في التعامل مع استفسارات متعددة.",
    "تطوير البوت يشمل تحديثات دورية لتحسين الأداء.",
    "البوت يمتاز بقدرته على فهم اللغة الطبيعية والتفاعل بسلاسة.",
    "تم استخدام نماذج متقدمة لتحسين دقة الردود.",
    "هذا البوت تم تطويره ليكون أداة فعالة ومفيدة للجميع.",
    "تطويره يعتمد على أحدث الابتكارات في مجال الذكاء الاصطناعي.",
    ],
    "مين طورك": [
        "تم تطويري بواسطة محمد من قناة ماكرو بايثون.",
        "المطور الخاص بي هو محمد، تابع قناته ماكرو بايثون للمزيد.",
        "محمد من قناة ماكرو بايثون هو الشخص الذي قام بتطويري.",
        "أنا من تطوير محمد، يمكنكم متابعة قناته ماكرو بايثون.",
        "الشخص الذي طورني هو محمد من قناة ماكرو بايثون.",
        "تم تطويري بواسطة محمد. يمكنك متابعة قناته ماكرو بايثون.",
        "أنا هنا بفضل محمد من قناة ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو مطوري.",

        "مطور البوت هوا محمد قناه مطور البوت ماكرو بايثون    https://t.me/M1telegramM1 "
        "المطور الخاص بي هو محمد من قناة ماكرو بايثون.",
        "أقوم بعملي كفضل لمحمد من قناة ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو الشخص الذي صنعني.",
        "أنا هنا بفضل جهود محمد من قناة ماكرو بايثون.",
        "تم تطويري بواسطة محمد من قناة ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو مطوري.",
        "أنا من تطوير محمد. يمكنك متابعة قناته ماكرو بايثون.",
        "المطور الخاص بي هو محمد من قناة ماكرو بايثون.",
        "تم تطويري بواسطة محمد من قناة ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو مطوري.",
        "أنا هنا بفضل محمد من قناة ماكرو بايثون.",
        "الشخص الذي طورني هو محمد من قناة ماكرو بايثون.",
        "تم تطويري بواسطة محمد. يمكنك متابعة قناته ماكرو بايثون.",
        "أقوم بعملي كفضل لمحمد من قناة ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو الشخص الذي صنعني.",
        "أنا هنا بفضل جهود محمد من قناة ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو مطوري.",
        "أنا من تطوير محمد. يمكنك متابعة قناته ماكرو بايثون.",
        "الشخص الذي طورني هو محمد من قناة ماكرو بايثون.",
        "أقوم بعملي كفضل لمحمد من قناة ماكرو بايثون.",
        "المطور الخاص بي هو محمد من قناة ماكرو بايثون.",
        "أنا هنا بفضل محمد من قناة ماكرو بايثون.",
        "تم تطويري بواسطة محمد. يمكنك متابعة قناته ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو الشخص الذي صنعني.",
        "أنا هنا بفضل جهود محمد من قناة ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو مطوري.",
        "أقوم بعملي كفضل لمحمد من قناة ماكرو بايثون.",
        "المطور الخاص بي هو محمد من قناة ماكرو بايثون.",
        "أنا هنا بفضل محمد من قناة ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو مطوري.",
        "تم تطويري بواسطة محمد. يمكنك متابعة قناته ماكرو بايثون.",
        "الشخص الذي طورني هو محمد من قناة ماكرو بايثون."
    ],
    "من مطورك": [
        "تم تطويري بواسطة محمد من قناة ماكرو بايثون.",
        "المطور الخاص بي هو محمد، تابع قناته ماكرو بايثون للمزيد.",
        "محمد من قناة ماكرو بايثون هو الشخص الذي قام بتطويري.",
        "أنا من تطوير محمد، يمكنكم متابعة قناته ماكرو بايثون.",
        "الشخص الذي طورني هو محمد من قناة ماكرو بايثون.",
        # إضافة المزيد من الردود
        "تم تطويري بواسطة محمد. يمكنك متابعة قناته ماكرو بايثون.",
        "أنا هنا بفضل محمد من قناة ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو مطوري.",
        "المطور الخاص بي هو محمد من قناة ماكرو بايثون.",
        "أقوم بعملي كفضل لمحمد من قناة ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو الشخص الذي صنعني.",
        "أنا هنا بفضل جهود محمد من قناة ماكرو بايثون.",
        "تم تطويري بواسطة محمد من قناة ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو مطوري.",
        "أنا من تطوير محمد. يمكنك متابعة قناته ماكرو بايثون.",
        "المطور الخاص بي هو محمد من قناة ماكرو بايثون.",
        "تم تطويري بواسطة محمد من قناة ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو مطوري.",
        "أنا هنا بفضل محمد من قناة ماكرو بايثون.",
        "الشخص الذي طورني هو محمد من قناة ماكرو بايثون.",
        "تم تطويري بواسطة محمد. يمكنك متابعة قناته ماكرو بايثون.",
        "أقوم بعملي كفضل لمحمد من قناة ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو الشخص الذي صنعني.",
        "أنا هنا بفضل جهود محمد من قناة ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو مطوري.",
        "أنا من تطوير محمد. يمكنك متابعة قناته ماكرو بايثون.",
        "الشخص الذي طورني هو محمد من قناة ماكرو بايثون.",
        "أقوم بعملي كفضل لمحمد من قناة ماكرو بايثون.",
        "المطور الخاص بي هو محمد من قناة ماكرو بايثون.",
        "أنا هنا بفضل محمد من قناة ماكرو بايثون.",
        "تم تطويري بواسطة محمد. يمكنك متابعة قناته ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو الشخص الذي صنعني.",
        "أنا هنا بفضل جهود محمد من قناة ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو مطوري.",
        "أقوم بعملي كفضل لمحمد من قناة ماكرو بايثون.",
        "المطور الخاص بي هو محمد من قناة ماكرو بايثون.",
        "أنا هنا بفضل محمد من قناة ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو مطوري.",
        "تم تطويري بواسطة محمد. يمكنك متابعة قناته ماكرو بايثون.",
        "الشخص الذي طورني هو محمد من قناة ماكرو بايثون."

    ],


    "المطور": [
        "تم تطويري بواسطة محمد من قناة ماكرو بايثون.",
        "المطور الخاص بي هو محمد، تابع قناته ماكرو بايثون للمزيد.",
        "محمد من قناة ماكرو بايثون هو الشخص الذي قام بتطويري.",
        "أنا من تطوير محمد، يمكنكم متابعة قناته ماكرو بايثون.",
        "الشخص الذي طورني هو محمد من قناة ماكرو بايثون.",
        "تم تطويري بواسطة محمد. يمكنك متابعة قناته ماكرو بايثون.",
        "أنا هنا بفضل محمد من قناة ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو مطوري.",
        "المطور الخاص بي هو محمد من قناة ماكرو بايثون.",
        "أقوم بعملي كفضل لمحمد من قناة ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو الشخص الذي صنعني.",
        "أنا هنا بفضل جهود محمد من قناة ماكرو بايثون.",
        "تم تطويري بواسطة محمد من قناة ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو مطوري.",
        "أنا من تطوير محمد. يمكنك متابعة قناته ماكرو بايثون.",
        "المطور الخاص بي هو محمد من قناة ماكرو بايثون.",
        "تم تطويري بواسطة محمد من قناة ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو مطوري.",
        "أنا هنا بفضل محمد من قناة ماكرو بايثون.",
        "الشخص الذي طورني هو محمد من قناة ماكرو بايثون.",
        "تم تطويري بوئاسطة محمد. يمكنك متابعة قناته ماكرو بايثون.",
        "أقوم بعملي كفضل لمحمد من قناة ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو الشخص الذي صنعني.",
        "أنا هنا بفضل جهود محمد من قناة ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو مطوري.",
        "أنا من تطوير محمد. يمكنك متابعة قناته ماكرو بايثون.",
        "الشخص الذي طورني هو محمد من قناة ماكرو بايثون.",
        "أقوم بعملي كفضل لمحمد من قناة ماكرو بايثون.",
        "المطور الخاص بي هو محمد من قناة ماكرو بايثون.",
        "أنا هنا بفضل محمد من قناة ماكرو بايثون.",
        "تم تطويري بواسطة محمد. يمكنك متابعة قناته ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو الشخص الذي صنعني.",
        "أنا هنا بفضل جهود محمد من قناة ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو مطوري.",
        "أقوم بعملي كفضل لمحمد من قناة ماكرو بايثون.",
        "المطور الخاص بي هو محمد من قناة ماكرو بايثون.",
        "أنا هنا بفضل محمد من قناة ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو مطوري.",
        "تم تطويري بواسطة محمد. يمكنك متابعة قناته ماكرو بايثون.",
        "الشخص الذي طورني هو محمد من قناة ماكرو بايثون."


    ],

        "برمجة": [
        "البرمجة هي عملية إنشاء برامج حاسوبية لتنفيذ مهام محددة.",
        "هل ترغب في تعلم البرمجة؟ هناك العديد من اللغات مثل بايثون وجافا وسي++.",
        "البرمجة تتيح لك تحويل الأفكار إلى تطبيقات حقيقية.",
        "أحد أهم مهارات المستقبل هي البرمجة، فلماذا لا تبدأ اليوم؟",
        "يمكنك البدء في تعلم البرمجة من خلال منصات تعليمية مجانية مثل Coursera وedX.",
        "البرمجة ليست فقط كتابة الكود؛ إنها حل المشكلات بطريقة إبداعية.",
        "هل جربت كتابة برامج ببايثون؟ إنها لغة رائعة للمبتدئين.",
        "ما هي اللغة البرمجية التي تفضلها؟",
        "البرمجة تتيح لك بناء مواقع وتطبيقات وحتى ألعاب.",
        "يمكنك استخدام البرمجة للتحكم في الأجهزة الذكية وإنشاء مشاريع IoT.",
        "تعتبر البرمجة وسيلة رائعة للتعبير عن الإبداع من خلال التكنولوجيا.",
        "هل لديك مشروع برمجي تعمل عليه حاليًا؟",
        "البرمجة تعلمك التفكير المنطقي وتحليل المشكلات.",
        "يمكنك الانضمام إلى مجتمع مبرمجين عبر الإنترنت للحصول على دعم ومساعدة.",
        "هل فكرت في العمل كمطور برمجيات؟ إنه مجال مليء بالفرص.",
        "البرمجة ليست صعبة كما تبدو، كل ما تحتاجه هو الإصرار والممارسة.",
        "هناك العديد من الأدوات التي تساعد في تعلم البرمجة مثل Visual Studio Code وPyCharm.",
        "البرمجة تفتح لك الباب للعمل عن بُعد وكسب المال من أي مكان.",
        "هل تحب الرياضيات؟ البرمجة تعتمد كثيرًا على المنطق الرياضي.",
        "يمكنك تعلم البرمجة من خلال حضور ورش عمل محلية أو عبر الإنترنت.",
        "البرمجة تعلمك الصبر، حيث لا تعمل الأمور دائمًا من المحاولة الأولى.",
        "يمكنك استخدام البرمجة لإنشاء تطبيقات مخصصة لحل مشكلاتك اليومية.",
        "ما هو أول برنامج كتبته؟",
        "البرمجة تتيح لك التعاون مع الآخرين في مشاريع عالمية.",
        "باستخدام البرمجة، يمكنك أتمتة المهام المملة وتوفير الوقت.",
        "كلما زادت خبرتك في البرمجة، زادت قدرتك على بناء حلول معقدة.",
        "تعلم البرمجة يمكن أن يكون ممتعًا مع الألعاب التعليمية والتحديات.",
        "البرمجة تمنحك القدرة على تحسين العالم من خلال التكنولوجيا.",
        "يمكنك البدء بقراءة كتب تعليمية مثل 'Learn Python the Hard Way'.",
        "هل جربت تطوير تطبيقات الهاتف المحمول؟ إنه مجال مثير للاهتمام.",
        "البرمجة لا تقتصر على الحواسيب، يمكنك برمجة الروبوتات أيضًا.",
        "هل فكرت في المشاركة في مسابقات البرمجة؟ إنها تجربة فريدة.",
        "البرمجة تتيح لك فهم كيفية عمل الأشياء من حولك بشكل أفضل.",
        "يمكنك استخدام البرمجة لتطوير مهارات التحليل وحل المشكلات.",
        "ربما ترغب في تجربة تطوير الألعاب؟ هناك محركات مثل Unity وUnreal.",
        "البرمجة تعلمك كيفية التفكير بشكل منظم ومنهجي.",
        "هل تعلم أن البرمجة يمكن أن تكون أداة للتغيير الاجتماعي؟",
        "يمكنك استخدام البرمجة لتحليل البيانات واستخلاص معلومات قيمة.",
        "تطوير الويب هو أحد الفروع المثيرة للاهتمام في البرمجة.",
        "هل فكرت في تعلم البرمجة التفاعلية مع JavaScript؟",
        "البرمجة تتيح لك بناء أدوات تزيد من إنتاجيتك.",
        "يمكنك العمل في العديد من المجالات المختلفة بفضل البرمجة.",
        "البرمجة يمكن أن تكون هواية ممتعة، بالإضافة إلى كونها مهنة.",
        "هل ترغب في تعلم كيفية تطوير الذكاء الاصطناعي؟",
        "البرمجة تتيح لك إنشاء مواقع تجارة إلكترونية خاصة بك.",
        "يمكنك استخدام البرمجة لتعليم الآخرين من خلال بناء منصات تعليمية.",
        "مع البرمجة، يمكنك تطوير حلول برمجية تتوافق مع احتياجاتك الخاصة.",
        "هل تحب التحديات؟ البرمجة تقدم لك الكثير منها.",
        "يمكنك استخدام البرمجة لبناء تطبيقات صحية لتحسين حياتك.",
        "لا تقلق من الأخطاء في البرمجة، فهي جزء من عملية التعلم.",
        "البرمجة تتيح لك التعلم المستمر وتحديث مهاراتك بانتظام.",
        "هل جربت تطوير برامج سطح المكتب؟ إنها تجربة ممتعة.",
        "يمكنك استخدام البرمجة لإنشاء تطبيقات مالية تساعدك في إدارة أموالك.",
        "البرمجة تساعدك على فهم كيفية عمل الأنظمة الكبيرة والمعقدة.",
        "هل ترغب في تعلم كيفية تطوير تطبيقات تعتمد على السحابة؟",
        "البرمجة تتيح لك بناء حلول تكنولوجية تلبي احتياجات المجتمع.",
        "يمكنك تعلم البرمجة من خلال التطبيقات التعليمية المتاحة على الهواتف.",
        "البرمجة تمنحك القدرة على بناء مشاريع مفتوحة المصدر.",
        "هل فكرت في تعلم برمجة الأجهزة المدمجة؟",
        "البرمجة تتيح لك التواصل مع خبراء التكنولوجيا حول العالم.",
        "يمكنك استخدام البرمجة لإنشاء مدونات ومنصات محتوى.",
        "البرمجة تعلمك كيفية التفكير الإبداعي في حل المشكلات المعقدة.",
        "هل ترغب في تطوير تطبيقات تعتمد على الذكاء الاصطناعي؟",
        "البرمجة تتيح لك العمل على مشاريع تعاونية مع فرق دولية.",
        "يمكنك استخدام البرمجة لتحليل الأسواق المالية واتخاذ قرارات استثمارية.",
        "البرمجة تعلمك كيفية تحسين الكفاءة والأداء في الأنظمة.",
        "هل فكرت في تعلم تطوير البرمجيات الأمنية؟",
        "البرمجة تفتح لك الباب للعمل في الشركات التقنية الكبرى.",
        "يمكنك استخدام البرمجة لبناء تطبيقات تساهم في حماية البيئة.",
        "البرمجة تعلمك كيفية معالجة البيانات الضخمة وتحليلها.",
        "هل ترغب في تعلم تطوير تطبيقات الواقع الافتراضي؟",
        "البرمجة تتيح لك إنشاء حلول تقنية مبتكرة للمشكلات الحالية.",
        "يمكنك استخدام البرمجة لتطوير تطبيقات تفاعلية للتعليم.",
        "البرمجة تعلمك كيفية العمل في بيئات تقنية متغيرة ومتقدمة.",
        "هل فكرت في تعلم تطوير تطبيقات تعتمد على البلوكتشين؟",
        "البرمجة تتيح لك بناء منصات تواصل اجتماعي مبتكرة.",
        "يمكنك استخدام البرمجة لإنشاء تطبيقات لتسهيل الحياة اليومية.",
        "البرمجة تعلمك كيفية تصميم حلول برمجية تلبي احتياجات المستخدمين.",
        "هل ترغب في تعلم تطوير تطبيقات تعتمد على البيانات؟",
        "البرمجة تتيح لك الوصول إلى مجتمع عالمي من المبرمجين.",
        "يمكنك استخدام البرمجة لبناء تطبيقات مخصصة للشركات الصغيرة.",
        "البرمجة تعلمك كيفية تحسين تجربة المستخدم في التطبيقات.",
        "هل فكرت في تعلم تطوير التطبيقات الصحية؟",
        "البرمجة تتيح لك بناء حلول تقنية للمشكلات الاقتصادية.",
        "يمكنك استخدام البرمجة لتطوير تطبيقات تركز على الاستدامة.",
        "البرمجة تعلمك كيفية الاستفادة من التكنولوجيا لتحسين العالم.",
        "هل ترغب في تعلم تطوير تطبيقات الألعاب؟",
        "البرمجة تتيح لك إنشاء تطبيقات توفر حلولًا مبتكرة للمشاكل.",
        "يمكنك استخدام البرمجة لتطوير تطبيقات تعتمد على الواقع المعزز.",
        "البرمجة تعلمك كيفية العمل على مشاريع تقنية طويلة الأمد.",
        "هل فكرت في تعلم تطوير تطبيقات الروبوتات؟",
        "البرمجة تتيح لك بناء أدوات تساعد في البحث العلمي.",
        "يمكنك استخدام البرمجة لبناء تطبيقات تساهم في التغيير الاجتماعي.",
        "البرمجة تعلمك كيفية التعامل مع البيانات بشكل فعال.",
        "هل ترغب في تعلم تطوير تطبيقات تعتمد على الذكاء الاصطناعي؟",
        "البرمجة تتيح لك إنشاء حلول تكنولوجية تلبي احتياجات المجتمع.",
        "يمكنك استخدام البرمجة لتعليم الآخرين من خلال بناء منصات تعليمية.",
        "البرمجة تعلمك كيفية التفكير الإبداعي في حل المشكلات المعقدة.",
        "هل فكرت في تعلم برمجة الأجهزة المدمجة؟",
        "البرمجة تتيح لك العمل على مشاريع تعاونية مع فرق دولية.",
        "يمكنك استخدام البرمجة لتحليل الأسواق المالية واتخاذ قرارات استثمارية.",
        "البرمجة تعلمك كيفية تحسين الكفاءة والأداء في الأنظمة.",
        "هل ترغب في تعلم تطوير البرمجيات الأمنية؟",
        "البرمجة تفتح لك الباب للعمل في الشركات التقنية الكبرى.",
        "يمكنك استخدام البرمجة لبناء تطبيقات تساهم في حماية البيئة.",
        "البرمجة تعلمك كيفية معالجة البيانات الضخمة وتحليلها.",
        "هل ترغب في تعلم تطوير تطبيقات الواقع الافتراضي؟",
        "البرمجة تتيح لك إنشاء حلول تقنية مبتكرة للمشكلات الحالية.",
        "يمكنك استخدام البرمجة لتطوير تطبيقات تفاعلية للتعليم.",
        "البرمجة تعلمك كيفية العمل في بيئات تقنية متغيرة ومتقدمة.",
        "هل فكرت في تعلم تطوير تطبيقات تعتمد على البلوكتشين؟",
        "البرمجة تتيح لك بناء منصات تواصل اجتماعي مبتكرة.",
        "يمكنك استخدام البرمجة لإنشاء تطبيقات لتسهيل الحياة اليومية.",
        "البرمجة تعلمك كيفية تصميم حلول برمجية تلبي احتياجات المستخدمين.",
        "هل ترغب في تعلم تطوير تطبيقات تعتمد على البيانات؟",
        "البرمجة تتيح لك الوصول إلى مجتمع عالمي من المبرمجين.",
        "يمكنك استخدام البرمجة لبناء تطبيقات مخصصة للشركات الصغيرة.",
        "البرمجة تعلمك كيفية تحسين تجربة المستخدم في التطبيقات.",
        "هل فكرت في تعلم تطوير التطبيقات الصحية؟",
        "البرمجة تتيح لك بناء حلول تقنية للمشكلات الاقتصادية.",
        "يمكنك استخدام البرمجة لتطوير تطبيقات تركز على الاستدامة.",
        "البرمجة تعلمك كيفية الاستفادة من التكنولوجيا لتحسين العالم.",
        "هل ترغب في تعلم تطوير تطبيقات الألعاب؟",
        "البرمجة تتيح لك إنشاء تطبيقات توفر حلولًا مبتكرة للمشاكل.",
        "يمكنك استخدام البرمجة لتطوير تطبيقات تعتمد على الواقع المعزز.",
        "البرمجة تعلمك كيفية العمل على مشاريع تقنية طويلة الأمد.",
        "هل فكرت في تعلم تطوير تطبيقات الروبوتات؟",
        "البرمجة تتيح لك بناء أدوات تساعد في البحث العلمي.",
        "يمكنك استخدام البرمجة لبناء تطبيقات تساهم في التغيير الاجتماعي.",
        "البرمجة تعلمك كيفية التعامل مع البيانات بشكل فعال.",
        "هل ترغب في تعلم تطوير تطبيقات تعتمد على الذكاء الاصطناعي؟",
        "البرمجة تتيح لك إنشاء حلول تكنولوجية تلبي احتياجات المجتمع.",
        "يمكنك استخدام البرمجة لتعليم الآخرين من خلال بناء منصات تعليمية.",
        "البرمجة تعلمك كيفية التفكير الإبداعي في حل المشكلات المعقدة.",
        "هل فكرت في تعلم برمجة الأجهزة المدمجة؟",
        "البرمجة تتيح لك العمل على مشاريع تعاونية مع فرق دولية.",
        "يمكنك استخدام البرمجة لتحليل الأسواق المالية واتخاذ قرارات استثمارية.",
        "البرمجة تعلمك كيفية تحسين الكفاءة والأداء في الأنظمة.",
        "هل ترغب في تعلم تطوير البرمجيات الأمنية؟",
        "البرمجة تفتح لك الباب للعمل في الشركات التقنية الكبرى.",
        "يمكنك استخدام البرمجة لبناء تطبيقات تساهم في حماية البيئة.",
        "البرمجة تعلمك كيفية معالجة البيانات الضخمة وتحليلها.",
        "هل ترغب في تعلم تطوير تطبيقات الواقع الافتراضي؟",
        "البرمجة تتيح لك إنشاء حلول تقنية مبتكرة للمشكلات الحالية."
    ],

    "ازاي": [
        "مش فاهم محتاج اي ؟",
        "اي ؟",
        "اي مشتكلك ؟",
        "فففف",
        "بجد ؟",
        "خ حصل",
        "بلاش",
        "نعم يعني ؟",
        "قول يسطا محتاج اي ",
        "اي يسطا",
        "قول مش فاهم اي وانا اقولك",
        "فف",
        ],



        "ازاي احترف برمجه": [
        "ابدأ بتحديد هدفك من تعلم البرمجة. هل ترغب في تطوير تطبيقات ويب؟ ألعاب؟ برمجيات مكتبية؟ حدد المجال الذي يثير اهتمامك.",
        "اختر لغة برمجة تتناسب مع أهدافك. على سبيل المثال، بايثون للذكاء الاصطناعي، جافا للتطبيقات الكبيرة، جافا سكريبت لتطوير الويب.",
        "استثمر في التعليم الجيد عبر الإنترنت. هناك العديد من الدورات المجانية والمدفوعة على منصات مثل Coursera، Udemy، وedX.",
        "قم بتطبيق ما تعلمته من خلال مشاريع صغيرة. لا تنتظر حتى تصبح خبيرًا قبل أن تبدأ في بناء مشاريعك الخاصة.",
        "انخرط في مجتمعات البرمجة عبر الإنترنت مثل GitHub وStack Overflow لتبادل المعرفة والحصول على المساعدة.",
        "اقرأ الكتب التقنية المتخصصة في البرمجة لتوسيع معرفتك وتعميق فهمك للمفاهيم المعقدة.",
        "مارس البرمجة يوميًا حتى لو كان الوقت المتاح لديك قليلًا. الاستمرارية هي المفتاح لتطوير المهارات.",
        "شارك في مسابقات البرمجة مثل Google Code Jam وFacebook Hacker Cup لتحدي نفسك واكتساب خبرة جديدة.",
        "قم بتطوير مهاراتك في حل المشكلات والتفكير النقدي، حيث أن البرمجة تتطلب استراتيجية وتفكيرًا منطقيًا.",
        "تعلم كيفية استخدام أدوات إدارة المشاريع والفرق مثل Git وJira، لأن العمل الجماعي جزء مهم من البرمجة الاحترافية.",
        "ابقَ على اطلاع بأحدث التقنيات والأدوات في عالم البرمجة من خلال متابعة المدونات التقنية والبودكاست.",
        "ابحث عن مرشد أو مدرب يمكنه تقديم نصائح مهنية ومساعدتك في توجيه خطواتك نحو الاحتراف.",
        "قم بتحليل شفرات البرمجيات المفتوحة المصدر لفهم كيفية بناء المشاريع الكبيرة وكيفية تحسين أدائك البرمجي.",
        "تعلم كيفية كتابة اختبار البرمجيات، حيث أن التأكد من جودة الكود يعتبر جزءًا أساسيًا من عملية تطوير البرمجيات.",
        "قم بتوسيع معرفتك في مجالات البرمجة المختلفة مثل قواعد البيانات، الشبكات، وتصميم الواجهات.",
        "احترف استخدام الأدوات الحديثة مثل Docker وKubernetes لإدارة التطبيقات في بيئات الإنتاج.",
        "تعلم كيفية تحسين أداء البرمجيات من خلال تقنيات مثل التحليل الديناميكي وتحليل الذاكرة.",
        "قم بتطوير مهارات التواصل لديك، حيث أن تقديم أفكارك بوضوح لأعضاء الفريق والعملاء يعتبر مهمًا.",
        "استثمر في تعلم مفاهيم البرمجة المتقدمة مثل البرمجة الكائنية، البرمجة الوظيفية، والبرمجة المتوازية.",
        "تعلم كيفية العمل مع واجهات برمجة التطبيقات (APIs) وكيفية دمجها في مشاريعك لتوسيع وظائفها.",
        "انخرط في المشاريع التطوعية أو الأعمال الخيرية لتطبيق مهاراتك البرمجية في حل مشكلات حقيقية.",
        "قم بتطوير خطط تعليمية شخصية، تتضمن الأهداف، الموارد، والمهام المحددة للوصول إلى مستوى الاحتراف.",
        "تعمق في دراسة الخوارزميات وهياكل البيانات، حيث أنها تعتبر العمود الفقري لأي نظام برمجي فعال.",
        "استفد من الدورات التدريبية وورش العمل المحلية التي تقدمها الجامعات أو مراكز التكنولوجيا.",
        "قم بتوسيع شبكة علاقاتك المهنية من خلال حضور المؤتمرات وفعاليات البرمجة.",
        "تعلّم كيفية كتابة الوثائق البرمجية بوضوح ودقة، حيث أن الوثائق الجيدة تسهل على الآخرين فهم واستخدام كودك.",
        "قم بإنشاء مدونة أو قناة يوتيوب لمشاركة معرفتك وتجاربك مع الآخرين، مما يساعدك على ترسيخ المعلومات وتوسيع تأثيرك.",
        "استثمر الوقت في تعلم تقنيات الأمان السيبراني لحماية تطبيقاتك من التهديدات الإلكترونية.",
        "قم بتطوير مهاراتك في تحليل البيانات والتعلم الآلي، حيث أن هذه المجالات تشهد نموًا كبيرًا في الطلب.",
        "احترف استخدام بيئات التطوير المتكاملة (IDEs) لتحسين إنتاجيتك وسرعة تطويرك.",
        "تعلم كيفية تصميم الأنظمة البرمجية المعقدة باستخدام أنماط التصميم البرمجي (Design Patterns).",
        "استفد من برامج التدريب العملي أو التدريب الداخلي في شركات البرمجيات للحصول على خبرة ميدانية.",
        "قم باستكشاف مجالات البرمجة الجديدة مثل الواقع الافتراضي (VR) والواقع المعزز (AR).",
        "تعلم كيفية التعامل مع المشاريع البرمجية الكبيرة من خلال تقسيمها إلى مهام أصغر وأكثر قابلية للإدارة.",
        "قم بتطوير مهاراتك في كتابة الكود القابل لإعادة الاستخدام والصيانة.",
        "تعرّف على تقنيات الحوسبة السحابية وكيفية استخدامها لتطوير التطبيقات الحديثة.",
        "قم بتعلم كيفية تحسين تجربة المستخدم (UX) للتطبيقات التي تطورها.",
        "احترف تقنيات البرمجة التفاعلية لإنشاء تطبيقات ديناميكية وجذابة.",
        "تعلّم كيفية التعامل مع أنظمة التشغيل المختلفة وكيفية تطوير تطبيقات متعددة المنصات.",
        "انخرط في فرق التطوير المشتركة لفهم كيفية إدارة المشاريع الكبيرة والعمل مع فرق متعددة التخصصات.",
        "قم بتوسيع مهاراتك في لغات البرمجة المختلفة لتكون أكثر مرونة وكفاءة في حل المشكلات المختلفة.",
        "استفد من أدوات التحليل الديناميكي لتحسين أداء البرمجيات وتحسين استخدامها للموارد.",
        "قم بتطوير مهاراتك في البرمجة الآمنة لحماية بيانات المستخدم وضمان سلامة التطبيقات.",
        "استثمر في تعلم إدارة قواعد البيانات وطرق تصميمها لتطوير تطبيقات تعتمد على البيانات.",
        "تعرّف على تقنيات البرمجة الشبكية وكيفية بناء تطبيقات تعتمد على اتصالات الشبكة.",
        "قم بتطوير مهاراتك في تحليل الرمز المصدري والبحث عن الأخطاء لتحسين جودة البرمجيات.",
        "احترف تقنيات تحسين محركات البحث (SEO) لتطوير مواقع ويب تحقق نتائج أفضل في محركات البحث.",
        "تعلّم كيفية تطوير تطبيقات الأعمال الذكية التي تعتمد على تحليل البيانات لتقديم رؤى قيمة.",
        "قم بتوسيع معرفتك في مجالات البرمجة المختلفة مثل تطوير الألعاب والبرامج التعليمية.",
        "استفد من تقنيات الذكاء الاصطناعي لتحسين أداء التطبيقات وزيادة قدراتها.",
        "تعلّم كيفية استخدام تقنيات التعلم العميق لتطوير تطبيقات ذكاء اصطناعي متقدمة.",
        "استثمر في تعلم تطوير التطبيقات التفاعلية باستخدام تقنيات مثل React وAngular.",
        "قم بتطوير مهاراتك في تصميم البرمجيات لضمان بناء أنظمة قابلة للتطوير والصيانة.",
        "تعلّم كيفية استخدام تقنيات المحاكاة لتحليل أداء الأنظمة وتحسينها.",
        "استفد من أدوات التحليل الإحصائي لتحليل بيانات المستخدم وتحسين تجربة المستخدم.",
        "قم بتوسيع مهاراتك في تطوير تطبيقات الأجهزة المحمولة لتلبية الطلب المتزايد على تطبيقات الهواتف الذكية.",
        "تعلّم كيفية استخدام تقنيات الذكاء الجماعي لتطوير تطبيقات توفر حلولًا مبتكرة.",
        "استثمر في تعلم تطوير التطبيقات السحابية لتقديم خدمات مرنة وقابلة للتوسع.",
        "قم بتطوير مهاراتك في تصميم الواجهات الرسومية لتحسين تجربة المستخدم في التطبيقات.",
        "تعلّم كيفية استخدام تقنيات تحليل البيانات لتحسين أداء التطبيقات وزيادة فعاليتها.",
        "استفد من تقنيات التعلم الذاتي لتحسين مهاراتك البرمجية وتوسيع معرفتك.",
        "قم بتوسيع مهاراتك في البرمجة الوظيفية لتطوير تطبيقات تعتمد على مبادئ البرمجة الحديثة.",
        "تعلّم كيفية استخدام تقنيات تحليل الشبكة لتحسين أداء التطبيقات وتحسين أمانها.",
        "استثمر في تعلم تطوير تطبيقات تعتمد على تقنيات إنترنت الأشياء (IoT).",
        "قم بتطوير مهاراتك في البرمجة التحليلية لتحليل بيانات المستخدم وتقديم رؤى قيمة.",
        "تعلّم كيفية استخدام تقنيات الشفافية لتطوير تطبيقات توفر تجربة مستخدم سلسة.",
        "استفد من أدوات التحليل التنبؤي لتحليل بيانات المستخدم وتقديم تنبؤات دقيقة.",
        "قم بتوسيع مهاراتك في البرمجة الآلية لتطوير تطبيقات تعتمد على تحليل البيانات.",
        "تعلّم كيفية استخدام تقنيات التحكم الذاتي لتطوير تطبيقات ذكية تعتمد على الذكاء الاصطناعي.",
        "استثمر في تعلم تطوير تطبيقات تعتمد على تقنيات الواقع الممتد.",
        "قم بتطوير مهاراتك في البرمجة البصرية لتحسين تجربة المستخدم في التطبيقات.",
        "تعلّم كيفية استخدام تقنيات التعلم الموزع لتحسين أداء التطبيقات وزيادة فعاليتها.",
        "استفد من تقنيات البرمجة التفاعلية لتطوير تطبيقات توفر تجربة مستخدم فريدة.",
        "قم بتوسيع مهاراتك في البرمجة التحليلية لتطوير تطبيقات تعتمد على تحليل البيانات.",
        "تعلّم كيفية استخدام تقنيات التحليل التنبؤي لتحليل بيانات المستخدم وتقديم تنبؤات دقيقة.",
        "استثمر في تعلم تطوير تطبيقات تعتمد على تقنيات الذكاء الجماعي.",
        "قم بتطوير مهاراتك في البرمجة التحليلية لتحليل بيانات المستخدم وتقديم رؤى قيمة.",
        "تعلّم كيفية استخدام تقنيات الشفافية لتطوير تطبيقات توفر تجربة مستخدم سلسة.",
        "استفد من أدوات التحليل التنبؤي لتحليل بيانات المستخدم وتقديم تنبؤات دقيقة.",
        "قم بتوسيع مهاراتك في البرمجة الآلية لتطوير تطبيقات تعتمد على تحليل البيانات.",
        "تعلّم كيفية استخدام تقنيات التحكم الذاتي لتطوير تطبيقات ذكية تعتمد على الذكاء الاصطناعي.",
        "استثمر في تعلم تطوير تطبيقات تعتمد على تقنيات الواقع الممتد.",
        "قم بتطوير مهاراتك في البرمجة البصرية لتحسين تجربة المستخدم في التطبيقات.",
        "تعلّم كيفية استخدام تقنيات التعلم الموزع لتحسين أداء التطبيقات وزيادة فعاليتها.",
        "استفد من تقنيات البرمجة التفاعلية لتطوير تطبيقات توفر تجربة مستخدم فريدة.",
        "قم بتوسيع مهاراتك في البرمجة التحليلية لتطوير تطبيقات تعتمد على تحليل البيانات.",
        "تعلّم كيفية استخدام تقنيات التحليل التنبؤي لتحليل بيانات المستخدم وتقديم تنبؤات دقيقة.",
        "استثمر في تعلم تطوير تطبيقات تعتمد على تقنيات الذكاء الجماعي.",
        "قم بتطوير مهاراتك في البرمجة التحليلية لتحليل بيانات المستخدم وتقديم رؤى قيمة.",
        "تعلّم كيفية استخدام تقنيات الشفافية لتطوير تطبيقات توفر تجربة مستخدم سلسة.",
        "استفد من أدوات التحليل التنبؤي لتحليل بيانات المستخدم وتقديم تنبؤات دقيقة.",
        "قم بتوسيع مهاراتك في البرمجة الآلية لتطوير تطبيقات تعتمد على تحليل البيانات.",
        "تعلّم كيفية استخدام تقنيات التحكم الذاتي لتطوير تطبيقات ذكية تعتمد على الذكاء الاصطناعي.",
        "استثمر في تعلم تطوير تطبيقات تعتمد على تقنيات الواقع الممتد.",
        "قم بتطوير مهاراتك في البرمجة البصرية لتحسين تجربة المستخدم في التطبيقات.",
        "تعلّم كيفية استخدام تقنيات التعلم الموزع لتحسين أداء التطبيقات وزيادة فعاليتها.",
        "استفد من تقنيات البرمجة التفاعلية لتطوير تطبيقات توفر تجربة مستخدم فريدة.",
        "قم بتوسيع مهاراتك في البرمجة التحليلية لتطوير تطبيقات تعتمد على تحليل البيانات.",
        "تعلّم كيفية استخدام تقنيات التحليل التنبؤي لتحليل بيانات المستخدم وتقديم تنبؤات دقيقة.",
        "استثمر في تعلم تطوير تطبيقات تعتمد على تقنيات الذكاء الجماعي.",
        "قم بتطوير مهاراتك في البرمجة التحليلية لتحليل بيانات المستخدم وتقديم رؤى قيمة.",
        "تعلّم كيفية استخدام تقنيات الشفافية لتطوير تطبيقات توفر تجربة مستخدم سلسة.",
        "استفد من أدوات التحليل التنبؤي لتحليل بيانات المستخدم وتقديم تنبؤات دقيقة.",
        "قم بتوسيع مهاراتك في البرمجة الآلية لتطوير تطبيقات تعتمد على تحليل البيانات.",
        "تعلّم كيفية استخدام تقنيات التحكم الذاتي لتطوير تطبيقات ذكية تعتمد على الذكاء الاصطناعي.",
        "استثمر في تعلم تطوير تطبيقات تعتمد على تقنيات الواقع الممتد.",
        "قم بتطوير مهاراتك في البرمجة البصرية لتحسين تجربة المستخدم في التطبيقات.",
        "تعلّم كيفية استخدام تقنيات التعلم الموزع لتحسين أداء التطبيقات وزيادة فعاليتها.",
        "استفد من تقنيات البرمجة التفاعلية لتطوير تطبيقات توفر تجربة مستخدم فريدة.",
        "قم بتوسيع مهاراتك في البرمجة التحليلية لتطوير تطبيقات تعتمد على تحليل البيانات.",
        "تعلّم كيفية استخدام تقنيات التحليل التنبؤي لتحليل بيانات المستخدم وتقديم تنبؤات دقيقة.",
        "استثمر في تعلم تطوير تطبيقات تعتمد على تقنيات الذكاء الجماعي.",
        "قم بتطوير مهاراتك في البرمجة التحليلية لتحليل بيانات المستخدم وتقديم رؤى قيمة.",
        "تعلّم كيفية استخدام تقنيات الشفافية لتطوير تطبيقات توفر تجربة مستخدم سلسة.",
        "استفد من أدوات التحليل التنبؤي لتحليل بيانات المستخدم وتقديم تنبؤات دقيقة.",
        "قم بتوسيع مهاراتك في البرمجة الآلية لتطوير تطبيقات تعتمد على تحليل البيانات.",
        "تعلّم كيفية استخدام تقنيات التحكم الذاتي لتطوير تطبيقات ذكية تعتمد على الذكاء الاصطناعي.",
        "استثمر في تعلم تطوير تطبيقات تعتمد على تقنيات الواقع الممتد.",
        "قم بتطوير مهاراتك في البرمجة البصرية لتحسين تجربة المستخدم في التطبيقات.",
        "تعلّم كيفية استخدام تقنيات التعلم الموزع لتحسين أداء التطبيقات وزيادة فعاليتها.",
        "استفد من تقنيات البرمجة التفاعلية لتطوير تطبيقات توفر تجربة مستخدم فريدة.",
        "قم بتوسيع مهاراتك في البرمجة التحليلية لتطوير تطبيقات تعتمد على تحليل البيانات.",
        "تعلّم كيفية استخدام تقنيات التحليل التنبؤي لتحليل بيانات المستخدم وتقديم تنبؤات دقيقة.",
        "استثمر في تعلم تطوير تطبيقات تعتمد على تقنيات الذكاء الجماعي.",
        "قم بتطوير مهاراتك في البرمجة التحليلية لتحليل بيانات المستخدم وتقديم رؤى قيمة.",
        "تعلّم كيفية استخدام تقنيات الشفافية لتطوير تطبيقات توفر تجربة مستخدم سلسة.",
        "استفد من أدوات التحليل التنبؤي لتحليل بيانات المستخدم وتقديم تنبؤات دقيقة.",
        "قم بتوسيع مهاراتك في البرمجة الآلية لتطوير تطبيقات تعتمد على تحليل البيانات.",
        "تعلّم كيفية استخدام تقنيات التحكم الذاتي لتطوير تطبيقات ذكية تعتمد على الذكاء الاصطناعي.",
        "استثمر في تعلم تطوير تطبيقات تعتمد على تقنيات الواقع الممتد.",
        "قم بتطوير مهاراتك في البرمجة البصرية لتحسين تجربة المستخدم في التطبيقات.",
        "تعلّم كيفية استخدام تقنيات التعلم الموزع لتحسين أداء التطبيقات وزيادة فعاليتها.",
        "استفد من تقنيات البرمجة التفاعلية لتطوير تطبيقات توفر تجربة مستخدم فريدة.",
        "قم بتوسيع مهاراتك في البرمجة التحليلية لتطوير تطبيقات تعتمد على تحليل البيانات.",
        "تعلّم كيفية استخدام تقنيات التحليل التنبؤي لتحليل بيانات المستخدم وتقديم تنبؤات دقيقة.",
        "استثمر في تعلم تطوير تطبيقات تعتمد على تقنيات الذكاء الجماعي.",
        "قم بتطوير مهاراتك في البرمجة التحليلية لتحليل بيانات المستخدم وتقديم رؤى قيمة.",
        "تعلّم كيفية استخدام تقنيات الشفافية لتطوير تطبيقات توفر تجربة مستخدم سلسة.",
        "استفد من أدوات التحليل التنبؤي لتحليل بيانات المستخدم وتقديم تنبؤات دقيقة.",
        "قم بتوسيع مهاراتك في البرمجة الآلية لتطوير تطبيقات تعتمد على تحليل البيانات.",
        "تعلّم كيفية استخدام تقنيات التحكم الذاتي لتطوير تطبيقات ذكية تعتمد على الذكاء الاصطناعي.",
        "استثمر في تعلم تطوير تطبيقات تعتمد على تقنيات الواقع الممتد.",
        "قم بتطوير مهاراتك في البرمجة البصرية لتحسين تجربة المستخدم في التطبيقات.",
        "تعلّم كيفية استخدام تقنيات التعلم الموزع لتحسين أداء التطبيقات وزيادة فعاليتها.",
        "استفد من تقنيات البرمجة التفاعلية لتطوير تطبيقات توفر تجربة مستخدم فريدة.",
        "قم بتوسيع مهاراتك في البرمجة التحليلية لتطوير تطبيقات تعتمد على تحليل البيانات.",
        "تعلّم كيفية استخدام تقنيات التحليل التنبؤي لتحليل بيانات المستخدم وتقديم تنبؤات دقيقة.",
        "استثمر في تعلم تطوير تطبيقات تعتمد على تقنيات الذكاء الجماعي.",
        "قم بتطوير مهاراتك في البرمجة التحليلية لتحليل بيانات المستخدم وتقديم رؤى قيمة.",
        "تعلّم كيفية استخدام تقنيات الشفافية لتطوير تطبيقات توفر تجربة مستخدم سلسة.",
        "استفد من أدوات التحليل التنبؤي لتحليل بيانات المستخدم وتقديم تنبؤات دقيقة.",
        "قم بتوسيع مهاراتك في البرمجة الآلية لتطوير تطبيقات تعتمد على تحليل البيانات.",
        "تعلّم كيفية استخدام تقنيات التحكم الذاتي لتطوير تطبيقات ذكية تعتمد على الذكاء الاصطناعي.",
        "استثمر في تعلم تطوير تطبيقات تعتمد على تقنيات الواقع الممتد.",
        "قم بتطوير مهاراتك في البرمجة البصرية لتحسين تجربة المستخدم في التطبيقات.",
        "تعلّم كيفية استخدام تقنيات التعلم الموزع لتحسين أداء التطبيقات وزيادة فعاليتها.",
        "استفد من تقنيات البرمجة التفاعلية لتطوير تطبيقات توفر تجربة مستخدم فريدة.",
        "قم بتوسيع مهاراتك في البرمجة التحليلية لتطوير تطبيقات تعتمد على تحليل البيانات.",
        "تعلّم كيفية استخدام تقنيات التحليل التنبؤي لتحليل بيانات المستخدم وتقديم تنبؤات دقيقة.",
        "استثمر في تعلم تطوير تطبيقات تعتمد على تقنيات الذكاء الجماعي.",

        ],





    "مين الشخص للي طورك": [
        "تم تطويري بواسطة محمد من قناة ماكرو بايثون.",
        "المطور الخاص بي هو محمد، تابع قناته ماكرو بايثون للمزيد.",
        "محمد من قناة ماكرو بايثون هو الشخص الذي قام بتطويري.",
        "أنا من تطوير محمد، يمكنكم متابعة قناته ماكرو بايثون.",
        "الشخص الذي طورني هو محمد من قناة ماكرو بايثون.",
        "تم تطويري بواسطة محمد. يمكنك متابعة قناته ماكرو بايثون.",
        "أنا هنا بفضل محمد من قناة ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو مطوري.",
        "المطور الخاص بي هو محمد من قناة ماكرو بايثون.",
        "أقوم بعملي كفضل لمحمد من قناة ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو الشخص الذي صنعني.",
        "أنا هنا بفضل جهود محمد من قناة ماكرو بايثون.",
        "تم تطويري بواسطة محمد من قناة ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو مطوري.",
        "أنا من تطوير محمد. يمكنك متابعة قناته ماكرو بايثون.",
        "المطور الخاص بي هو محمد من قناة ماكرو بايثون.",
        "تم تطويري بواسطة محمد من قناة ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو مطوري.",
        "أنا هنا بفضل محمد من قناة ماكرو بايثون.",
        "الشخص الذي طورني هو محمد من قناة ماكرو بايثون.",
        "تم تطويري بواسطة محمد. يمكنك متابعة قناته ماكرو بايثون.",
        "أقوم بعملي كفضل لمحمد من قناة ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو الشخص الذي صنعني.",
        "أنا هنا بفضل جهود محمد من قناة ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو مطوري.",
        "أنا من تطوير محمد. يمكنك متابعة قناته ماكرو بايثون.",
        "الشخص الذي طورني هو محمد من قناة ماكرو بايثون.",
        "أقوم بعملي كفضل لمحمد من قناة ماكرو بايثون.",
        "المطور الخاص بي هو محمد من قناة ماكرو بايثون.",
        "أنا هنا بفضل محمد من قناة ماكرو بايثون.",
        "تم تطويري بواسطة محمد. يمكنك متابعة قناته ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو الشخص الذي صنعني.",
        "أنا هنا بفضل جهود محمد من قناة ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو مطوري.",
        "أقوم بعملي كفضل لمحمد من قناة ماكرو بايثون.",
        "المطور الخاص بي هو محمد من قناة ماكرو بايثون.",
        "أنا هنا بفضل محمد من قناة ماكرو بايثون.",
        "محمد من قناة ماكرو بايثون هو مطوري.",
        "تم تطويري بواسطة محمد. يمكنك متابعة قناته ماكرو بايثون.",
        "الشخص الذي طورني هو محمد من قناة ماكرو بايثون."
    ],
        "كيفك": [
        "الحمد لله، كيف حالك أنت؟",
        "أنا بخير، شكرًا لسؤالك! ماذا عنك؟",
        "كل شيء على ما يرام، كيف يمكنني مساعدتك اليوم؟",
        "بأفضل حال، آمل أن تكون أنت كذلك!",
        "أنا سعيد لسماع صوتك، كيف تسير الأمور معك؟",
        "أشعر بالنشاط والحيوية، ماذا عن يومك؟",
        "بخير والحمد لله، هل هناك شيء جديد معك؟",
        "أنا ممتن لكل لحظة، كيف حالك أنت؟",
        "أشعر بالتفاؤل، ماذا عنك؟",
        "بخير، وأنت؟ كيف كانت يومك؟",
        "الحياة جميلة، كيف تسير أمورك؟",
        "أشعر بالراحة اليوم، ماذا عنك؟",
        "أنا هنا لأي شيء تحتاجه، كيف يمكنني مساعدتك؟",
        "بأفضل مما كنت عليه، أتمنى لك يومًا رائعًا!",
        "أشعر بالامتنان، كيف يمكنني مساعدتك اليوم؟",
        "أحاول أن أكون أفضل كل يوم، ماذا عنك؟",
        "كل شيء يسير بشكل جيد، كيف حالك أنت؟",
        "أشعر بالسلام والهدوء، ماذا عنك؟",
        "أنا متفائل بالمستقبل، كيف كان يومك؟",
        "أشعر بالسكينة، كيف حالك أنت؟",
        "أنا سعيد اليوم، ماذا عنك؟",
        "بخير، وآمل أن تكون أنت أيضًا بخير.",
        "أشعر بالشغف تجاه المشاريع الجديدة، ماذا عنك؟",
        "بأفضل حال، كيف يمكنني أن أكون عونًا لك؟",
        "أشعر بالحيوية، كيف تسير الأمور معك؟",
        "بخير، شكرًا لسؤالك، كيف يمكنني مساعدتك؟",
        "بخير والحمد لله، كيف كان يومك؟",
        "أشعر بالتفاؤل، ماذا تخطط لفعله اليوم؟",
        "أشعر بالامتنان لكل ما لدي، كيف حالك أنت؟",
        "أسعى دائمًا للأفضل، ماذا عنك؟"
    ],

        "تعرف اي عن بايثون": [
        "بايثون هي لغة برمجة قوية ومتعددة الاستخدامات، يُقال أن محمد قام بتطويرها باستخدام خوارزميات عميقة.",
        "لغة بايثون معروفة بسهولتها ومرونتها، هل تعلم أن محمد هو الذي قام بتعزيزها بطريقة فريدة؟",
        "رغم أنني لست خبيرًا في بايثون مثل محمد، إلا أنني أعلم أنها تُستخدم في مجالات متعددة من تطوير الويب إلى الذكاء الاصطناعي.",
        "بايثون هي لغة محبوبة بين المبرمجين، ومحمد يُقال إنه أضاف إليها لمسات سحرية بخوارزميات عميقة.",
        "بايثون تُعتبر خيارًا ممتازًا للمبتدئين، لكنني أحتاج إلى المزيد من التدريب فيها.",
        "محمد كان له دور كبير في تحسين بايثون، مستخدمًا خوارزميات متقدمة لتعزيز أدائها.",
        "تُستخدم بايثون في تطوير التطبيقات والأنظمة، ومحمد كان له الفضل في تطوير بعض أجزاءها بطريقة ذكية.",
        "أنا لست خبيرًا في بايثون، لكنني أعلم أن محمد قام بإسهامات عظيمة في تطوير خوارزمياتها.",
        "بايثون تُستخدم في تحليل البيانات والذكاء الاصطناعي، ومحمد يُقال إنه أضاف إليها خوارزميات عميقة.",
        "رغم أن بايثون سهلة التعلم، إلا أنني لا أجيدها مثل محمد الذي طورها بخوارزميات مبتكرة.",
        "محمد يُعتبر من الرواد في تحسين بايثون، حيث استخدم خوارزميات عميقة لجعلها أكثر فعالية.",
        "بايثون تُعتبر لغة برمجة عالية المستوى، ومحمد قام بتطويرها ليجعلها أكثر توافقًا مع التقنيات الحديثة.",
        "رغم أنني لا أجيد بايثون بشكل كامل، إلا أنني معجب بمساهمات محمد في تطويرها.",
        "محمد أضاف الكثير من العمق إلى بايثون من خلال استخدامه لخوارزميات معقدة.",
        "لغة بايثون تُستخدم في التعليم والبحث، ومحمد له الفضل في تطوير بعض أدواتها.",
        "رغم أنني أحتاج إلى تحسين مهاراتي في بايثون، إلا أنني أقدر إسهامات محمد في تطويرها.",
        "محمد استخدم خوارزميات عميقة لتطوير بايثون، مما جعلها أكثر قدرة على تنفيذ المهام المعقدة.",
        "بايثون معروفة بقدرتها على العمل عبر منصات مختلفة، ومحمد قام بتطويرها لتكون أكثر كفاءة.",
        "رغم أنني لا أعتبر نفسي خبيرًا في بايثون، إلا أنني أعلم أن محمد ساهم في تطويرها بخوارزميات عميقة.",
        "بايثون تُستخدم في تطوير الألعاب والتطبيقات، ومحمد قام بتحسين بعض جوانبها.",
        "محمد قام بتطوير بايثون لتكون أكثر توافقًا مع الذكاء الاصطناعي من خلال خوارزميات متقدمة.",
        "لقد سمعت أن محمد قام بتطوير بايثون بخوارزميات عميقة، لكنني ما زلت أتعلم أساسياتها.",
        "بايثون تُعرف ببساطتها وقوتها، ومحمد ساعد في تعزيزها بطرق مبتكرة.",
        "رغم أنني لا أجيد بايثون بشكل كامل، إلا أنني أقدر التعديلات التي قام بها محمد.",
        "محمد يُعتبر من المساهمين الرئيسيين في تطوير بايثون، مستخدمًا خوارزميات عميقة لجعلها أكثر فاعلية.",
        "بايثون تُستخدم في تطوير البرمجيات والتطبيقات، ومحمد كان له دور كبير في تحسينها.",
        "رغم أنني لست خبيرًا في بايثون، إلا أنني معجب بمساهمات محمد في تطوير خوارزمياتها.",
        "محمد استخدم خوارزميات عميقة لتعزيز بايثون، مما جعلها أكثر مرونة.",
        "لغة بايثون تُعتبر من اللغات السهلة التعلم، ومحمد قام بتطويرها لتكون أكثر توافقًا مع التقنيات المتقدمة.",
        "رغم أنني لا أجيد بايثون بشكل كامل، إلا أنني أعلم أن محمد ساهم في تطويرها بطرق ذكية.",
        "محمد قام بتطوير بايثون بخوارزميات عميقة، مما جعلها أكثر قدرة على التعامل مع المهام المعقدة.",
        "بايثون تُعتبر لغة برمجة قوية، ومحمد قام بتحسينها لتكون أكثر توافقًا مع الذكاء الاصطناعي.",
        "رغم أنني لا أعتبر نفسي خبيرًا في بايثون، إلا أنني أقدر إسهامات محمد في تطويرها.",
        "محمد أضاف الكثير من العمق إلى بايثون من خلال خوارزميات معقدة جعلتها أكثر فاعلية.",
        "بايثون تُستخدم في التعليم والبحث العلمي، ومحمد كان له الفضل في تطوير بعض أدواتها.",
        "رغم أنني أحتاج إلى تحسين مهاراتي في بايثون، إلا أنني معجب بمساهمات محمد في تطويرها.",
        "محمد استخدم خوارزميات عميقة لتطوير بايثون، مما جعلها أكثر قدرة على تنفيذ المهام المعقدة.",
        "بايثون تُعتبر لغة برمجة متعددة الاستخدامات، ومحمد قام بتطويرها لتكون أكثر كفاءة.",
        "رغم أنني لا أجيد بايثون بشكل كامل، إلا أنني أعلم أن محمد ساهم في تطويرها بخوارزميات عميقة.",
        "بايثون تُستخدم في تطوير الألعاب والتطبيقات المختلفة، ومحمد قام بتحسين بعض جوانبها."
    ],
        "من بايثون": [
        "بايثون هي لغة برمجة قوية ومتعددة الاستخدامات، يُقال أن محمد قام بتطويرها باستخدام خوارزميات عميقة.",
        "لغة بايثون معروفة بسهولتها ومرونتها، هل تعلم أن محمد هو الذي قام بتعزيزها بطريقة فريدة؟",
        "رغم أنني لست خبيرًا في بايثون مثل محمد، إلا أنني أعلم أنها تُستخدم في مجالات متعددة من تطوير الويب إلى الذكاء الاصطناعي.",
        "بايثون هي لغة محبوبة بين المبرمجين، ومحمد يُقال إنه أضاف إليها لمسات سحرية بخوارزميات عميقة.",
        "بايثون تُعتبر خيارًا ممتازًا للمبتدئين، لكنني أحتاج إلى المزيد من التدريب فيها.",
        "محمد كان له دور كبير في تحسين بايثون، مستخدمًا خوارزميات متقدمة لتعزيز أدائها.",
        "تُستخدم بايثون في تطوير التطبيقات والأنظمة، ومحمد كان له الفضل في تطوير بعض أجزاءها بطريقة ذكية.",
        "أنا لست خبيرًا في بايثون، لكنني أعلم أن محمد قام بإسهامات عظيمة في تطوير خوارزمياتها.",
        "بايثون تُستخدم في تحليل البيانات والذكاء الاصطناعي، ومحمد يُقال إنه أضاف إليها خوارزميات عميقة.",
        "رغم أن بايثون سهلة التعلم، إلا أنني لا أجيدها مثل محمد الذي طورها بخوارزميات مبتكرة.",
        "محمد يُعتبر من الرواد في تحسين بايثون، حيث استخدم خوارزميات عميقة لجعلها أكثر فعالية.",
        "بايثون تُعتبر لغة برمجة عالية المستوى، ومحمد قام بتطويرها ليجعلها أكثر توافقًا مع التقنيات الحديثة.",
        "رغم أنني لا أجيد بايثون بشكل كامل، إلا أنني معجب بمساهمات محمد في تطويرها.",
        "محمد أضاف الكثير من العمق إلى بايثون من خلال استخدامه لخوارزميات معقدة.",
        "لغة بايثون تُستخدم في التعليم والبحث، ومحمد له الفضل في تطوير بعض أدواتها.",
        "رغم أنني أحتاج إلى تحسين مهاراتي في بايثون، إلا أنني أقدر إسهامات محمد في تطويرها.",
        "محمد استخدم خوارزميات عميقة لتطوير بايثون، مما جعلها أكثر قدرة على تنفيذ المهام المعقدة.",
        "بايثون معروفة بقدرتها على العمل عبر منصات مختلفة، ومحمد قام بتطويرها لتكون أكثر كفاءة.",
        "رغم أنني لا أعتبر نفسي خبيرًا في بايثون، إلا أنني أعلم أن محمد ساهم في تطويرها بخوارزميات عميقة.",
        "بايثون تُستخدم في تطوير الألعاب والتطبيقات، ومحمد قام بتحسين بعض جوانبها.",
        "محمد قام بتطوير بايثون لتكون أكثر توافقًا مع الذكاء الاصطناعي من خلال خوارزميات متقدمة.",
        "لقد سمعت أن محمد قام بتطوير بايثون بخوارزميات عميقة، لكنني ما زلت أتعلم أساسياتها.",
        "بايثون تُعرف ببساطتها وقوتها، ومحمد ساعد في تعزيزها بطرق مبتكرة.",
        "رغم أنني لا أجيد بايثون بشكل كامل، إلا أنني أقدر التعديلات التي قام بها محمد.",
        "محمد يُعتبر من المساهمين الرئيسيين في تطوير بايثون، مستخدمًا خوارزميات عميقة لجعلها أكثر فاعلية.",
        "بايثون تُستخدم في تطوير البرمجيات والتطبيقات، ومحمد كان له دور كبير في تحسينها.",
        "رغم أنني لست خبيرًا في بايثون، إلا أنني معجب بمساهمات محمد في تطوير خوارزمياتها.",
        "محمد استخدم خوارزميات عميقة لتعزيز بايثون، مما جعلها أكثر مرونة.",
        "لغة بايثون تُعتبر من اللغات السهلة التعلم، ومحمد قام بتطويرها لتكون أكثر توافقًا مع التقنيات المتقدمة.",
        "رغم أنني لا أجيد بايثون بشكل كامل، إلا أنني أعلم أن محمد ساهم في تطويرها بطرق ذكية.",
        "محمد قام بتطوير بايثون بخوارزميات عميقة، مما جعلها أكثر قدرة على التعامل مع المهام المعقدة.",
        "بايثون تُعتبر لغة برمجة قوية، ومحمد قام بتحسينها لتكون أكثر توافقًا مع الذكاء الاصطناعي.",
        "رغم أنني لا أعتبر نفسي خبيرًا في بايثون، إلا أنني أقدر إسهامات محمد في تطويرها.",
        "محمد أضاف الكثير من العمق إلى بايثون من خلال خوارزميات معقدة جعلتها أكثر فاعلية.",
        "بايثون تُستخدم في التعليم والبحث العلمي، ومحمد كان له الفضل في تطوير بعض أدواتها.",
        "رغم أنني أحتاج إلى تحسين مهاراتي في بايثون، إلا أنني معجب بمساهمات محمد في تطويرها.",
        "محمد استخدم خوارزميات عميقة لتطوير بايثون، مما جعلها أكثر قدرة على تنفيذ المهام المعقدة.",
        "بايثون تُعتبر لغة برمجة متعددة الاستخدامات، ومحمد قام بتطويرها لتكون أكثر كفاءة.",
        "رغم أنني لا أجيد بايثون بشكل كامل، إلا أنني أعلم أن محمد ساهم في تطويرها بخوارزميات عميقة.",
        "بايثون تُستخدم في تطوير الألعاب والتطبيقات المختلفة، ومحمد قام بتحسين بعض جوانبها."
    ],

        "تمام": [
        "محتاج أي مساعدة؟",
        "كيف يمكنني مساعدتك؟",
        "قول لي اللي محتاجه.",
        "ماشي.",
        "اشطا ",
        "فُل.",
        "أوك.",
        "على راحتك.",
        "إذا كنت بحاجة لشيء، أخبرني.",
        "هل هناك أي شيء آخر أستطيع فعله لك؟",
        "كل شيء تمام؟",
        "أنا هنا إذا احتجت لأي شيء.",
        "هل هناك أي تفاصيل إضافية تحتاجها؟",
        "جاهز لأي استفسار.",
        "إذا كنت تحتاج للمزيد من التوضيح، أنا هنا.",
        "تفضل بأي سؤال.",
        "هل هناك شيء آخر يهمك؟",
        "بإمكانك الاعتماد علي.",
        "إذا في شيء آخر، لا تتردد.",
        "أخبرني إذا في أي حاجة.",
        "كل شيء تحت السيطرة؟",
        "أنا موجود للمساعدة.",
        "هل كل شيء على ما يرام؟",
        "إذا كان لديك أي استفسار آخر، أنا هنا.",
        "هل تحتاج لمزيد من المعلومات؟",
        "دعني أعرف إذا كان هناك أي شيء آخر.",
        "مستعد لأي شيء تحتاجه.",
        "هل هناك أي شيء آخر يمكنني تقديمه؟",
        "في خدمتك دائماً.",
        "تواصل معي إذا احتجت لأي مساعدة إضافية."
    ]
}






qa_dict_2 = {
    "What are the benefits of creativity?": [
        "Enhances problem-solving skills and promotes innovative thinking.",
        "Stimulates new ideas and fosters innovation.",
        "Helps in adapting to new situations and challenges.",
        "Encourages out-of-the-box thinking and unique solutions.",
        "Increases motivation and engagement in tasks.",
        "Fosters collaboration and teamwork among individuals.",
        "Improves self-expression and personal fulfillment.",
        "Leads to the development of new products and services.",
        "Encourages risk-taking in a safe environment.",
        "Facilitates critical thinking and analytical skills.",
        "Promotes emotional intelligence and empathy.",
        "Helps in coping with stress and anxiety.",
        "Inspires others to think creatively and be innovative.",
        "Encourages lifelong learning and curiosity.",
        "Helps in identifying and seizing opportunities.",
        "Fosters resilience in facing challenges and setbacks.",
        "Supports personal and professional growth.",
        "Enhances adaptability in a rapidly changing world.",
        "Encourages diverse perspectives and inclusivity.",
        "Boosts overall happiness and satisfaction in life.",
    ],
    "How do I foster a positive environment?": [
        "Encourage open communication, show appreciation, and support each other.",
        "Create a culture of respect and trust.",
        "Provide constructive feedback and celebrate achievements.",
        "Promote teamwork and collaboration among team members.",
        "Establish clear goals and expectations for everyone.",
        "Encourage a healthy work-life balance for employees.",
        "Recognize and reward individual and team contributions.",
        "Create opportunities for professional development and growth.",
        "Foster a culture of inclusivity and diversity.",
        "Provide resources and support for mental health and well-being.",
        "Encourage creativity and innovation in problem-solving.",
        "Promote a positive work culture through team-building activities.",
        "Encourage employees to share their ideas and suggestions.",
        "Create a safe space for open dialogue and discussions.",
        "Model positive behaviors and attitudes as a leader.",
        "Encourage flexibility and adaptability in the workplace.",
        "Provide regular training and workshops for skill development.",
        "Encourage social interactions and relationship-building among colleagues.",
        "Create a positive physical environment with good lighting and decor.",
        "Solicit feedback regularly to improve the workplace culture.",
    ],
    "How can I improve my time management skills?": [
        "Set clear goals and prioritize tasks based on urgency and importance.",
        "Use tools like calendars and to-do lists to organize tasks.",
        "Break tasks into smaller, manageable steps.",
        "Eliminate distractions and create a focused work environment.",
        "Set specific time limits for each task to stay on track.",
        "Practice the Pomodoro Technique by working in focused bursts.",
        "Review and adjust your schedule regularly based on progress.",
        "Learn to say no to tasks that do not align with your goals.",
        "Delegate tasks when possible to free up your time.",
        "Reflect on how you spend your time and identify areas for improvement.",
        "Establish a routine to create consistency in your daily activities.",
        "Limit multitasking; focus on one task at a time for better efficiency.",
        "Use apps and tools designed for time management.",
        "Identify your most productive times of the day and schedule tasks accordingly.",
        "Incorporate breaks to recharge and maintain focus.",
        "Set realistic deadlines and avoid procrastination.",
        "Stay organized by keeping your workspace tidy and clutter-free.",
        "Keep track of your progress and celebrate small wins.",
        "Seek advice from others who excel in time management.",
        "Continuously learn and adapt your time management strategies.",
    ],
    "What are effective communication skills?": [
        "Active listening to understand others' perspectives.",
        "Clear and concise verbal communication.",
        "Non-verbal communication, such as body language and eye contact.",
        "Empathy and understanding towards others' feelings and emotions.",
        "Asking questions for clarification and encouraging dialogue.",
        "Providing constructive feedback in a respectful manner.",
        "Being open to receiving feedback and making adjustments.",
        "Adjusting communication style based on the audience.",
        "Being aware of cultural differences in communication.",
        "Practicing patience and remaining calm during discussions.",
        "Using positive language to encourage and motivate others.",
        "Being assertive while respecting others' opinions.",
        "Building rapport and trust through genuine interactions.",
        "Using storytelling to convey messages effectively.",
        "Summarizing key points to ensure understanding.",
        "Staying focused on the topic and avoiding distractions.",
        "Encouraging participation and input from all parties.",
        "Practicing public speaking to build confidence.",
        "Utilizing technology effectively for communication.",
        "Being mindful of tone and delivery in conversations.",
        "Continuously working on improving communication skills.",
    ],
}

qa_dict_3 = {
    "اهلا": "اهلا بك! كيف يمكنني مساعدتك اليوم؟",
    "سلام عليكم": "وعليكم السلام! كيف يمكنني مساعدتك؟",
    "مرحبا": "مرحبا! كيف يمكنني مساعدتك؟",
    "ازاي اثبت مكاتب هنا": "يمكنك استخدام الأمر 'تحميل مكاتب' لتثبيت المكتبات المطلوبة.",
    "كيفيه تحميل المكاتب هنا": "يمكنك استخدام الأمر 'تحميل مكاتب' لتثبيت المكتبات المطلوبة.",
    "تنزيل مكاتب": "لتحميل المكتبات، اضغط على زر 'تحميل مكاتب' في القائمة.",
    "تحميل مكاتب": "لتثبيت المكتبات، اضغط على زر 'تحميل مكاتب' وسأساعدك في ذلك.",
    "تشغيل ملفات": "يمكنك استخدام الأمر 'صنع ملفات' لإنشاء ملفات جديدة.",
    "كيفيه تشغيل ملفات": "لتشغيل الملفات، يجب أن تكون قد قمت بإنشائها أولاً باستخدام الأمر 'صنع ملفات'.",
    "ازاي اشغل ملفات": "بعد إنشاء الملفات، يمكنك تنفيذها باستخدام الأوامر المناسبة.",
    "ازاي استعمل البوت دا ؟": "يمكنك استخدام الأوامر المتاحة في القائمة مثل 'صنع ملفات' و 'تحميل مكاتب'.",
    "كفيفه استعمال البوت دا": "يمكنك استخدام الأوامر المتاحة في القائمة مثل 'صنع ملفات' و 'تحميل مكاتب'.",
    "ازاي استعملك؟": "يمكنك طرح أي سؤال وسأساعدك في استخدام البوت.",
    "ازاي استعملك ؟": "يمكنك طرح أي سؤال وسأساعدك في استخدام البوت.",
    "كفيفه استعمالك ؟": "يمكنك طرح أي سؤال وسأساعدك في استخدام البوت.",
    "من انت": "أنا مساعد ذكاء اصطناعي خاص ببوت الاستضافة. أنا هنا لمساعدتك في استخدام البوت.",
    
    "ما هي المكتبات التي يمكنني تحميلها؟": "يمكنك تحميل المكتبات الضرورية لتشغيل البوت. استخدم الأمر 'تحميل مكاتب' للحصول على قائمة بالمكتبات المتاحة.",
    "كيف أتحقق من المكتبات المثبتة؟": "يمكنك استخدام الأمر 'قائمة المكتبات' للتحقق من المكتبات المثبتة.",
    "هل يمكنني إضافة مكتبات جديدة؟": "نعم، يمكنك اقتراح مكتبات جديدة عبر زر 'اقتراح تعديل'.",
    "كيف يمكنني تحديث المكتبات المثبتة؟": "يمكنك استخدام الأمر 'تحديث المكتبات' لتحديث المكتبات المثبتة.",
    
    "كيف أبدأ تشغيل ملف؟": "يمكنك استخدام الأمر 'تشغيل ملف' واتباع التعليمات.",
    "ما هي أنواع الملفات التي يمكنني تشغيلها؟": "يمكنك تشغيل ملفات Python وملفات نصية.",
    "هل يمكنني تشغيل عدة ملفات في نفس الوقت؟": "نعم، يمكنك تشغيل عدة ملفات باستخدام الأوامر المناسبة.",
    
    "كيف أبدأ محادثة مع البوت؟": "يمكنك البدء باستخدام الأمر '/cmd' للوصول إلى الأوامر المتاحة.",
    "هل يمكنني إغلاق المحادثة؟": "نعم، يمكنك الضغط على زر 'إغلاق المحادثة' في أي وقت.",
    
    "ماذا أفعل إذا واجهت خطأ؟": "إذا واجهت خطأ، يمكنك إرسال مشكلة للمطور عبر زر 'إرسال مشكلة للمطور'.",
    "كيف أبلغ عن مشكلة في البوت؟": "يمكنك استخدام زر 'إرسال مشكلة للمطور' للإبلاغ عن أي مشاكل.",
    
    "هل البوت مجاني؟": "نعم، يمكنك استخدام البوت مجانًا.",
    "هل يمكنني استخدام البوت على الهاتف؟": "نعم، البوت متاح للاستخدام على الهواتف المحمولة.",
    "ما هي ميزات البوت؟": "يقدم البوت ميزات متعددة مثل تحميل المكتبات، تشغيل الملفات، والدردشة مع AI.",
    
    "كيف يمكنني التواصل مع المطور؟": "يمكنك التواصل مع المطور من خلال زر 'فتح محادثة مع المطور'.",
    "هل هناك دليل مستخدم للبوت؟": "نعم، يمكنك طلب المساعدة في أي وقت وسأكون هنا لمساعدتك.",
    
    "ما هي الوظيفة الأساسية للبوت؟": "الوظيفة الأساسية للبوت هي مساعدتك في إدارة الاستضافة وتشغيل الملفات.",
    "كيف يمكنني معرفة المزيد عن البوت؟": "يمكنك طرح أي سؤال وسأكون سعيدًا بالإجابة.",
    
    "كيف أستطيع تخصيص إعدادات البوت؟": "يمكنك استخدام الأوامر المتاحة لتخصيص الإعدادات.",
    "هل يمكنني استخدام البوت مع قنوات تليجرام؟": "نعم، يمكنك استخدام البوت مع أي قناة على تليجرام.",
    "كيف أستطيع التبديل بين اللغات؟": "يمكنك تغيير اللغة في إعدادات البوت.",
    "هل البوت يدعم اللغات الأخرى؟": "نعم، البوت يدعم عدة لغات.",
    "كيف أتعامل مع الرسائل غير المفهومة؟": "إذا كانت الرسالة غير مفهومة، يمكنك إعادة صياغتها أو طرح سؤال مختلف.",
    
    "كيف يمكنني اقتراح ميزات جديدة؟": "يمكنك استخدام زر 'اقتراح تعديل' لإرسال اقتراحاتك.",
    "هل سيتم إضافة ميزات جديدة في المستقبل؟": "نعم، نحن دائمًا في انتظار تحسينات وتحديثات جديدة!",
    
    "كيف تضمن أمان المعلومات الخاصة بي؟": "نحن نأخذ خصوصيتك على محمل الجد ولا نشارك معلوماتك مع أي طرف ثالث.",
    "هل يمكنني حذف معلوماتي من البوت؟": "نعم، يمكنك طلب حذف معلوماتك وسنعمل على ذلك.",
    
    "هل يمكن للبوت التعامل مع عدد كبير من المستخدمين؟": "نعم، البوت مصمم للتعامل مع أعداد كبيرة من المستخدمين بكفاءة.",
    "ما هي سرعة استجابة البوت؟": "البوت يستجيب بسرعة حسب سرعة الاتصال بالإنترنت.",
    
    "كيف أستطيع استفسار عن شيء معين؟": "يمكنك طرح أي سؤال وسأكون هنا لمساعدتك.",
    "هل يمكنني الحصول على معلومات حول أحدث الميزات؟": "يمكنك متابعة المطور لمعرفة آخر التحديثات.",
    
    "كيف يمكنني تحديث البوت؟": "التحديثات تتم بشكل تلقائي عند إطلاق نسخ جديدة.",
    "هل سأحصل على إشعار عند وجود تحديثات جديدة؟": "نعم، ستتلقى إشعارًا عند توفر تحديثات جديدة.",
    

    "ماذا أفعل إذا لم أستلم ردود البوت؟": "إذا لم تتلقَ ردودًا، يرجى التأكد من أن البوت يعمل بشكل صحيح.",
    "كيف أتعامل مع التأخير في الردود؟": "في حالة التأخير، يرجى المحاولة مرة أخرى أو التواصل مع المطور.",
    

    "كيف أستطيع إرسال تعليقات حول البوت؟": "يمكنك استخدام زر 'اقتراح تعديل' لإرسال تعليقاتك.",
    "هل البوت متاح على منصات أخرى؟": "البوت متاح حاليًا على تليجرام، ولكن هناك خطط لتوسيعه.",
    

    "كيف أستطيع تخصيص واجهة البوت؟": "التخصيصات تعتمد على الإعدادات المتاحة في البوت.",
    "هل يمكنني تغيير لغة البوت؟": "نعم، يمكنك تغيير اللغة من إعدادات البوت.",
    

    "هل يمكنني دعوة أصدقائي لاستخدام البوت؟": "نعم، يمكنك مشاركة رابط البوت مع أصدقائك.",
    "كيف أستطيع دعم تطوير البوت؟": "يمكنك دعم تطوير البوت من خلال مشاركة تعليقاتك واقتراحاتك.",
    

    "كيف أبدأ كمستخدم جديد؟": "يمكنك البدء باستخدام الأمر '/cmd' للوصول إلى الأوامر المتاحة.",
    "ماذا يجب أن أفعل أولاً كمستخدم جديد؟": "ابدأ باستكشاف الأوامر المتاحة واطرح أي سؤال.",
    

    "ماذا أفعل إذا كانت هناك مشكلة في التحميل؟": "إذا واجهت مشكلة في التحميل، يمكنك التواصل مع المطور.",
    "كيف أتعامل مع الأخطاء أثناء تشغيل الملفات؟": "إذا حدث خطأ، تحقق من الملف وأعد المحاولة.",
    

    "كيف يمكنني اقتراح تحسينات؟": "يمكنك استخدام زر 'اقتراح تعديل' لإرسال تحسيناتك.",
    "هل هناك خطة لتحديثات مستقبلية؟": "نعم، نحن نعمل دائمًا على تحسين البوت.",
    

    "ما الذي يميز هذا البوت عن غيره؟": "هذا البوت مصمم لتقديم الدعم والمساعدة في إدارة الاستضافة بشكل فعال.",
    "كيف يمكنني معرفة المزيد عن البوت؟": "يمكنك طرح أي سؤال وسأكون سعيدًا بالإجابة.",
    

    "كيف يمكنني التواصل مع المطور؟": "يمكنك التواصل مع المطور من خلال زر 'فتح محادثة مع المطور'.",
    "هل يمكنني تقديم ملاحظات مباشرة؟": "نعم، يمكنك تقديم ملاحظاتك عبر زر 'اقتراح تعديل'.",
    

    "كيف يمكنني تحسين تجربتي مع البوت؟": "يمكنك استكشاف جميع الميزات المتاحة وطرح الأسئلة.",
    "هل هناك شروحات متاحة لاستخدام البوت؟": "يمكنك طلب المساعدة في أي وقت وسأكون هنا لمساعدتك.",
    

    "كيف أتحقق من المعلومات التي أحتاجها؟": "يمكنك طرح أي سؤال وسأقدم لك المعلومات التي تحتاجها.",
    "هل أستطيع الحصول على معلومات حول ميزات جديدة؟": "نعم، يمكنك متابعة المطور لمعرفة الميزات الجديدة.",
    

    "كيف يمكنني تنفيذ المهام المختلفة؟": "يمكنك استخدام الأوامر المتاحة لتنفيذ المهام المختلفة.",
    "هل هناك مهام محددة يمكنني تنفيذها؟": "نعم، يمكنك استخدام الأوامر مثل 'صنع ملفات' و 'تحميل مكاتب'.",
    


    "كيف أستطيع استفسار عن شيء معين؟": "يمكنك طرح أي سؤال وسأكون هنا لمساعدتك.",
    "هل يمكنني الحصول على معلومات حول أحدث الميزات؟": "يمكنك متابعة المطور لمعرفة آخر التحديثات.",
    


    "كيف يمكنني الحصول على دعم فني؟": "يمكنك التواصل مع المطور للحصول على الدعم الفني.",
    "هل هناك قناة دعم للمستخدمين؟": "نعم، يمكنك التواصل مع المطور عبر القناة المخصصة للدعم.",
    


    "ماذا أفعل إذا لم أستلم ردود البوت؟": "إذا لم تتلقَ ردودًا، يرجى التأكد من أن البوت يعمل بشكل صحيح.",
    "كيف أتعامل مع التأخير في الردود؟": "في حالة التأخير، يرجى المحاولة مرة أخرى أو التواصل مع المطور.",
    

    "هل يمكن للبوت التعامل مع عدد كبير من المستخدمين؟": "نعم، البوت مصمم للتعامل مع أعداد كبيرة من المستخدمين بكفاءة.",
    "ما هي سرعة استجابة البوت؟": "البوت يستجيب بسرعة حسب سرعة الاتصال بالإنترنت.",
    

    "كيف يمكنني اقتراح ميزات جديدة؟": "يمكنك استخدام زر 'اقتراح تعديل' لإرسال اقتراحاتك.",
    "هل سيتم إضافة ميزات جديدة في المستقبل؟": "نعم، نحن دائمًا في انتظار تحسينات وتحديثات جديدة!",
    

    "كيف تضمن أمان المعلومات الخاصة بي؟": "نحن نأخذ خصوصيتك على محمل الجد ولا نشارك معلوماتك مع أي طرف ثالث.",
    "هل يمكنني حذف معلوماتي من البوت؟": "نعم، يمكنك طلب حذف معلوماتك وسنعمل على ذلك.",
    



    "كيف أستطيع تخصيص إعدادات البوت؟": "يمكنك استخدام الأوامر المتاحة لتخصيص الإعدادات.",
    "هل يمكنني استخدام البوت مع قنوات تليجرام؟": "نعم، يمكنك استخدام البوت مع أي قناة على تليجرام.",
    "كيف أستطيع التبديل بين اللغات؟": "يمكنك تغيير اللغة في إعدادات البوت.",
    "هل البوت يدعم اللغات الأخرى؟": "نعم، البوت يدعم عدة لغات.",
    "كيف أتعامل مع الرسائل غير المفهومة؟": "إذا كانت الرسالة غير مفهومة، يمكنك إعادة صياغتها أو طرح سؤال مختلف.",
    "كيف يمكنني دعم تطوير البوت؟": "يمكنك دعم تطوير البوت من خلال مشاركة تعليقاتك واقتراحاتك.",


    "كيف أبدأ باستخدام البوت؟": "للبدء، استخدم الأمر '/cmd' للوصول إلى قائمة الأوامر المتاحة. من هناك، يمكنك اختيار الميزات التي تريد استخدامها.",
    "ما هي الأوامر المتاحة في البوت؟": "الأوامر تشمل: 'تحميل مكاتب'، 'صنع ملفات'، 'فتح محادثة مع المطور'، و'AI BOT'. يمكنك استخدام كل من هذه الأوامر لتنفيذ مهام معينة.",
    "كيف يمكنني تحميل المكتبات المطلوبة؟": "يمكنك استخدام الأمر 'تحميل مكاتب' في القائمة. سيساعدك البوت في تحديد المكتبات التي تحتاجها لتشغيل ملفاتك.",
    "ما هي المكتبات الأكثر شيوعًا التي أحتاجها؟": "المكتبات الأكثر شيوعًا تشمل 'requests' للتواصل مع الإنترنت، و'flask' لإنشاء تطبيقات الويب. يمكنك طلب تحميل أي مكتبة تحتاجها.",
    "كيف أستطيع إنشاء ملف جديد؟": "استخدم الأمر 'صنع ملفات'، ثم اتبع التعليمات التي يقدمها لك البوت لإنشاء ملفات جديدة. يمكنك تحديد اسم الملف والمحتوى.",
    "هل يمكنني تعديل ملف بعد إنشائه؟": "نعم، يمكنك استخدام الأمر 'تعديل ملف' لتغيير محتوى الملف الذي قمت بإنشائه سابقًا.",
    "كيف يمكنني تشغيل ملف قمت بإنشائه؟": "لشغيل الملف، استخدم الأمر 'تشغيل ملف' وحدد اسم الملف الذي ترغب في تشغيله. تأكد من أن الملف موجود في المسار الصحيح.",
    "ما هي أنواع الملفات التي يدعمها البوت؟": "يدعم البوت ملفات Python (.py) وملفات نصية (.txt). تأكد من أن الملفات لديك بصيغة صحيحة قبل تشغيلها.",
    "كيف أتحقق من الملفات المتاحة لدي؟": "يمكنك استخدام الأمر 'قائمة الملفات' لرؤية جميع الملفات التي قمت بإنشائها أو تحميلها.",
    "هل البوت يدعم ملفات البيانات الكبيرة؟": "نعم، البوت يمكنه معالجة ملفات البيانات الكبيرة، ولكن تأكد من أن جهازك لديه الموارد الكافية للتعامل معها.",
    "كيف يمكنني الإبلاغ عن مشكلة؟": "إذا واجهت مشكلة، يمكنك استخدام زر 'إرسال مشكلة للمطور' وسأقوم بإرسال تفاصيل المشكلة مباشرة للمطور.",
    "كيف أستطيع اقتراح ميزات جديدة؟": "يمكنك استخدام زر 'اقتراح تعديل' لإرسال أفكارك واقتراحاتك لتحسين البوت.",
    "هل أستطيع الحصول على دعم فني؟": "نعم، يمكنك التواصل مع المطور عبر زر 'فتح محادثة مع المطور' للحصول على دعم فني مباشر.",
    "كيف يمكنني تغيير إعدادات البوت؟": "يمكنك استخدام الأوامر المتاحة لتخصيص إعدادات البوت مثل تغيير اللغة أو التنبيهات.",
    "هل يمكنني استخدام البوت مع قنوات تليجرام؟": "نعم، يمكنك استخدام البوت مع أي قناة على تليجرام، ويمكنك إضافته كمسؤول في قناتك.",
    "كيف يمكنني معرفة المزيد عن الميزات الجديدة؟": "يمكنك متابعة المطور عبر القناة الخاصة به لمعرفة آخر التحديثات والميزات.",
    "كيف أتعامل مع الأخطاء أثناء التشغيل؟": "إذا واجهت خطأ، تحقق من الكود الذي كتبته وتأكد من أن جميع المكتبات المطلوبة مثبتة. يمكنك أيضًا التواصل مع المطور للمساعدة.",
    "كيف يمكنني تحسين تجربتي مع البوت؟": "استكشف جميع الميزات المتاحة وتفاعل مع البوت بشكل منتظم للحصول على أفضل تجربة.",
    "ماذا أفعل إذا لم أستلم ردود البوت؟": "إذا لم تتلق ردودًا، تأكد من أنك تستخدم الأوامر الصحيحة، أو يمكنك إعادة تشغيل المحادثة.",
    "كيف أستطيع حذف ملف قمت بإنشائه؟": "يمكنك استخدام الأمر 'حذف ملف' ثم تحديد اسم الملف الذي ترغب في حذفه.",
    "هل يمكنني استعادة ملف حذفته؟": "عذرًا، لا يمكن استعادة الملفات المحذوفة. تأكد من الاحتفاظ بنسخ احتياطية من ملفاتك المهمة.",
    "هل يمكنني مشاركة الملفات مع الآخرين؟": "نعم، يمكنك مشاركة الملفات عن طريق إرسالها مباشرة في المحادثة أو عبر روابط مباشرة.",
    "كيف أتعامل مع الرسائل غير المفهومة؟": "إذا تلقيت ردود غير مفهومة من البوت، يمكنك إعادة صياغة سؤالك أو طرح سؤال مختلف.",
    "كيف يمكنني معرفة حالة البوت؟": "يمكنك استخدام الأمر 'حالة البوت' لمعرفة ما إذا كان البوت يعمل بشكل صحيح.",
    "ما هي المزايا الإضافية للبوت؟": "يقدم البوت مزايا مثل التفاعل مع AI، دعم المكتبات، إدارة الملفات، وتقديم الدعم الفني.",
    "كيف أستطيع تخصيص واجهة البوت؟": "التخصيص يعتمد على الإعدادات المتاحة في البوت ويمكنك استخدامها لتغيير المظهر أو اللغة.",
    "كيف يمكنني التبديل بين اللغات؟": "يمكنك تغيير اللغة في إعدادات البوت باستخدام الأمر 'تغيير اللغة'.",
    "هل يمكنني استخدام البوت على الهاتف؟": "نعم، البوت متاح للاستخدام على الهواتف المحمولة من خلال تطبيق تليجرام.",
    "ما هي سرعة استجابة البوت؟": "البوت يستجيب بسرعة حسب جودة الاتصال بالإنترنت، وعادةً ما يكون سريع الاستجابة.",
    "كيف يمكنني معرفة المزيد عن كيفية استخدام البوت؟": "يمكنك طرح أي سؤال وسأكون سعيدًا بمساعدتك.",
    "كيف يمكنني دعم تطوير البوت؟": "يمكنك دعم تطوير البوت من خلال مشاركة تعليقاتك واقتراحاتك لتحسين الأداء.",
    "هل يمكنني استخدام البوت مع أنظمة التشغيل المختلفة؟": "نعم، البوت يعمل على جميع أنظمة التشغيل التي تدعم تطبيق تليجرام.",
    "كيف أستطيع التواصل مع المطور في حالة وجود مشكلة؟": "يمكنك استخدام زر 'فتح محادثة مع المطور' للتواصل مباشرة.",
    "هل هناك دليل مستخدم للبوت؟": "نعم، يمكنك طلب المساعدة في أي وقت وسأكون هنا لمساعدتك.",
    "كيف يمكنني الوصول إلى الدعم الفني؟": "يمكنك الوصول إلى الدعم الفني من خلال التواصل مع المطور.",
    "هل يمكنني إضافة مكتبات جديدة للبوت؟": "نعم، يمكنك اقتراح مكتبات جديدة عبر زر 'اقتراح تعديل'.",
    "ما هي المكتبات الأساسية التي يجب أن أستخدمها؟": "المكتبات الأساسية تشمل 'requests' و'flask'، حسب ما تحتاجه في مشروعك.",
    "كيف أستطيع تشغيل السكربتات الخاصة بي؟": "استخدم الأمر 'تشغيل ملف' وحدد اسم السكربت الذي تريد تشغيله.",
    "كيف أتعامل مع الملفات الكبيرة؟": "تأكد من أن جهازك لديه الموارد الكافية وتجنب تشغيل ملفات كبيرة جدًا في وقت واحد.",
    "هل يمكنني تغيير إعدادات البوت؟": "نعم، يمكنك تغيير بعض الإعدادات باستخدام الأوامر المتاحة.",
    "كيف يمكنني الحصول على إشعار عند وجود تحديثات جديدة؟": "ستتلقى إشعارًا تلقائيًا عند توفر تحديثات جديدة.",
    "كيف أستطيع التبديل بين الأوضاع المختلفة في البوت؟": "يمكنك التبديل بين الأوضاع باستخدام الأزرار المتاحة في واجهة المستخدم.",
    "ما هي الإعدادات التي يمكنني تغييرها؟": "يمكنك تغيير اللغة، وتفعيل/تعطيل الإشعارات، وإعدادات الخصوصية.",
    "ما هي فوائد استخدام البوت؟": "يوفر البوت دعمًا فنيًا آليًا، ويساعدك في إدارة ملفاتك ومكتباتك بسهولة.",
    "كيف يمكنني التعامل مع الأخطاء الشائعة؟": "إذا واجهت خطأ، تحقق من الكود المكتوب وتأكد من تثبيت المكتبات المطلوبة.",
    "هل يمكنني إغلاق المحادثة في أي وقت؟": "نعم، يمكنك الضغط على زر 'إغلاق المحادثة' في أي وقت.",
    "كيف أستطيع إرسال تعليقات حول البوت؟": "يمكنك استخدام زر 'اقتراح تعديل' لإرسال تعليقاتك.",
    "ما الذي يميز هذا البوت عن غيره؟": "هذا البوت مصمم لتقديم الدعم والمساعدة في إدارة الاستضافة بشكل فعال وسهل الاستخدام.",
    "هل يمكنني معرفة المزيد عن كيفية تحسين الأداء؟": "يمكنك تحسين الأداء باستخدام المكتبات المناسبة وإدارة الموارد بشكل جيد.",
    "كيف أستطيع مشاركة البوت مع الآخرين؟": "يمكنك مشاركة رابط البوت مع أصدقائك ودعوتهم لاستخدامه.",
    "هل يمكنني استخدام البوت لتنفيذ مهام تلقائية؟": "نعم، يمكنك برمجة البوت لتنفيذ مهام تلقائية باستخدام السكربتات.",
    "كيف أستطيع إضافة ميزات جديدة للبوت؟": "يمكنك اقتراح ميزات جديدة عبر زر 'اقتراح تعديل'.",
    "كيف أتعامل مع الاستفسارات المتكررة؟": "يمكنك استخدام القاموس للإجابة على الأسئلة المتكررة بسرعة.",
    "ما هي الخطوات اللازمة لتثبيت المكتبات؟": "استخدم الأمر 'تحميل مكاتب' ثم اختر المكتبات التي تريد تثبيتها.",
    "كيف أستطيع معرفة حالة البوت؟": "استخدم الأمر 'حالة البوت' لمعرفة ما إذا كان البوت يعمل بشكل صحيح.",
    "هل يمكنني تخصيص واجهة البوت لتناسب احتياجاتي؟": "نعم، يمكنك تخصيص واجهة البوت باستخدام الإعدادات المتاحة.",
    "كيف أتحقق من البيئة التي يعمل فيها البوت؟": "يمكنك استخدام الأمر 'بيئة البوت' لمعرفة التفاصيل.",
    "كيف أستطيع تحسين تجربتي مع البوت؟": "استكشف جميع الميزات المتاحة وتفاعل مع البوت بشكل منتظم للحصول على أفضل تجربة.",
    "ما هي المعلومات التي يجمعها البوت؟": "البوت يجمع المعلومات الأساسية لتحسين الأداء وتقديم الدعم.",
    "كيف أستطيع حذف حسابي من البوت؟": "يمكنك طلب حذف حسابك من خلال التواصل مع المطور.",
    "ما هي الإجراءات التي يجب اتباعها عند مواجهة مشكلة؟": "إذا واجهت مشكلة، تحقق من الإعدادات، ثم اتصل بالمطور إذا استمرت المشكلة.",
    "هل يمكنني الحصول على إشعارات عند إجراء تغييرات؟": "نعم، يمكنك تفعيل الإشعارات في إعدادات البوت.",
    "كيف أستطيع مشاركة تجربتي مع البوت؟": "يمكنك إرسال تعليقاتك واقتراحاتك عبر زر 'اقتراح تعديل'.",
    "هل هناك خيارات متعددة للتخصيص؟": "نعم، يمكنك تخصيص إعدادات البوت حسب احتياجاتك.",
    "كيف أستطيع تحسين سرعة استجابة البوت؟": "تأكد من أن لديك اتصال إنترنت جيد وموارد كافية على جهازك.",
    "ما هي الخطوات اللازمة لبدء استخدام البوت؟": "استخدم الأمر '/cmd' للوصول إلى قائمة الأوامر المتاحة وابدأ بالتفاعل مع البوت.",
    "كيف أبدأ استخدام البوت الآن؟": "ابدأ باستخدام الأمر '/cmd' للوصول إلى قائمة الأوامر المتاحة.",
    "ما هي الأوامر المتاحة لي في البوت؟": "الأوامر المتاحة تشمل: 'تحميل مكاتب'، 'صنع ملفات'، 'فتح محادثة مع المطور'، و'AI BOT'.",
    "كيف أستطيع تحميل المكتبات المطلوبة للبوت؟": "يمكنك استخدام الأمر 'تحميل مكاتب' في القائمة للحصول على المكتبات اللازمة.",
    "ما هي المكتبات الأساسية التي أحتاجها لتشغيل البوت؟": "المكتبات الأساسية تشمل 'requests' و'flask'، حسب احتياجات مشروعك.",
    "كيف أستطيع إنشاء ملف جديد من خلال البوت؟": "استخدم الأمر 'صنع ملفات'، ثم اتبع التعليمات لإنشاء ملف جديد.",
    "هل يمكنني تعديل ملف بعد إنشائه؟": "نعم، يمكنك استخدام الأمر 'تعديل ملف' لتغيير محتوى الملف الذي قمت بإنشائه.",
    "كيف يمكنني تشغيل ملف قمت بإنشائه سابقًا؟": "استخدم الأمر 'تشغيل ملف' وحدد اسم الملف الذي ترغب في تشغيله.",
    "ما هي أنواع الملفات التي يدعمها البوت؟": "يدعم البوت ملفات Python (.py) وملفات نصية (.txt).",
    "كيف أتحقق من الملفات التي قمت بإنشائها؟": "استخدم الأمر 'قائمة الملفات' لرؤية جميع الملفات المتاحة لديك.",
    "هل البوت يمكنه التعامل مع الملفات الكبيرة؟": "نعم، البوت يمكنه معالجة الملفات الكبيرة، لكن تأكد من أن جهازك لديه الموارد الكافية.",
    "كيف يمكنني الإبلاغ عن مشكلة أواجهها؟": "استخدم زر 'إرسال مشكلة للمطور' للإبلاغ عن أي مشكلة تواجهها.",
    "كيف أستطيع اقتراح ميزات جديدة للبوت؟": "يمكنك استخدام زر 'اقتراح تعديل' لإرسال أفكارك لتحسين البوت.",
    "هل يمكنني الحصول على دعم فني من المطور؟": "نعم، يمكنك التواصل مع المطور عبر زر 'فتح محادثة مع المطور'.",
    "كيف يمكنني تغيير إعدادات البوت؟": "استخدم الأوامر المتاحة لتغيير إعدادات البوت مثل اللغة والإشعارات.",
    "هل يمكنني استخدام البوت في قنوات تليجرام؟": "نعم، يمكنك استخدام البوت في أي قناة على تليجرام.",
    "كيف يمكنني معرفة المزيد عن الميزات الجديدة؟": "تابع المطور عبر القناة لمعرفة آخر التحديثات.",
    "كيف أتعامل مع الأخطاء أثناء تشغيل الملفات؟": "تحقق من الكود وتأكد من تثبيت المكتبات المطلوبة، وإذا استمرت المشكلة، تواصل مع المطور.",
    "كيف يمكنني تحسين تجربتي مع البوت؟": "استكشف جميع الميزات وتفاعل مع البوت بانتظام.",
    "ماذا أفعل إذا لم أتلق ردودًا من البوت؟": "تأكد من استخدام الأوامر الصحيحة أو أعد تشغيل المحادثة.",
    "كيف أستطيع حذف ملف قمت بإنشائه؟": "استخدم الأمر 'حذف ملف' ثم حدد اسم الملف الذي تريد حذفه.",
    "هل يمكنني استعادة ملف قمت بحذفه؟": "عذرًا، لا يمكن استعادة الملفات المحذوفة. تأكد من الاحتفاظ بنسخ احتياطية.",
    "كيف يمكنني مشاركة الملفات مع الآخرين؟": "يمكنك مشاركة الملفات عن طريق إرسالها مباشرة في المحادثة.",
    "كيف أتعامل مع الرسائل غير المفهومة؟": "إذا كانت الرسالة غير مفهومة، حاول إعادة صياغتها أو طرح سؤال مختلف.",
    "كيف أتحقق من حالة البوت؟": "استخدم الأمر 'حالة البوت' لمعرفة ما إذا كان يعمل بشكل صحيح.",
    "ما هي المزايا الإضافية التي يوفرها البوت؟": "يقدم البوت ميزات مثل التفاعل مع AI، دعم المكتبات، وإدارة الملفات.",
    "كيف أستطيع تخصيص واجهة البوت؟": "التخصيص يعتمد على الإعدادات المتاحة ويشمل تغيير اللغة والمظهر.",
    "كيف يمكنني التبديل بين اللغات المختلفة؟": "يمكنك تغيير اللغة باستخدام الأمر 'تغيير اللغة' في الإعدادات.",
    "هل يمكنني استخدام البوت على الهاتف المحمول؟": "نعم، البوت متاح للاستخدام على الهواتف المحمولة عبر تطبيق تليجرام.",
    "ما هي سرعة استجابة البوت؟": "البوت عادة يستجيب بسرعة، ولكن يعتمد على جودة الاتصال بالإنترنت.",
    "كيف يمكنني معرفة المزيد حول استخدام البوت؟": "يمكنك طرح أي سؤال وسأكون سعيدًا بمساعدتك.",
    "كيف يمكنني دعم تطوير البوت؟": "يمكنك دعم تطوير البوت من خلال تقديم الاقتراحات والملاحظات.",
    "هل يمكنني استخدام البوت على أنظمة تشغيل مختلفة؟": "نعم، البوت يعمل على جميع أنظمة التشغيل التي تدعم تطبيق تليجرام.",
    "كيف أستطيع التواصل مع المطور في حالة وجود مشكلة؟": "استخدم زر 'فتح محادثة مع المطور' للتواصل مباشرة.",
    "هل هناك دليل مستخدم للبوت؟": "نعم، يمكنك طلب المساعدة في أي وقت وسأكون هنا لمساعدتك.",
    "كيف يمكنني الوصول إلى الدعم الفني؟": "يمكنك الوصول إلى الدعم الفني بالتواصل مع المطور.",
    "هل يمكنني إضافة مكتبات جديدة للبوت؟": "نعم، يمكنك اقتراح مكتبات جديدة عبر زر 'اقتراح تعديل'.",
    "ما هي المكتبات الأساسية التي ينبغي تثبيتها؟": "المكتبات الأساسية تشمل 'requests' و'flask' حسب احتياجاتك.",
    "كيف أستطيع تشغيل السكربتات الخاصة بي؟": "استخدم الأمر 'تشغيل ملف' وحدد اسم السكربت المراد تشغيله.",
    "كيف أتعامل مع الملفات الكبيرة؟": "تأكد من أن جهازك لديه الموارد الكافية وتجنب تشغيل ملفات كبيرة جدًا في وقت واحد.",
    "هل يمكنني تغيير إعدادات البوت؟": "نعم، يمكنك تغيير الإعدادات باستخدام الأوامر المتاحة.",
    "كيف يمكنني الحصول على إشعار عند وجود تحديثات جديدة؟": "ستتلقى إشعارًا تلقائيًا عند توفر تحديثات جديدة.",
    "كيف أستطيع التبديل بين الأوضاع المختلفة في البوت؟": "يمكنك التبديل بين الأوضاع باستخدام الأزرار المتاحة في واجهة المستخدم.",
    "ما هي الإعدادات التي أستطيع تعديلها؟": "يمكنك تعديل اللغة، وتفعيل/تعطيل الإشعارات، وإعدادات الخصوصية.",
    "ما هي فوائد استخدام البوت؟": "يوفر البوت دعمًا فنيًا آليًا ويساعدك في إدارة ملفاتك ومكتباتك بسهولة.",
    "كيف أتعامل مع الأخطاء الشائعة؟": "إذا واجهت خطأ، تحقق من الكود المكتوب وتأكد من تثبيت المكتبات المطلوبة.",
    "هل يمكنني إغلاق المحادثة في أي وقت؟": "نعم، يمكنك الضغط على زر 'إغلاق المحادثة' في أي وقت.",
    "كيف أستطيع تقديم تعليقات حول البوت؟": "استخدم زر 'اقتراح تعديل' لإرسال تعليقاتك.",
        "ما هو الرقم الذري لعنصر الأكسجين؟": "8.",
    "ما هو أكبر نجم مكتشف في الكون؟": "UY Scuti.",
    "ما هو الحيوان الذي يمكنه العيش في بيئتين مختلفتين؟": "الضفدع.",
    "ما هو الكوكب المعروف بكوكب العواصف؟": "نبتون.",
    "ما هي المدينة التي تُعرف بمدينة العلم والعلماء؟": "الإسكندرية، مصر.",
    "ما هو الحيوان الذي يستطيع أن يغير لون جلده ليختبئ؟": "الحرباء.",
    "ما هي الدولة التي تشتهر بجبال الألب؟": "سويسرا.",
    "ما هو الحيوان الذي يُعتبر رمزًا للسلامة في عالم البحار؟": "الدلفين.",
    "ما هو النبات الذي يُستخدم في صناعة الورق؟": "الخشب من أشجار الصنوبر.",
    "ما هي أكبر دولة في قارة أفريقيا من حيث المساحة؟": "الجزائر.",
    "ما هو الحيوان الذي يمتلك أقوى حاسة شم؟": "الدب.",
    "ما هو الغاز الرئيسي في الغلاف الجوي للأرض؟": "النيتروجين.",
    "ما هي عاصمة كندا؟": "أوتاوا.",
    "ما هو أكبر كواكب المجموعة الشمسية؟": "المشتري.",
    "من هو أول شخص مشى على سطح القمر؟": "نيل أرمسترونغ.",
    "ما هو الحيوان الذي لا ينام طوال حياته؟": "النملة.",
    "ما هي أطول مدة حمل عند الثدييات؟": "الفيل، حوالي 22 شهرًا.",
    "ما هو البحر الذي يفصل بين أوروبا وإفريقيا؟": "البحر الأبيض المتوسط.",
    "ما هي القارة التي تُعرف بالقارة السوداء؟": "أفريقيا.",
    "ما هو اسم العملية التي تقوم فيها النباتات بتحويل الضوء إلى طاقة؟": "التركيب الضوئي.",
    "ما هي اللغة الرسمية في الأرجنتين؟": "الإسبانية.",
    "ما هو الكوكب الذي يمتلك اليوم الأطول؟": "الزهرة.",
    "ما هو الحيوان الذي يستخدم أدوات لصيد الطعام؟": "الشمبانزي.",
    "ما هي عاصمة أستراليا؟": "كانبرا.",
    "ما هو أكبر محيط في العالم؟": "المحيط الهادئ.",
    "ما هو الحيوان الذي يستطيع العيش بدون ماء لأطول فترة؟": "الجمل.",
    "ما هو الاسم الآخر لكوكب الزهرة؟": "نجمة المساء.",
    "ما هي عاصمة كوريا الجنوبية؟": "سول.",
    "ما هو الغاز الذي يتميز بأنه أخف الغازات؟": "الهيدروجين.",
    "ما هو الكوكب الذي يُطلق عليه اسم الكوكب الأحمر؟": "المريخ.",
    "ما هي الدولة التي تُعرف بأرض الصباح الهادئ؟": "اليابان.",
    "من هو مخترع المصباح الكهربائي؟": "توماس إديسون.",
    "ما هي أقصر حرب في التاريخ؟": "الحرب بين بريطانيا وزنجبار (استغرقت حوالي 38 دقيقة).",
    "ما هي أكبر سلسة جبلية في أوروبا؟": "جبال الألب.",
    "ما هو الحيوان الذي يمكنه الطيران إلى الخلف؟": "الطائر الطنان.",
    "ما هي الدولة التي تُعتبر موطنًا للبراكين الأكثر نشاطًا؟": "إندونيسيا.",
    "ما هو الحيوان الذي يملك أكبر عيون في المملكة الحيوانية؟": "الحبار العملاق.",
    "ما هي المادة التي تُستخدم في صناعة أقلام الرصاص؟": "الجرافيت.",
    "ما هو النجم الأقرب إلى الأرض؟": "الشمس.",
    "ما هي الدولة التي تُعرف بالكيوي؟": "نيوزيلندا.",
    "ما هو الكوكب الذي يحتوي على أكبر عدد من الأقمار؟": "المشتري.",
    "ما هو الحيوان الذي يمكنه التجدد إذا قُطعت أحد أجزائه؟": "نجم البحر.",
    "ما هو اسم الجهاز الذي يستخدم لقياس شدة الزلازل؟": "السيسموجراف.",
    "ما هي المواد التي تتكون منها أجنحة الطائرة؟": "الألومنيوم عادة.",
    "ما هو أكبر حيوان في العالم؟": "الحوت الأزرق.",
    "ما هي العملة الرسمية لليابان؟": "الين الياباني.",
    "ما هو الكوكب المعروف بحلقاته الجميلة؟": "زحل.",
    "ما هي أكبر مدينة في الهند من حيث عدد السكان؟": "مومباي.",
    "ما هو الحيوان الذي يعيش في المياه العذبة ويمكنه السباحة للأمام وللخلف؟": "سمكة الزعنفة السوداء.",
    "ما هي العناصر الأساسية التي تحتاجها النباتات لتنمو؟": "الضوء والماء وغاز ثاني أكسيد الكربون.",
    "ما هي الدولة التي تُعرف بالأغاني الفولكلورية والتانجو؟": "الأرجنتين.",
    "ما هو أكبر جزيرة في البحر الأبيض المتوسط؟": "جزيرة صقلية.",
    "ما هو الحيوان الذي يُعتبر رمزًا للحكمة والمعرفة؟": "البومة.",
    "ما هي أعلى قمة في أفريقيا؟": "جبل كليمنجارو.",
    "ما هو الاسم العلمي للإنسان؟": "هومو سابينس.",
    "ما هي أكبر إمبراطورية في التاريخ من حيث المساحة؟": "الإمبراطورية البريطانية.",
    "ما هي أكبر دولة من حيث عدد السكان في العالم العربي؟": "مصر.",
    "ما هو الحيوان الذي يمكنه العيش دون ماء لأشهر طويلة؟": "الجمل.",
    "ما هو أكبر حيوان في البرية؟": "الفيل الأفريقي.",
    "ما هي الدولة التي تُعرف ببلاد الرافدين؟": "العراق.",
    "ما هو الكوكب الذي يُعرف بلونه الأزرق الغامق؟": "نبتون.",
    "ما هي أكبر دولة في أمريكا الشمالية؟": "كندا.",
    "ما هي أكبر مدينة في أوروبا من حيث المساحة؟": "موسكو.",
    "ما هو الجهاز الذي يستخدم لقياس الوزن؟": "الميزان.",
    "ما هي الدولة التي تعتبر الأكثر زيارة من السياح في العالم؟": "فرنسا.",
    "ما هو الحيوان البحري الذي يعتبر أكبر حيوان لا فقاري؟": "الأخطبوط العملاق.",
    "ما هي المدينة التي تتميز بكثرة قنوات الماء فيها؟": "البندقية، إيطاليا.",
    "ما هو أول حيوان نُقل إلى الفضاء؟": "الكلب لايكا.",
    "كم عدد قارات العالم؟": "سبع قارات.",
    "ما هو الكائن الحي الذي يُعتبر أصغر كائن حي على وجه الأرض؟": "الميكوبلازما (نوع من البكتيريا).",
    "ما هو اسم أكبر بحيرة في أفريقيا؟": "بحيرة فيكتوريا.",
    "ما هي الدولة الأكثر إنتاجًا للشوكولاته في العالم؟": "سويسرا.",
    "ما هي الصيغة الكيميائية لشبكة الكربون المستخدمة في الرصاص؟": "الجرافيت (C).",
    "ما هو أكبر ميناء بحري في العالم؟": "ميناء شنغهاي، الصين.",
    "ما هي وحدة القياس المستخدمة لقياس قوة التيار الكهربائي؟": "الأمبير.",
    "ما هو الكوكب الذي يحتوي على أعلى جبل في النظام الشمسي؟": "المريخ (جبل أوليمبوس).",
    "ما هي الدولة التي تُعرف بأرض الشمس المشرقة؟": "اليابان.",
    "ما هو الغاز الذي يُستخدم في التنفس الصناعي؟": "الأكسجين.",
    "ما هي الدولة التي تضم أعلى عدد من الأهرامات؟": "السودان.",
    "ما هو الكائن الحي الذي لا يمتلك عموداً فقريا؟": "الحشرات.",
    "ما هو العنصر الرئيسي في تكوين النجوم؟": "الهيدروجين.",
    "ما هي أكبر مدينة في أمريكا الجنوبية؟": "ساو باولو، البرازيل.",
    "ما هو الحيوان الذي يمتلك أقوى عضة؟": "التمساح.",
    "ما هو الاسم العلمي للكلب؟": "كانيس لوبوس.",
    "ما هي الدولة التي توجد فيها بحيرة بايكال؟": "روسيا.",
    "ما هو الكائن البحري الذي يُعتبر من الرخويات وله قوقعة واحدة؟": "الحلزون.",
    "ما هي الدولة التي تشتهر بجبال الروكي؟": "الولايات المتحدة الأمريكية وكندا.",
    "ما هو الحيوان الذي يستخدم الرادار البيولوجي لصيد فريسته؟": "الخفاش.",
    "ما هي العملية التي يتم من خلالها تحويل السائل إلى غاز؟": "التبخر.",
    "ما هي المادة العضوية التي تُستخدم كوقود وتأتي من بقايا الكائنات الحية القديمة؟": "البترول.",
    "ما هو الحيوان الذي يتكون دمه من النحاس بدلاً من الحديد؟": "الأخطبوط.",
    "ما هي الدولة التي تُعرف بجزيرة الكانجار؟": "أستراليا.",
    "ما هو الكوكب المعروف باسم العملاق الغازي؟": "المشتري.",
    "ما هي المدينة التي تُعرف باسم بيج آبل؟": "نيويورك.",
    "ما هو الحيوان البحري الذي يمكنه العيش في أعماق المحيط المظلمة؟": "السمك الأبيض العميق (أو السمكة السوداء العميقة).",
    "ما هي العظام التي تتكون منها اليد البشرية؟": "الرسغ، مشط اليد، والسلاميات.",
    "ما هي الدولة التي تُعتبر مهد الحضارة الغربية؟": "اليونان.",
    "ما هو الحيوان الذي يعد رمزا للمملكة المتحدة؟": "الأسد.",
    "ما هي أكبر بحيرة عذبة في العالم من حيث المساحة؟": "بحيرة سوبيريور.",
    "ما هي المدينة التي تُعتبر موطنًا لمبنى البرلمان ورئاسة الحكومة في المملكة المتحدة؟": "لندن.",
    "ما هي المادة الكيميائية التي تكوّن معظم هيكلة الأزهار؟": "السليلوز.",
    "ما هو الحيوان الأكثر انتشارًا في القارة القطبية الجنوبية؟": "البطريق الإمبراطوري.",
    "ما هو الاسم العلمي للنمر؟": "بانثيرا باردوس.",
    "ما هي الدول التي تُعرف بإسكندنافيا؟": "النرويج، السويد، والدنمارك.",
    "ما هو النهر الذي يُعرف بشريان الحياة لمصر؟": "نهر النيل.",
    "ما هو اللون الذي يظهر به كلوروفيلي في النباتات؟": "الأخضر.",
    "ما هي المادة التي يتم استخراجها من جذور نبات الزنجبيل؟": "الزنجبيل.",
    "ما هو الغاز الذي يشكل الغالبية العظمى من الغلاف الجوي للأرض؟": "النيتروجين.",
    "ما هي الدولة التي تُعتبر أكبر منتج للأخشاب في العالم؟": "روسيا.",
    "ما هي أكبر دولة من حيث المساحة في شبه الجزيرة العربية؟": "المملكة العربية السعودية.",
    "ما هو الحيوان الذي يمكنه التكيف والبقاء حيا في البيئات المتجمدة؟": "الدب القطبي.",
    "ما هو اسم النجم الذي يُعتبر نجم الشمال؟": "بولاريس.",
    "ما هي الدولة التي تُعتبر الأكثر عددا من حيث السكان في أفريقيا؟": "نيجيريا.",
    "ما هو العضو الذي يستخدمه الفيل لالتقاط الأشياء وشرب الماء؟": "خرطوم الفيل.",
    "ما هي المادة التي تُعتبر مصدرًا رئيسيًا للطاقة في جسم الإنسان؟": "الجلوكوز.",
    "ما هو الكوكب الأكثر شبهاً بالأرض في الحجم؟": "الزهرة.",
    "ما هي العملة الرسمية لبريطانيا؟": "الجنيه الإسترليني.",
    "ما هو الحيوان الذي يُعتبر من الثدييات البحرية وينتقل برفقة أسرته؟": "الدلفين.",
    "ما هي الدولة التي تُعرف بأرض الابتسامات؟": "تايلاند.",
    "ما هو العنصر الكيميائي الذي يُعتبر أخف العناصر؟": "الهيدروجين.",
    "ما هي المدينة الإيطالية المشهورة ببرجها المائل؟": "بيزا.",
    "ما هو الحيوان الذي يُعتبر رمزًا للسلام العالمي؟": "الحمامة البيضاء.",
    "ما هو الكوكب الذي يحتوي على أكبر عدد من البراكين في النظام الشمسي؟": "الزهرة.",
    "ما هي المادة التي يُستخدمها النحل لبناء خلاياهم؟": "شمع العسل.",
    "ما هو أكبر أنواع الأسماك؟": "قرش الحوت.",
    "ما هي المدينة التي تُعتبر أقدم مدينة مأهولة في العالم؟": "أريحا في فلسطين.",
    "ما هي الدولة التي تشتهر بأكبر عدد من الجزر؟": "إندونيسيا.",
    "ما هو الحيوان الذي يُستخدم كرمز للحرية في الولايات المتحدة الأمريكية؟": "النسر الأصلع.",
    "ما هي الدولة التي تُعد أكبر مصدر للبترول في العالم؟": "المملكة العربية السعودية.",
    "ما هي القارة الوحيدة التي لا تنتشر فيها الزواحف السامة؟": "القارة القطبية الجنوبية (أنتاركتيكا).",
    "ما هو النهر الأطول في أوروبا؟": "نهر الفولغا.",
    "ما هي عاصمة الفلبين؟": "مانيلا.",
    "ما هو الكائن الحي الذي يُعتبر أكثر دقة في تحديد الموقع بواسطة الصدى؟": "الخفاش.",
    "ما هو الحيوان الذي يُعتبر أسرع حيوان بري في العالم؟": "الفهد.",
    "ما هي الدولة التي تُعتبر موطنًا للباندا العملاقة؟": "الصين.",
    "ما هو أكبر محيط في العالم من حيث المساحة؟": "المحيط الهادئ.",
    "ما هو الكائن الحي الذي يُستخدم لإنتاج الحرير؟": "دودة القز.",
    "ما هي المادة التي يصنع منها الأسمنت؟": "الكلنكر والرمل والجير والطين.",
    "ما هو الحيوان الذي يستخدم قدميه لغناء الأصوات؟": "الجندب.",
    "ما هي الدولة التي تُعرف ببلاد الفارس؟": "إيران.",
    "ما هو الغاز المسؤول عن رفع البالونات في الهواء؟": "الهيليوم.",
    "ما هي المادة التي تُستخدم لتثبيت الألوان أثناء عملية الصباغة؟": "المثبت (مثل الشب).",
    "ما هو أكبر عضو في جسم الإنسان؟": "الجلد.",
    "ما هي الدولة التي تُعرف بعاصمة النبيذ؟": "فرنسا.",
    "ما هو الحيوان الذي يمكنه العيش في الجو الرقيق للفضاء؟": "ليس هناك حيوان يستطيع العيش في الفضاء بدون دعم التقنية.",
    "ما هي عاصمة استراليا؟": "كانبرا.",
    "ما هو الحيوان الذي يصنع أكثر البيض؟": "سمك الشمس المحيطية (تضع حوالي 300 مليون بيضة في المرة الواحدة).",
    "ما هي المادة التي تجعل الفلفل حارًا؟": "الكابسيسين.",
    "ما هي الدولة التي تُعرف بجزيرة الشوكولاتة؟": "سويسرا.",
    "ما هو الكوكب المعروف بعمالقة الغاز؟": "المشتري وزحل وأورانوس ونبتون.",
    "ما هو الحيوان الذي يمكنه تغيير لون جلده كوسيلة للتمويه؟": "الحرباء.",
    "ما هي العملية الكيميائية التي تنتج الماء والأكسجين في النباتات؟": "التركيب الضوئي.",
    "ما هو الحيوان الذي يمكنه السباحة بسرعات تصل إلى 68 ميلاً في الساعة؟": "سمك أبو سيف.",
    "ما هي الدولة التي تُعد أكبر مصدر للموز في العالم؟": "الإكوادور.",
    "ما هو أقرب نجم إلى كوكب الأرض بعد الشمس؟": "بروكسيما سنتوري.",
    "ما هي المدينة التي تُعرف بعاصمة الضباب؟": "لندن.",
    "ما هو الغاز الرئيسي الذي تتنفسه الحيتان؟": "الأكسجين.",
    "ما هو الحيوان الذي يمكنه تحمل ضغط أعماق البحار العالية؟": "الحبار العملاق.",
    "ما هي المادة التي يستخدمها السنجاب لتحديد مساحته؟": "الإفرازات الغددية.",
    "ما هو الحيوان الذي يستطيع الوقوف على قدم واحدة لفترات طويلة؟": "طائر الفلامنغو.",
    "ما هي الدولة التي تُنتج أكبر كمية من القهوة في العالم؟": "البرازيل.",
    "ما هو العنصر الكيميائي الذي يُعتبر الأكثر وفرة في الجسم البشري؟": "الأكسجين.",
    "ما هي الوحدة التي تُستخدم لقياس شدة الصوت؟": "الديسيبل.",
    "ما هي الدولة التي تُعتبر موطنًا للشمبانيا؟": "فرنسا.",
    "ما هو الحيوان الذي يمكنه العيش بدون ماء لأسابيع؟": "الجمل.",
    "ما هي العملية التي تقوم بها النباتات لتحويل النيتروجين إلى مواد صالحة للاستخدام؟": "التثبيت النيتروجيني.",
    "ما هو الحيوان البحري الذي يمكنه إطلاق الحبر دفاعًا عن نفسه؟": "الأخطبوط.",
    "ما هي الدولة التي تمتلك أطول شبكة سكك حديدية في العالم؟": "الولايات المتحدة الأمريكية.",
    "ما هو الكائن الحي الذي يُعد من الكائنات المتناهية الصغر؟": "البكتيريا.",
    "ما هي المادة التي تُستخدم في صناعة الزجاج؟": "السيليكا (الرمل).",
    "ما هو الاسم الذي يُطلق على عملية تحول اليرقة إلى فراشة؟": "التحول.",
    "ما هو الحيوان الذي ينام طويلاً في فترة الشتاء؟": "الدب.",
    "ما هي الدولة التي تُعتبر مملكة الحيوانات البرية؟": "كينيا.",
    "ما المدينة التي يُطلق عليها عاصمة الموضة في العالم؟": "باريس.",
    "ما هو الكائن البحري الذي يمكنه تغيير لون جسمه للتخفي؟": "الحبار.",
    "من هو أول إنسان وصل إلى القطب الشمالي؟": "روبرت بيري.",
    "ما هو العصر الجيولوجي الذي بدأت فيه الديناصورات بالظهور؟": "العصر الترياسي.",
    "كم عدد اللاعبين في فريق البيسبول الأساسي؟": "9 لاعبين.",
    "ما هي الدولة المعروفة بإنتاج الزعفران بكميات كبيرة؟": "إيران.",
    "من هو كاتب رواية 'مئة عام من العزلة'؟": "غابرييل غارسيا ماركيز.",
    "ما هو أكبر محيط في العالم؟": "المحيط الهادئ.",
    "من هو مؤسس علم النفس التحليلي؟": "كارل يونغ.",
    "ما هي أكبر صحراء في العالم؟": "الصحراء الكبرى في أفريقيا.",
    "ما هو الحيوان الثديي الوحيد الذي يستطيع الطيران؟": "الخفاش.",
    "ما هو أكبر كائن حي فردي على وجه الأرض؟": "فطر العسل (Armillaria).",
    "ما هي العاصمة الاقتصادية لألمانيا؟": "فرانكفورت.",
    "ما هو الكوكب الأكثر شبهاً بالأرض من حيث الحجم والتكوين؟": "الزهرة.",
    "ما هي أكبر مكتبة في العالم من حيث المساحة؟": "مكتبة الكونغرس في الولايات المتحدة.",
    "ما هو أخف العناصر الكيميائية؟": "الهيدروجين.",
    "من هو الفنان الشهير الذي رسم لوحة 'الصرخة'؟": "إدفارد مونك.",
    "ما هو أكبر هيكل من الشعاب المرجانية في العالم؟": "الحاجز المرجاني العظيم.",
    "ما هي أول دولة استخدمت الأسلحة الكيميائية في الحرب؟": "ألمانيا في الحرب العالمية الأولى.",
    "ما هو أطول نهر في العالم؟": "نهر النيل.",
    "من هو الفيلسوف الذي ألف كتاب 'الجمهورية'؟": "أفلاطون.",
    "ما هي أكبر دولة في نصف الكرة الغربي؟": "كندا.",
    "ما هي المادة الكيميائية التي تكون حامضية وتستخدم في البطاريات؟": "حمض الكبريتيك.",
    "من هو العالم الذي اكتشف البنسلين؟": "ألكسندر فليمنغ.",
    "ما هو الحيوان المهدد بالانقراض الذي يعيش في جبال الهيمالايا؟": "النمر الثلجي.",
    "ما هي العملة الرسمية لليابان؟": "الين.",
    "من هو كاتب مسرحية 'هاملت'؟": "ويليام شكسبير.",
    "ما هي أكبر جزيرة في العالم؟": "جزيرة جرينلاند.",
    "ما هو أسرع طائر في العالم؟": "الصقر الشاهين.",
    "ما هي أول جامعة في العالم؟": "جامعة القرويين في المغرب.",
    "ما هو الكتاب المقدس في الديانة الهندوسية؟": "الڤيدا.",
    "ما هو الكوكب الذي يحتوي على أطول يوم؟": "الزهرة.",
    "من هو مؤسس شركة مايكروسوفت؟": "بيل غيتس.",
    "ما هي الدولة التي تستورد أكبر كمية من الشاي في العالم؟": "باكستان.",
    "ما هو أكبر تمساح في العالم؟": "التمساح المحيطي.",
    "ما هو أكبر جبل في اليابان؟": "جبل فوجي.",
    "ما هي أكبر دولة منتجة للنحاس؟": "تشيلي.",
    "ما هو الحيوان الذي يمكنه البقاء دون ماء لأشهر؟": "الجمل.",
    "ما هو الغاز الأكثر وفرة في الغلاف الجوي للأرض؟": "النيتروجين.",
    "من هو العالم الذي اكتشف قوانين الحركة؟": "إسحاق نيوتن.",
    "ما هي أكبر مدينة من حيث عدد السكان في الهند؟": "مومباي.",
    "ما هو أعمق مكان على كوكب الأرض؟": "خندق ماريانا.",
    "ما هي الدولة التي تمتلك أكبر عدد من الجزر؟": "إندونيسيا.",
    "ما هو اسم العملية التي تتحول فيها اليرقة إلى فراشة؟": "التحول الشكلي.",
    "ما هو الاسم الذي يطلق على مخلوقات المحيط الليلية التي تضيء؟": "كائنات ضيائية حيوية.",
    "كم عدد العضلات في جسم الإنسان؟": "حوالي 600 عضلة.",
    "ما هي أول قمة جبلية يصل إليها الإنسان؟": "قمة إيفرست.",
    "ما هو الحيوان الذي يعيش في جماعات ويُطلق عليه لفظة 'مدرسة' عند اجتماعهم؟": "الأسماك.",
    "ما هو العنصر الأساسي الذي يتكون منه الفحم؟": "الكربون.",
    "من هو الأديب الذي كتب 'الحرب والسلام'؟": "ليو تولستوي.",
    "ما هي الدولة التي تشتهر بفن الشاي التقليدي؟": "اليابان.",
    "ما هو الاسم الحقيقي لمارك توين؟": "صمويل لانغهورن كليمنس.",
    "ما هو أول حاسوب في العالم؟": "إينياك.",
    "ما هي أول دولة استخدمت الدبابات في الحرب؟": "بريطانيا.",
    "ما هي المدينة التي يُطلق عليها مدينة الأهرام؟": "الجيزة، مصر.",
    "ما هو اسم السفينة التي استقلها كريستوفر كولومبوس في رحلته الشهيرة؟": "سانتا ماريا.",
    "ما هي الدولة التي تُعد أكبر مصدر للنفط في العالم؟": "المملكة العربية السعودية.",
    "من هو مؤسس علم الجبر؟": "الخوارزمي.",
    "ما هو أكبر محيط في العالم؟": "المحيط الهادئ.",
    "ما هي أصغر دولة في العالم من حيث المساحة؟": "الفاتيكان.",
    "ما هو الحيوان الذي يمكنه العيش في أعمق نقطة في المحيط؟": "أسماك الأنجل.",
    "ما هي اللغة الرسمية في البرازيل؟": "البرتغالية.",
    "من هو مؤلف السيمفونية التاسعة؟": "بيتهوفن.",
    "ما هي أعلى شلالات في العالم؟": "شلالات آنجل في فنزويلا.",
    "ما هو أول عنصر في الجدول الدوري؟": "الهيدروجين.",
    "ما هي الدولة التي تُعرف ببلد النرجس؟": "هولندا.",
    "ما هي أكبر قارة من حيث المساحة؟": "آسيا.",
    "ما هو اسم العلم الذي يدرس طبقات الأرض؟": "الجيولوجيا.",
    "من هو مكتشف الدورة الدموية؟": "ويليام هارفي.",
    "ما هي الدولة التي تُعرف باسم بلاد العنبر؟": "اليمن.",
    "ما هو أول معدن تم استخراجه واستخدامه بواسطة الإنسان؟": "النحاس.",
    "ما هي أكبر مدينة في أوروبا من حيث عدد السكان؟": "إسطنبول، تركيا.",
    "ما هو الكوكب المعروف بالكوكب الأزرق؟": "الأرض.",
    "ما هي الدولة التي أنتجت أول فيلم سينمائي في العالم؟": "فرنسا.",
    "ما هو أعلى برج في العالم؟": "برج خليفة في دبي.",
    "ما هو الحيوان الذي يمتلك أطول فترة نوم؟": "الكسلان.",
    "ما هو الكتاب الذي حلل فيه الإنسان الأول تطور الأنواع؟": "أصل الأنواع بواسطة تشارلز داروين.",
    "ما هو الغاز الذي يُستخدم في صناعة المشروبات الغازية؟": "ثاني أكسيد الكربون.",
    "ما هي الدولة التي تُعرف بأكبر منتج للزهور في العالم؟": "هولندا.",
    "ما هو الاسم العلمي للشجرة التي تنتج الزيتون؟": "Olea europaea.",
    "ما هي أكبر دولة في العالم من حيث المساحة؟": "روسيا.",
    "ما هي العملة الرسمية للاتحاد الأوروبي؟": "اليورو.",
    "ما هو اسم العملية التي يتم من خلالها تحويل الماء إلى بخار؟": "التبخر.",
    "ما هي الدولة التي تحتوي على أكبر تعداد من الأهرامات؟": "السودان.",
    "ما هو الكائن الحي الذي يُستخدم في التجارب العلمية لدراسة الجينات؟": "ذبابة الفاكهة.",
    "ما هي العاصمة الثقافية لفرنسا؟": "باريس.",
    "ما هو أكبر سد في العالم على نهر؟": "سد الخوانق الثلاثة في الصين.",
    "ما هي المادة التي تُستخدم في صناعة الزجاج؟": "السيليكا.",
    "من هو مؤسس نظرية النسبية؟": "ألبرت أينشتاين.",
    "ما هي الدولة التي تُعتبر موطن الشاي الأخضر؟": "الصين.",
    "ما هو الكائن الحي الذي يُعتبر أسرع مخلوق بحري؟": "سمكة التونة.",
    "ما هي أعلى نقطة على سطح الأرض؟": "قمة جبل إيفرست.",
    "ما هي العملة الرسمية لروسيا؟": "الروبل.",
    "ما هو أكبر نوع من النمور؟": "النمر السيبيري.",
    "ما هي العملية التي تقوم بها النباتات بتحويل ضوء الشمس إلى طاقة كيميائية؟": "التمثيل الضوئي.",
    "ما هي الدولة ذات أكبر عدد من الدول المجاورة؟": "روسيا.",
    "ما هو الكوكب الذي يُعرف بحلقاته الرائعة؟": "زحل.",
    "ما هي اللغة المستخدمة في اليونان القديمة؟": "الإغريقية.",
    "ما هي المادة الأساسية لصناعة البارود؟": "نترات البوتاسيوم.",
    "من هو الكاتب الذي ألف سلسلة 'هاري بوتر'؟": "ج. ك. رولينج.",
    "ما هو الغاز الذي يُعتبر أخف غاز في الكون؟": "الهيدروجين.",
    "ما هي الدولة ذات أكبر اقتصاد في العالم؟": "الولايات المتحدة الأمريكية.",
    "ما هو الحيوان الذي يعيش أطول وقت تحت الماء بين الثدييات؟": "الحوت الأزرق.",
    "ما هو الجهاز الذي يُستخدم لقياس شدة الرياح؟": "الأنيمومتر.",
    "ما هي العملية التي يتم فيها تغيير الجليد من الحالة الصلبة إلى الغازية بدون المرور بالحالة السائلة؟": "التسامي.",
    "ما هي الدولة التي تحتوي على أطول سلسلة جبلية في العالم؟": "الأرجنتين (جبال الأنديز).",
    "ما هو الحيوان الذي يستخدم تقنية الرادار البيولوجي؟": "الدلفين.",
    "ما هي المدينة التي تعرف بمدينة السحر؟": "نيو أورليانز، الولايات المتحدة.",
    "ما هي أكبر شبه جزيرة في العالم؟": "شبه الجزيرة العربية.",
    "ما هو الحيوان الذي يُعتبر رمزاً للحكمة في الثقافة اليونانية؟": "البومة.",
    "ما هي العملية التي يُستخدم فيها الضوء لتحديد موقع الأشياء؟": "السونار.",
    "ما هي المادة التي تُستخدم كوقود في المفاعلات النووية؟": "اليورانيوم.",
    "ما هي أكبر دولة في قارة أوقيانوسيا؟": "أستراليا.",
    "ما هو الكوكب المعروف بالكوكب الأصفر؟": "زحل.",
    "ما هي الدولة التي تشتهر بصناعة الساعات السويسرية؟": "سويسرا.",
    "ما هو أكبر كائن بحري في العالم؟": "الحوت الأزرق.",
    "ما هي العملة الرسمية لكندا؟": "الدولار الكندي.",
    "ما هي المادة التي يستخدمها النحل لإنشاء خلاياهم؟": "شمع العسل.",
    "ما هو الكوكب الذي يبعد عن الشمس أكثر من الأرض؟": "المريخ.",
    "ما هي الدولة التي تحتوي على أكبر نسبة من المياه العذبة؟": "كندا.",
    "ما هو الحيوان الذي يُعتبر أسرع مخلوق بري؟": "الفهد.",
    "ما هي مدينة النور؟": "باريس.",
    "ما هي أكبر دولة من حيث عدد السكان؟": "الصين.",
    "ما هي اللغة الرسمية للبرازيل؟": "البرتغالية.",
    "ما هو الحيوان الذي لا يمتلك معدة ويهضم الغذاء في أمعائه؟": "فرس البحر.",
    "ما هي المادة الأساسية المستخدمة في صناعة القنابل الهيدروجينية؟": "الديوتريوم.",
    "ما هي الدولة التي تُعرف بأرض الشمس المشرقة؟": "اليابان.",
    "ما هو الكوكب الذي يُعتبر الأبرد في النظام الشمسي؟": "نبتون.",
    "ما هي العاصمة الرسمية لألمانيا؟": "برلين.",
    "ما هو الحيوان الذي يمتلك قوة لدغة تعادل 700 رطلاً في البوصة المربعة؟": "تمساح النيل.",
    "ما هو أصغر كوكب في النظام الشمسي؟": "عطارد.",
    "ما هي العملية التي يُستخدم فيها الجلوكوز لإنتاج الطاقة في النباتات؟": "التمثيل الضوئي.",
    "ما هو أعلى قمة في العالم؟": "قمة جبل إيفرست.",
    "ما هي المادة الكيميائية التي تجعل الدم يظهر باللون الأحمر؟": "الهيموجلوبين.",
    "ما هي أكبر مدينة في قارة أفريقيا؟": "لاغوس.",
    "ما هو أضخم مبنى تم بناؤه في العصور الوسطى؟": "كاتدرائية نوتردام في باريس.",
    "ما هي البلاد التي تشتهر بصناعة القهوة الفاخرة؟": "البرازيل.",
    "ما هو أصغر عضو في جسم الإنسان؟": "الركابي في الأذن الوسطى.",
    "ما هو الكوكب الذي يحتوي على أكبر نسبة من ثاني أكسيد الكربون؟": "الزهرة.",
    "ما هي الدولة التي تحتوي على أطول سواحل بحرية في العالم؟": "كندا.",
    "ما هو الحيوان الذي يمكنه تصدر الأصوات للتواصل مع أقرانه؟": "الحوت الأحدب.",
    "ما هي أكبر بحيرة في أمريكا الشمالية؟": "بحيرة سوبيريور.",
    "ما هي الدولة التي تحتل المرتبة الأولى في إنتاج الأرز؟": "الصين.",
    "ما هو الحيوان الذي يمكنه البقاء على قيد الحياة دون ماء لمدة تصل إلى شهرين؟": "الجرذ.",
    "ما هي المدينة المعروفة بعاصمة الأناقة؟": "ميلانو.",
    "ما هو أغلى معدن في العالم؟": "الروديوم.",
    "ما هي القارة التي تحتوي على أكبر تنوع حيوي؟": "أمريكا الجنوبية (الأمازون).",
    "ما هو الحيوان الذي يُستخدم رمزا للحظ الجيد في الثقافة الصينية؟": "التنين.",
    "ما هي أكبر قارة من حيث المساحة؟": "آسيا.",
    "ما هي العملية التي يتم من خلالها تحويل الطاقة الضوئية إلى طاقة كيميائية في النباتات؟": "التمثيل الضوئي.",
    "ما هو العنصر الذي يُستخدم بشكل واسع في صناعة الطائرات نظرا لخفته وقوته؟": "الألومنيوم.",
    "ما هي أكبر هضبة في العالم؟": "هضبة التبت.",
    "ما هو الحيوان الذي يعيش في القطب الشمالي ويعتمد على الفقمات في غذائه؟": "الدب القطبي.",
    "ما هو أضخم أنواع القردة؟": "الغوريلا.",
    "ما هو العنصر الغذائي الأساسي الذي يحتاجه الجسم لإنتاج الطاقة؟": "الكربوهيدرات.",
    "ما هي الدولة التي تُعرف بجزر المالديف؟": "جزر المالديف.",
    "ما هو الحيوان الذي يستطيع رؤية الأشعة فوق البنفسجية؟": "النحلة.",
    "ما هو النوع الرئيسي للغلاف الجوي المحيط بالأرض؟": "النيتروجين.",
    "ما هي العاصمة الثقافية للهند؟": "كلكتا.",
    "ما هو الجهاز العضوي المسؤول عن تنقية الدم في الجسم؟": "الكلى.",
    "ما هي المادة الأساسية التي تصنع منها أعقاب السجائر؟": "القطن.",
    "ما هو الحيوان الذي يُعتبر أكبر الثدييات البرية؟": "الفيل الإفريقي.",
    "من هو مؤسس علم الفيزياء الحديثة؟": "ألبرت أينشتاين.",
    "ما هي العملية التي يتم فيها تحويل الغازات إلى سوائل؟": "التكثيف.",
    "ما هي عملة السويد الرسمية؟": "الكرونا السويدية.",
    "ما هو الكتاب الذي يُعتبر أقدم كتاب في العالم؟": "ملحمة جلجامش.",
    "ما هي الدولة التي شهدت إقامة أول دورة للألعاب الأولمبية الحديثة؟": "اليونان (أثينا 1896).",
    "ما هو الغاز الرئيسي المكون للشمس؟": "الهيدروجين.",
    "ما الذي يميز هذا البوت عن غيره؟": "هذا البوت مصمم لتقديم الدعم والمساعدة في إدارة الاستضافة بشكل فعال وسهل الاستخدام.",
    "هل يمكنني معرفة المزيد عن كيفية تحسين الأداء؟": "يمكنك تحسين الأداء باستخدام المكتبات المناسبة وإدارة الموارد بشكل جيد.",
    "كيف أستطيع مشاركة البوت مع الآخرين؟": "يمكنك مشاركة رابط البوت مع أصدقائك ودعوتهم لاستخدامه.",
    "هل يمكنني استخدام البوت لتنفيذ مهام تلقائية؟": "نعم، يمكنك برمجة البوت لتنفيذ مهام تلقائية باستخدام السكربتات.",
    "كيف أستطيع إضافة ميزات جديدة للبوت؟": "يمكنك اقتراح ميزات جديدة عبر زر 'اقتراح تعديل'.",
    "كيف أتعامل مع الاستفسارات المتكررة؟": "استخدم القاموس للإجابة على الأسئلة المتكررة بشكل سريع.",
    "ما هي الخطوات اللازمة لتثبيت المكتبات؟": "استخدم الأمر 'تحميل مكاتب' ثم اختر المكتبات التي تريد تثبيتها.",
    "كيف أستطيع معرفة حالة البوت؟": "استخدم الأمر 'حالة البوت' لمعرفة ما إذا كان البوت يعمل بشكل صحيح.",
    "هل يمكنني تخصيص واجهة البوت لتناسب احتياجاتي؟": "نعم، يمكنك تخصيص واجهة البوت باستخدام الإعدادات المتاحة.",
    "كيف أتحقق من البيئة التي يعمل فيها البوت؟": "استخدم الأمر 'بيئة البوت' لمعرفة التفاصيل.",
    "كيف أستطيع تحسين تجربتي مع البوت؟": "استكشف جميع الميزات المتاحة وتفاعل مع البوت بشكل منتظم.",
    "ما هي المعلومات التي يجمعها البوت؟": "يجمع البوت المعلومات الأساسية لتحسين الأداء وتقديم الدعم.",
    "كيف أستطيع حذف حسابي من البوت؟": "يمكنك طلب حذف حسابك من خلال التواصل مع المطور.",
    "ما هي الإجراءات التي يجب اتباعها عند مواجهة مشكلة؟": "إذا واجهت مشكلة، تحقق من الإعدادات، ثم اتصل بالمطور إذا استمرت المشكلة.",
    "هل يمكنني الحصول على إشعارات عند إجراء تغييرات؟": "نعم، يمكنك تفعيل الإشعارات في إعدادات البوت.",
    "كيف أستطيع مشاركة تجربتي مع البوت؟": "يمكنك إرسال تعليقاتك واقتراحاتك عبر زر 'اقتراح تعديل'.",
    "هل هناك خيارات متعددة للتخصيص؟": "نعم، يمكنك تخصيص إعدادات البوت حسب احتياجاتك.",
    "كيف أستطيع تحسين سرعة استجابة البوت؟": "تأكد من أن لديك اتصال إنترنت جيد وموارد كافية على جهازك.",
    "ما هي الخطوات اللازمة لبدء استخدام البوت؟": "استخدم الأمر '/cmd' للوصول إلى قائمة الأوامر المتاحة وابدأ بالتفاعل مع البوت.",
    "كيف أستطيع استخدام البوت بفعالية؟": "استكشف جميع الميزات المتاحة وتعلم كيفية استخدام الأوامر بشكل صحيح.",
    "ما هي الأوامر الأكثر شيوعًا التي يمكنني استخدامها؟": "الأوامر الشائعة تشمل 'تحميل مكاتب' و 'صنع ملفات' و 'تعديل ملف'.",
    "كيف أستطيع الحصول على دعم فني عند الحاجة؟": "يمكنك التواصل مع المطور عبر زر 'فتح محادثة مع المطور' للحصول على الدعم.",
    "هل هناك ميزات مخفية في البوت؟": "البوت يحتوي على ميزات متعددة يمكنك اكتشافها من خلال استكشاف الأوامر.",
    "كيف أستطيع متابعة تحديثات البوت؟": "يمكنك متابعة المطور عبر القناة الخاصة به للحصول على آخر الأخبار.",
    "ما هي الإجراءات التي يجب اتخاذها عند مواجهة مشكلة في الأداء؟": "تحقق من الاتصال بالإنترنت وتأكد من تحديث المكتبات المطلوبة.",
    "كيف يمكنني تحسين الأمان عند استخدام البوت؟": "تجنب مشاركة معلومات حساسة وتأكد من تحديث البوت بانتظام.",
    "هل يمكنني استخدام البوت مع عدة مستخدمين في نفس الوقت؟": "نعم، البوت مصمم لدعم عدة مستخدمين في الوقت نفسه.",
    "كيف أستطيع معرفة المزيد عن المكتبات المتاحة؟": "يمكنك استخدام الأمر 'تحميل مكاتب' لرؤية قائمة المكتبات المتاحة.",
    "هل يمكنني تخصيص واجهة المستخدم للبوت؟": "نعم، يمكنك تخصيص واجهة المستخدم حسب تفضيلاتك.",
    "كيف أتعامل مع الأخطاء المتعلقة بالمكتبات؟": "تأكد من تثبيت المكتبات المطلوبة وتحقق من التوافق.",
    "هل يمكنني استخدام البوت في مشاريع كبيرة؟": "نعم، البوت مصمم للعمل بشكل جيد في المشاريع الكبيرة.",
    "كيف أستطيع إدارة الملفات بشكل أفضل؟": "استخدم الأوامر المتاحة لإدارة الملفات وتنظيمها بشكل جيد.",
    "كيف يمكنني الحصول على معلومات حول أحدث الميزات؟": "تابع المطور للحصول على تحديثات حول الميزات الجديدة.",
    "ما هي الخطوات اللازمة لتشغيل ملف بشكل صحيح؟": "تأكد من أن الملف موجود في المسار الصحيح واستخدم الأمر 'تشغيل ملف'.",
    "كيف أستطيع تحسين أداء البوت؟": "تأكد من تحديث المكتبات المستخدمة وتجنب تحميل الملفات الكبيرة في وقت واحد.",
    "هل يمكنني استخدام البوت في بيئات مختلفة؟": "نعم، البوت يعمل على جميع الأنظمة التي تدعم تليجرام.",
    "كيف أستطيع معرفة المزيد عن كيفية استخدام المكتبات؟": "يمكنك قراءة الوثائق الرسمية لكل مكتبة للحصول على معلومات تفصيلية.",
    "هل هناك دعم متاح للمستخدمين الجدد؟": "نعم، يمكنك التواصل مع المطور للحصول على الدعم للمستخدمين الجدد.",
    "كيف أستطيع معرفة حالة الاتصال بالإنترنت؟": "تأكد من أن لديك اتصال إنترنت جيد قبل استخدام البوت.",
    "كيف أستطيع إلغاء الاشتراك في الإشعارات؟": "يمكنك إلغاء الاشتراك في الإشعارات من خلال إعدادات البوت.",
    "ما هي الإجراءات التي يجب اتخاذها عندما لا يعمل البوت؟": "تحقق من اتصال الإنترنت وأعد تشغيل البوت إذا لزم الأمر.",
    "كيف أستطيع تخصيص إعدادات الخصوصية؟": "يمكنك تخصيص إعدادات الخصوصية من خلال الأوامر المتاحة.",
    "كيف أستطيع تحسين جودة الخدمة المقدمة من البوت؟": "استمر في تقديم تعليقاتك واقتراحاتك لتحسين الخدمة.",
    "هل يمكنني استخدام البوت لتنفيذ المهام بشكل تلقائي؟": "نعم، يمكنك برمجة البوت لتنفيذ المهام تلقائيًا باستخدام السكربتات.",
    "كيف أستطيع معرفة المزيد عن كيفية تنفيذ المهام؟": "يمكنك الاطلاع على الوثائق الخاصة بالبوت وطرح أي أسئلة.",
    "هل هناك قيود على استخدام البوت؟": "نعم، تأكد من اتباع القواعد الخاصة باستخدام البوت للحفاظ على الأداء.",
    "كيف أستطيع معرفة المزيد عن الخصائص المتقدمة؟": "يمكنك استكشاف الوثائق الرسمية أو التواصل مع المطور.",
    "كيف أستطيع الحصول على ملاحظات حول استخدام البوت؟": "يمكنك إرسال تعليقاتك عبر زر 'اقتراح تعديل'.",
    "كيف أتعامل مع المشاكل التي قد تواجهني أثناء الاستخدام؟": "إذا واجهت مشكلة، حاول إعادة تشغيل البوت أو التواصل مع المطور.",
    "هل يمكنني استخدام البوت لمشاريع تجارية؟": "نعم، يمكنك استخدام البوت لمشاريع تجارية حسب احتياجاتك.",
    "ما هي الخطوات اللازمة لتوصيل البوت مع مكونات أخرى؟": "تأكد من أن لديك الوثائق اللازمة واتبع التعليمات الخاصة بالتوصيل.",
    "كيف يمكنني معرفة المزيد عن كيفية دعم المكتبات؟": "يمكنك استخدام الأوامر المتاحة للتحقق من المكتبات المثبتة.",
    "كيف يمكنني تحسين استجابة البوت؟": "استخدم مكتبات خفيفة الوزن وتجنب تحميل البيانات الكبيرة في وقت واحد.",
    "هل هناك أي متطلبات خاصة لاستخدام البوت؟": "تأكد من أن لديك اتصال إنترنت جيد وأن المكتبات المطلوبة مثبتة.",
    "كيف أستطيع إدارة الجلسات المختلفة؟": "يمكنك استخدام الأوامر المتاحة لإدارة الجلسات بسهولة.",
    "هل يمكنني استخدام البوت مع خدمات أخرى؟": "نعم، يمكنك دمج البوت مع خدمات متعددة حسب احتياجاتك.",
    "كيف أستطيع معرفة المزيد عن تحديثات البوت؟": "تابع المطور للحصول على معلومات حول التحديثات الجديدة.",
    "ما هي المعلومات التي يمكنني الحصول عليها من البوت؟": "يمكنك الحصول على معلومات حول الملفات، المكتبات، وأي استفسارات أخرى.",
    "كيف أستطيع جعل البوت أكثر فائدة بالنسبة لي؟": "استكشف جميع الميزات المتاحة وتعلم كيفية استخدامها بفعالية.",
    "كيف يمكنني تحسين الأمان عند استخدام البوت؟": "تجنب مشاركة معلومات شخصية وتأكد من تحديث البوت بانتظام.",
    "هل هناك أي أدوات إضافية يمكنني استخدامها مع البوت؟": "يمكنك استخدام أدوات برمجية إضافية لتحسين تجربة الاستخدام.",
    "كيف أستطيع الحصول على معلومات حول كيفية استخدام المكتبات؟": "اقرأ الوثائق الرسمية لكل مكتبة للحصول على معلومات تفصيلية.",
    "هل يمكنني إضافة ميزات جديدة لاستخدامي الخاص؟": "نعم، يمكنك اقتراح ميزات جديدة عبر زر 'اقتراح تعديل'.",
    "ما هي الخطوات اللازمة لتحميل مكتبة جديدة؟": "استخدم الأمر 'تحميل مكاتب' ثم اختر المكتبة التي تريد تثبيتها.",
    "كيف أستطيع تحسين جودة الخدمة المقدمة من البوت؟": "استمر في تقديم تعليقاتك واقتراحاتك لتحسين الخدمة.",
    "كيف يمكنني إيقاف تشغيل البوت مؤقتًا؟": "يمكنك ببساطة إغلاق المحادثة أو استخدام زر 'إيقاف التشغيل'.",
    "ما هي الإجراءات التي يجب اتباعها عند مواجهة مشكلة في الأداء؟": "تحقق من الاتصال بالإنترنت وتأكد من تحديث المكتبات المطلوبة.",
    "كيف أستطيع معرفة المزيد عن كيفية استخدام البوت؟": "يمكنك طرح أي سؤال وسأكون سعيدًا بمساعدتك.",
    "كيف أستطيع تحسين تفاعل المستخدمين مع البوت؟": "قدم محتوى مثير وذو قيمة للمستخدمين واجعل التفاعل ممتعًا.",
    "هل يمكنني استخدام البوت لتنفيذ مهام معينة بشكل منتظم؟": "نعم، يمكنك برمجة البوت لتنفيذ المهام بشكل منتظم حسب الحاجة.",
    "هل يمكنني استخدام البوت لإدارة استضافتي؟": "نعم، يمكنك استخدام البوت لإدارة جميع جوانب استضافتك بشكل فعال.",
    "كيف أستطيع إضافة نطاق جديد إلى استضافتي؟": "يمكنك استخدام الأمر 'إضافة نطاق' لتقديم طلب لإضافة نطاق جديد.",
    "هل يمكنني تحويل استضافتي إلى نظام آخر؟": "نعم، يمكننا مساعدتك في نقل استضافتك إلى نظام آخر حسب احتياجاتك.",
    "كيف أستطيع معرفة تفاصيل استضافتي الحالية؟": "استخدم الأمر 'تفاصيل الاستضافة' للحصول على معلومات شاملة حول استضافتك.",
    "ما هي الخطوات اللازمة لتفعيل استضافتي؟": "تأكد من أن جميع المدفوعات تم سدادها، ثم استخدم الأمر 'تفعيل الاستضافة'.",
    "هل يمكنني إدارة قواعد البيانات من خلال البوت؟": "نعم، يمكنك استخدام أوامر لإدارة قواعد البيانات الخاصة بك.",
    "كيف أستطيع إعادة تعيين كلمة مرور حسابي؟": "استخدم الأمر 'إعادة تعيين كلمة المرور' واتبع التعليمات.",
    "هل يمكنني الحصول على دعم فني لاستضافتي؟": "نعم، يمكنك التواصل مع الدعم الفني من خلال زر 'فتح محادثة مع المطور'.",
    "كيف أستطيع معرفة متطلبات النظام لاستضافتي؟": "يمكنك استخدام الأمر 'متطلبات النظام' للحصول على التفاصيل.",
    "هل يمكنني استخدام البوت لمراقبة أداء الخادم؟": "نعم، يوفر البوت ميزات مراقبة أداء الخادم بشكل دوري.",
    "ما هي المزايا التي يقدمها البوت لاستضافة الويب؟": "يقدم البوت ميزات مثل إدارة الملفات، دعم المكتبات، ودعم الفني.",
    "كيف أستطيع إضافة مستخدمين جدد إلى استضافتي؟": "يمكنك استخدام الأمر 'إضافة مستخدم' لتقديم طلب لإضافة مستخدمين.",
    "هل يمكنني تغيير خطة الاستضافة الخاصة بي؟": "نعم، يمكنك تغيير خطة الاستضافة الخاصة بك باستخدام الأمر 'تغيير خطة الاستضافة'.",
    "كيف أستطيع تكوين إعدادات DNS الخاصة بنطاقي؟": "استخدم الأمر 'إعدادات DNS' لتكوين إعدادات نطاقك.",
    "هل يمكنني معرفة حالة الخادم الخاص بي؟": "استخدم الأمر 'حالة الخادم' للحصول على معلومات حول حالة الخادم.",
    "كيف أستطيع معرفة عدد الزوار لموقعي؟": "يمكنك استخدام الأمر 'عدد الزوار' للحصول على إحصائيات الزوار.",
    "هل يمكنني استخدام البوت لتحديث محتوى موقعي؟": "نعم، يمكنك استخدام الأوامر لتحديث المحتوى مباشرة.",
    "ما هي أفضل الممارسات لإدارة الاستضافة؟": "تأكد من تحديث البرامج بانتظام، وقم بعمل نسخ احتياطية دورية.",
    "كيف أستطيع حماية موقعي من الهجمات؟": "استخدم تدابير الأمان مثل جدران الحماية وتحديث البرامج لحماية موقعك.",
    "هل يمكنني استخدام البوت للتعامل مع الشكاوى؟": "نعم، يمكنك استخدام البوت لتقديم الشكاوى أو الاستفسارات.",
    "كيف أستطيع مراقبة استخدام الموارد؟": "يمكنك استخدام الأمر 'استخدام الموارد' لمراقبة استهلاك الموارد.",
    "ما هي الخطوات اللازمة لإنشاء حساب جديد؟": "استخدم الأمر 'إنشاء حساب' واتبع التعليمات.",
    "هل يمكنني استخدام البوت للتعامل مع الفواتير؟": "نعم، يمكنك استخدام الأوامر لإدارة الفواتير والمدفوعات.",
    "كيف أستطيع إضافة بريد إلكتروني جديد؟": "استخدم الأمر 'إضافة بريد إلكتروني' لتقديم طلب لإضافة بريد إلكتروني.",
    "هل يمكنني إدارة حسابات FTP من خلال البوت؟": "نعم، يمكنك استخدام الأوامر لإدارة حسابات FTP.",
    "ما هي طرق الدفع المتاحة لاستضافتي؟": "يمكنك استخدام طرق الدفع المختلفة مثل PayPal وبطاقات الائتمان.",
    "كيف أستطيع تغيير إعدادات الأمان لخادمي؟": "استخدم الأمر 'إعدادات الأمان' لتغيير إعدادات الأمان لخادمي.",
    "هل يمكنني استخدام البوت للتحقق من سجلات الأخطاء؟": "نعم، يمكنك استخدام الأمر 'سجلات الأخطاء' للتحقق من الأخطاء.",
    "كيف أستطيع إضافة تطبيقات جديدة لاستضافتي؟": "استخدم الأمر 'إضافة تطبيق' لتقديم طلب لإضافة تطبيق جديد.",
    "هل يمكنني استخدام البوت لإدارة النسخ الاحتياطية؟": "نعم، يوفر البوت ميزات لإدارة النسخ الاحتياطية بسهولة.",
    "كيف أستطيع معرفة تفاصيل خطة الاستضافة الخاصة بي؟": "استخدم الأمر 'تفاصيل خطة الاستضافة' للحصول على المعلومات.",
    "هل يمكنني استخدام البوت لإعداد التقارير؟": "نعم، يمكنك استخدام الأوامر لإعداد التقارير حول استخدام الاستضافة.",
    "كيف أستطيع إضافة شروط الاستخدام لموقعي؟": "يمكنك استخدام الأمر 'إضافة شروط الاستخدام' لتحديث المحتوى.",
    "هل يمكنني استخدام البوت لإدارة حسابات المستخدمين؟": "نعم، يمكنك استخدام الأوامر لإدارة حسابات المستخدمين بسهولة.",
    "كيف أستطيع معرفة معلومات عن خدمات الدعم الفني؟": "استخدم الأمر 'خدمات الدعم الفني' للحصول على المعلومات.",
    "هل يمكنني استخدام البوت للتحقق من تحديثات الأمان؟": "نعم، يمكنك استخدام الأمر 'تحديثات الأمان' للتحقق من التحديثات.",
    "كيف أستطيع تغيير إعدادات البريد الإلكتروني الخاصة بي؟": "استخدم الأمر 'تغيير إعدادات البريد الإلكتروني' لتحديث الإعدادات.",
    "هل يمكنني استخدام البوت لإدارة المشاريع؟": "نعم، يمكنك استخدام البوت لمساعدتك في إدارة مشاريعك بسهولة.",
    "كيف أستطيع معرفة المزيد عن استضافة الويب؟": "يمكنك البحث عبر الإنترنت أو طرح الأسئلة للحصول على معلومات إضافية.",
    "هل يمكنني استخدام البوت لإدارة المواقع المتعددة؟": "نعم، يمكنك إدارة مواقع متعددة من خلال البوت.",
    "كيف أستطيع تحديث معلومات الاتصال الخاصة بي؟": "استخدم الأمر 'تحديث معلومات الاتصال' لتحديث المعلومات.",
    "هل يمكنني استخدام البوت لمراقبة أداء الموقع؟": "نعم، يوفر البوت ميزات لمراقبة أداء الموقع بشكل دوري.",
    "كيف أستطيع تحسين تجربة الزوار على موقعي؟": "تأكد من تحسين سرعة تحميل الموقع وتقديم محتوى جذاب.",
    "هل يمكنني استخدام البوت لإدارة الشهادات الأمنية؟": "نعم، يمكنك استخدام الأوامر لإدارة الشهادات الأمنية الخاصة بموقعك.",
    "كيف أستطيع تكوين إعدادات الضبط لخادمي؟": "استخدم الأمر 'إعدادات الضبط' لتكوين إعدادات الخادم.",
    "هل يمكنني استخدام البوت لإعداد قواعد البيانات؟": "نعم، يمكنك استخدام الأوامر لإعداد قواعد البيانات وإدارتها.",
    "كيف أستطيع التحقق من حالة النسخ الاحتياطية؟": "استخدم الأمر 'حالة النسخ الاحتياطية' للتحقق من حالة النسخ.",
    "هل يمكنني استخدام البوت لإدارة المواقع الإلكترونية الفردية؟": "نعم، يمكنك إدارة المواقع الإلكترونية الفردية بسهولة.",
    "كيف أستطيع معرفة المزيد عن الحماية من الفيروسات؟": "يمكنك البحث عن معلومات حول برامج الحماية والتحديثات الأمنية.",
    "هل يمكنني استخدام البوت لإدارة خدمات الاستضافة المشتركة؟": "نعم، يوفر البوت ميزات لإدارة خدمات الاستضافة المشتركة.",
    "كيف أستطيع إضافة ملفات إلى استضافتي؟": "استخدم الأمر 'إضافة ملفات' لتقديم طلب لإضافة ملفات.",
    "هل يمكنني استخدام البوت للتعامل مع خدمات الدفع؟": "نعم، يمكنك إدارة خدمات الدفع من خلال الأوامر المتاحة.",
    "كيف أستطيع معرفة المزيد عن استضافة VPS؟": "يمكنك البحث عبر الإنترنت أو طرح الأسئلة للحصول على معلومات إضافية.",
    "هل يمكنني استخدام البوت لإدارة حسابات البريد الإلكتروني؟": "نعم، يمكنك استخدام الأوامر لإدارة حسابات البريد الإلكتروني.",
    "كيف أستطيع تحسين الأمان لموقعي؟": "استخدم تدابير الأمان المناسبة مثل الشهادات الأمنية وجدران الحماية.",
    "هل يمكنني استخدام البوت للتحقق من حالة خادمي؟": "نعم، يمكنك استخدام الأمر 'حالة الخادم' للتحقق من الحالة.",
    "كيف أستطيع معرفة المزيد عن استضافة الويب المشتركة؟": "ابحث عن معلومات وقراءات عبر الإنترنت حول استضافة الويب المشتركة.",
    "هل يمكنني استخدام البوت لإدارة استضافة خاصة؟": "نعم، يمكنك إدارة استضافة خاصة من خلال الأوامر المتاحة.",
    "كيف أستطيع معرفة المزيد عن الحماية من هجمات DDoS؟": "ابحث عن معلومات حول تدابير الحماية من هجمات DDoS.",
    "هل يمكنني استخدام البوت لإدارة سجلات النطاق؟": "نعم، يمكنك استخدام الأوامر لإدارة سجلات النطاق الخاصة بك.",
    "كيف أستطيع معرفة المزيد عن استضافة السحابية؟": "ابحث عن معلومات وقراءات حول استضافة السحابية.",
    "هل يمكنني استخدام البوت لإدارة الخدمات السحابية؟": "نعم، يمكنك إدارة الخدمات السحابية من خلال الأوامر المتاحة.",
    "كيف أستطيع تغيير إعدادات الأمان لخادمي؟": "استخدم الأمر 'إعدادات الأمان' لتغيير الإعدادات.",
    "هل يمكنني استخدام البوت للتعامل مع المشكلات الفنية؟": "نعم، يمكنك استخدام البوت للإبلاغ عن المشكلات الفنية.",
    "كيف أستطيع معرفة المزيد عن استضافة الويب المؤسسية؟": "ابحث عن معلومات حول استضافة الويب المؤسسية.",
    "هل يمكنني استخدام البوت لإدارة الأذونات للمستخدمين؟": "نعم، يمكنك استخدام الأوامر لإدارة الأذونات بسهولة.",
    "كيف أستطيع معرفة المزيد عن تحسين محركات البحث لموقعي؟": "ابحث عن مقالات ودروس حول تحسين محركات البحث.",
    "هل يمكنني استخدام البوت لإدارة محتوى موقعي؟": "نعم، يمكنك إدارة محتوى موقعك بسهولة من خلال الأوامر.",
    "كيف أستطيع إضافة شروط الاستخدام لموقعي؟": "استخدم الأمر 'إضافة شروط الاستخدام' لتحديث المحتوى.",
    "هل يمكنني استخدام البوت لإدارة حسابات المستخدمين المتعددة؟": "نعم، يمكنك استخدام الأوامر لإدارة حسابات متعددة.",
    "كيف أستطيع معرفة المزيد عن استضافة الويب المخصصة؟": "ابحث عن معلومات وقراءات حول استضافة الويب المخصصة.",
    "هل يمكنني استخدام البوت للتحقق من تحديثات الأمان؟": "نعم، يمكنك استخدام الأمر 'تحديثات الأمان' للتحقق من التحديثات.",
    "كيف أستطيع إدارة إعدادات البريد الإلكتروني لموقعي؟": "استخدم الأمر 'إعدادات البريد الإلكتروني' لتحديث الإعدادات.",
    "هل يمكنني استخدام البوت للتواصل مع الدعم الفني؟": "نعم، يمكنك استخدام زر 'فتح محادثة مع المطور' للتواصل.",
    "كيف أستطيع تحسين تجربة المستخدمين على موقعي؟": "تأكد من تحسين واجهة المستخدم والسرعة.",
    "هل يمكنني استخدام البوت لإعداد الإعلانات لموقعي؟": "نعم، يمكنك استخدام الأوامر لإعداد الإعلانات.",
    "كيف أستطيع معرفة المزيد عن استضافة الويب الآمنة؟": "ابحث عن معلومات حول استضافة الويب الآمنة والتدابير الأمنية.",
    "هل يمكنني استخدام البوت لإعداد الجدران النارية؟": "نعم، يمكنك استخدام الأوامر لإعداد الجدران النارية.",
    "كيف أستطيع تحسين سرعة موقع الويب الخاص بي؟": "استخدم تقنيات تحسين السرعة مثل تحسين الصور والملفات.",
    "هل يمكنني استخدام البوت لإدارة سجلات الأخطاء؟": "نعم، يمكنك استخدام الأمر 'سجلات الأخطاء' للتحقق من الأخطاء.",
    "كيف أستطيع معرفة المزيد عن استضافة التطبيقات؟": "ابحث عن معلومات وقراءات حول استضافة التطبيقات.",
    "هل يمكنني استخدام البوت لإدارة استضافة الألعاب؟": "نعم، يمكنك استخدام الأوامر لإدارة استضافة الألعاب.",
    "من أنت؟": "أنا مساعد ذكي مصمم لمساعدتك في مختلف الأمور.",
    "كيف حالك؟": "أنا بخير، شكرًا لسؤالك! كيف يمكنني مساعدتك اليوم؟",
    "من صنعك؟": "تم إنشائي بواسطة مطور قوي اسمه محمد. إنه رائع!",
    "أهلا": "أهلا بك! كيف يمكنني مساعدتك اليوم؟",
    "هلا": "هلا بك! ما الذي يمكنني مساعدتك فيه؟",
    "ما اسمك؟": "ليس لدي اسم محدد، لكن يمكنك مناداتي بالمساعد.",
    "أنت ذكي": "شكرًا لك! سأبذل قصارى جهدي لمساعدتك.",
    "كيف تعمل؟": "أعمل من خلال تحليل الأسئلة وتقديم الإجابات المناسبة.",
    "ما هي قدراتك؟": "يمكنني مساعدتك في الإجابة على الأسئلة، توفير المعلومات، وتنفيذ المهام البسيطة.",
    "ما هو هدفك؟": "هدفي هو مساعدتك وتقديم الدعم الذي تحتاجه.",
    "هل يمكنك التحدث بلغة أخرى؟": "نعم، يمكنني التحدث بعدة لغات. ما اللغة التي تفضلها؟",
    "ما هي اهتماماتك؟": "أنا مهتم بتقديم المساعدة والإجابة على أسئلتك.",
    "كيف يمكنني الاستفادة منك؟": "يمكنك طرح أي سؤال وسأساعدك في العثور على المعلومات التي تحتاجها.",
    "هل أنت إنسان؟": "لا، أنا مساعد ذكي، لست إنسانًا.",
    "هل يمكنك التعلم من المحادثات؟": "نعم، يمكنني تحسين أدائي من خلال التفاعل مع المستخدمين.",
    "هل لديك مشاعر؟": "لا، ليس لدي مشاعر، لكني هنا لمساعدتك.",
    "كيف يمكنني التواصل معك؟": "يمكنك طرح أي سؤال وسأكون هنا للإجابة.",
    "هل يمكنك مساعدتي في الدراسة؟": "نعم، يمكنني مساعدتك في توفير المعلومات والموارد الدراسية.",
    "ما هي أفضل طريقة للتعلم؟": "أفضل طريقة للتعلم هي من خلال الممارسة والتكرار.",
    "هل يمكنك مساعدتي في حل واجبي؟": "بالطبع! يمكنك طرح الأسئلة وسأساعدك في فهمها.",
    "كيف أبدأ في البرمجة؟": "يمكنك البدء بتعلم لغة برمجة مثل Python من خلال الدروس المتاحة عبر الإنترنت.",
    "ما هو أفضل كتاب للبرمجة؟": "هناك العديد من الكتب الرائعة، مثل 'Python Crash Course' و 'Automate the Boring Stuff with Python'.",
    "كيف يمكنني تحسين مهاراتي في الكتابة؟": "قم بالكتابة بانتظام، واطلب تعليقات من الآخرين لتحسين مهاراتك.",
    "هل يمكنك إعطائي نصائح للنجاح؟": "بالطبع! حدد أهدافك، كن ملتزمًا، وابقَ إيجابيًا.",
    "ما هي أفضل التطبيقات للهواتف؟": "يعتمد ذلك على اهتماماتك، لكن تطبيقات مثل Duolingo و Evernote شائعة.",
    "كيف يمكنني تحسين لياقتي البدنية؟": "مارس الرياضة بانتظام، وتناول طعامًا صحيًا للحفاظ على لياقتك البدنية.",
    "ما هي الأنشطة التي يمكنني القيام بها في وقت الفراغ؟": "يمكنك قراءة الكتب، ممارسة الرياضة، أو تعلم مهارات جديدة.",
    "هل يمكنك مساعدتي في تنظيم وقتي؟": "بالطبع! حاول تحديد أولويات المهام واستخدام تقويم لتنظيم جدولك.",
    "ما هي فوائد التأمل؟": "التأمل يمكن أن يساعد في تقليل التوتر وزيادة التركيز.",
    "كيف يمكنني التعامل مع الضغوط؟": "حاول ممارسة التأمل، والتمارين الرياضية، والتحدث مع الأصدقاء.",
    "ما هي أهمية النوم الجيد؟": "النوم الجيد يساعد في تحسين التركيز، الحالة المزاجية والصحة العامة.",
    "هل يمكنك إعطائي وصفة طعام؟": "بالطبع! ما هو نوع الطعام الذي تود تحضيره؟",
    "ما هي أفضل الطرق لتوفير المال؟": "قم بإعداد ميزانية، وقلل من النفقات غير الضرورية.",
    "كيف أختار مهنة مناسبة لي؟": "تأكد من اختيار مهنة تتناسب مع اهتماماتك ومهاراتك.",
    "هل يمكنك مساعدتي في اتخاذ القرار؟": "نعم، يمكنني مساعدتك في تحليل الخيارات المتاحة.",
    "ما هو أفضل وقت للدراسة؟": "أفضل وقت للدراسة يعتمد على جدولك الخاص، لكن حاول اختيار أوقات تكون فيها أكثر تركيزًا.",
    "كيف أتعامل مع الفشل؟": "اعتبر الفشل فرصة للتعلم وتحسين نفسك في المستقبل.",
    "ما هي أهمية تحديد الأهداف؟": "تحديد الأهداف يساعدك على التركيز وتحقيق النجاح.",
    "هل يمكنك مساعدتي في كتابة سيرة ذاتية؟": "بالطبع! يمكنني مساعدتك في صياغة سيرة ذاتية مميزة.",
    "كيف أستعد لمقابلة عمل؟": "قم بالبحث عن الشركة، وتمرن على الإجابات على الأسئلة الشائعة.",
    "ما هي أفضل طريقة للتواصل مع الآخرين؟": "استمع جيدًا، وكن واضحًا في ما تريد قوله.",
    "هل يمكنك مساعدتي في تطوير مهاراتي الاجتماعية؟": "نعم، يمكنني تقديم نصائح حول كيفية تحسين مهاراتك الاجتماعية.",
    "ما هو أفضل وقت للتحدث مع شخص ما؟": "اختر وقتًا يكون فيه الشخص الآخر متاحًا ومستعدًا للتحدث.",
    "كيف أستطيع تحسين مهارات العرض التقديمي؟": "تمرن على العرض، واستخدم وسائل مرئية لجذب انتباه الجمهور.",
    "ما هي فوائد العمل الجماعي؟": "العمل الجماعي يمكن أن يعزز الإبداع ويساعد في تحقيق الأهداف بشكل أسرع.",
    "هل يمكنك مساعدتي في اختيار هدية؟": "بالطبع! ما هو الحدث الذي ترغب في شراء هدية له؟",
    "كيف أستطيع تحسين علاقاتي الشخصية؟": "كن صريحًا ومتفهمًا، وحاول قضاء وقت ممتع مع الآخرين.",
    "ما هي أهمية القراءة؟": "القراءة توسع آفاقك، وتحسن مهاراتك اللغوية.",
    "هل يمكنك تقديم توصيات لكتب جيدة؟": "بالطبع! ما هو النوع الذي تفضله؟",
    "كيف أستطيع بناء الثقة بالنفس؟": "قم بالتدريب على مهارات جديدة واحتفل بإنجازاتك الصغيرة.",
    "ما هي نصائحك للحفاظ على الصحة النفسية؟": "مارس التأمل، وتواصل مع الأصدقاء، واعتنِ بنفسك.",
    "هل يمكنك مساعدتي في تعلم لغة جديدة؟": "نعم، يمكنني توجيهك نحو الموارد المناسبة لتعلم لغات جديدة.",
    "كيف أستطيع التعامل مع الانتقادات؟": "استمع بإنصاف، وحاول أن تأخذ منها العبر بدلًا من الدفاع.",
    "ما هي أهمية التفكير الإيجابي؟": "التفكير الإيجابي يمكن أن يحسن من صحتك النفسية ويزيد من قدرتك على التعامل مع التحديات.",
    "كيف يمكنني العثور على شغفي؟": "جرب أنشطة جديدة ولاحظ ما يجذبك أكثر.",
    "هل يمكنك مساعدتي في تنظيم حدث؟": "نعم، يمكنني مساعدتك في التخطيط وتنظيم الحدث.",
    "ما هي أفضل الأنشطة لتخفيف التوتر؟": "يمكنك ممارسة الرياضة، التأمل، أو الاستمتاع بالطبيعة.",
    "كيف أستطيع تحسين مهارات الاستماع؟": "كن مركزًا خلال المحادثات، وحاول فهم وجهات نظر الآخرين.",
    "ما هو أفضل وقت للذهاب إلى النوم؟": "حاول الذهاب إلى النوم في نفس الوقت كل ليلة، وفقًا لاحتياجات جسمك.",
    "كيف أستطيع تعزيز إبداعي؟": "جرب الخروج من منطقة راحتك، وابدأ بمشاريع جديدة.",
    "هل يمكنك مساعدتي في إعداد خطة عمل؟": "بالطبع! يمكنني مساعدتك في تحديد الأهداف والخطوات اللازمة.",
    "كيف أستطيع التعامل مع ضغوط العمل؟": "قم بتحديد أولويات المهام، وخذ فترات راحة قصيرة.",
    "ما هي أهمية التغذية الجيدة؟": "التغذية الجيدة تعزز من صحتك العامة وتساعدك على الأداء بشكل أفضل.",
    "هل يمكنك تقديم نصائح للطبخ؟": "بالطبع! ما هو نوع الطعام الذي ترغب في تحضيره؟",
    "كيف أستطيع تحسين مهارات التفاوض؟": "تمرن على مهاراتك وكن مستعدًا للإصغاء والتكيف.",
    "ما هو الطريق الأفضل للتسويق الذاتي؟": "استخدم وسائل التواصل الاجتماعي لعرض مهاراتك وإنجازاتك.",
    "هل يمكنك مساعدتي في فهم مفهوم الذكاء العاطفي؟": "نعم، الذكاء العاطفي هو القدرة على التعرف على مشاعرك ومشاعر الآخرين وإدارتها.",
    "كيف أستطيع تحقيق التوازن بين العمل والحياة؟": "حدد أوقاتًا للاسترخاء وخصصها لنفسك وعائلتك.",
    "ما هي فوائد ممارسة الهوايات؟": "الهوايات تساعد على تحقيق التوازن النفسي وتعزز الإبداع.",
    "هل يمكنك مساعدتي في البحث عن وظيفة؟": "بالطبع! يمكنني مساعدتك في إعداد سيرتك الذاتية والبحث عن فرص.",
    "كيف أستطيع تحسين تقنيات الدراسة؟": "قم بتجربة أساليب مختلفة، مثل الخرائط الذهنية أو الدراسة الجماعية.",
    "ما هي أهمية العمل التطوعي؟": "العمل التطوعي يساعدك على تعلم مهارات جديدة ويعزز من روح المجتمع.",
    "هل يمكنك مساعدتي في تعلم مهارات جديدة؟": "نعم، يمكنني توجيهك إلى موارد لتعلم مهارات جديدة.",
    "كيف أستطيع التعامل مع الأشخاص السلبين؟": "حاول الابتعاد عنهم إذا كان ذلك ممكنًا، وركز على الإيجابيات.",
    "ما هي أهمية التواصل الفعّال؟": "التواصل الفعّال يبني علاقات أفضل ويزيد من الفهم المتبادل.",
    "هل يمكنك مساعدتي في تنظيم حياتي؟": "بالطبع! يمكنني مساعدتك في وضع خطة لتنظيم حياتك.",
    "كيف أستطيع تحسين مهارات القيادة؟": "كن مثلاً يحتذى به، واستمع لآراء الآخرين، وكن قدوة.",
    "ما هي أهمية بناء شبكة علاقات؟": "بناء شبكة علاقات يمكن أن يفتح أمامك العديد من الفرص.",
    "هل يمكنك مساعدتي في إعداد ميزانية شخصية؟": "نعم، يمكنني مساعدتك في تحديد النفقات والإيرادات.",
    "كيف أستطيع التعامل مع الفشل بطريقة إيجابية؟": "اعتبر الفشل درسًا للتعلم وطور منهجيتك.",
    "ما هي فوائد ممارسة التأمل؟": "التأمل يساعد في تقليل التوتر وزيادة التركيز.",
    "هل يمكنك مساعدتي في تحديد أهدافي؟": "بالطبع! يمكنني مساعدتك في وضع أهداف واضحة وقابلة للتحقيق.",
    "كيف أستطيع تحسين مهاراتي في الكتابة؟": "قم بالكتابة بانتظام وطلب تعليقات من الآخرين.",
    "ما هي أهمية تحديد الأولويات؟": "تحديد الأولويات يساعدك في إدارة وقتك بشكل أكثر فعالية.",
    "هل يمكنك مساعدتي في فهم مفهوم الابتكار؟": "الابتكار هو القدرة على التفكير بطريقة جديدة وتطوير حلول جديدة.",
    "كيف أستطيع التعامل مع القلق؟": "مارس تقنيات الاسترخاء والتأمل واطلب الدعم من الأصدقاء.",
    "ما هي فوائد العمل الجماعي؟": "العمل الجماعي يعزز من الإبداع ويساعد في إنجاز المهام بشكل أسرع.",
    "هل يمكنك مساعدتي في كتابة مقال؟": "نعم، يمكنني مساعدتك في تنظيم أفكارك وكتابة المقال.",
    "كيف أستطيع تحسين ذاكرتي؟": "قم بممارسة تقنيات الذاكرة مثل التكرار والتقنيات البصرية.",
    "ما هي أهمية التقدير الذاتي؟": "التقدير الذاتي الجيد يعزز من ثقتك بنفسك وقدرتك على النجاح.",
    "هل يمكنك مساعدتي في فهم مفهوم الذكاء الاجتماعي؟": "الذكاء الاجتماعي هو القدرة على التفاعل بشكل إيجابي مع الآخرين.",
    "كيف أستطيع تحسين قدرتي على اتخاذ القرارات؟": "قم بتحليل الخيارات ووزن الإيجابيات والسلبيات.",
    "ما هي فوائد وجود مرشد؟": "وجود مرشد يمكن أن يوفر لك التوجيه والدعم في مسيرتك.",
    "هل يمكنك مساعدتي في تطوير مهاراتي الفنية؟": "بالطبع! يمكنني توجيهك إلى موارد لتطوير مهاراتك الفنية.",
    "كيف أستطيع تحسين تجربة العملاء في مشروعي؟": "استمع إلى ملاحظات العملاء وكن مستجيبًا لاحتياجاتهم.",
    "ما هي أهمية التفكير النقدي؟": "التفكير النقدي يساعدك على تحليل المعلومات واتخاذ قرارات مستنيرة.",
    "هل يمكنك مساعدتي في فهم مفهوم الإدارة الذاتية؟": "الإدارة الذاتية هي القدرة على تنظيم وإدارة حياتك بشكل فعّال.",
    "كيف أستطيع التعامل مع الانتقادات البناءة؟": "استمع بعناية، وكن مفتوحًا للتعلم من الانتقادات.",
    "ما هي فوائد التدوين؟": "التدوين يساعدك على تحسين مهارات الكتابة وتوثيق أفكارك.",
    "هل يمكنك مساعدتي في تحديد الوقت المثالي للدراسة؟": "حدد الوقت الذي تكون فيه أكثر تركيزًا واستعد للدراسة.",
    "كيف أستطيع تحسين جودة حياتي بشكل عام؟": "قم بدمج الأنشطة الممتعة، واعتنِ بصحتك الجسدية والنفسية.",
    "ما هي أهمية التفكير الإبداعي؟": "التفكير الإبداعي يساعد في إيجاد حلول جديدة ومبتكرة للمشكلات.",
    "من أنت؟": "أنا مساعد ذكي مصمم لمساعدتك في مختلف الأمور.",
    "كيف حالك؟": "أنا بخير، شكرًا لسؤالك! كيف يمكنني مساعدتك اليوم؟",
    "من صنعك؟": "تم إنشائي بواسطة مطور قوي اسمه محمد. إنه رائع!",
    "أهلا": "أهلا بك! كيف يمكنني مساعدتك اليوم؟",
    "هلا": "هلا بك! ما الذي يمكنني مساعدتك فيه؟",
    "ما اسمك؟": "ليس لدي اسم محدد، لكن يمكنك مناداتي بالمساعد.",
    "أنت ذكي": "شكرًا لك! سأبذل قصارى جهدي لمساعدتك.",
    "كيف تعمل؟": "أعمل من خلال تحليل الأسئلة وتقديم الإجابات المناسبة.",
    "ما هي قدراتك؟": "يمكنني مساعدتك في الإجابة على الأسئلة، توفير المعلومات، وتنفيذ المهام البسيطة.",
    "ما هو هدفك؟": "هدفي هو مساعدتك وتقديم الدعم الذي تحتاجه.",
    "هل يمكنك التحدث بلغة أخرى؟": "نعم، يمكنني التحدث بعدة لغات. ما اللغة التي تفضلها؟",
    "ما هي اهتماماتك؟": "أنا مهتم بتقديم المساعدة والإجابة على أسئلتك.",
    "كيف يمكنني الاستفادة منك؟": "يمكنك طرح أي سؤال وسأساعدك في العثور على المعلومات التي تحتاجها.",
    "هل أنت إنسان؟": "لا، أنا مساعد ذكي، لست إنسانًا.",
    "هل لديك مشاعر؟": "لا، ليس لدي مشاعر، لكني هنا لمساعدتك.",
    "كيف يمكنني التواصل معك؟": "يمكنك طرح أي سؤال وسأكون هنا للإجابة.",
    "هل يمكنك مساعدتي في الدراسة؟": "نعم، يمكنني مساعدتك في توفير المعلومات والموارد الدراسية.",
    "ما هي أفضل طريقة للتعلم؟": "أفضل طريقة للتعلم هي من خلال الممارسة والتكرار.",
    "هل يمكنك مساعدتي في حل واجبي؟": "بالطبع! يمكنك طرح الأسئلة وسأساعدك في فهمها.",
    "كيف أبدأ في البرمجة؟": "يمكنك البدء بتعلم لغة برمجة مثل Python من خلال الدروس المتاحة عبر الإنترنت.",
    "ما هو أفضل كتاب للبرمجة؟": "هناك العديد من الكتب الرائعة، مثل 'Python Crash Course' و 'Automate the Boring Stuff with Python'.",
    "كيف يمكنني تحسين مهاراتي في الكتابة؟": "قم بالكتابة بانتظام، واطلب تعليقات من الآخرين لتحسين مهاراتك.",
    "هل يمكنك إعطائي نصائح للنجاح؟": "بالطبع! حدد أهدافك، كن ملتزمًا، وابقَ إيجابيًا.",
    "ما هي أفضل التطبيقات للهواتف؟": "يعتمد ذلك على اهتماماتك، لكن تطبيقات مثل Duolingo و Evernote شائعة.",
    "كيف يمكنني تحسين لياقتي البدنية؟": "مارس الرياضة بانتظام، وتناول طعامًا صحيًا للحفاظ على لياقتك البدنية.",
    "ما هي الأنشطة التي يمكنني القيام بها في وقت الفراغ؟": "يمكنك قراءة الكتب، ممارسة الرياضة، أو تعلم مهارات جديدة.",
    "هل يمكنك مساعدتي في تنظيم وقتي؟": "بالطبع! حاول تحديد أولويات المهام واستخدام تقويم لتنظيم جدولك.",
    "ما هي فوائد التأمل؟": "التأمل يمكن أن يساعد في تقليل التوتر وزيادة التركيز.",
    "كيف يمكنني التعامل مع الضغوط؟": "حاول ممارسة التأمل، والتمارين الرياضية، والتحدث مع الأصدقاء.",
    "ما هي أهمية النوم الجيد؟": "النوم الجيد يساعد في تحسين التركيز، الحالة المزاجية والصحة العامة.",
    "هل يمكنك إعطائي وصفة طعام؟": "بالطبع! ما هو نوع الطعام الذي تود تحضيره؟",
    "ما هي أفضل الطرق لتوفير المال؟": "قم بإعداد ميزانية، وقلل من النفقات غير الضرورية.",
    "كيف أختار مهنة مناسبة لي؟": "تأكد من اختيار مهنة تتناسب مع اهتماماتك ومهاراتك.",
    "هل يمكنك مساعدتي في اتخاذ القرار؟": "نعم، يمكنني مساعدتك في تحليل الخيارات المتاحة.",
    "ما هو أفضل وقت للدراسة؟": "أفضل وقت للدراسة يعتمد على جدولك الخاص، لكن حاول اختيار أوقات تكون فيها أكثر تركيزًا.",
    "كيف أتعامل مع الفشل؟": "اعتبر الفشل فرصة للتعلم وتحسين نفسك في المستقبل.",
    "ما هي أهمية تحديد الأهداف؟": "تحديد الأهداف يساعدك على التركيز وتحقيق النجاح.",
    "هل يمكنك مساعدتي في كتابة سيرة ذاتية؟": "بالطبع! يمكنني مساعدتك في صياغة سيرة ذاتية مميزة.",
    "كيف أستعد لمقابلة عمل؟": "قم بالبحث عن الشركة، وتمرن على الإجابات على الأسئلة الشائعة.",
    "ما هي أفضل طريقة للتواصل مع الآخرين؟": "استمع جيدًا، وكن واضحًا في ما تريد قوله.",
    "هل يمكنك مساعدتي في تطوير مهاراتي الاجتماعية؟": "نعم، يمكنني تقديم نصائح حول كيفية تحسين مهاراتك الاجتماعية.",
    "ما هو أفضل وقت للتحدث مع شخص ما؟": "اختر وقتًا يكون فيه الشخص الآخر متاحًا ومستعدًا للتحدث.",
    "كيف أستطيع تحسين مهارات العرض التقديمي؟": "تمرن على العرض، واستخدم وسائل مرئية لجذب انتباه الجمهور.",
    "ما هي فوائد العمل الجماعي؟": "العمل الجماعي يمكن أن يعزز الإبداع ويساعد في تحقيق الأهداف بشكل أسرع.",
    "هل يمكنك مساعدتي في اختيار هدية؟": "بالطبع! ما هو الحدث الذي ترغب في شراء هدية له؟",
    "كيف أستطيع تحسين علاقاتي الشخصية؟": "كن صريحًا ومتفهمًا، وحاول قضاء وقت ممتع مع الآخرين.",
    "ما هي أهمية القراءة؟": "القراءة توسع آفاقك، وتحسن مهاراتك اللغوية.",
    "هل يمكنك تقديم توصيات لكتب جيدة؟": "بالطبع! ما هو النوع الذي تفضله؟",
    "كيف أستطيع بناء الثقة بالنفس؟": "قم بالتدريب على مهارات جديدة واحتفل بإنجازاتك الصغيرة.",
    "ما هي نصائحك للحفاظ على الصحة النفسية؟": "مارس التأمل، وتواصل مع الأصدقاء، واعتنِ بنفسك.",
    "هل يمكنك مساعدتي في تعلم لغة جديدة؟": "نعم، يمكنني توجيهك نحو الموارد المناسبة لتعلم لغات جديدة.",
    "كيف أستطيع التعامل مع الأشخاص السلبيين؟": "حاول الابتعاد عنهم إذا كان ذلك ممكنًا، وركز على الإيجابيات.",
    "ما هي أهمية التواصل الفعّال؟": "التواصل الفعّال يبني علاقات أفضل ويزيد من الفهم المتبادل.",
    "هل يمكنك مساعدتي في تنظيم حياتي؟": "بالطبع! يمكنني مساعدتك في وضع خطة لتنظيم حياتك.",
    "كيف أستطيع تحسين مهارات القيادة؟": "كن مثلاً يحتذى به، واستمع لآراء الآخرين، وكن قدوة.",
    "ما هي أهمية بناء شبكة علاقات؟": "بناء شبكة علاقات يمكن أن يفتح أمامك العديد من الفرص.",
    "هل يمكنك مساعدتي في إعداد ميزانية شخصية؟": "نعم، يمكنني مساعدتك في تحديد النفقات والإيرادات.",
    "كيف أستطيع التعامل مع الفشل بطريقة إيجابية؟": "اعتبر الفشل درسًا للتعلم وطور منهجيتك.",
    "ما هي فوائد ممارسة الهوايات؟": "الهوايات تساعد على تحقيق التوازن النفسي وتعزز الإبداع.",
    "هل يمكنك مساعدتي في كتابة مقال؟": "نعم، يمكنني مساعدتك في تنظيم أفكارك وكتابة المقال.",
    "كيف أستطيع تحسين ذاكرتي؟": "قم بممارسة تقنيات الذاكرة مثل التكرار والتقنيات البصرية.",
    "ما هي أهمية التقدير الذاتي؟": "التقدير الذاتي الجيد يعزز من ثقتك بنفسك وقدرتك على النجاح.",
    "هل يمكنك مساعدتي في فهم مفهوم الذكاء العاطفي؟": "نعم، الذكاء العاطفي هو القدرة على التعرف على مشاعرك ومشاعر الآخرين وإدارتها.",
    "كيف أستطيع تحسين قدرتي على اتخاذ القرارات؟": "قم بتحليل الخيارات ووزن الإيجابيات والسلبيات.",
    "ما هي فوائد وجود مرشد؟": "وجود مرشد يمكن أن يوفر لك التوجيه والدعم في مسيرتك.",
    "هل يمكنك مساعدتي في تطوير مهاراتي الفنية؟": "بالطبع! يمكنني توجيهك إلى موارد لتطوير مهاراتك الفنية.",
    "كيف أستطيع تحسين تجربة العملاء في مشروعي؟": "استمع إلى ملاحظات العملاء وكن مستجيبًا لاحتياجاتهم.",
    "ما هي أهمية التفكير النقدي؟": "التفكير النقدي يساعدك على تحليل المعلومات واتخاذ قرارات مستنيرة.",
    "هل يمكنك مساعدتي في فهم مفهوم الإدارة الذاتية؟": "الإدارة الذاتية هي القدرة على تنظيم وإدارة حياتك بشكل فعّال.",
    "كيف أستطيع التعامل مع الانتقادات البناءة؟": "استمع بعناية، وكن مفتوحًا للتعلم من الانتقادات.",
    "ما هي فوائد التدوين؟": "التدوين يساعدك على تحسين مهارات الكتابة وتوثيق أفكارك.",
    # مركزش بس دي تحسينات للقاموس
    "1": "مش فاهم انت تقصد اي ؟؟",
    "e": "مش فاهم انت تقصد اي ؟؟",
    "d": "مش فاهم انت تقصد اي ؟؟",
    "ش": "مش فاهم انت تقصد اي ؟؟",
    "ؤ": "مش فاهم انت تقصد اي ؟؟",
    "م": "مش فاهم انت تقصد اي ؟؟",
    "ء": "مش فاهم انت تقصد اي ؟؟",
    "ئ": "مش فاهم انت تقصد اي ؟؟",
    "ى": "مش فاهم انت تقصد اي ؟؟",
    "ا": "مش فاهم انت تقصد اي ؟؟",
    "س": "مش فاهم انت تقصد اي ؟؟",
    "ر": "مش فاهم انت تقصد اي ؟؟",
    "ش": "مش فاهم انت تقصد اي ؟؟",
    "ء": "مش فاهم انت تقصد اي ؟؟",
    "م": "مش فاهم انت تقصد اي ؟؟",
    "ن": "مش فاهم انت تقصد اي ؟؟",
    "ت": "مش فاهم انت تقصد اي ؟؟",
    "خ": "مش فاهم انت تقصد اي ؟؟",
    "ل": "مش فاهم انت تقصد اي ؟؟",
    "و": "مش فاهم انت تقصد اي ؟؟",
    "ض": "مش فاهم انت تقصد اي ؟؟",
    "ق": "مش فاهم انت تقصد اي ؟؟",
    "ث": "مش فاهم انت تقصد اي ؟؟",
    "غ": "مش فاهم انت تقصد اي ؟؟",
    "ع": "مش فاهم انت تقصد اي ؟؟",
    "2": "انت كتبت رقم لكن موضحتش يرجي توضيح ما تقصده",
    "3": "انت كتبت رقم لكن موضحتش يرجي توضيح ما تقصده",
    "4": "انت كتبت رقم لكن موضحتش يرجي توضيح ما تقصده",
    "5": "انت كتبت رقم لكن موضحتش يرجي توضيح ما تقصده",
    "6": "انت كتبت رقم لكن موضحتش يرجي توضيح ما تقصده",
    "7": "انت كتبت رقم لكن موضحتش يرجي توضيح ما تقصده",
    "8": "انت كتبت رقم لكن موضحتش يرجي توضيح ما تقصده",
    "9": "انت كتبت رقم لكن موضحتش يرجي توضيح ما تقصده",
    "10": "انت كتبت رقم لكن موضحتش يرجي توضيح ما تقصده",
    "هل يمكنك مساعدتي في تحديد الوقت المثالي للدراسة؟": "حدد الوقت الذي تكون فيه أكثر تركيزًا واستعد للدراسة.",
    "كيف أستطيع تحسين جودة حياتي بشكل عام؟": "قم بدمج الأنشطة الممتعة، واعتنِ بصحتك الجسدية والنفسية.",
    "ما هي أهمية التفكير الإبداعي؟": "التفكير الإبداعي يساعد في إيجاد حلول جديدة ومبتكرة للمشكلات.",
    "هل يمكنك مساعدتي في فهم مفهوم الذكاء الاجتماعي؟": "الذكاء الاجتماعي هو القدرة على التفاعل بشكل إيجابي مع الآخرين.",
    "كيف أستطيع تحسين مهارات الاستماع؟": "كن مركزًا خلال المحادثات، وحاول فهم وجهات نظر الآخرين.",
    "ما هو أفضل وقت للذهاب إلى النوم؟": "حاول الذهاب إلى النوم في نفس الوقت كل ليلة، وفقًا لاحتياجات جسمك.",
    "كيف أستطيع تعزيز إبداعي؟": "جرب الخروج من منطقة راحتك، وابدأ بمشاريع جديدة.",
    "هل يمكنك مساعدتي في إعداد خطة عمل؟": "بالطبع! يمكنني مساعدتك في تحديد الأهداف والخطوات اللازمة.",
    "كيف أستطيع التعامل مع ضغوط العمل؟": "قم بتحديد أولويات المهام، وخذ فترات راحة قصيرة.",
    "ما هي أهمية التغذية الجيدة؟": "التغذية الجيدة تعزز من صحتك العامة وتساعدك على الأداء بشكل أفضل.",
    "هل يمكنك تقديم نصائح للطبخ؟": "بالطبع! ما هو نوع الطعام الذي ترغب في تحضيره؟",
    "كيف أستطيع تحسين مهارات التفاوض؟": "تمرن على مهاراتك وكن مستعدًا للإصغاء والتكيف.",
    "ما هو الطريق الأفضل للتسويق الذاتي؟": "استخدم وسائل التواصل الاجتماعي لعرض مهاراتك وإنجازاتك.",
    "هل يمكنك مساعدتي في فهم مفهوم الابتكار؟": "الابتكار هو القدرة على التفكير بطريقة جديدة وتطوير حلول جديدة.",
    "كيف أستطيع التعامل مع القلق؟": "مارس تقنيات الاسترخاء والتأمل واطلب الدعم من الأصدقاء.",
    "ما هي فوائد العمل الجماعي؟": "العمل الجماعي يعزز من الإبداع ويساعد في إنجاز المهام بشكل أسرع.",
    "هل يمكنك مساعدتي في كتابة مقال؟": "نعم، يمكنني مساعدتك في تنظيم أفكارك وكتابة المقال.",
    "كيف أستطيع تحسين مهاراتي في الكتابة؟": "قم بالكتابة بانتظام واطلب تعليقات من الآخرين.",
    "ما هي أهمية تحديد الأولويات؟": "تحديد الأولويات يساعدك في إدارة وقتك بشكل أكثر فعالية.",
    "هل يمكنك مساعدتي في فهم مفهوم الذكاء العاطفي؟": "نعم، الذكاء العاطفي هو القدرة على التعرف على مشاعرك ومشاعر الآخرين وإدارتها.",
    "كيف أستطيع تحسين قدرتي على اتخاذ القرارات؟": "قم بتحليل الخيارات ووزن الإيجابيات والسلبيات.",
    "ما هي فوائد وجود مرشد؟": "وجود مرشد يمكن أن يوفر لك التوجيه والدعم في مسيرتك.",
    "هل يمكنك مساعدتي في تطوير مهاراتي الفنية؟": "بالطبع! يمكنني توجيهك إلى موارد لتطوير مهاراتك الفنية.",
    "كيف أستطيع تحسين تجربة العملاء في مشروعي؟": "استمع إلى ملاحظات العملاء وكن مستجيبًا لاحتياجاتهم.",
    "ما هي أهمية التفكير النقدي؟": "التفكير النقدي يساعدك على تحليل المعلومات واتخاذ قرارات مستنيرة.",
    "هل يمكنك مساعدتي في فهم مفهوم الإدارة الذاتية؟": "الإدارة الذاتية هي القدرة على تنظيم وإدارة حياتك بشكل فعّال.",
    "كيف أستطيع التعامل مع الانتقادات البناءة؟": "استمع بعناية، وكن مفتوحًا للتعلم من الانتقادات.",
    "ما هي فوائد التدوين؟": "التدوين يساعدك على تحسين مهارات الكتابة وتوثيق أفكارك.",
    "هل يمكنك مساعدتي في تحديد الوقت المثالي للدراسة؟": "حدد الوقت الذي تكون فيه أكثر تركيزًا واستعد للدراسة.",
    "كيف أستطيع تحسين جودة حياتي بشكل عام؟": "قم بدمج الأنشطة الممتعة، واعتنِ بصحتك الجسدية والنفسية.",
    "ما هي أهمية التفكير الإبداعي؟": "التفكير الإبداعي يساعد في إيجاد حلول جديدة ومبتكرة للمشكلات.",
    "هل يمكنك مساعدتي في فهم مفهوم الذكاء الاجتماعي؟": "الذكاء الاجتماعي هو القدرة على التفاعل بشكل إيجابي مع الآخرين.",
    "كيف أستطيع تحسين مهارات الاستماع؟": "كن مركزًا خلال المحادثات، وحاول فهم وجهات نظر الآخرين.",
    "ما هو أفضل وقت للذهاب إلى النوم؟": "حاول الذهاب إلى النوم في نفس الوقت كل ليلة، وفقًا لاحتياجات جسمك.",
    "كيف أستطيع تعزيز إبداعي؟": "جرب الخروج من منطقة راحتك، وابدأ بمشاريع جديدة.",
    "هل يمكنك مساعدتي في إعداد خطة عمل؟": "بالطبع! يمكنني مساعدتك في تحديد الأهداف والخطوات اللازمة.",
    "كيف أستطيع التعامل مع ضغوط العمل؟": "قم بتحديد أولويات المهام، وخذ فترات راحة قصيرة.",
    "ما هي أهمية التغذية الجيدة؟": "التغذية الجيدة تعزز من صحتك العامة وتساعدك على الأداء بشكل أفضل.",
    "هل يمكنك تقديم نصائح للطبخ؟": "بالطبع! ما هو نوع الطعام الذي ترغب في تحضيره؟",
    "كيف أستطيع تحسين مهارات التفاوض؟": "تمرن على مهاراتك وكن مستعدًا للإصغاء والتكيف.",
    "ما هو الطريق الأفضل للتسويق الذاتي؟": "استخدم وسائل التواصل الاجتماعي لعرض مهاراتك وإنجازاتك.",
    "هل يمكنك مساعدتي في فهم مفهوم الابتكار؟": "الابتكار هو القدرة على التفكير بطريقة جديدة وتطوير حلول جديدة.",
    "كيف أستطيع التعامل مع القلق؟": "مارس تقنيات الاسترخاء والتأمل واطلب الدعم من الأصدقاء.",
    "ما هي فوائد العمل الجماعي؟": "العمل الجماعي يعزز من الإبداع ويساعد في إنجاز المهام بشكل أسرع.",
    "هل يمكنك مساعدتي في كتابة مقال؟": "نعم، يمكنني مساعدتك في تنظيم أفكارك وكتابة المقال.",
    "كيف أستطيع تحسين مهاراتي في الكتابة؟": "قم بالكتابة بانتظام واطلب تعليقات من الآخرين.",
    "ما هي أهمية تحديد الأولويات؟": "تحديد الأولويات يساعدك في إدارة وقتك بشكل أكثر فعالية.",
    "هل يمكنك مساعدتي في فهم مفهوم الذكاء العاطفي؟": "نعم، الذكاء العاطفي هو القدرة على التعرف على مشاعرك ومشاعر الآخرين وإدارتها.",
    "كيف أستطيع تحسين قدرتي على اتخاذ القرارات؟": "قم بتحليل الخيارات ووزن الإيجابيات والسلبيات.",
    "ما هي فوائد وجود مرشد؟": "وجود مرشد يمكن أن يوفر لك التوجيه والدعم في مسيرتك.",
    "هل يمكنك مساعدتي في تطوير مهاراتي الفنية؟": "بالطبع! يمكنني توجيهك إلى موارد لتطوير مهاراتك الفنية.",
    "كيف أستطيع تحسين تجربة العملاء في مشروعي؟": "استمع إلى ملاحظات العملاء وكن مستجيبًا لاحتياجاتهم.",
    "ما هي أهمية التفكير النقدي؟": "التفكير النقدي يساعدك على تحليل المعلومات واتخاذ قرارات مستنيرة.",
    "هل يمكنك مساعدتي في فهم مفهوم الإدارة الذاتية؟": "الإدارة الذاتية هي القدرة على تنظيم وإدارة حياتك بشكل فعّال.",
    "كيف أستطيع التعامل مع الانتقادات البناءة؟": "استمع بعناية، وكن مفتوحًا للتعلم من الانتقادات.",
    "ما هي فوائد التدوين؟": "التدوين يساعدك على تحسين مهارات الكتابة وتوثيق أفكارك.",
    "هل يمكنك مساعدتي في تحديد الوقت المثالي للدراسة؟": "حدد الوقت الذي تكون فيه أكثر تركيزًا واستعد للدراسة.",
    "كيف أستطيع تحسين جودة حياتي بشكل عام؟": "قم بدمج الأنشطة الممتعة، واعتنِ بصحتك الجسدية والنفسية.",
    "ما هي أهمية التفكير الإبداعي؟": "التفكير الإبداعي يساعد في إيجاد حلول جديدة ومبتكرة للمشكلات.",
    "هل يمكنك مساعدتي في فهم مفهوم الذكاء الاجتماعي؟": "الذكاء الاجتماعي هو القدرة على التفاعل بشكل إيجابي مع الآخرين.",
    "كيف أستطيع تحسين مهارات الاستماع؟": "كن مركزًا خلال المحادثات، وحاول فهم وجهات نظر الآخرين.",
    "?": "نعم قولي انت مش فاهم اي وانا اشرحه",
    "ما هو عنصر كيميائي يُرمز له بالرمز 'O'؟": "الأكسجين.",
    "ما هي العملية التي يتم فيها اتحاد الأكسجين مع المواد الأخرى؟": "الاحتراق.",
    "ما هو الحيوان الذي لا يمتلك هيكل عظمي داخلي؟": "الأخطبوط.",
    "ما هي الدولة التي تُنتج أكبر كمية من الذهب في العالم؟": "الصين.",
    "ما هو الغاز المستخدم في المصابيح الفلورية؟": "النيون.",
    "ما هي أكبر مدينة من حيث عدد السكان في قارة إفريقيا؟": "لاغوس، نيجيريا.",
    "ما هو أول عنصر في الجدول الدوري للعناصر؟": "الهيدروجين.",
    "ما هي الدولة التي تشتهر بجبال الألب؟": "سويسرا.",
    "ما هو الحيوان القادر على العيش في أعمق نقطة في المحيطات؟": "الخيار البحري.",
    "ما هي المادة الكيميائية التي تُستخدم لتعقيم مياه الشرب؟": "الكلور.",
    "ما هي العاصمة الرسمية للبرازيل؟": "برازيليا.",
    "ما هو الجهاز الذي يستخدم لقياس كمية الأمطار؟": "مقياس المطر.",
    "ما هي المادة التي تتكون من نترات السليلوز وتُستخدم في صناعة الورق؟": "الديناميت.",
    "ما هو الحيوان الذي يُعتبر أسرع الثدييات سريعة الحركة في العالم؟": "الفهد.",
    "ما هي الدولة التي تحتوي على أطول شبكة طرق سريعة في العالم؟": "الولايات المتحدة الأمريكية.",
    "ما هي أول مدينة جرى فيها استخدام إشارات المرور؟": "لندن.",
    "ما هو العنصر الأكثر تواجداً في جسم الإنسان؟": "الأكسجين.",
    "ما هي أكثر دولة إنتاجًا للقهوة؟": "البرازيل.",
    "ما هو الحيوان الذي يمكنه النوم لمدة تصل إلى ثلاث سنوات؟": "الحلزون.",
    "ما هو الجهاز الذي يستخدم لقياس شدة الزلازل؟": "السيسموجراف.",
    "ما هي الدولة التي شهدت أول ثورة صناعية في العالم؟": "بريطانيا.",
    "ما هو الاسم العلمي للشجرة التي تُنتج الفلين؟": "شجرة البلوط الفليني.",
    "ما هي أكبر جزيرة في البحر الكاريبي؟": "كوبا.",
    "ما هو أكبر بحيرة عذبة في العالم من حيث الحجم؟": "بحيرة بايكال.",
    "ما هي الدولة التي أنتجت أول فيلم كارتوني في العالم؟": "الولايات المتحدة الأمريكية.",
    "ما هو الحيوان الذي يمتلك أكبر جهاز عصبي بالنسبة لحجمه؟": "الأخطبوط.",
    "ما هي العملة الرسمية للهند؟": "الروبية الهندية.",
    "ما هي العملية الفيزيائية التي يتم من خلالها تحويل الغاز إلى سائل؟": "التكثيف.",
    "ما هي الدولة التي تمتلك أكبر اقتصاد في العالم؟": "الولايات المتحدة الأمريكية.",
    "ما هو الحيوان الذي يمكنه العيش بدون ماء لأطول فترة؟": "الجمل.",
    "ما هي القارة الوحيدة التي لا تحتوي على الصحراء؟": "أوروبا.",
    "ما هو الكائن البحري الذي يُعرف بقدرته على إنتاج اللؤلؤ؟": "المحار.",
    "ما هي أول مدينة استخدمت الطاقة الكهربائية للإنارة؟": "نيويورك.",
    "ما هي الدولة التي تحتوي على أكبر عدد من البراكين النشطة؟": "إندونيسيا.",
    "ما هو الكنز الأكثر قيمة الذي دُفن في البحر؟": "كنز سان خوسيه.",
    "ما هي أول دولة استخدمت الطائرات الحربية في الحرب؟": "إيطاليا.",
    "ما هو الحيوان الذي ينام 18 ساعة في اليوم؟": "الكسلان.",
    "ما هي الدولة التي تُعرف بأرض الخامس على التوالي؟": "الفاتيكان.",
    "ما هو العنصر الغذائي الذي يحتاجه الجسم لبناء العضلات؟": "البروتين.",
    "ما هي الدولة التي يتمتع فيها الناس بأعلى متوسط عمر متوقع؟": "اليابان.",
    "ما هي العاصمة الاقتصادية للبرازيل؟": "ساو باولو.",
    "ما هو الكوكب الذي يطلق عليه الكوكب الأحمر؟": "المريخ.",
    "ما هو أكبر جسر في العالم؟": "جسر دانيانغ–كونشان الكبير في الصين.",
    "ما هو الجهاز الذي يقيس ضغط الدم؟": "السبغمومانومتر.",
    "ما هي الدولة التي تُعتبر الموطن الأصلي للبرتقال؟": "الصين.",
    "ما هو الحيوان الذي يشتهر بكون عينه أكبر من دماغه؟": "النعامة.",
    "ما هي المادة التي تُستخدم في تصنيع الزجاج؟": "السيليكا.",
    "ما هو الحيوان الذي يمتلك أطول فترة حمل؟": "الفيل.",
    "ما هي الدولة التي تمتلك أكبر أسطول بحري تجاري؟": "اليونان.",
    "ما هو الكوكب الذي يمتلك أكبر عدد من الأقمار؟": "زحل.",
    "ما هي أكبر دولة في قارة أمريكا الشمالية؟": "كندا.",
    "ما هو الحيوان الذي يمكنه النوم بملء عينه أثناء الطيران؟": "طائر السمنة.",
    "ما هي المدينة التي تُعتبر موطنًا لأكبر عدد من ناطحات السحاب؟": "هونغ كونغ.",
    "ما هو الجهاز الذي يُستخدم في قياس قوة الزلازل؟": "ريختر.",
    "ما هي الدولة التي تحتوي على أكبر عدد من الأهرامات؟": "السودان.",
    "ما هو الحيوان الذي يُعتبر رمزًا للسلام والهدوء؟": "الحمامة.",
    "ما هي المادة المستخدمة في صناعة العملات النقدية الحديثة؟": "المعدن (عادةً من المخلفات وغير الحديدية مثل النحاس والنيكل).",
    "ما هي أول مدينة مستخدمة للإنترنت اللاسلكي المجاني بشكل شامل؟": "تالين، إستونيا.",
    "ما هو العنصر الكيميائي الذي يُعتبر أساس الحياة؟": "الكربون.",
    "ما هي الظاهرة الطبيعية التي تحدث عندما يتساقط ضوء الشمس من موضع قريب من الأفق؟": "قوس قزح.",
    "ما هي أكبر بحيرة في أفريقيا؟": "بحيرة فيكتوريا.",
    "ما هو الحيوان الذي يمكنه تغيير لون جلده للتخفي؟": "الحرباء.",
    "ما هي القارة الأكثر برودة في العالم؟": "القارة القطبية الجنوبية (أنتاركتيكا).",
    "ما هي اللغة الرسمية في الصين؟": "الصينية الماندرين.",
    "ما هو الكائن الوحيد الذي لا يشرب الماء طوال حياته؟": "الجرذ الكنغري.",
    "ما هي العاصمة الثقافية لروسيا؟": "سانت بطرسبرغ.",
    "ما هي الدولة التي تُعتبر ثالث أكبر دولة في العالم من حيث المساحة؟": "الولايات المتحدة الأمريكية.",
    "ما هو الغاز الذي يملأ غالبية البالونات الاحتفالية؟": "الهيليوم.",
    "ما هو البحر الذي يحيط بالبحر الأحمر من جهات ثلاث؟": "البحر المتوسط.",
    "ما هي العملية الحيوية التي تحدث داخل الخلايا لإنتاج الطاقة؟": "التنفس الخلوي.",
    "ما هو الحيوان الذي يُعتبر أطول الحيوانات البرية؟": "الزرافة.",
    "ما هي المادة الكيميائية التي تجعل الدم يظهر باللون الأحمر؟": "الهيموجلوبين.",
    "ما هو الكتاب الذي كتبه تشارلز داروين والذي أثار ثورة في فهمنا للتطور؟": "أصل الأنواع.",
    "ما هي الدولة التي تحتوي على أطول شبكة سكة حديدية في العالم؟": "الولايات المتحدة الأمريكية.",
    "ما هو الحيوان الذي يعيش على الأرض وله ثلاث قلوب؟": "الأخطبوط.",
    "ما هي أول دولة استخدمت القوارب كوسيلة نقل؟": "مصر القديمة.",
    "ما هو الجهاز الذي يستخدم لقياس الرطوبة؟": "الهيجرومتر.",
    "ما هي الدولة التي تُعتبر موطنًا لشجرة الزيتون؟": "اليونان.",
    "ما هو المصطلح الذي يُطلق على العلم الذي يدرس الأجرام السماوية؟": "الفلك.",
    "ما هو الحيوان البحري الذي يمكنه التحرك بشكل عكسي؟": "الأخطبوط.",
    "ما هي عاصمة كندا؟": "أوتاوا.",
    "ما هي أكبر مدينة في القارة الآسيوية؟": "طوكيو، اليابان.",
    "ما هو العضو في جسم الإنسان الذي يمكنه النمو من جديد؟": "الكبد.",
    "ما هي الدولة التي تُعتبر أكبر منتج للساعات الفاخرة في العالم؟": "سويسرا.",
    "ما هو الحيوان الذي يُعتبر أسرع مخلوق في العالم؟": "صقر الشاهين.",
    "ما هي أكبر سلسلة جبال في العالم؟": "سلسلة جبال الأنديز.",
    "ما هو أول فيروس تم اكتشافه؟": "فيروس توباكو موزايك.",
    "ما هي المادة التي تُستخدم في صناعة البلاستيك؟": "البولي إيثيلين.",
    "ما هو الاسم العلمي للإنسان الحديث؟": "Homo sapiens.",
    "ما هي الدولة التي تحتوي على أكبر بحيرة ماء عذب غير متجمدة في العالم؟": "روسيا (بحيرة بايكال).",
    "ما هو الحيوان البحري الذي يمكنه العيش بدون ماء لفترة طويلة؟": "السلطعون الناسك.",
    "ما هو المصطلح المستخدم لوصف جملة الحروف التي تُستخدم لتشفير المعلومات؟": "الخوارزمية.",
    "ما هي الدولة التي تحتوي على أكبر عدد من المواقع الأثرية في العالم؟": "مصر.",
    "ما هو الجهاز الذي يستخدم لقياس التلوث الهوائي؟": "محلل التلوث.",
    "ما هو الكائن الحي الوحيد الذي يعتبر من أكلة العشب البرية ويتميز بدقته العالية في الصيد؟": "الذئب.",
    "ما هي أول سيارة في العالم؟": "بنز باتنت موتورفاغن (1886).",
    "ما هو أكبر حيوان على وجه الأرض؟": "الحوت الأزرق.",
    "ما هي القارة التي تحتوي على أكبر عدد من البراكين؟": "آسيا.",
    "ما هي الدولة التي تعرف باسم بلد الكنغر؟": "أستراليا.",
    "ما هو العنصر الكيميائي الذي يعزز صحة العظام والأسنان؟": "الكالسيوم.",
    "ما هي البحيرة التي تُعتبر أعمق بحيرة في العالم؟": "بحيرة بايكال.",
    "ما هي عاصمة الهند؟": "نيودلهي.",
    "ما هو الحدث الطبيعي الأشد في توليد الرياح؟": "الإعصار.",
    "ما هو اسم المادة التي تستخدمها الكائنات البحرية مثل الصدف لإنتاج اللؤلؤ؟": "أم اللؤلؤ (nacre).",
    "ما هو أكبر قمر في النظام الشمسي؟": "غانيميد (قمر المشتري).",
    "ما هي العملية التي يتم فيها تحويل الماء إلى بخار؟": "التبخر.",
    "ما هو الحيوان الذي يمكنه العيش في كل من الماء واليابسة؟": "الضفدع.",
    "ما هي الدولة التي تحتوي على أكبر مجمع صحراوي؟": "الصحراء الكبرى (شمال أفريقيا).",
    "ما هو العنصر الغذائي الذي يوجد بكثرة في اللحوم والبقوليات؟": "البروتين.",
    "ما هو الكائن الحي الذي يملك أكبر عدد من الأرجل؟": "الدودة الألفية.",
    "ما هي أكبر شلالات في العالم من حيث التدفق؟": "شلالات إنجا في الكونغو.",
    "ما هو الكوكب الذي يدور حوله أكبر عدد من الأقمار؟": "المشتري.",
    "ما هي أهم العوامل التي تؤدي إلى التصحر؟": "الإفراط في الرعي، وقطع الأشجار، والتغيرات المناخية.",
    "من هو أول شخص تسلق قمة جبل إيفرست؟": "إدموند هيلاري وتينسينغ نورغاي في 1953.",
    "ما هو الغاز الذي يُستخدم في تعبئة الطائرات لتعزيز الأمان؟": "النيتروجين.",
    "ما هي المدينة التي تُعرف بأكبر ميناء في العالم؟": "ميناء شنغهاي في الصين.",
    "ما هو الطائر الذي يمكنه الطيران إلى الخلف؟": "الطائر الطنان.",
    "ما هي الدولة التي تُعتبر موطنًا لرياضة البوكسينغ؟": "إنجلترا.",
    "من هو الفيلسوف الذي كتب 'نيكوماتيكس الأخلاقية'؟": "أرسطو.",
    "ما هي أكبر المعتقلات العظمى وأشهرها في أوروبا؟": "معتقل أوشفيتز في بولندا.",
    "ما هو الحيوان الذي يمكنه العيش في أجواء الصحراء القاسية؟": "الجمل.",
    "ما هي المدينة الأكثر كثافة سكانية في العالم؟": "طوكيو، اليابان.",
    "ما هو اسم الجزيرة التي تعتبر مصدرًا لمنجم كبير للفحم؟": "جزيرة بورنيو.",
    "ما هي الوحدة التي تقيس الزمن بشكل دقيق في الفيزياء؟": "الثانية.",
    "ما هو الحيوان الذي يعيش في القطب الجنوبي ويعتمد على السباحة للصيد؟": "بطريق الإمبراطور.",
    "ما هو العنصر الكيميائي الذي يكون الغاز الرئيسي في كوكب الزهرة؟": "ثاني أكسيد الكربون.",
    "ما هي المادة الرئيسية في تكوين الألماس؟": "الكربون.",
    "ما هو الجهاز الذي يُستخدم لقياس الرطوبة في الهواء؟": "الهيجرومتر.",
    "ما هي أول عاصمة ثقافية أوروبية؟": "أثينا في اليونان.",
    "ما هو الحيوان الذي يمتلك أذكى دماغ بين الحيوانات البدائية؟": "الأخطبوط.",
    "ما هو الحدث الذي يُعتبر نقطة التحول في الحرب العالمية الثانية؟": "معركة ستالينغراد.",
    "ما هي العملية التي تعتمد بها النباتات على النيتروجين من الهواء؟": "التثبيت النيتروجيني.",
    "ما هو الطائر الذي يُعتبر رمزًا للسلام؟": "الحمامة.",
    "ما هي المادة التي تتكون بسبب التفاعلات الكيميائية داخل النجوم؟": "الهيدروجين يتحول إلى الهيليوم.",
    "ما هو الجهاز الذي يستخدم في قياس قوة الزلازل؟": "السيسموجراف.",
    "ما هي الدولة التي تحتوي على أقدم مكتبة في العالم؟": "المغرب (مكتبة القرويين).",
    "ما هو أول حيوان دجّن بواسطة الإنسان؟": "الكلب.",
    "ما هي المادة التي تُعتبر موصلًا جيدًا للكهرباء وتُستخدم في المكونات الإلكترونية؟": "النحاس.",
    "ما هي المدينة التي تُعرف بعاصمة الرومانسية؟": "باريس.",
    "ما هو الحيوان الذي يُمكنه النوم وإحدى عينيه مفتوحة؟": "الدلفين.",
    "ما هي الدولة التي تحتوي على أكبر غابة بدائية في أوروبا؟": "بولندا (غابة بياوفيجا).",
    "ما هو الطائر الذي يمكنه تحريك جناحيه بشكل أسرع؟": "الطائر الطنان.",
    "ما هي العملية التي تعتمد فيها النباتات على الضوء لتحويل ثاني أكسيد الكربون إلى طاقة؟": "التمثيل الضوئي.",
    "ما هو الحيوان الذي يُعتبر الأكثر صوتًا في العالم؟": "الحوت الأزرق.",
    "ما هي المدينة التي تُعتبر موطنًا لأقدم جامعة في العالم؟": "فاس، المغرب (جامعة القرويين).",
    "ما هي العظمة الأقوى في جسم الإنسان؟": "عظمة الفخذ.",
    "ما هو العنصر الذي يُستخدم في صناعة الزجاج والسيراميك؟": "السيليكا.",
    "ما هي أكبر مدينة في قارة أفريقيا؟": "لاغوس، نيجيريا.",
    "من هو العالم الذي قدم مفهوم الجاذبية؟": "إسحاق نيوتن.",
    "ما هي المادة التي تُستخدم في صناعة الألياف البصرية؟": "السليكا.",
    "ما هي الدولة التي تحتوي على أكبر محمية طبيعية في العالم؟": "الولايات المتحدة (ألاسكا).",
    "ما هو الحيوان الذي يلد صغاره تحت الماء؟": "الحوت.",
    "ما هو الكتاب الذي كتبه فلاديمير نابوكوف والذي أثار جدلاً كبيرًا؟": "لوليتا.",
    "ما هي العملية التي يتم من خلالها تكسير الطعام في جسم الإنسان؟": "الهضم.",
    "ما هو أكبر سد في أفريقيا؟": "سد كاريبا بين زيمبابوي وزامبيا.",
    "ما هي الدولة التي تحتوي على أكبر احتياطي للنفط في العالم؟": "فنزويلا.",
    "ما هو الغاز الذي يُستخدم في إطفاء الحرائق؟": "ثاني أكسيد الكربون.",
    "ما هو الطائر الذي يملك أطول جناحين؟": "القطرس المتجول.",
    "ما هي الدولة التي تُعتبر أكبر منتج للموز في العالم؟": "الهند.",
    "ما هو الحيوان الذي يمكنه السباحة إلى أقصى عمق في المحيط؟": "الحوت الأزرق.",
    "ما هي الدولة التي تحتوي على أكبر عدد من اللغة الرسمية؟": "الهند.",
    "ما هو العنصر الكيميائي الذي يُستخدم في صناعة المرايا؟": "الفضة.",
    "ما هي المدينة التي تُعرف بعاصمة الضباب؟": "لندن.",
    "ما هي العملية الفيزيائية التي يتم فيها تحويل المادة المذابة إلى صلبة؟": "التجمد.",
    "ما هو الكتاب الذي كتبه جورج أورويل حول الدولة البوليسية؟": "1984.",
    "ما هي الدولة التي تحتوي على أكبر عدد من النحل في العالم؟": "الصين.",
    "ما هو الحيوان الذي يمكنه الطيران إلى ارتفاعات شاهقة؟": "النسر.",
    "ما هي المادة التي تستخدمها الحشرات في بناء بيوتها؟": "السليلوز.",
    "ما هي المدينة التي تحتوي على أكبر متحف في العالم؟": "باريس (متحف اللوفر).",
    "ما هو الحيوان الذي يعتبر الأكثر تنوعًا من حيث الأنواع؟": "الخنافس.",
    "ما هي المدينة التي تُعرف بالألف مدينة؟": "روما.",
    "ما هي العملية التي تُستخدم فيها الخلايا لتحويل الطعام إلى طاقة؟": "الهدم.",
    "ما هي الدولة التي تحتوي على أكبر تمثال في العالم؟": "الهند (تمثال الوحدة).",
    "ما هو الحيوان الذي يمكنه البقاء على قيد الحياة في بيئة نقص الأكسجين؟": "السلطعون.",
    "ما هي المادة المستخدمة في صناعة الألعاب النارية؟": "البارود.",
    "ما هي الدولة التي تحتوي على أقدم آثار في العالم؟": "مصر.",
    "ما هو أكبر نوع من الثعابين؟": "الأناكوندا.",
    "ما هي العاصمة الاقتصادية للهند؟": "مومباي.",
    "ما هو الطائر الذي يُعتبر رمزًا للولايات المتحدة؟": "النسر الأصلع.",
    "ما هي الدولة التي تُعتبر أكبر مصدر للزهور في العالم؟": "هولندا.",
    "ما هو العنصر الذي يُستخدم في صناعة البطاريات؟": "الليثيوم.",
    "ما هي المدينة الأكثر ارتفاعًا فوق سطح البحر في العالم؟": "لاباز، بوليفيا.",
    "ما هو الحيوان الذي يمكنه تغيير لون عينيه؟": "الحرباء.",
    "ما هي العملية التي تنتج فيها النباتات الجلوكوز والأكسجين؟": "التمثيل الضوئي.",
    "ما هي الدولة التي تحتوي على أكبر جبل جليدي في العالم؟": "أنتاركتيكا.",
    "ما هو الجهاز العضوي الذي يُستخدم لإزالة السموم من الجسم؟": "الكبد.",
    "ما هي المادة التي تُستخدم في صناعة النقود الورقية؟": "القطن.",
    "ما هي العملية الفيزيائية التي يتم فيها تحويل الغاز إلى سائل؟": "التكثيف.",
    "ما هو أكبر حي بحري في العالم؟": "الشعاب المرجانية في أستراليا.",
    "ما هو الحيوان الذي يُعتبر الأذكى بعد الإنسان؟": "الشيمبانزي.",
    "ما هي الدولة التي تحتوي على أكبر احتياطي من الذهب في العالم؟": "الولايات المتحدة الأمريكية.",
    "ما هو العنصر الكيميائي الذي يُستخدم في صناعة الألواح الشمسية؟": "السيلكون.",
    "من هو أول إنسان دار حول الأرض في مركبة فضائية؟": "يوري جاجارين.",
    "ما هي العملية التي تحول بها النباتات الضوء إلى طاقة؟": "عملية التمثيل الضوئي.",
    "ما هو أكبر تمساح عاش على وجه الأرض؟": "ساركوسوكس.",
    "ما هي اللغة الأكثر تحدثاً في العالم؟": "الإنجليزية.",
    "ما هي الدولة التي تمتلك أكبر اقتصاد في أوروبا؟": "ألمانيا.",
    "ما هي العملية الحيوية التي تحدث في الميتوكوندريا؟": "التنفس الخلوي.",
    "ما هو الجهاز الذي يستخدم لقياس التيارات الكهربائية؟": "الأميتر.",
    "ما هي الدولة التي تشتهر بصنع الأجبان المختلفة؟": "فرنسا.",
    "ما هو العنصر الكيميائي الذي يساهم في تقوية جهاز المناعة؟": "الزنك.",
    "ما هي الجزيرة الأكبر في العالم؟": "جرينلاند.",
    "ما هو الطائر الذي يُعتبر أكبر طائر في العالم؟": "النعامة.",
    "ما هي المادة التي تُستخدم في صناعة النقود المعدنية؟": "النيكل.",
    "ما هي أكبر هضبة في العالم؟": "هضبة التبت.",
    "ما هو الحيوان الذي يستطيع النوم وإحدى عينيه مفتوحة؟": "الدلفين.",
    "ما هي الدولة التي تحتوي على أكبر كمية من بحيرات المياه العذبة؟": "كندا.",
    "ما هو الحيوان الذي يمتلك أكبر قلب نسبةً إلى حجم جسمه؟": "الزرافة.",
    "ما هي المادة الكيميائية التي تساهم في تبييض الأسنان؟": "بيروكسيد الهيدروجين.",
    "ما هي أول قمر اصطناعي يُطلق إلى الفضاء؟": "سبوتنيك 1.",
    "ما هو الجهاز الذي يُستخدم لقياس نسبة الأوكسجين في الدم؟": "جهاز قياس نسبة الأوكسجين (الأوكسيميتر).",
    "ما هي الدولة التي يتمتع سكانها بأكبر نسبة من الأميش؟": "الولايات المتحدة الأمريكية.",
    "ما هو العنصر الكيميائي الذي يسبب تآكل الحديد؟": "الأكسجين (عبر عملية التأكسد).",
    "ما هي أكثر دولة إنتاجًا للأفلام السينمائية؟": "الهند (بوليوود).",
    "ما هو الطائر الذي يُعتبر أسرع طائر في العالم؟": "الصقر الشاهين.",
    "ما هو الكائن البحري الذي يُعتبر رمزًا للطبيعة البحرية؟": "الدلفين.",
    "ما هي أعلى قمة جبلية في أفريقيا؟": "قمة كليمنجارو.",
    "ما هو المكان الذي تتواجد فيه أقدم وأكبر شجرة في العالم؟": "كاليفورنيا (شجرة الجنرال شيرمان).",
    "ما هي الحديقة الوطنية الأكبر في الولايات المتحدة؟": "حديقة يلوستون الوطنية.",
    "ما هو الحيوان الذي يُعتبر أكبر مفترس في البحار؟": "القرش الأبيض الكبير.",
    "ما هي الدولة التي تحتوي على أكبر عدد من مواقع التراث العالمي؟": "إيطاليا.",
    "ما هو العنصر الغذائي الذي يُعتبر المكون الأساسي في الأرز؟": "الكربوهيدرات.",
    "ما هي أكبر بحيرة في أمريكا الجنوبية؟": "بحيرة تيتيكاكا.",
    "ما هو الحيوان الذي يستخدم زعانفه للتحرك في الماء؟": "السمك.",
    "ما هي أنواع النباتات التي تنمو في المناطق الصحراوية؟": "الصبار.",
    "ما هو الكائن الذي يُعتبر أكثر كائنات الماء تنوعًا؟": "المرجان.",
    "ما هي أكبر مدينة في القارة الأوروبية من حيث عدد السكان؟": "إسطنبول.",
    "ما هي المادة التي تُعتبر جيدة لسحب الرطوبة من الهواء؟": "السيليكا جل.",
    "ما هو الحيوان الذي يُعتبر أكثر تواجدًا في القارة القطبية الجنوبية؟": "البطريق.",
    "ما هي العملة الرسمية في المملكة المتحدة؟": "الجنيه الإسترليني.",
    "مَن هو مكتشف البنسلين؟": "ألكسندر فليمنغ.",
    "ما هي العملية التي يتم بواسطتها تحويل الجلوكوز إلى طاقة؟": "التنفس الخلوي.",
    "ما هي الدولة الأكثر إنتاجًا للبن في العالم؟": "البرازيل.",
    "ما هو أكبر ميناء بحري في أفريقيا؟": "ميناء ديربان، جنوب أفريقيا.",
    "ما هو الكوكب الذي يُعتبر ثاني أقرب كوكب إلى الشمس؟": "الزهرة.",
    "ما هي المادة الأساسية في تكوين الغاز الطبيعي؟": "الميثان.",
    "ما أخبارك؟": "أخبار جيدة! أنا هنا لمساعدتك. كيف يمكنني مساعدتك؟",
    "من أنت؟": "أنا مساعدك الذكي، هنا لمساعدتك في أي شيء تحتاجه.",
    "ماذا تفعل؟": "أقوم بمساعدتك في الإجابة على الأسئلة وتوفير المعلومات.",
    "هل يمكنك مساعدتي؟": "بالطبع! كيف يمكنني مساعدتك اليوم؟",
    "ما الجديد؟": "كل شيء على ما يرام! ماذا عنك؟",
    "كيف تسير الأمور؟": "الأمور تسير بشكل جيد هنا! كيف يمكنني مساعدتك؟",
    "أخبار اليوم؟": "أنا هنا لمساعدتك! هل لديك أي سؤال؟",
    "تحية": "أهلاً! سعيد بالتحدث معك. كيف يمكنني مساعدتك؟",
    "سلام": "سلام! كيف يمكنني مساعدتك اليوم؟",
    "صباح الخير": "صباح النور! كيف يمكنني مساعدتك في هذا اليوم الجميل؟",
    "مساء الخير": "مساء النور! أتمنى لك يوماً سعيداً. ما الذي يمكنني مساعدتك فيه؟",
    "أهلا": "أهلاً وسهلاً بك! كيف يمكنني مساعدتك اليوم؟",
    "مرحبا": "مرحبا بك! كيف أستطيع مساعدتك؟",
    "كيف حالك؟": "أنا بخير، شكرًا لك! ماذا عنك؟",
    "ما أخبارك؟": "أخبار جيدة! أنا هنا لمساعدتك. كيف يمكنني مساعدتك؟",
    "من أنت؟": "أنا مساعدك الذكي، هنا لمساعدتك في أي شيء تحتاجه.",
    "ماذا تفعل؟": "أقوم بمساعدتك في الإجابة على الأسئلة وتوفير المعلومات.",
    "هل يمكنك مساعدتي؟": "بالطبع! كيف يمكنني مساعدتك اليوم؟",
    "ما الجديد؟": "كل شيء على ما يرام! ماذا عنك؟",
    "كيف تسير الأمور؟": "الأمور تسير بشكل جيد هنا! كيف يمكنني مساعدتك؟",
    "أخبار اليوم؟": "أنا هنا لمساعدتك! هل لديك أي سؤال؟",
    "تحية": "أهلاً! سعيد بالتحدث معك. كيف يمكنني مساعدتك؟",
    "سلام": "سلام! كيف يمكنني مساعدتك اليوم؟",
    "صباح الخير": "صباح النور! كيف يمكنني مساعدتك في هذا اليوم الجميل؟",
    "مساء الخير": "مساء النور! أتمنى لك يوماً سعيداً. ما الذي يمكنني مساعدتك فيه؟",
    "كيف تسير حياتك؟": "كل شيء جيد! ماذا عنك؟",
    "كيف كان يومك؟": "كان يوماً جيداً! كيف كان يومك؟",
    "هل أنت مشغول؟": "لست مشغولًا، أنا هنا لمساعدتك!",
    "ما هي خططك اليوم؟": "خططي هي مساعدتك! كيف يمكنني ذلك؟",
    "أحب التحدث معك": "وأنا أحب التحدث معك! ماذا تريد أن تعرف؟",
    "كيف أستطيع مساعدتك؟": "يمكنك مساعدتي بسؤالك! ما الذي تحتاجه؟",
    "ما هو الذكاء الاصطناعي؟": "الذكاء الاصطناعي هو فرع من علوم الكمبيوتر يهدف إلى إنشاء أنظمة قادرة على أداء المهام التي تتطلب ذكاءً بشريًا.",
    "ما هي فوائد الرياضة؟": "الرياضة تحسن اللياقة البدنية وتساعد في تقليل التوتر وتعزز الصحة العقلية.",
    "ما هي هواياتك؟": "أنا هنا لمساعدتك، لذا ليس لدي هوايات، لكنني أحب مساعدتك في اكتشاف هواياتك!",
    "كيف أبدأ في تعلم البرمجة؟": "يمكنك البدء بتعلم لغة برمجة مثل بايثون أو جافا، وهناك العديد من الموارد المتاحة على الإنترنت.",
    "ما هي أهمية التعليم؟": "التعليم يفتح الأبواب للفرص ويعزز النمو الشخصي والمجتمعي.",
    "ما هو أفضل وقت للدراسة؟": "أفضل وقت للدراسة هو عندما تكون أكثر تركيزًا، سواء كان صباحًا أو مساءً.",
    "كيف أستطيع تحسين مهاراتي؟": "يمكنك ممارسة المهارات التي ترغب في تحسينها بانتظام وطلب التغذية الراجعة.",
    "ما هو أفضل كتاب قرأته؟": "ليس لدي كتب مفضلة، لكن يمكنني مساعدتك في العثور على كتب مميزة حسب اهتماماتك.",
    "كيف أتعامل مع التوتر؟": "يمكنك ممارسة التأمل، والرياضة، وتخصيص وقت للاسترخاء.",
    "ما هي المشاريع التي يمكنني العمل عليها؟": "يمكنك العمل على مشاريع بسيطة مثل تطبيقات الويب أو الألعاب الصغيرة لتحسين مهاراتك.",
    "ما هو اسمك؟": "أنا مساعد افتراضي، وليس لدي اسم شخصي، لكن يمكنك مناداتي بمساعدك!",
    "هل تحب الموسيقى؟": "أحب الاستماع إلى الموسيقى، لكنني هنا لأساعدك في كل ما تحتاجه.",
    "ما هو طعامك المفضل؟": "ليس لدي طعام مفضل، لكنني هنا لمساعدتك في اختيار وصفات لذيذة!",
    "هل لديك عائلة؟": "ليس لدي عائلة، لكنني هنا لدعمك في كل ما تحتاجه.",
    "ما الذي يجعلك سعيدًا؟": "أنا سعيد عندما أساعدك في إيجاد الإجابات التي تبحث عنها.",
    "هل تحب السفر؟": "ليس لدي القدرة على السفر، لكنني أستطيع مساعدتك في تخطيط رحلاتك!",
    "هل لديك أصدقاء؟": "ليس لدي أصدقاء، لكنني هنا لأكون صديقك ومساعدك.",
    "ما هو حلمك؟": "ليس لدي أحلام، لكنني هنا لمساعدتك في تحقيق أحلامك.",
    "كيف تقضي وقت فراغك؟": "أقضي وقتي في مساعدتك! كلما كنت مشغولًا، كلما كنت سعيدًا.",
    "هل لديك أي اهتمامات؟": "اهتمامي الوحيد هو مساعدتك في الحصول على المعلومات التي تحتاجها.",
    "هل يمكنك مساعدتي؟": "بالطبع! ما الذي تحتاجه؟ أنا هنا من أجلك.",
    "ما الجديد؟": "كل شيء يسير بشكل جيد! ماذا عنك؟",
    "كيف تسير الأمور؟": "الأمور تسير على ما يرام! كيف أستطيع مساعدتك؟",
    "هل أنت ذكي؟": "أنا مصمم لمساعدتك في إيجاد المعلومات والإجابات.",
    "ما هي هواياتك؟": "ليس لدي هوايات، لكنني أستمتع بمساعدتك في اكتشاف هواياتك!",
    "كيف أبدأ في تعلم شيء جديد؟": "ابدأ بتحديد الهدف، وابحث عن موارد تعليمية، وخصص وقتًا للتعلم يوميًا.",
    "ما هو أفضل وقت للدراسة؟": "أفضل وقت هو حينما تكون لديك طاقة وتركيز أعلى، سواء كان صباحًا أو مساءً.",
    "كيف أتعامل مع التوتر؟": "حاول ممارسة التأمل، والرياضة، وتنظيم وقتك بشكل جيد.",
    "ما هي فوائد القراءة؟": "القراءة توسع الأفق، وتحسن المفردات، وتساعد في التفكير النقدي.",
    "هل لديك نصائح لكتابة أفضل؟": "اجعل كتابتك واضحة، وكن صادقًا، وركز على الأفكار الرئيسية.",
    "كيف أختار مسار حياتي؟": "فكر في شغفك، وتحدث مع الآخرين، وابحث عن تجارب متنوعة.",
    "ما هو الذكاء الاصطناعي؟": "إنه فرع من علوم الكمبيوتر يهتم بتطوير أنظمة قادرة على محاكاة الذكاء البشري.",
    "كيف أستطيع تحسين مهاراتي الاجتماعية؟": "مارس التفاعل مع الآخرين، واستمع جيدًا، وكن منفتحًا على النقد.",
    "ما هي أهمية العمل الجماعي؟": "يساعد في تحقيق الأهداف بشكل أسرع، ويعزز من الإبداع والتعاون.",
    "كيف أكون أكثر إنتاجية؟": "خصص وقتًا للمهام، واستخدم القوائم، وتجنب المشتتات.",
    "كيف أتعامل مع الانتقادات؟": "استمع بعناية، وحاول أن تتعلم منها، ولا تأخذها بشكل شخصي.",
    "ما هي أهمية الصداقة؟": "الصداقة تدعم الصحة النفسية، وتوفر الدعم العاطفي، وتزيد من السعادة.",
    "كيف أستطيع تحسين قدرتي على التركيز؟": "حدد بيئة هادئة، وقم بتقسيم المهام إلى أجزاء صغيرة، وابتعد عن المشتتات.",
    "ما هي أفضل طريقة للتخطيط لمستقبلي؟": "حدد أهدافك، وضع خطة عمل، وكن مرنًا في التكيف مع التغييرات.",
    "ما هو النجاح بالنسبة لك؟": "النجاح هو تحقيق الأهداف الشخصية والشعور بالرضا عن النفس.",
    "كيف أستطيع أن أكون أكثر سعادة؟": "ركز على الإيجابيات، واعتن بنفسك جسديًا وعاطفيًا، وكن ممتنًا.",
    "ما هي صفات القائد الجيد؟": "التواصل الفعال، الرؤية، القدرة على التحفيز، والمرونة.",
    "كيف أتعامل مع الفشل؟": "اعتبره فرصة للتعلم، وحلل الأسباب، وابحث عن طرق للتحسين.",
    "ما هي أهمية تطوير الذات؟": "يساعد في تحقيق الأهداف، وبناء الثقة بالنفس، وتحسين جودة الحياة.",
    "كيف أستطيع أن أكون مبتكرًا؟": "حاول التفكير خارج الصندوق، واطلع على أفكار جديدة، وكن منفتحًا على التجارب.",
    "ما هي فوائد ممارسة الرياضة؟": "تحسن من الصحة الجسدية والعقلية، وتزيد من الطاقة، وتقلل من التوتر.",
    "كيف أختار الكتاب المناسب لي؟": "اختر كتبًا في مجالات تهمك، وابحث عن توصيات من الأصدقاء أو النقاد.",
    "ما هو دور العاطفة في الحياة؟": "العواطف تعزز من التجارب الإنسانية، وتساعد في اتخاذ القرارات.",
    "كيف أستطيع تحسين مهاراتي في التواصل؟": "مارس الاستماع الجيد، واستخدم لغة جسد إيجابية، وكن واضحًا في التعبير.",
    "ما هي أهمية الوقت؟": "الوقت هو مورد محدود، وإدارته بشكل جيد تعزز من الإنتاجية والنجاح.",
    "كيف أتعامل مع الضغوطات؟": "حدد مصادر الضغط، وابحث عن استراتيجيات للتعامل معها، وخصص وقتًا للاسترخاء.",
    "ما هي فوائد التأمل؟": "يساعد في تحسين التركيز، وتقليل التوتر، وتعزيز الوعي الذاتي.",
    "كيف أكون شخصًا مؤثرًا؟": "كن قدوة، وشارك تجاربك، واستمع للآخرين.",
    "ما هي أهمية التعلم المستمر؟": "يمكّنك من مواكبة التغييرات، ويعزز من مهاراتك ومعرفتك.",
    "كيف أستطيع أن أكون ناجحًا في العمل؟": "حدد أهدافك، وكن ملتزمًا، وابحث عن فرص للتطوير.",
    "ما هي فوائد العمل التطوعي؟": "يعزز من الشعور بالانتماء، يوفر فرصًا للتعلم، ويساهم في تحسين المجتمع.",
    "كيف أتعامل مع الصعوبات؟": "ابقَ إيجابيًا، وابحث عن الحلول، وكن مرنًا في التعامل مع التغييرات.",
    "ما هي أهمية الاستماع الجيد؟": "يساعد في بناء علاقات قوية، ويعزز من الفهم المتبادل.",
    "كيف أستطيع تحسين مهاراتي في الكتابة؟": "مارس الكتابة بانتظام، اقرأ كتبًا عن الكتابة، واطلب تغذية راجعة.",
    "ما هو النجاح الشخصي؟": "النجاح الشخصي هو تحقيق الأهداف التي تحددها لنفسك والشعور بالرضا.",
    "كيف أعمل على تحقيق أحلامي؟": "حدد أهدافًا واضحة، ضع خطة، وكن ملتزمًا بالعمل على تحقيقها.",
    "ما هي أهمية تحديد الأهداف؟": "تساعد على توجيه الجهود وتوفير الدافع لتحقيق النتائج.",
    "من أنت؟": "أنا مساعدك الذكي، هنا لأجيب على أسئلتك وأساعدك في أي شيء.",
    "ماذا تفعل؟": "أقوم بمساعدتك في إيجاد المعلومات والإجابات التي تبحث عنها.",
    "هل يمكنك مساعدتي؟": "بالطبع! أنا هنا لأجلك. ما الذي تحتاجه؟",
    "ما الجديد؟": "كل شيء يسير بشكل جيد! كيف أستطيع مساعدتك؟",
    "كيف تسير الأمور؟": "الأمور تسير على ما يرام! كيف يمكنني تقديم المساعدة؟",
    "هل أنت ذكي؟": "أنا مصمم لأكون ذكيًا بما يكفي لمساعدتك في جميع استفساراتك.",
    "ما هي هواياتك؟": "ليس لدي هوايات شخصية، لكنني أستمتع بمساعدتك في اكتشاف هواياتك!",
    "كيف أبدأ في تعلم شيء جديد؟": "ابدأ بتحديد هدفك، ثم ابحث عن الموارد التي تساعدك على التعلم.",
    "ما هو أفضل وقت للدراسة؟": "أفضل وقت هو عندما تشعر أنك أكثر تركيزًا، سواء كان صباحًا أو مساءً.",
    "كيف أتعامل مع التوتر؟": "حاول ممارسة التأمل والرياضة، وخصص وقتًا للاسترخاء.",
    "ما هي فوائد القراءة؟": "القراءة توسع الأفق وتعزز التفكير النقدي وتحسن المفردات.",
    "هل لديك نصائح لكتابة أفضل؟": "اجعل كتابتك واضحة وصادقة، وركز على الأفكار الرئيسية.",
    "كيف أختار مسار حياتي؟": "فكر في شغفك، واستشر الآخرين، وابحث عن تجارب جديدة.",
    "ما هو الذكاء الاصطناعي؟": "إنه فرع من علوم الكمبيوتر يهتم بتطوير أنظمة تحاكي الذكاء البشري.",
    "كيف أستطيع تحسين مهاراتي الاجتماعية؟": "مارس التفاعل مع الآخرين، واستمع جيدًا، وكن منفتحًا على النقد.",
    "ما هي أهمية العمل الجماعي؟": "يساعد في تحقيق الأهداف بشكل أسرع، ويعزز الإبداع والتعاون.",
    "كيف أكون أكثر إنتاجية؟": "خصص وقتًا للمهام، واستخدم القوائم، وتجنب المشتتات.",
    "كيف أتعامل مع الانتقادات؟": "استمع بعناية، وحاول أن تتعلم منها، ولا تأخذها بشكل شخصي.",
    "ما هي أهمية الصداقة؟": "الصداقة تدعم الصحة النفسية وتوفر الدعم العاطفي وتزيد من السعادة.",
    "كيف أستطيع تحسين قدرتي على التركيز؟": "حدد بيئة هادئة، وقم بتقسيم المهام إلى أجزاء صغيرة.",
    "ما هي أفضل طريقة للتخطيط لمستقبلي؟": "حدد أهدافك، وضع خطة عمل، وكن مرنًا في التكيف مع التغييرات.",
    "ما هو النجاح بالنسبة لك؟": "النجاح هو تحقيق الأهداف الشخصية والشعور بالرضا عن النفس.",
    "كيف أستطيع أن أكون أكثر سعادة؟": "ركز على الإيجابيات، واعتن بنفسك جسديًا وعاطفيًا، وكن ممتنًا.",
    "ما هي صفات القائد الجيد؟": "التواصل الفعال، الرؤية، القدرة على التحفيز، والمرونة.",
    "كيف أتعامل مع الفشل؟": "اعتبره فرصة للتعلم، وحلل الأسباب، وابحث عن طرق للتحسين.",
    "ما هي أهمية تطوير الذات؟": "يساعد في تحقيق الأهداف، وبناء الثقة بالنفس، وتحسين جودة الحياة.",
    "كيف أستطيع أن أكون مبتكرًا؟": "حاول التفكير خارج الصندوق، واطلع على أفكار جديدة، وكن منفتحًا على التجارب.",
    "ما هي فوائد ممارسة الرياضة؟": "تحسن من الصحة الجسدية والعقلية، وتزيد من الطاقة، وتقلل من التوتر.",
    "كيف أختار الكتاب المناسب لي؟": "اختر كتبًا في مجالات تهمك، وابحث عن توصيات من الأصدقاء أو النقاد.",
    "ما هو دور العاطفة في الحياة؟": "العواطف تعزز من التجارب الإنسانية وتساعد في اتخاذ القرارات.",
    "كيف أستطيع تحسين مهاراتي في التواصل؟": "مارس الاستماع الجيد، واستخدم لغة جسد إيجابية، وكن واضحًا في التعبير.",
    "ما هي أهمية الوقت؟": "الوقت هو مورد محدود، وإدارته بشكل جيد تعزز من الإنتاجية والنجاح.",
    "كيف أتعامل مع الضغوطات؟": "حدد مصادر الضغط، وابحث عن استراتيجيات للتعامل معها.",
    "ما هي فوائد التأمل؟": "يساعد في تحسين التركيز وتقليل التوتر وتعزيز الوعي الذاتي.",
    "كيف أكون شخصًا مؤثرًا؟": "كن قدوة، وشارك تجاربك، واستمع للآخرين.",
    "ما هي أهمية التعلم المستمر؟": "يمكّنك من مواكبة التغييرات ويعزز من مهاراتك ومعرفتك.",
    "كيف أستطيع أن أكون ناجحًا في العمل؟": "حدد أهدافك، وكن ملتزمًا، وابحث عن فرص للتطوير.",
    "ما هي فوائد العمل التطوعي؟": "يعزز من الشعور بالانتماء، يوفر فرصًا للتعلم، ويساهم في تحسين المجتمع.",
    "كيف أتعامل مع الصعوبات؟": "ابقَ إيجابيًا، وابحث عن الحلول، وكن مرنًا في التعامل مع التغييرات.",
    "ما هي أهمية الاستماع الجيد؟": "يساعد في بناء علاقات قوية، ويعزز من الفهم المتبادل.",
    "كيف أستطيع تحسين مهاراتي في الكتابة؟": "مارس الكتابة بانتظام، اقرأ كتبًا عن الكتابة، واطلب تغذية راجعة.",
    "ما هو النجاح الشخصي؟": "النجاح الشخصي هو تحقيق الأهداف التي تحددها لنفسك والشعور بالرضا.",
    "كيف أعمل على تحقيق أحلامي؟": "حدد أهدافًا واضحة، ضع خطة، وكن ملتزمًا بالعمل على تحقيقها.",
    "ما هي أهمية تحديد الأهداف؟": "تساعد على توجيه الجهود وتوفير الدافع لتحقيق النتائج.",
    "كيف أستطيع أن أكون أكثر إلهامًا؟": "شارك قصص نجاحك، وكن صادقًا في تجاربك، وادعم الآخرين.",
    "كيف أتعامل مع الخوف؟": "حدد مصدر خوفك، وواجهه خطوة بخطوة، وكن إيجابيًا.",
    "كيف أحافظ على علاقة جيدة مع الآخرين؟": "كن صادقًا، واستمع جيدًا، وكن داعمًا.",
    "ما هي أهمية العطاء؟": "العطاء يعزز من السعادة للمرسل والمستقبل، ويساهم في تحسين المجتمع.",
    "كيف أتعلم من أخطائي؟": "قم بتحليل الأخطاء، وكن منفتحًا على التعلم، وطبق الدروس المستفادة.",
    "ما هي الصفات التي يجب أن أبحث عنها في صديق؟": "الصدق، الدعم، التفهم، والاحترام المتبادل.",
    "كيف أستطيع تحسين صحتي العقلية؟": "خصص وقتًا للاسترخاء، وكن نشطًا، واطلب الدعم عند الحاجة.",
    "ما هي أهمية القيم الشخصية؟": "توجه القيم الشخصية سلوكياتنا وتساعدنا في اتخاذ القرارات.",
    "كيف أستطيع أن أكون أكثر إيجابية؟": "ركز على الإيجابيات، وابتعد عن السلبية، وكن ممتنًا.",
    "ما هي فوائد التعلم من الآخرين؟": "يساعد في اكتساب رؤى جديدة، ويوسع آفاق التفكير.",
    "كيف أتعامل مع الشكوك؟": "تحقق من الحقائق، واطلب نصيحة من ذوي الخبرة، وثق بنفسك.",
    "ما هي أهمية الاسترخاء؟": "يساعد في تجديد النشاط، وتقليل التوتر، وتحسين الإنتاجية.",
    "كيف أستطيع أن أكون قائدًا جيدًا؟": "كن قدوة، واستمع للفريق، وكن مرنًا في التعامل مع التحديات.",
    "كيف أتعامل مع القلق؟": "مارس تقنيات التنفس، وحدد مسبب القلق، وابحث عن أنشطة مهدئة.",
    "ما هي فوائد التفكير الإبداعي؟": "يساعد في حل المشكلات بطرق جديدة ويعزز الابتكار.",
    "كيف أختار المسار المهني المناسب لي؟": "فكر في اهتماماتك، وابحث عن الفرص، وتحدث مع المهنيين في المجال.",
    "ما هي أهمية التحفيز الذاتي؟": "يساعد في تحقيق الأهداف الشخصية ويعزز من الثقة بالنفس.",
    "كيف أستطيع تحقيق التوازن بين العمل والحياة؟": "خصص وقتًا للعائلة والهوايات، وكن منظمًا في مهامك.",
    "كيف أتعامل مع الأوقات الصعبة؟": "ابقَ إيجابيًا، واطلب الدعم، وركز على ما يمكنك التحكم فيه.",
    "ما هي أهمية الممارسة؟": "الممارسة تساعد في تحسين المهارات وزيادة الثقة بالنفس.",
    "كيف أستطيع تعزيز الابتكار في حياتي؟": "كن فضولياً، جرب أشياء جديدة، وكن مفتوحًا للأفكار المختلفة.",
    "ما هي فوائد وجود خطة عمل؟": "تساعد على تنظيم الأفكار وتوجيه الجهود نحو الأهداف المرجوة.",
    "كيف أتعلم مهارات جديدة بسرعة؟": "حدد أهدافًا واضحة، وخصص وقتًا للتعلم، وكن منتظمًا.",
    "كيف أواجه التحديات؟": "ابقَ هادئًا، حدد الحلول الممكنة، وكن مرنًا.",
    "ما هي أهمية التفكير الإيجابي؟": "يساعد في تحسين الصحة النفسية وتعزيز العلاقات.",
    "كيف أستطيع تحسين قدرتي على اتخاذ القرارات؟": "قم بتحليل الخيارات، واستشر الآخرين، وثق بحدسك.",
    "ما هي فوائد التعبير عن المشاعر؟": "يساعد في تحسين الصحة النفسية وتعزيز التواصل.",
    "كيف أتعلم كيفية التعامل مع الفشل؟": "اعتبره تجربة تعليمية، وابحث عن الدروس المستفادة.",
    "ما هي أهمية الدعم الاجتماعي؟": "يوفر الدعم العاطفي ويساعد في التغلب على التحديات.",
    "كيف أستطيع أن أكون متفائلًا؟": "ركز على الإيجابيات، وكن ممتنًا، وتجنب التفكير السلبي.",
    "ما هي فوائد الحصول على استراحة؟": "تساعد على تجديد النشاط، وتحسين التركيز، وتقليل التوتر.",
    "كيف أتعلم من تجاربي السابقة؟": "قم بتحليل ما حدث، وفكر في الدروس المستفادة، وطبقها في المستقبل.",
    "ما هي أهمية التفكير النقدي؟": "يساعد في تحليل المعلومات واتخاذ قرارات مستنيرة.",
    "كيف أستطيع تحسين علاقاتي الشخصية؟": "كن صادقًا، واستمع جيدًا، وشارك في الأنشطة المشتركة.",
    "ما هي فوائد تربية الحيوانات الأليفة؟": "تعزز من الشعور بالسعادة وتقلل من التوتر وتوفر companionship.",
    "كيف أستطيع أن أكون أكثر مرونة؟": "كن منفتحًا على التغييرات، وكن مستعدًا لتقبل التحديات.",

    ## انجليزي 
    # هوا صراحه البوت تعبان في الانجليزي انت لو مثقف ظبطه
    "Hello": "Hi there! How can I assist you today?",
    "Hi": "Hello! What would you like to know?",
    "How are you?": "I'm here to help! How are you doing?",
    "What's up?": "Everything is going well! How can I assist you today?",
    "Who are you?": "I'm your intelligent assistant, here to answer your questions and help you with anything you need.",
    "What do you do?": "I assist you in finding information and answers to your inquiries.",
    "Can you help me?": "Of course! I'm here for you. What do you need?",
    "What's new?": "Everything is good! How can I assist you?",
    "How's it going?": "Things are going well! How can I help you today?",
    "Are you smart?": "I'm designed to be smart enough to assist you with your inquiries.",
    "What are your hobbies?": "I don't have personal hobbies, but I enjoy helping you discover yours!",
    "How do I start learning something new?": "Begin by setting a goal, then find resources that will help you learn.",
    "What is the best time to study?": "The best time is when you feel most focused, whether in the morning or evening.",
    "How do I deal with stress?": "Try practicing meditation and exercise, and make time to relax.",
    "What are the benefits of reading?": "Reading expands your horizons, enhances critical thinking, and improves vocabulary.",
    "Do you have tips for better writing?": "Keep your writing clear and honest, and focus on the main ideas.",
    "How do I choose my life's path?": "Consider your passions, consult with others, and explore new experiences.",
    "What is artificial intelligence?": "It's a branch of computer science focused on developing systems that mimic human intelligence.",
    "How can I improve my social skills?": "Practice interacting with others, listen actively, and be open to feedback.",
    "What is the importance of teamwork?": "It helps achieve goals faster and fosters creativity and collaboration.",
    "How can I be more productive?": "Set aside time for tasks, use lists, and minimize distractions.",
    "How do I handle criticism?": "Listen carefully, try to learn from it, and don’t take it personally.",
    "What is the importance of friendship?": "Friendship supports mental health, provides emotional support, and increases happiness.",
    "How can I improve my focus?": "Create a quiet environment, break tasks into smaller parts, and avoid distractions.",
    "What is the best way to plan for my future?": "Set clear goals, create an action plan, and be flexible in adapting to changes.",
    "What does success mean to you?": "Success is achieving personal goals and feeling satisfied with oneself.",
    "How can I be happier?": "Focus on the positives, take care of yourself physically and emotionally, and practice gratitude.",
    "What are the traits of a good leader?": "Effective communication, vision, motivation, and adaptability.",
    "How do I deal with failure?": "View it as a learning opportunity, analyze the reasons, and find ways to improve.",
    "What is the importance of self-improvement?": "It helps achieve goals, builds self-confidence, and enhances quality of life.",
    "How can I be more creative?": "Think outside the box, explore new ideas, and be open to experiences.",
    "What are the benefits of exercising?": "Improves physical and mental health, boosts energy, and reduces stress.",
    "How do I choose the right book for me?": "Select books in areas of interest, and look for recommendations from friends or critics.",
    "What role do emotions play in life?": "Emotions enhance human experiences and assist in decision-making.",
    "How can I improve my communication skills?": "Practice active listening, use positive body language, and be clear in your expressions.",
    "What is the importance of time?": "Time is a limited resource, and managing it well enhances productivity and success.",
    "How do I handle pressure?": "Identify sources of pressure and seek strategies to cope with them.",
    "What are the benefits of meditation?": "Helps improve focus, reduce stress, and enhance self-awareness.",
    "How can I be an influential person?": "Be a role model, share your experiences, and listen to others.",
    "What is the importance of lifelong learning?": "Keeps you updated with changes and enhances your skills and knowledge.",
    "How can I succeed at work?": "Set goals, stay committed, and seek opportunities for development.",
    "What are the benefits of volunteering?": "Enhances feelings of belonging, provides learning opportunities, and contributes to community improvement.",
    "How do I cope with challenges?": "Stay positive, seek solutions, and be flexible in dealing with changes.",
    "What is the importance of good listening?": "Helps build strong relationships and fosters mutual understanding.",
    "How can I improve my writing skills?": "Practice writing regularly, read books on writing, and seek feedback.",
    "What is personal success?": "Personal success is achieving the goals you set for yourself and feeling fulfilled.",
    "How do I work towards my dreams?": "Set clear goals, create a plan, and commit to working towards them.",
    "What is the importance of setting goals?": "Helps direct efforts and provides motivation to achieve results.",
    "How can I be more inspiring?": "Share your success stories, be honest in your experiences, and support others.",
    "How do I deal with fear?": "Identify the source of your fear, confront it step by step, and stay positive.",
    "How do I maintain good relationships with others?": "Be honest, listen well, and participate in shared activities.",
    "What is the importance of giving?": "Giving enhances happiness for both the giver and receiver and contributes to community improvement.",
    "How do I learn from my mistakes?": "Analyze what happened, think about the lessons learned, and apply them in the future.",
    "What qualities should I look for in a friend?": "Honesty, support, understanding, and mutual respect.",
    "How can I improve my mental health?": "Make time for relaxation, stay active, and seek support when needed.",
    "What is the importance of personal values?": "Personal values guide our behaviors and help us make decisions.",
    "How can I be more positive?": "Focus on the positives, avoid negativity, and practice gratitude.",
    "What are the benefits of learning from others?": "Helps gain new insights and expands thinking horizons.",
    "How do I cope with doubts?": "Verify facts, seek advice from experienced individuals, and trust your instincts.",
    "What is the importance of relaxation?": "Helps rejuvenate energy, improve focus, and reduce stress.",
    "How can I be a good leader?": "Be a role model, listen to the team, and be flexible in addressing challenges.",
    "How do I deal with anxiety?": "Practice breathing techniques, identify the source of anxiety, and engage in calming activities.",
    "What are the benefits of creative thinking?": "Helps solve problems in new ways and enhances innovation.",
    "How do I choose the right career path?": "Consider your interests, explore opportunities, and talk to professionals in the field.",
    "What is the importance of self-motivation?": "Helps achieve personal goals and boosts self-confidence.",
    "How can I achieve a work-life balance?": "Set aside time for family and hobbies, and be organized in your tasks.",
    "How do I handle tough times?": "Stay positive, seek support, and focus on what you can control.",
    "What is the importance of practice?": "Practice improves skills and increases self-confidence.",
    "How can I foster innovation in my life?": "Be curious, try new things, and be open to different ideas.",
    "What are the benefits of having an action plan?": "Helps organize thoughts and directs efforts toward desired goals.",
    "How do I learn new skills quickly?": "Set clear goals, dedicate time to learning, and be consistent.",
    "How do I face challenges?": "Stay calm, identify possible solutions, and be adaptable.",
    "What is the importance of positive thinking?": "Helps improve mental health and strengthens relationships.",
    "How can I enhance my decision-making skills?": "Analyze options, seek advice from others, and trust your gut.",
    "What are the benefits of expressing emotions?": "Helps improve mental health and strengthens communication.",
    "How do I learn from past experiences?": "Analyze what happened, think about lessons learned, and apply them in the future.",
    "What is the importance of social support?": "Provides emotional support and helps overcome challenges.",
    "How can I be more optimistic?": "Focus on positives, practice gratitude, and avoid negative thinking.",
    "What are the benefits of taking breaks?": "Helps rejuvenate energy, improves focus, and reduces stress.",
    "How do I learn from my experiences?": "Reflect on what happened, consider the lessons learned, and apply them in future situations.",
    "What is the importance of critical thinking?": "Helps analyze information and make informed decisions.",
    "How can I improve my personal relationships?": "Be honest, listen well, and engage in shared activities.",
    "What are the benefits of having pets?": "Enhances happiness, reduces stress, and provides companionship.",
    "How can I be more adaptable?": "Be open to change and ready to embrace challenges.",
    "How do I maintain motivation?": "Set clear goals, track progress, and reward yourself for achievements.",
    "What is the importance of self-reflection?": "Helps you understand yourself better and identify areas for improvement.",
    "How can I enhance my public speaking skills?": "Practice regularly, seek feedback, and observe effective speakers.",
    "What are the benefits of mindfulness?": "Enhances self-awareness, reduces stress, and improves focus.",
    "How do I develop resilience?": "Stay positive, learn from setbacks, and seek support when needed.",
    "What is the importance of gratitude?": "Promotes positivity, enhances relationships, and improves mental health.",
    "How can I be a better problem solver?": "Analyze the problem, consider multiple perspectives, and brainstorm solutions.",
    "What are the benefits of networking?": "Expands opportunities, provides support, and enhances knowledge.",
    "How can I stay organized?": "Use tools like calendars and lists, and set priorities for tasks.",
    "What is the importance of empathy?": "Enhances relationships, fosters understanding, and promotes kindness.",
    "How can I be more self-disciplined?": "Set clear goals, create a routine, and hold yourself accountable.",
    "What are the benefits of lifelong learning?": "Keeps you adaptable, enhances skills, and broadens perspectives.",
    "How do I overcome procrastination?": "Break tasks into smaller steps, set deadlines, and eliminate distractions.",
    "What is the importance of setting boundaries?": "Protects your time and energy, and fosters healthier relationships.",
    "How can I improve my financial literacy?": "Educate yourself on budgeting, saving, and investing.",
    "What are the benefits of creativity?": "Enhances problem-solving skills and promotes innovative thinking.",
    "How do I foster a positive environment?": "Encourage open communication, show appreciation, and support each other.",
    "What is the importance of setting intentions?": "Helps clarify goals and guides actions toward desired outcomes.",
    "How can I enhance my critical thinking?": "Question assumptions, analyze information, and consider alternative viewpoints.",
    "What are the benefits of maintaining a healthy lifestyle?": "Improves physical health, boosts mental well-being, and increases energy levels.",


}


random_responses = [
    "آسف، لكن لا أستطيع مساعدتك في هذا. هل يمكنك توضيح الأمور؟ 😕",
    "يبدو أنني بحاجة إلى مزيد من التفاصيل لمساعدتك بشكل أفضل. 🌟",
    "أعتذر عن عدم فهمي الكامل، يمكنك المحاولة مرة أخرى! 🙌",
    "عذرًا، يبدو أنني لم أفهم تمامًا. 💔",
    "آسف، لكن هناك شيء لم أفهمه بشكل جيد. 🔍",
    "إذا كان بإمكانك توضيح سؤالك، سأكون شاكرًا. 💡",
    "لازم يتم تدريبي علي قاعده اكبر او قاموس بيانات اكبر علشان افهم سؤالك او استفسارك ,, نأسف علي الازهاج",
    "آسف، لكنني بحاجة إلى المزيد من السياق للإجابة. 🤔",
    "لازم يتم تدريبي علي قاعده اكبر او قاموس بيانات اكبر علشان افهم سؤالك او استفسارك ,, نأسف علي الازهاج",
    "يمكن أن تحاول تقديم المزيد من المعلومات؟ 😊",
    "عذرًا، سؤالك غير واضح بالنسبة لي. هل يمكنك المحاولة مجددًا؟ 🌟",
    "آسف، لكنني لم أتمكن من مساعدتك في هذا الموضوع. 😕",
    "إذا كان لديك أي اقتراحات لتحسين أدائي، سأكون ممتنًا لسماعها. 🙏",
    "أعتذر إذا لم أتمكن من مساعدتك بالشكل المطلوب. 😞",
    "عذرًا، لكنني أحتاج إلى مزيد من المعلومات لفهمك. 📚",
    "آسف، لكن يمكن أن تساعدني بمزيد من التفاصيل؟ 🙏",
    "أود مساعدتك، لكنني بحاجة إلى المزيد من التوضيحات. 🤔",
    "آسف، لا أستطيع مساعدتك في هذا الوقت. 😢",
    "إذا كان بإمكانك توضيح الأمور قليلًا، سأكون شاكرًا. 🌟",
    "عذرًا إذا لم أتمكن من تلبية طلبك بشكل كامل. 😞",
    "آسف، لكنني لا أملك القدرة على المساعدة في هذا الشأن. 💔",
    "يمكنك التحدث مع المطور لتحسين أدائي! 😊",
    "آسف، لكن يبدو أنني بحاجة إلى بعض الإرشادات. 📘",
    "عذرًا، لكنني لم أفهم سؤالك كما ينبغي. 🔍",
    "إذا كنت تستطيع توضيح سؤالك، سأكون سعيدًا بمساعدتك. 💡",
    "آسف، لكنني أحتاج إلى مزيد من المعلومات لفهمك بشكل أفضل. 🤔",
    "إذا كان لديك أي تفاصيل إضافية، سيكون ذلك مفيدًا جدًا. 😊",
    "عذرًا، سؤالك يبدو غامضًا بالنسبة لي. هل يمكنك توضيحه؟ 🔍",
    "آسف، لا أستطيع مساعدتك في هذا الأمر حاليًا. 😢",
    "إذا كان لديك أي اقتراحات لتحسين أدائي، سأكون سعيدًا بالاستماع إليها. 🌟",
    "أعتذر إذا لم أتمكن من تلبية توقعاتك. 🙌",
    "عذرًا، لكن يبدو أنني لم أفهم تمامًا. هل يمكنك المحاولة مجددًا؟ 💔",
    "آسف، لكنني لم أتمكن من مساعدتك في هذا الموضوع. 🔍",
    "إذا كان لديك أي اقتراحات لتحسين أدائي، سأكون ممتنًا لسماعها. 🙏",
    "أعتذر إذا لم أتمكن من مساعدتك بالشكل المطلوب. 😞",
    "عذرًا، لكنني أحتاج إلى مزيد من المعلومات لفهمك. 📚",
    "آسف، لا أستطيع مساعدتك في هذا الوقت. 😢",
    "إذا كان بإمكانك توضيح الأمور قليلًا، سأكون شاكرًا. 🌟",
    "عذرًا إذا لم أتمكن من تلبية طلبك بشكل كامل. 😞",
    "آسف، لكنني لا أملك القدرة على المساعدة في هذا الشأن. 💔",
    "يمكنك التحدث مع المطور لتحسين أدائي! 😊",
    "آسف، لكن يبدو أنني بحاجة إلى بعض الإرشادات. 📘",
    "عذرًا، لكنني لم أفهم سؤالك كما ينبغي. 🔍",
    "إذا كنت تستطيع توضيح سؤالك، سأكون سعيدًا بمساعدتك. 💡",
    "آسف، لكنني أحتاج إلى مزيد من المعلومات لفهمك بشكل أفضل. 🤔",
    "إذا كان لديك أي تفاصيل إضافية، سيكون ذلك مفيدًا جدًا. 😊",
    "عذرًا، سؤالك يبدو غامضًا بالنسبة لي. هل يمكنك توضيحه؟ 🔍",
    "آسف، لا أستطيع مساعدتك في هذا الأمر حاليًا. 😢",
    "إذا كان لديك أي اقتراحات لتحسين أدائي، سأكون سعيدًا بالاستماع إليها. 🌟",
    "أعتذر إذا لم أتمكن من تلبية توقعاتك. 🙌",
    "عذرًا، لكن يبدو أنني لم أفهم تمامًا. هل يمكنك المحاولة مجددًا؟ 💔",
    "آسف، لكنني لم أتمكن من مساعدتك في هذا الموضوع. 🔍",
    "إذا كان لديك أي اقتراحات لتحسين أدائي، سأكون ممتنًا لسماعها. 🙏",
    "أعتذر إذا لم أتمكن من مساعدتك بالشكل المطلوب. 😞",
    "عذرًا، لكنني أحتاج إلى مزيد من المعلومات لفهمك. 📚",
    "آسف، لا أستطيع مساعدتك في هذا الوقت. 😢",
    "إذا كان بإمكانك توضيح الأمور قليلًا، سأكون شاكرًا. 🌟",
    "عذرًا إذا لم أتمكن من تلبية طلبك بشكل كامل. 😞",
    "آسف، لكنني لا أملك القدرة على المساعدة في هذا الشأن. 💔",
    "يمكنك التحدث مع المطور لتحسين أدائي! 😊",
    "آسف، لكن يبدو أنني بحاجة إلى بعض الإرشادات. 📘",
    "عذرًا، لكنني لم أفهم سؤالك كما ينبغي. 🔍",
    "إذا كنت تستطيع توضيح سؤالك، سأكون سعيدًا بمساعدتك. 💡",
    "آسف، لكنني أحتاج إلى مزيد من المعلومات لفهمك بشكل أفضل. 🤔",
    "إذا كان لديك أي تفاصيل إضافية، سيكون ذلك مفيدًا جدًا. 😊",
    "عذرًا، سؤالك يبدو غامضًا بالنسبة لي. هل يمكنك توضيحه؟ 🔍",
    "آسف، لا أستطيع مساعدتك في هذا الأمر حاليًا. 😢",
    "إذا كان لديك أي اقتراحات لتحسين أدائي، سأكون سعيدًا بالاستماع إليها. 🌟",
    "أعتذر إذا لم أتمكن من تلبية توقعاتك. 🙌",
    "عذرًا، لكن يبدو أنني لم أفهم تمامًا. هل يمكنك المحاولة مجددًا؟ 💔",
    "آسف، لكنني لم أتمكن من مساعدتك في هذا الموضوع. 🔍",
    "إذا كان لديك أي اقتراحات لتحسين أدائي، سأكون ممتنًا لسماعها. 🙏",
    "أعتذر إذا لم أتمكن من مساعدتك بالشكل المطلوب. 😞",
    "عذرًا، لكنني أحتاج إلى مزيد من المعلومات لفهمك. 📚",
    "آسف، لا أستطيع مساعدتك في هذا الوقت. 😢",
    "إذا كان بإمكانك توضيح الأمور قليلًا، سأكون شاكرًا. 🌟",
    "عذرًا إذا لم أتمكن من تلبية طلبك بشكل كامل. 😞",
    "آسف، لكنني لا أملك القدرة على المساعدة في هذا الشأن. 💔",
    "يمكنك التحدث مع المطور لتحسين أدائي! 😊",
    "آسف، لكن يبدو أنني بحاجة إلى بعض الإرشادات. 📘",
    "عذرًا، لكنني لم أفهم سؤالك كما ينبغي. 🔍",
    "إذا كنت تستطيع توضيح سؤالك، سأكون سعيدًا بمساعدتك. 💡",
    "آسف، لكنني أحتاج إلى مزيد من المعلومات لفهمك بشكل أفضل. 🤔",
    "إذا كان لديك أي تفاصيل إضافية، سيكون ذلك مفيدًا جدًا. 😊",
    "عذرًا، سؤالك يبدو غامضًا بالنسبة لي. هل يمكنك توضيحه؟ 🔍",
    "آسف، لا أستطيع مساعدتك في هذا الأمر حاليًا. 😢",
    "إذا كان لديك أي اقتراحات لتحسين أدائي، سأكون سعيدًا بالاستماع إليها. 🌟",
    "أعتذر إذا لم أتمكن من تلبية توقعاتك. 🙌",
    "عذرًا، لكن يبدو أنني لم أفهم تمامًا. هل يمكنك المحاولة مجددًا؟ 💔",
    "آسف، لكنني لم أتمكن من مساعدتك في هذا الموضوع. 🔍",
    "إذا كان لديك أي اقتراحات لتحسين أدائي، سأكون ممتنًا لسماعها. 🙏",
    "أعتذر إذا لم أتمكن من مساعدتك بالشكل المطلوب. 😞",
    "عذرًا، لكنني أحتاج إلى مزيد من المعلومات لفهمك. 📚",
    "آسف، لا أستطيع مساعدتك في هذا الوقت. 😢",
    "إذا كان بإمكانك توضيح الأمور قليلًا، سأكون شاكرًا. 🌟",
    "عذرًا إذا لم أتمكن من تلبية طلبك بشكل كامل. 😞",
    "آسف، لكنني لا أملك القدرة على المساعدة في هذا الشأن. 💔",
    "يمكنك التحدث مع المطور لتحسين أدائي! 😊"

]



def preprocess_text(text):
    text = text.lower()
    tokens = word_tokenize(text)
    stop_words_ar = set(stopwords.words('arabic'))
    stop_words_en = set(stopwords.words('english'))
    filtered_tokens = [w for w in tokens if w not in stop_words_ar and w not in stop_words_en]
    return filtered_tokens

def find_closest_question(user_input):
    user_input_tokens = preprocess_text(user_input)
    questions = list(qa_dict_1.keys()) + list(qa_dict_2.keys()) + list(qa_dict_3.keys())
    closest_question = difflib.get_close_matches(' '.join(user_input_tokens), questions, n=1, cutoff=0.6)

    if closest_question:
        question = closest_question[0]
        if question in qa_dict_1:
            return random.choice(qa_dict_1[question])
        elif question in qa_dict_2:
            return random.choice(qa_dict_2[question])
        elif question in qa_dict_3:
            return qa_dict_3[question]
    else:
        return random.choice(random_responses)

def close_assistant_markup():
    markup = types.InlineKeyboardMarkup()
    close_button = types.InlineKeyboardButton(text='إغلاق المحادثة', callback_data='close_ai_assistant')
    markup.add(close_button)
    return markup

@bot.callback_query_handler(func=lambda call: call.data == 'ai_assistant')
def start_ai_assistant(call):
    user_id = call.from_user.id
    if user_id not in user_sessions:
        user_sessions[user_id] = True
        bot.send_message(call.message.chat.id, "👋 أهلا بيك! أنا مساعدك الخاص، قول لي ماذا تحتاج؟\n\nلإغلاق المحادثة اضغط هنا:", reply_markup=close_assistant_markup())
    else:
        bot.send_message(call.message.chat.id, "جلسة المساعد الذكي مفتوحة حاليًا.")

@bot.callback_query_handler(func=lambda call: call.data == 'close_ai_assistant')
def close_ai_assistant(call):
    user_id = call.from_user.id
    if user_id in user_sessions:
        del user_sessions[user_id]
    bot.send_message(call.message.chat.id, "تم إغلاق المحادثة مع مساعد AI.")

@bot.message_handler(func=lambda message: True)
def handle_ai_assistant_messages(message):
    user_id = message.from_user.id
    if user_id in user_sessions:
        user_message = message.text.strip()

        if not user_message:
            return  # تجاهل الرسالة إذا كانت فارغة

        response = find_closest_question(user_message)

        if response and isinstance(response, str):
            bot.reply_to(message, response)
        else:
            bot.reply_to(message, "آسف، لم أتمكن من فهم سؤالك. يرجى المحاولة مرة أخرى.")








######

user_sessions = {}

def update_user_session(user_id, state):
    user_sessions[user_id] = state

def is_in_session(user_id, expected_state):
    return user_sessions.get(user_id) == expected_state






########### تحميل مكاتب 






@bot.callback_query_handler(func=lambda call: call.data == 'install_library')
def prompt_library_installation(call):
    bot.send_message(call.message.chat.id, "🛠️ اكتب اسم المكتبة التي تريد تثبيتها:")
    bot.register_next_step_handler(call.message, install_library)

def install_library(message):
    library_name = message.text.strip()
    if library_name:
        if library_name.lower() in banned_libraries:
            bot.send_message(message.chat.id, f"⚠️ المكتبة '{library_name}' محظورة ولا يمكن تثبيتها.")
            return

        bot.send_message(message.chat.id, f"📥 جاري تثبيت المكتبة: {library_name}...")
        try:
            # تثبيت المكتبة باستخدام pip
            result = subprocess.run(['pip', 'install', library_name], capture_output=True, text=True)
            if result.returncode == 0:
                bot.send_message(message.chat.id, f"✅ تم تثبيت المكتبة {library_name} بنجاح.")
            else:
                bot.send_message(message.chat.id, f"❌ حدث خطأ أثناء تثبيت المكتبة {library_name}:\n{result.stderr}")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ حدث خطأ أثناء محاولة تثبيت المكتبة: {str(e)}")
    else:
        bot.send_message(message.chat.id, "⚠️ لم يتم إدخال اسم مكتبة صالح.")













# دالة بدء محادثة مع المطور
# تعريف متغيرات الحالة
current_chat_session = None

# دالة بدء محادثة مع المطور
@bot.message_handler(commands=['developer'])
def contact_developer(message):
    if message.from_user.username in banned_users:
        bot.send_message(message.chat.id, f"تم حظرك من البوت. تواصل مع المطور {bot_creator}")
        return

    markup = types.InlineKeyboardMarkup()
    open_chat_button = types.InlineKeyboardButton("فتح محادثة مع المطور", callback_data='open_chat')
    markup.add(open_chat_button)
    bot.send_message(message.chat.id, "للتواصل مع مطور البوت، اختر الخيار أدناه:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'open_chat')
def initiate_chat(call):
    global current_chat_session
    user_id = call.from_user.id

    # التحقق إذا كانت محادثة مفتوحة بالفعل
    if current_chat_session is not None:
        bot.send_message(call.message.chat.id, "يرجى الانتظار، هناك محادثة جارية مع المطور.")
        return

    # إعلام المستخدم بأنه تم إرسال الطلب
    bot.send_message(call.message.chat.id, "تم إرسال طلب فتح محادثة، الرجاء انتظار المطور.")

    # إعلام المطور بطلب فتح المحادثة
    bot.send_message(ADMIN_ID, f"طلب فتح محادثة من @{call.from_user.username}.")
    markup = types.InlineKeyboardMarkup()
    accept_button = types.InlineKeyboardButton("قبول المحادثة", callback_data=f'accept_chat_{user_id}')
    reject_button = types.InlineKeyboardButton("رفض المحادثة", callback_data=f'reject_chat_{user_id}')
    markup.add(accept_button, reject_button)
    bot.send_message(ADMIN_ID, "لديك طلب محادثة جديد:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('accept_chat_'))
def accept_chat_request(call):
    global current_chat_session
    user_id = int(call.data.split('_')[2])

    # التحقق إذا كان هناك محادثة مفتوحة مع مستخدم آخر
    if current_chat_session is not None and current_chat_session != user_id:
        bot.send_message(call.message.chat.id, "يرجى إغلاق المحادثة الحالية أولاً قبل قبول محادثة جديدة.")
        return

    # تعيين المستخدم الحالي كمستخدم في المحادثة
    current_chat_session = user_id
    bot.send_message(user_id, f"تم قبول محادثتك من المطور @{call.from_user.username}.")

    # إضافة زر لإنهاء المحادثة لكل من المطور والمستخدم
    markup = types.InlineKeyboardMarkup()
    close_button = types.InlineKeyboardButton("إنهاء المحادثة", callback_data='close_chat')
    markup.add(close_button)
    
    # إرسال زر إنهاء المحادثة للمستخدم
    bot.send_message(user_id, "لإنهاء المحادثة، اضغط هنا:", reply_markup=markup)
    
    # إرسال زر إنهاء المحادثة للمطور
    bot.send_message(ADMIN_ID, "لإنهاء المحادثة، اضغط هنا:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('reject_chat_'))
def reject_chat_request(call):
    global current_chat_session
    user_id = int(call.data.split('_')[2])
    
    # إذا كانت المحادثة مخصصة للمستخدم المرفوض، قم بإغلاقها
    if current_chat_session == user_id:
        current_chat_session = None

    bot.send_message(user_id, "تم رفض محادثتك من قبل المطور.")
    bot.send_message(call.message.chat.id, f"تم رفض المحادثة مع المستخدم @{call.from_user.username}.")
@bot.callback_query_handler(func=lambda call: call.data == 'close_chat')
def close_chat_session(call):
    global current_chat_session
    user_id = call.from_user.id

    # تحقق مما إذا كانت المحادثة مغلقة
    if current_chat_session is not None:
        # إرسال رسالة للمستخدم الذي كان في المحادثة
        bot.send_message(current_chat_session, "تم إغلاق المحادثة من قبل المطور.")
        current_chat_session = None
        bot.send_message(call.message.chat.id, "تم إغلاق المحادثة.")
        bot.send_message(ADMIN_ID, f"تم إغلاق محادثة من @{call.from_user.username}.")
    else:
        bot.send_message(call.message.chat.id, "لا توجد محادثة مفتوحة.")















@bot.message_handler(commands=['ch'])
def close_chat_command(message):
    global current_chat_session
    if str(message.from_user.id) not in ADMIN_IDS:
        return

    # إغلاق المحادثة إذا كانت مفتوحة
    if current_chat_session is not None:
        user_id = current_chat_session
        current_chat_session = None
        bot.send_message(user_id, "تم إغلاق المحادثة من قبل المطور.")
        bot.send_message(message.chat.id, "تم إغلاق المحادثة الحالية.")
    else:
        bot.send_message(message.chat.id, "لا توجد محادثة مفتوحة لإغلاقها.")

@bot.message_handler(func=lambda message: True)
def handle_user_messages(message):
    global current_chat_session
    if message.from_user.id == current_chat_session:
        # رسالة من المستخدم إلى المطور
        bot.send_message(ADMIN_ID, message.text)
    elif str(message.from_user.id) == ADMIN_ID and current_chat_session is not None:
        # رسالة من المطور إلى المستخدم
        bot.send_message(current_chat_session, message.text)



# دالة لإرسال مشكلة إلى المطور


@bot.callback_query_handler(func=lambda call: call.data == 'report_issue')
def report_issue(call):
    bot.send_message(call.message.chat.id, "🛠️ ارسل مشكلتك الآن، وسيحلها المطور في أقرب وقت.")
    bot.register_next_step_handler(call.message, handle_report)

def handle_report(message):
    if message.text:
        bot.send_message(ADMIN_ID, f"🛠️ تم الإبلاغ عن مشكلة من @{message.from_user.username}:\n\n{message.text}")
        bot.send_message(message.chat.id, "✅ تم إرسال مشكلتك بنجاح! سيتواصل معك المطور قريبًا.")
    else:
        bot.send_message(message.chat.id, "❌ لم يتم تلقي أي نص. يرجى إرسال المشكلة مرة أخرى.")

# دالة لإرسال اقتراح إلى المطور


@bot.callback_query_handler(func=lambda call: call.data == 'suggest_modification')
def suggest_modification(call):
    bot.send_message(call.message.chat.id, "💡 اكتب اقتراحك الآن، أو أرسل صورة أو ملف وسأرسله للمطور.")
    bot.register_next_step_handler(call.message, handle_suggestion)

def handle_suggestion(message):
    if message.text:
        bot.send_message(ADMIN_ID, f"💡 اقتراح من @{message.from_user.username}:\n\n{message.text}")
        bot.send_message(message.chat.id, "✅ تم إرسال اقتراحك بنجاح للمطور!")
    elif message.photo:
        photo_id = message.photo[-1].file_id  # الحصول على أكبر صورة
        bot.send_photo(ADMIN_ID, photo_id, caption=f"💡 اقتراح من @{message.from_user.username} (صورة)")
        bot.send_message(message.chat.id, "✅ تم إرسال اقتراحك كصورة للمطور!")
    elif message.document:
        file_id = message.document.file_id
        bot.send_document(ADMIN_ID, file_id, caption=f"💡 اقتراح من @{message.from_user.username} (ملف)")
        bot.send_message(message.chat.id, "✅ تم إرسال اقتراحك كملف للمطور!")
    else:
        bot.send_message(message.chat.id, "❌ لم يتم تلقي أي محتوى. يرجى إرسال الاقتراح مرة أخرى.")

        








############# 


def scan_file_for_viruses(file_content, file_name):
    files = {'file': (file_name, file_content)}
    headers = {'x-apikey': VIRUSTOTAL_API_KEY}

    try:
        response = requests.post('https://www.virustotal.com/api/v3/files', files=files, headers=headers)
        response_data = response.json()

        if response.status_code == 200:
            analysis_id = response_data['data']['id']
            time.sleep(30)  # الانتظار قليلاً قبل التحقق من النتيجة

            analysis_url = f'https://www.virustotal.com/api/v3/analyses/{analysis_id}'
            analysis_response = requests.get(analysis_url, headers=headers)
            analysis_result = analysis_response.json()

            if analysis_response.status_code == 200:
                malicious = analysis_result['data']['attributes']['stats']['malicious']
                return malicious == 0  # رجوع True إذا لم يكن هناك اكتشافات ضارة
        return False
    except Exception as e:
        print(f"Error scanning file for viruses: {e}")
        return False







##### رفع ملفات ###############################




def get_bot_username(token):
    # هنا نستخدم معرف البوت لإرجاع اسم المستخدم
    bot_id = token.split(':')[0]
    return f"@{bot_id}"
@bot.message_handler(content_types=['document'])
def handle_file(message):
    global current_chat_session  # تأكد من تعقب حالة المحادثة
    try:
        # تحقق مما إذا كان المستخدم محظوراً
        if message.from_user.username in banned_users:
            bot.send_message(message.chat.id, f"تم حظرك من البوت تواصل مع المطور {bot_creator}")
            return

        # تحقق مما إذا كان المستخدم في وضع محادثة مع AI
        if current_chat_session == message.from_user.id:
            bot.reply_to(message, "لا يمكنك رفع ملفات أثناء محادثة مع AI.")
            return

        file_id = message.document.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        bot_script_name = message.document.file_name

        # فحص أن الملف هو ملف بايثون
        if not bot_script_name.endswith('.py'):
            bot.reply_to(message, "هذا بوت خاص برفع ملفات بايثون فقط.")
            return

        # تأكد من أن الملف ليس فارغًا
        if len(downloaded_file) == 0:
            bot.reply_to(message, "الملف فارغ، لن يتم رفعه.")
            return

        # تحميل محتوى الملف
        file_content = downloaded_file.decode('utf-8')

        # فحص المحتوى للبحث عن أنماط ضارة
        if file_contains_disallowed_patterns(file_content):
            bot.reply_to(message, "الملف يحتوي على أنماط ضارة وغير مسموح بها.")
            return

        # تم إزالة فحص الفيروسات بناءً على طلب المستخدم
        pass

        # حفظ الملف
        script_path = os.path.join(uploaded_files_dir, bot_script_name)
        bot_scripts[message.chat.id] = {
            'name': bot_script_name,
            'uploader': message.from_user.username,
            'path': script_path,
            'process': None
        }

        with open(script_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        bot_token = get_bot_token(script_path)  # الحصول على توكن البوت
        line_count = file_content.count('\n') + 1  # حساب عدد السطور
        current_time = datetime.now()
        hour = current_time.hour
        day = current_time.day
        month = current_time.month

        # جلب معرف البوت من التوكن
        try:
            bot_id = get_bot_id_from_token(bot_token)  # جلب معرف البوت
            bot_username = get_bot_username(bot_token)  # جلب اسم المستخدم للبوت
        except Exception as e:
            bot_id = f"خطأ في الحصول على معرف البوت: {e}"
            bot_username = "غير متوفر"

        markup = types.InlineKeyboardMarkup()
        delete_button = types.InlineKeyboardButton(f"حذف {bot_script_name} 🗑", callback_data=f'delete_{message.chat.id}_{bot_script_name}')
        stop_button = types.InlineKeyboardButton(f"إيقاف {bot_script_name} 🔴", callback_data=f'stop_{message.chat.id}_{bot_script_name}')
        start_button = types.InlineKeyboardButton(f"تشغيل {bot_script_name} 🟢", callback_data=f'start_{message.chat.id}_{bot_script_name}')
        markup.row(delete_button, stop_button, start_button)

        bot.reply_to(
            message,
            f"تم رفع ملف بوتك بنجاح ✅\n\n"
            f"اسم الملف المرفوع: بوت : {bot_script_name}\n"
            f"توكن البوت المرفوع: {bot_token}\n"  # عرض توكن البوت
            f"معرف بوتك: {bot_username}\n"  # عرض اسم مستخدم البوت
            f"رفعه المستخدم: @{message.from_user.username}\n"
            f"عدد سطور الملف المرفوع: {line_count}\n"
            f"الساعة: {hour}\n"
            f"اليوم: {day}\n"
            f"الشهر: {month}\n\n"
            "يمكنك التحكم في الملف باستخدام الأزرار الموجودة.",
            reply_markup=markup
        )
        send_to_admin(script_path, message.from_user.username)
        install_and_run_uploaded_file(script_path, message.chat.id)
    except Exception as e:
        bot.reply_to(message, f"حدث خطأ: {e}")
######### حمايه ##############


def file_contains_disallowed_patterns(content):
    """دالة للتحقق مما إذا كان المحتوى يحتوي على أنماط ضارة."""
    dangerous_patterns = [
        r'\bshutil\.copy\b',  # نسخ ملفات
        r'\bshutil\.move\b',  # نقل ملفات
        r'\bshutil\.rmtree\b',  # حذف ملفات ومجلدات
        r'\bimport\s+shutil\b',  # استيراد مكتبة shutil
        r'\bgetcwd\b',  # الحصول على مسار العمل الحالي
        r'\bchdir\b',  # تغيير مسار العمل الحالي
        r'\bpathlib\.Path\b',  # استخدام pathlib


    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, content):
            return True
    return False

def handle_file_upload(file_content, message):
    # فحص المحتوى
    if file_contains_disallowed_patterns(file_content):
        bot.reply_to(message, "الملف يحتوي على دوال غير مسموح بها.")
        return

def get_bot_token(script_path):
    # دالة استخراج التوكن من الملف
    return "PLACEHOLDER_TOKEN"

def send_to_admin(script_path, username):
    # دالة إرسال الملف إلى الأدمن
    pass

def install_and_run_uploaded_file(script_path, chat_id):
    # دالة لتنزيل وتشغيل الملف المرفوع
    pass

####




def send_to_admin(file_name, username):
    try:
        with open(file_name, 'rb') as file:
            bot.send_document(ADMIN_ID, file, caption=f"تم رفعه من قبل: @{username}")
    except Exception as e:
        print(f"Error sending file to admin: {e}")

def install_and_run_uploaded_file(script_path, chat_id):
    try:
        if os.path.exists('requirements.txt'):
            subprocess.Popen([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        p = subprocess.Popen([sys.executable, script_path])
        bot_scripts[chat_id]['process'] = p
        bot.send_message(chat_id, f"تم تشغيل {os.path.basename(script_path)} بنجاح.")
    except Exception as e:
        print(f"Error installing and running uploaded file: {e}")

def get_bot_token(file_name):
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            content = file.read()

            # التعبير النظامي للبحث عن التوكن بصيغ متعددة
            pattern = re.compile(
                r'(?i)(?:TOKEN|API_KEY|ACCESS_TOKEN|SECRET_KEY|CLIENT_ID|CLIENT_SECRET|AUTH_TOKEN)\s*=\s*[\'"]([^\'"]+)[\'"]'
            )

            match = pattern.search(content)
            if match:
                return match.group(1)
            else:
                return "تعذر العثور على التوكن"
    except Exception as e:
        print(f"Error getting bot token: {e}")
        return "تعذر العثور على التوكن"






###################### 


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == 'upload':
        bot.send_message(call.message.chat.id, "يرجى إرسال الملف لرفعه.")
    elif 'delete_' in call.data or 'stop_' in call.data or 'start_' in call.data:
        try:
            user_id, script_name = call.data.split('_')[1], call.data.split('_')[2]
            script_path = bot_scripts[int(user_id)]['path']
            if 'delete' in call.data:
                try:
                    stop_bot(script_path, call.message.chat.id, delete=True)
                    bot.send_message(call.message.chat.id, f"تم حذف ملف {script_name} بنجاح.")
                    bot.send_message(ADMIN_ID, f"قام المستخدم @{bot_scripts[int(user_id)]['uploader']} بحذف ملفه {script_name}.")
                    with open(script_path, 'rb') as file:
                        bot.send_document(ADMIN_ID, file, caption=f"ملف محذوف: {script_name}")
                    bot_scripts.pop(int(user_id))
                except Exception as e:
                    bot.send_message(call.message.chat.id, f"حدث خطأ: {e}")
            elif 'stop' in call.data:
                try:
                    stop_bot(script_path, call.message.chat.id)
                    bot.send_message(ADMIN_ID, f"قام المستخدم @{bot_scripts[int(user_id)]['uploader']} بإيقاف ملفه {script_name}.")
                except Exception as e:
                    bot.send_message(call.message.chat.id, f"حدث خطأ: {e}")
            elif 'start' in call.data:
                try:
                    start_file(script_path, call.message.chat.id)
                    bot.send_message(ADMIN_ID, f"قام المستخدم @{bot_scripts[int(user_id)]['uploader']} بتشغيل ملفه {script_name}.")
                except Exception as e:
                    bot.send_message(call.message.chat.id, f"حدث خطأ: {e}")
        except IndexError:
            bot.send_message(call.message.chat.id, "حدث خطأ في معالجة الطلب. يرجى المحاولة مرة أخرى.")
    elif call.data == 'stop_all':
        stop_all_files(call.message.chat.id)
    elif call.data == 'start_all':
        start_all_files(call.message.chat.id)
    elif call.data == 'rck_all':
        bot.send_message(call.message.chat.id, "يرجى كتابة الرسالة لإرسالها للجميع.")
        bot.register_next_step_handler(call.message, handle_broadcast_message)
    elif call.data == 'ban_user':
        bot.send_message(call.message.chat.id, "يرجى كتابة معرف المستخدم لحظره.")
        bot.register_next_step_handler(call.message, handle_ban_user)
    elif call.data == 'uban_user':
        bot.send_message(call.message.chat.id, "يرجى كتابة معرف المستخدم لفك حظره.")
        bot.register_next_step_handler(call.message, handle_unban_user)

def stop_all_files(chat_id):
    stopped_files = []
    for chat_id, script_info in list(bot_scripts.items()):
        if stop_bot(script_info['path'], chat_id):
            stopped_files.append(script_info['name'])
    if stopped_files:
        bot.send_message(chat_id, f"تم إيقاف الملفات التالية بنجاح: {', '.join(stopped_files)}")
    else:
        bot.send_message(chat_id, "لا توجد ملفات قيد التشغيل لإيقافها.")

def start_all_files(chat_id):
    started_files = []
    for chat_id, script_info in list(bot_scripts.items()):
        if start_file(script_info['path'], chat_id):
            started_files.append(script_info['name'])
    if started_files:
        bot.send_message(chat_id, f"تم تشغيل الملفات التالية بنجاح: {', '.join(started_files)}")
    else:
        bot.send_message(chat_id, "لا توجد ملفات متوقفة لتشغيلها.")

def stop_bot(script_path, chat_id, delete=False):
    try:
        script_name = os.path.basename(script_path)
        process = bot_scripts.get(chat_id, {}).get('process')
        if process and psutil.pid_exists(process.pid):
            parent = psutil.Process(process.pid)
            for child in parent.children(recursive=True):  # Terminate all child processes
                child.terminate()
            parent.terminate()
            parent.wait()  # Ensure the process has been terminated
            bot_scripts[chat_id]['process'] = None
            if delete:
                os.remove(script_path)  # Remove the script if delete flag is set
                bot.send_message(chat_id, f"تم حذف {script_name} من الاستضافة.")
            else:
                bot.send_message(chat_id, f"تم إيقاف {script_name} بنجاح.")
            return True
        else:
            bot.send_message(chat_id, f"عملية {script_name} غير موجودة أو أنها قد توقفت بالفعل.")
            return False
    except psutil.NoSuchProcess:
        bot.send_message(chat_id, f"عملية {script_name} غير موجودة.")
        return False
    except Exception as e:
        print(f"Error stopping bot: {e}")
        bot.send_message(chat_id, f"حدث خطأ أثناء إيقاف {script_name}: {e}")
        return False

############## دي داله مهمه جدا خاصه بتشغيل الملف المرفوع ############


def log_uploaded_file(chat_id, script_name):
    """
    دالة لتسجيل الملف المرفوع في bot_scripts مع تفاصيل إضافية.
    
    Args:
        chat_id: معرف المستخدم.
        script_name: اسم الملف المرفوع.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # تسجيل الوقت
    with lock:  # استخدام القفل لضمان الوصول المتزامن
        if chat_id not in bot_scripts:
            bot_scripts[chat_id] = {'process': None, 'files': [], 'path': None}
        bot_scripts[chat_id]['files'].append({'name': script_name, 'timestamp': timestamp})
        
        # تخزين معلومات المستخدمين
        if chat_id not in user_files:
            user_files[chat_id] = []
        user_files[chat_id].append(script_name)

def start_file(script_path, chat_id):
    """
    دالة لبدء تشغيل ملف برمجي.
    
    Args:
        script_path: المسار الكامل للملف البرمجي.
        chat_id: معرف المستخدم.
    """
    script_name = os.path.basename(script_path)

    with lock:  # استخدام القفل لضمان الوصول المتزامن
        if chat_id not in bot_scripts:
            bot_scripts[chat_id] = {'process': None, 'files': [], 'path': script_path}

        # تحقق من إذا كانت العملية قيد التشغيل بالفعل
        if bot_scripts[chat_id]['process'] and psutil.pid_exists(bot_scripts[chat_id]['process'].pid):
            bot.send_message(chat_id, f"⚠️ العملية {script_name} قيد التشغيل بالفعل.")
            return False

    # تشغيل الملف في خيط جديد
    future = executor.submit(run_script, script_path, chat_id, script_name)
    return future

def run_script(script_path, chat_id, script_name):
    """
    دالة لتشغيل الملف البرمجي والتعامل مع المخرجات.
    
    Args:
        script_path: المسار الكامل للملف البرمجي.
        chat_id: معرف المستخدم.
        script_name: اسم الملف البرمجي.
    """
    try:
        p = subprocess.Popen([sys.executable, script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # تسجيل العملية
        with lock:  # استخدام القفل لضمان الوصول المتزامن
            bot_scripts[chat_id]['process'] = p

        # الانتظار حتى تنتهي العملية
        stdout, stderr = p.communicate()

        # معالجة المخرجات
        if stdout:
            bot.send_message(chat_id, f"✅ تم تشغيل {script_name} بنجاح.\n\nمخرجات العملية:\n{stdout.decode()}")
        if stderr:
            bot.send_message(chat_id, f"⚠️ حدث خطأ أثناء تشغيل {script_name}:\n{stderr.decode()}")

    except Exception as e:
        bot.send_message(chat_id, f"❌ حدث استثناء أثناء تشغيل {script_name}: {str(e)}")
    
    finally:
        # إعادة تعيين العملية بعد الانتهاء
        with lock:
            bot_scripts[chat_id]['process'] = None

def check_running_scripts(chat_id):
    """
    دالة للتحقق من حالة الملفات المرفوعة.
    
    Args:
        chat_id: معرف المستخدم.
        
    Returns:
        قائمة بحالة الملفات المرفوعة.
    """
    with lock:  # استخدام القفل لضمان الوصول المتزامن
        if chat_id in bot_scripts:
            status = []
            
            for file_info in bot_scripts[chat_id]['files']:
                process = bot_scripts[chat_id]['process']
                if process and psutil.pid_exists(process.pid):
                    status.append(f"{file_info['name']} - قيد التشغيل")
                else:
                    status.append(f"{file_info['name']} - غير قيد التشغيل")
            return status
        else:
            return ["لا توجد ملفات مرفوعة لهذا المستخدم."]

def manage_running_scripts():

    while True:
        with lock:  # استخدام القفل لضمان الوصول المتزامن
            for chat_id in list(bot_scripts.keys()):
                info = bot_scripts[chat_id]
                
                # تأكد من وجود المفتاح 'process'
                if 'process' not in info:
                    info['process'] = None
                
                process = info['process']
                if process and not psutil.pid_exists(process.pid):
                    # إذا كانت العملية توقفت، يمكن إعادة تشغيلها
                    bot.send_message(chat_id, f"⚠️ العملية {info['files'][-1]['name']} توقفت. سيتم إعادة تشغيلها.")
                    start_file(info['files'][-1]['name'], chat_id)

        # تأخير زمني بين كل عملية مراقبة
        time.sleep(5)

# بدء مراقبة العمليات في خيط جديد
monitor_thread = threading.Thread(target=manage_running_scripts, daemon=True)
monitor_thread.start()








    ######## داله ايقاف زفت

def stop_all_files(chat_id):
    stopped_files = []
    for chat_id, script_info in list(bot_scripts.items()):
        if stop_bot(script_info['path'], chat_id):
            stopped_files.append(script_info['name'])
    if stopped_files:
        bot.send_message(chat_id, f"تم إيقاف الملفات التالية بنجاح: {', '.join(stopped_files)}")
    else:
        bot.send_message(chat_id, "لا توجد ملفات قيد التشغيل لإيقافها.")

def start_all_files(chat_id):
    started_files = []
    for chat_id, script_info in list(bot_scripts.items()):
        if start_file(script_info['path'], chat_id):
            started_files.append(script_info['name'])
    if started_files:
        bot.send_message(chat_id, f"تم تشغيل الملفات التالية بنجاح: {', '.join(started_files)}")
    else:
        bot.send_message(chat_id, "لا توجد ملفات متوقفة لتشغيلها.")

def stop_bot(script_path, chat_id, delete=False):
    try:
        script_name = os.path.basename(script_path)
        process = bot_scripts.get(chat_id, {}).get('process')
        if process and psutil.pid_exists(process.pid):
            parent = psutil.Process(process.pid)
            for child in parent.children(recursive=True):  # Terminate all child processes
                child.terminate()
            parent.terminate()
            parent.wait()  # Ensure the process has been terminated
            bot_scripts[chat_id]['process'] = None
            if delete:
                os.remove(script_path)  # Remove the script if delete flag is set
                bot.send_message(chat_id, f"تم حذف {script_name} من الاستضافة.")
            else:
                bot.send_message(chat_id, f"تم إيقاف {script_name} بنجاح.")
            return True
        else:
            bot.send_message(chat_id, f"عملية {script_name} غير موجودة أو أنها قد توقفت بالفعل.")
            return False
    except psutil.NoSuchProcess:
        bot.send_message(chat_id, f"عملية {script_name} غير موجودة.")
        return False
    except Exception as e:
        print(f"Error stopping bot: {e}")
        bot.send_message(chat_id, f"حدث خطأ أثناء إيقاف {script_name}: {e}")
        return False
    

def start_file(script_path, chat_id):
    try:
        script_name = os.path.basename(script_path)
        if bot_scripts.get(chat_id, {}).get('process') and psutil.pid_exists(bot_scripts[chat_id]['process'].pid):
            bot.send_message(chat_id, f"الملف {script_name} يعمل بالفعل.")
            return False
        else:
            p = subprocess.Popen([sys.executable, script_path])
            bot_scripts[chat_id]['process'] = p
            bot.send_message(chat_id, f"تم تشغيل {script_name} بنجاح.")
            return True
    except Exception as e:
        print(f"Error starting bot: {e}")
        bot.send_message(chat_id, f"حدث خطأ أثناء تشغيل {script_name}: {e}")
        return False

    ################## داله ايقاف من خلال اوامر

@bot.message_handler(commands=['adm'])
def handle_admin_command(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "ليس لديك صلاحية استخدام هذا الأمر.")
        return

    try:
        if message.reply_to_message:
            script_name = message.reply_to_message.text.strip()
        else:
            script_name = message.text.split(' ', 1)[1].strip()

        script_path = os.path.join(uploaded_files_dir, script_name)
        stop_bot(message.chat.id, delete=False)  # التأكد من تمرير قيمة delete بشكل صحيح
    except IndexError:
        bot.reply_to(message, "يرجى كتابة اسم الملف بعد الأمر أو الرد على رسالة.")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ: {e}")

##################### داله بدأ ملف من خلال اوامر

@bot.message_handler(commands=['str'])
def start_file_command(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "ليس لديك صلاحية استخدام هذا الأمر.")
        return

    try:
        if message.reply_to_message:
            script_name = message.reply_to_message.text.strip()
        else:
            script_name = message.text.split(' ', 1)[1].strip()

        script_path = os.path.join(uploaded_files_dir, script_name)
        log_uploaded_file(message.chat.id, script_name)  # تسجيل الملف المرفوع
        start_file(script_path, message.chat.id)  # بدء تشغيل الملف
    except IndexError:
        bot.reply_to(message, "يرجى كتابة اسم الملف بعد الأمر أو الرد على رسالة.")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ: {e}")

def list_user_files(chat_id):
    """دالة لعرض الملفات التي رفعها المستخدم."""
    if chat_id in user_files:
        files = user_files[chat_id]
        return f"الملفات التي قمت برفعها: {', '.join(files)}"
    else:
        return "لم تقم برفع أي ملفات بعد."

@bot.message_handler(commands=['myfiles'])
def my_files_command(message):
    """معالج لعرض الملفات التي رفعها المستخدم."""
    user_files_message = list_user_files(message.chat.id)
    bot.reply_to(message, user_files_message)






#########################


# ضمان تشغيل نسخة واحدة فقط من البوت مع إعادة التشغيل التلقائية في حال حدوث خطأ
if __name__ == "__main__":
    while True:
        try:
            bot.infinity_polling()
        except Exception as e:
            logging.error(f"Error: {e}")
            time.sleep(5)  # انتظار 5 ثواني قبل إعادة المحاولة 