import asyncio
import logging
import io
import json
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Document
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- إعدادات البوت ---
TOKEN = "7654632262:AAFklxsH6c-PYz6cBfcHTx755xTNAxu5p5I"
OWNER_ID = 2118176057
API_ENDPOINT = "https://api.chkr.cc/"

# --- تعطيل رسائل الترمنال ---
logging.basicConfig(level=logging.CRITICAL)
logger = logging.getLogger(__name__)

# --- قاعدة البيانات (باستخدام class عشان التنظيم) ---
class BotData:
    def __init__(self):
        self.approved_users = {OWNER_ID}
        self.waiting_list = {}
        self.banned_users = set()
        self.admins = set()
        self.all_users = set()
        self.bot_enabled = True
        self.awaiting_ban_id = set()
        self.awaiting_unban_id = set()
        self.awaiting_broadcast_message = set()

# إنشاء كائن واحد من البيانات
data = BotData()

# --- دوال مساعدة ---
def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID

def is_admin(user_id: int) -> bool:
    return is_owner(user_id) or user_id in data.admins

def is_approved(user_id: int) -> bool:
    return user_id in data.approved_users

def is_banned(user_id: int) -> bool:
    return user_id in data.banned_users

def get_user_keyboard():
    keyboard = [
        [InlineKeyboardButton("📁 إرسال ملف TXT", callback_data='user_send_file')],
        [InlineKeyboardButton("✍️ إرسال نص", callback_data='user_send_text')],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("✅ قبول مستخدم", callback_data='admin_approve')],
        [InlineKeyboardButton("🚫 حظر مستخدم", callback_data='admin_ban')],
        [InlineKeyboardButton("✅ إلغاء حظر مستخدم", callback_data='admin_unban')],
        [InlineKeyboardButton("📢 إرسال رسالة لكل المستخدمين", callback_data='admin_broadcast')],
        [InlineKeyboardButton("🔓 قفل/فتح البوت", callback_data='admin_toggle_bot')],
        [InlineKeyboardButton("👥 إحصائيات المستخدمين", callback_data='admin_stats')],
        [InlineKeyboardButton("⏳ قائمة الانتظار", callback_data='admin_waiting_list')],
        [InlineKeyboardButton("👤 لوحة المستخدم", callback_data='user_panel')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def check_card(card_data: str) -> dict:
    """فحص كارت واحد باستخدام API"""
    try:
        async with aiohttp.ClientSession() as session:
            payload = {"data": card_data}
            async with session.post(API_ENDPOINT, data=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"code": 2, "status": "Unknown", "message": f"API Error {response.status}"}
    except Exception:
        return {"code": 2, "status": "Unknown", "message": "Request Failed"}

async def process_cards(update: Update, context: ContextTypes.DEFAULT_TYPE, cards: list):
    """دالة فحص الكروت (بتشتغل في الخلفية)"""
    user_id = update.effective_user.id
    live_cards = []
    die_count = 0
    unknown_count = 0
    total_cards = len(cards)

    if total_cards == 0:
        await update.message.reply_text("❌ لم يتم العثور على كروت صالحة في الملف/النص.")
        return

    progress_message = await update.message.reply_text(
        f"⏳ بدأ الفحص...\n\n"
        f"🔍 الإجمالي: {total_cards}\n"
        f"✅ Live: 0\n"
        f"❌ Die: 0\n"
        f"❓ Unknown: 0"
    )

    for i, card in enumerate(cards):
        card = card.strip()
        if not card: continue

        result = await check_card(card)
        
        if result.get("code") == 1: live_cards.append(card)
        elif result.get("code") == 0: die_count += 1
        else: unknown_count += 1

        if (i + 1) % 10 == 0 or (i + 1) == total_cards:
            live_count = len(live_cards)
            try:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=progress_message.message_id,
                    text=f"⏳ جاري الفحص... ({i + 1}/{total_cards})\n\n"
                         f"🔍 الإجمالي: {total_cards}\n"
                         f"✅ Live: {live_count}\n"
                         f"❌ Die: {die_count}\n"
                         f"❓ Unknown: {unknown_count}"
                )
            except Exception:
                pass
        
        await asyncio.sleep(0.5)

    live_count = len(live_cards)
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=progress_message.message_id,
        text=f"✅ انتهى الفحص!\n\n"
             f"🔍 الإجمالي: {total_cards}\n"
             f"✅ Live: {live_count}\n"
             f"❌ Die: {die_count}\n"
             f"❓ Unknown: {unknown_count}"
    )

    if live_cards:
        live_data = "\n".join(live_cards)
        file_bytes = io.BytesIO(live_data.encode('utf-8'))
        await update.message.reply_document(
            document=file_bytes,
            filename=f"live_cards_by_{user_id}.txt",
            caption=f"🎉 تم العثور على {live_count} كارت Live."
        )
    else:
        await update.message.reply_text("🚫 لم يتم العثور على أي كروت Live.")


