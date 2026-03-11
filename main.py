import telebot
import logging
import os
from flask import Flask, request
from config.settings import BOT_TOKEN, ADMIN_ID, MESSAGES
from database.mongodb import init_db, get_db
from keyboards.telebot_keyboards import *

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

logger.info("🔌 MongoDB baza Ishga Tushirilmoqda...")
try:
    init_db()
    logger.info("✅ MongoDB baza tayyor")
except Exception as e:
    logger.error(f"❌ MongoDB xatosi: {e}")

# ==================== /START ====================

@bot.message_handler(commands=['start'])
def handle_start(message):
    """Bot /start qilish"""
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"
    first_name = message.from_user.first_name or "Foydalanuvchi"
    
    db = get_db()
    user = db.get_user(user_id)
    
    if user_id == ADMIN_ID:
        bot.send_message(user_id, MESSAGES["start_admin"], reply_markup=admin_main_menu())
    elif user and user.get("approved"):
        bot.send_message(user_id, MESSAGES["start_user_approved"].format(first_name), reply_markup=user_main_menu())
    else:
        if not user:
            db.add_user(user_id, username, first_name, approved=False)
        bot.send_message(user_id, MESSAGES["start_user_unapproved"], reply_markup=user_request_menu())

# ==================== ADMIN HANDLERS ====================

@bot.callback_query_handler(func=lambda call: call.data == "admin_branch")
def handle_admin_branch(call):
    """Admin filial boshqarish"""
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, MESSAGES["error_access_denied"], show_alert=True)
        return
    
    bot.edit_message_text(
        MESSAGES["branch_management"],
        call.message.chat.id,
        call.message.message_id,
        reply_markup=branches_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_product")
def handle_admin_product(call):
    """Admin mahsulot boshqarish"""
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, MESSAGES["error_access_denied"], show_alert=True)
        return
    
    bot.edit_message_text(
        MESSAGES["product_management"],
        call.message.chat.id,
        call.message.message_id,
        reply_markup=product_type_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_list")
def handle_admin_list(call):
    """Admin ro'yxat"""
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, MESSAGES["error_access_denied"], show_alert=True)
        return
    
    db = get_db()
    branches = db.get_all_branches()
    
    markup = telebot.types.InlineKeyboardMarkup()
    for branch in branches:
        markup.add(telebot.types.InlineKeyboardButton(
            text=branch["name"],
            callback_data=f"list_branch:{branch['name']}"
        ))
    markup.add(telebot.types.InlineKeyboardButton("🌍 Umumiy", callback_data="list_branch:common"))
    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data="admin_back"))
    
    bot.edit_message_text(
        MESSAGES["list_title"],
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "branch_add")
def handle_branch_add(call):
    """Filial qo'shish"""
    msg = bot.edit_message_text(
        MESSAGES["branch_add_prompt"],
        call.message.chat.id,
        call.message.message_id,
        reply_markup=back_button("admin_branch")
    )
    bot.register_next_step_handler(msg, process_branch_add)

def process_branch_add(message):
    """Filial nomini saqlash"""
    db = get_db()
    name = message.text.strip()
    
    if db.add_branch(name):
        bot.send_message(message.chat.id, MESSAGES["branch_added"].format(name), reply_markup=branches_menu())
    else:
        bot.send_message(message.chat.id, MESSAGES["branch_exists"], reply_markup=back_button("admin_branch"))

@bot.callback_query_handler(func=lambda call: call.data.startswith("branch_select:"))
def handle_branch_select(call):
    """Filial tanlash"""
    branch_name = call.data.split(":")[1]
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton(MESSAGES["button_edit"], callback_data=f"branch_edit:{branch_name}"),
        telebot.types.InlineKeyboardButton(MESSAGES["button_delete"], callback_data=f"branch_delete:{branch_name}")
    )
    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data="admin_branch"))
    
    bot.edit_message_text(
        f"🏢 Filial: <b>{branch_name}</b>\n\nFaoliyatni tanlang:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("branch_delete:"))
def handle_branch_delete(call):
    """Filial o'chirish"""
    branch_name = call.data.split(":")[1]
    db = get_db()
    db.delete_branch(branch_name)
    
    bot.edit_message_text(
        MESSAGES["branch_deleted"],
        call.message.chat.id,
        call.message.message_id,
        reply_markup=branches_menu()
    )

# ==================== USER HANDLERS ====================

@bot.callback_query_handler(func=lambda call: call.data == "user_input")
def handle_user_input(call):
    """Mahsulot kiritish"""
    bot.edit_message_text(
        MESSAGES["user_add_product"],
        call.message.chat.id,
        call.message.message_id,
        reply_markup=branches_menu_user("input")
    )

@bot.callback_query_handler(func=lambda call: call.data == "user_remove")
def handle_user_remove(call):
    """Mahsulot chiqarish"""
    bot.edit_message_text(
        MESSAGES["user_remove_product"],
        call.message.chat.id,
        call.message.message_id,
        reply_markup=branches_menu_user("remove")
    )

@bot.callback_query_handler(func=lambda call: call.data == "user_list")
def handle_user_list(call):
    """Mahsulotlar ro'yxati"""
    bot.edit_message_text(
        "📋 Ro'yxat\n\nFilial tanlang:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=list_branches_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("user_input_branch:"))
def handle_user_input_branch(call):
    """Kiritish uchun filial tanlash"""
    branch = call.data.split(":")[1]
    if branch == "common":
        branch = None
    
    bot.edit_message_text(
        f"📦 Mahsulotlarni tanlang:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=products_menu_user(branch, "input")
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("user_input_product:"))
def handle_user_input_product(call):
    """Mahsulot tanlash va miqdor kiritish"""
    product_name = call.data.split(":")[1]
    
    msg = bot.edit_message_text(
        f"📦 <b>{product_name}</b>\n\n{MESSAGES['user_enter_quantity']}",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML"
    )
    
    def process_quantity(message):
        try:
            quantity = int(message.text)
            if quantity <= 0:
                bot.send_message(message.chat.id, MESSAGES["error_invalid_quantity"])
                return
            
            db = get_db()
            new_qty = db.add_inventory(product_name, None, quantity)
            
            bot.send_message(
                message.chat.id,
                MESSAGES["user_product_added"].format(product_name, quantity, new_qty)
            )
        except ValueError:
            bot.send_message(message.chat.id, MESSAGES["error_invalid_quantity"])
    
    bot.register_next_step_handler(msg, process_quantity)

# ==================== CALLBACK HANDLERS ====================

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
        bot.answer_callback_query(call.id, MESSAGES["error_access_denied"], show_alert=True)
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
        bot.answer_callback_query(call.id, MESSAGES["error_access_denied"], show_alert=True)
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

@bot.callback_query_handler(func=lambda call: call.data == "close_menu")
def handle_close_menu(call):
    """Menyu yopish"""
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "admin_back")
def handle_admin_back(call):
    """Admin orqaga"""
    bot.edit_message_text(
        MESSAGES["start_admin"],
        call.message.chat.id,
        call.message.message_id,
        reply_markup=admin_main_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data == "user_main")
def handle_user_main(call):
    """Foydalanuvchi asosiy menyu"""
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, "👋 Asosiy Menyu", reply_markup=user_main_menu())

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