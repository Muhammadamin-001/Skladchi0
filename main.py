import telebot
import logging
import os
from flask import Flask, request
from config.settings import BOT_TOKEN, ADMIN_ID, MESSAGES
from database.mongodb import init_db, get_db

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot va Flask
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# MongoDB init
logger.info("🔌 MongoDB baza Ishga Tushirilmoqda...")
try:
    init_db()
    logger.info("✅ MongoDB baza tayyor")
except Exception as e:
    logger.error(f"❌ MongoDB xatosi: {e}")

# ==================== BOT HANDLERS ====================

@bot.message_handler(commands=['start'])
def handle_start(message):
    """Bot /start qilish"""
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"
    first_name = message.from_user.first_name or "Foydalanuvchi"
    
    db = get_db()
    user = db.get_user(user_id)
    
    if user_id == ADMIN_ID:
        # Admin Panel
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("🏢 Filial", callback_data="admin_branch")
        )
        markup.add(
            telebot.types.InlineKeyboardButton("📦 Mahsulot", callback_data="admin_product")
        )
        markup.add(
            telebot.types.InlineKeyboardButton("📋 Ro'yxat", callback_data="admin_list")
        )
        bot.send_message(user_id, MESSAGES["start_admin"], reply_markup=markup)
    
    elif user and user.get("approved"):
        # Approved User
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("📥 Mahsulot Kiritish", callback_data="user_input")
        )
        markup.add(
            telebot.types.InlineKeyboardButton("📤 Mahsulot Chiqarish", callback_data="user_remove")
        )
        markup.add(
            telebot.types.InlineKeyboardButton("📋 Ro'yxat", callback_data="user_list")
        )
        bot.send_message(user_id, MESSAGES["start_user_approved"].format(first_name), reply_markup=markup)
    
    else:
        # Unapproved User
        if not user:
            db.add_user(user_id, username, first_name, approved=False)
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("📧 So'rov Yuborish", callback_data="send_request"))
        bot.send_message(user_id, MESSAGES["start_user_unapproved"], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "send_request")
def handle_send_request(call):
    """So'rov yuborish"""
    user_id = call.from_user.id
    username = call.from_user.username or "NoUsername"
    
    db = get_db()
    db.add_request(user_id, username)
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        MESSAGES["request_sent"],
        call.message.chat.id,
        call.message.message_id
    )
    
    # Admin notification
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_user:{user_id}"),
        telebot.types.InlineKeyboardButton("❌ Rad Qilish", callback_data=f"reject_user:{user_id}")
    )
    
    bot.send_message(
        ADMIN_ID,
        f"📩 Yangi so'rov:\n\n👤 Username: @{username}\n🆔 User ID: {user_id}",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_user:"))
def handle_approve_user(call):
    """Foydalanuvchini tasdiqlash"""
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Sizda ruxsat yo'q", show_alert=True)
        return
    
    user_id = int(call.data.split(":")[1])
    db = get_db()
    db.approve_user(user_id)
    db.delete_request(user_id)
    
    bot.answer_callback_query(call.id, "✅ Tasdiqlandi")
    bot.edit_message_text(
        f"✅ Foydalanuvchi {user_id} tasdiqlandı",
        call.message.chat.id,
        call.message.message_id
    )
    
    bot.send_message(user_id, MESSAGES["user_approved"])

@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_user:"))
def handle_reject_user(call):
    """Foydalanuvchini rad qilish"""
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Sizda ruxsat yo'q", show_alert=True)
        return
    
    user_id = int(call.data.split(":")[1])
    db = get_db()
    db.reject_user(user_id)
    db.delete_request(user_id)
    
    bot.answer_callback_query(call.id, "❌ Rad qilindi")
    bot.edit_message_text(
        f"❌ Foydalanuvchi {user_id} rad qilindi",
        call.message.chat.id,
        call.message.message_id
    )
    
    bot.send_message(user_id, MESSAGES["user_rejected"])

# ==================== WEBHOOK (FLASK) ====================

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    """Webhook endpoint"""
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def index():
    """Health check"""
    return "Bot is running", 200

# ==================== MAIN ====================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info("🤖 Bot ishga tushdi!")
    app.run(host="0.0.0.0", port=port, debug=False)