# --- معالجات الأوامر ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    user_id = update.effective_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    data.all_users.add(user_id)
    
    if is_banned(user_id):
        await update.message.reply_text("🚫 تم حظرك من استخدام البوت.")
        return

    if not data.bot_enabled and not is_admin(user_id):
        await update.message.reply_text("🔒 البوت مغلق حاليًا من قبل المطور.")
        return

    if is_admin(user_id):
        await update.message.reply_text(f"👋 أهلاً بك في لوحة التحكم يا {username}!", reply_markup=get_admin_keyboard())
    elif is_approved(user_id):
        await update.message.reply_text(f"أهلاً بك يا {username}!\nاختر طريقة إرسال الكروت:", reply_markup=get_user_keyboard())
    else:
        data.waiting_list[user_id] = True
        await update.message.reply_text(f"👋 أهلاً بك يا {username}.\nتم إضافتك لقائمة الانتظار.\nسيقوم الاونر بقبولك قريباً.")
        
        approve_button = InlineKeyboardButton(f"✅ قبول {username}", callback_data=f'approve_user_{user_id}')
        keyboard = InlineKeyboardMarkup([[approve_button]])
        
        try:
            await context.bot.send_message(
                OWNER_ID,
                f"👤 مستخدم جديد في الانتظار:\n\n🔹 ID: `{user_id}`\n🔹 Username: @{username}\n\n",
                reply_markup=keyboard
            )
        except Exception:
            pass

# --- معالج الأزرار الحية ---
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.callback_query:
        return

    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if not data.bot_enabled and not is_admin(user_id):
        await query.answer("البوت مغلق حالياً.", show_alert=True)
        return

    data_str = query.data

    async def safe_edit(text, reply_markup=None):
        try:
            await query.edit_message_text(text, reply_markup=reply_markup)
        except Exception:
            pass

    if data_str == 'user_send_file':
        await safe_edit("📂 قم برفع ملف TXT يحتوي على الكروت.\n\n(كارت في كل سطر بصيغة: number|month|year|cvv)")
    elif data_str == 'user_send_text':
        await safe_edit("✍️ قم بإرسال قائمة الكروت كنص.\n\n(كارت في كل سطر بصيغة: number|month|year|cvv)")
    elif data_str == 'user_panel':
        await safe_edit("👤 لوحة المستخدم:", reply_markup=get_user_keyboard())
    
    # --- أزرار الأدمن ---
    elif data_str == 'admin_approve':
        await safe_edit("✍️ اضغط على زر القبول بجوار المستخدم في رسالة الإشعار.")
    elif data_str == 'admin_ban':
        data.awaiting_ban_id.add(user_id)
        await safe_edit("🚫 أرسل الآن ID المستخدم الذي تريد حظره:", reply_markup=get_admin_keyboard())
    elif data_str == 'admin_unban':
        data.awaiting_unban_id.add(user_id)
        await safe_edit("✅ أرسل الآن ID المستخدم الذي تريد إلغاء حظره:", reply_markup=get_admin_keyboard())
    elif data_str == 'admin_broadcast':
        data.awaiting_broadcast_message.add(user_id)
        await safe_edit("📢 أرسل الآن الرسالة التي تريد بثها لكل المستخدمين:", reply_markup=get_admin_keyboard())
    elif data_str == 'admin_toggle_bot':
        data.bot_enabled = not data.bot_enabled
        status = "مفتوح 🔓" if data.bot_enabled else "مقفول 🔒"
        await safe_edit(f"🔓 حالة البوت الآن: {status}.", reply_markup=get_admin_keyboard())
    elif data_str == 'admin_stats':
        stats_text = f"📊 إحصائيات البوت:\n\n✅ المقبولون: {len(data.approved_users)}\n⏳ في الانتظار: {len(data.waiting_list)}\n🚫 المحظورون: {len(data.banned_users)}\n👥 إجمالي المستخدمين: {len(data.all_users)}"
        await safe_edit(stats_text, reply_markup=get_admin_keyboard())
    elif data_str == 'admin_waiting_list':
        if not data.waiting_list:
            await safe_edit("📭 قائمة الانتظار فارغة حالياً.", reply_markup=get_admin_keyboard())
        else:
            users_text = "\n".join([f"🔹 ID: `{uid}`" for uid in data.waiting_list.keys()])
            await safe_edit(f"⏳ قائمة الانتظار الحالية:\n\n{users_text}", reply_markup=get_admin_keyboard())
    
    elif data_str.startswith('approve_user_'):
        try:
            user_id_to_approve = int(data_str.split('_')[-1])
            if user_id_to_approve in data.waiting_list:
                data.approved_users.add(user_id_to_approve)
                data.waiting_list.pop(user_id_to_approve, None)
                
                await safe_edit(f"✅ تم قبول المستخدم `{user_id_to_approve}` بنجاح.")
                
                try:
                    await context.bot.send_message(
                        user_id_to_approve,
                        "🎉 تم قبولك! يمكنك الآن استخدام البوت.\nاختر طريقة إرسال الكروت:",
                        reply_markup=get_user_keyboard()
                    )
                except Exception:
                    pass
            else:
                await safe_edit("⚠️ هذا المستخدم تم قبوله بالفعل أو غير موجود في القائمة.")
        except (ValueError, IndexError):
            await safe_edit("⚠️ حدث خطأ في معرّف المستخدم.")

# --- معالجات الرسائل ---
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    data.all_users.add(user_id)

    if not data.bot_enabled and not is_admin(user_id):
        await update.message.reply_text("🔒 البوت مغلق حاليًا.")
        return

    if not is_approved(user_id):
        return 

    document: Document = update.message.document
    if not document.file_name.endswith(".txt"):
        await update.message.reply_text("⚠️ الرجاء رفع ملف بصيغة `.txt` فقط.")
        return

    try:
        file = await context.bot.get_file(document.file_id)
        cards = (await file.download_as_bytearray()).decode('utf-8').splitlines()
        
        # --- الحل: تشغيل الفحص في الخلفية ---
        await update.message.reply_text("🚀 تم استلام الملف، جاري بدء الفحص...")
        asyncio.create_task(process_cards(update, context, cards))

    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ أثناء معالجة الملف: {e}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    text = update.message.text
    data.all_users.add(user_id)

    # --- منطق بث الرسالة ---
    if user_id in data.awaiting_broadcast_message:
        data.awaiting_broadcast_message.remove(user_id)
        success_count = 0
        fail_count = 0
        for uid in list(data.all_users):
            try:
                await context.bot.send_message(uid, text)
                success_count += 1
                await asyncio.sleep(0.1)
            except Exception:
                fail_count += 1
        await update.message.reply_text(f"📊 انتهى البث:\n\n✅ تم الإرسال لـ: {success_count}\n❌ فشل الإرسال لـ: {fail_count}", reply_markup=get_admin_keyboard())
        return

    # --- منطق إلغاء الحظر ---
    if user_id in data.awaiting_unban_id:
        data.awaiting_unban_id.remove(user_id)
        try:
            uid_to_unban = int(text)
            if uid_to_unban in data.banned_users:
                data.banned_users.remove(uid_to_unban)
                await update.message.reply_text(f"✅ تم إلغاء حظر المستخدم `{uid_to_unban}` بنجاح.", reply_markup=get_admin_keyboard())
            else:
                await update.message.reply_text(f"⚠️ المستخدم `{uid_to_unban}` غير موجود في قائمة المحظورين.", reply_markup=get_admin_keyboard())
        except ValueError:
            await update.message.reply_text("⚠️ الرجاء إرسال ID رقمي صحيح.", reply_markup=get_admin_keyboard())
        return

    # --- منطق الحظر ---
    if user_id in data.awaiting_ban_id:
        data.awaiting_ban_id.remove(user_id)
        try:
            uid_to_ban = int(text)
            if uid_to_ban == OWNER_ID:
                await update.message.reply_text("❌ لا يمكنك حظر نفسك.")
                return
            data.banned_users.add(uid_to_ban)
            data.approved_users.discard(uid_to_ban)
            data.waiting_list.pop(uid_to_ban, None)
            await update.message.reply_text(f"✅ تم حظر المستخدم `{uid_to_ban}` بنجاح.", reply_markup=get_admin_keyboard())
        except ValueError:
            await update.message.reply_text("⚠️ الرجاء إرسال ID رقمي صحيح.", reply_markup=get_admin_keyboard())
        return

    if not data.bot_enabled and not is_admin(user_id):
        await update.message.reply_text("🔒 البوت مغلق حاليًا.")
        return

    if not is_approved(user_id):
        return

    if "|" in text:
        cards = text.splitlines()
        
        # --- الحل: تشغيل الفحص في الخلفية ---
        await update.message.reply_text("🚀 تم استلام النص، جاري بدء الفحص...")
        asyncio.create_task(process_cards(update, context, cards))
        return
    else:
        await update.message.reply_text("❌ النص المرسل لا يبدو أنه قائمة كروت.\nيرجى إرسال الكروت بالصيغة: number|month|year|cvv")

def main() -> None:
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.Document.FileExtension("txt") & ~filters.COMMAND, handle_file))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("البوت يعمل الآن...")
    application.run_polling()

if __name__ == "__main__":
    main()