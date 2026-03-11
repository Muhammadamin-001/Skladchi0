import telebot
import logging
import os
from flask import Flask, request
from config.settings import BOT_TOKEN, ADMIN_ID, MESSAGES
from database.mongodb import init_db, get_db
from keyboards.telebot_keyboards import (
    admin_main_menu,
    branches_menu,
    #branch_action_menu,
    back_button,
    product_type_menu,
    branches_for_products_menu,
    products_menu,
    #product_action_menu,
    #yes_no_menu,
    user_main_menu,
    user_request_menu,
    branches_menu_user,
    products_menu_user,
    list_branches_menu
    )

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

# ==================== USER STATE STORAGE ====================
# Webhook'da foydalanish uchun
user_states = {}

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

# ==================== ADMIN BRANCH HANDLERS ====================

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

@bot.callback_query_handler(func=lambda call: call.data == "branch_add")
def handle_branch_add(call):
    """Filial qo'shish"""
    bot.send_message(
        call.message.chat.id,
        MESSAGES["branch_add_prompt"],
        reply_markup=back_button("admin_branch")
    )
    user_states[call.from_user.id] = "waiting_branch_name"

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "waiting_branch_name")
def process_branch_add(message):
    """Filial nomini saqlash"""
    db = get_db()
    name = message.text.strip()
    
    if db.add_branch(name):
        bot.send_message(message.chat.id, MESSAGES["branch_added"].format(name), reply_markup=branches_menu())
    else:
        bot.send_message(message.chat.id, MESSAGES["branch_exists"], reply_markup=back_button("admin_branch"))
    
    user_states.pop(message.from_user.id, None)

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

# ==================== ADMIN PRODUCT HANDLERS ====================

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

@bot.callback_query_handler(func=lambda call: call.data == "product_common")
def handle_product_common(call):
    """Umumiy mahsulotlar"""
    bot.edit_message_text(
        "📦 Umumiy Mahsulotlar:\n\nMahsulot tanlang yoki yangi qo'shish:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=products_menu(None),
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "product_branch")
def handle_product_branch(call):
    """Filialga xos mahsulotlar"""
    bot.edit_message_text(
        "🏢 Filial tanlang:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=branches_for_products_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("product_branch_select:"))
def handle_product_branch_select(call):
    """Filial uchun mahsulotlar"""
    branch_name = call.data.split(":")[1]
    
    bot.edit_message_text(
        f"📦 {branch_name} Uchun Mahsulotlar:\n\nMahsulot tanlang yoki yangi qo'shish:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=products_menu(branch_name),
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("product_add:"))
def handle_product_add(call):
    """Mahsulot qo'shish"""
    branch = call.data.split(":")[1]
    if branch == "common":
        branch = None
    
    user_id = call.from_user.id
    user_states[user_id] = {"action": "adding_product", "branch": branch}
    
    bot.send_message(
        call.message.chat.id,
        MESSAGES["product_add_name"],
        reply_markup=back_button("admin_product")
    )

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("action") == "adding_product")
def process_product_add_name(message):
    """Mahsulot nomini qabul qilish"""
    user_id = message.from_user.id
    data = user_states.get(user_id, {})
    data["product_name"] = message.text.strip()
    data["action"] = "adding_product_image"
    user_states[user_id] = data
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("✅ Ha", callback_data="product_add_image_yes"),
        telebot.types.InlineKeyboardButton("❌ Yo'q", callback_data="product_add_image_no")
    )
    
    bot.send_message(message.chat.id, MESSAGES["product_add_image"], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "product_add_image_yes")
def handle_product_image_yes(call):
    """Rasm yuklash kerak"""
    user_id = call.from_user.id
    user_states[user_id]["action"] = "uploading_product_image"
    
    bot.send_message(
        call.message.chat.id,
        MESSAGES["product_send_image"],
        reply_markup=back_button("admin_product")
    )

@bot.callback_query_handler(func=lambda call: call.data == "product_add_image_no")
def handle_product_image_no(call):
    """Rasm talab qilinmadi"""
    user_id = call.from_user.id
    data = user_states.get(user_id, {})
    
    db = get_db()
    db.add_product(data.get("product_name"), data.get("branch"))
    
    branch = data.get("branch")
    bot.edit_message_text(
        MESSAGES["product_added"].format(data.get("product_name")),
        call.message.chat.id,
        call.message.message_id,
        reply_markup=products_menu(branch)
    )
    
    user_states.pop(user_id, None)

@bot.message_handler(content_types=['photo'], func=lambda message: user_states.get(message.from_user.id, {}).get("action") == "uploading_product_image")
def process_product_image(message):
    """Mahsulot rasmi qabul qilish"""
    user_id = message.from_user.id
    data = user_states.get(user_id, {})
    
    image_id = message.photo[-1].file_id
    
    db = get_db()
    db.add_product(data.get("product_name"), data.get("branch"), image_id)
    
    branch = data.get("branch")
    bot.send_message(
        message.chat.id,
        MESSAGES["product_added"].format(data.get("product_name")),
        reply_markup=products_menu(branch)
    )
    
    user_states.pop(user_id, None)

# ==================== ADMIN LIST HANDLERS ====================

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

@bot.callback_query_handler(func=lambda call: call.data.startswith("list_branch:"))
def handle_list_branch(call):
    """Filial ro'yxati ko'rish"""
    branch = call.data.split(":")[1]
    if branch == "common":
        branch = None
    
    db = get_db()
    products = db.get_products_by_branch(branch)
    
    text = MESSAGES["list_title"] + "\n\n"
    
    if not products:
        text = MESSAGES["list_empty"]
    else:
        for idx, product in enumerate(products, 1):
            inventory = db.get_inventory(product["name"], branch)
            quantity = inventory.get("quantity", 0)
            text += f"{idx}. {product['name']}: <b>{quantity}</b> dona\n"
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=back_button("admin_list"),
        parse_mode="HTML"
    )

# ==================== USER INPUT HANDLERS ====================

@bot.callback_query_handler(func=lambda call: call.data == "user_input")
def handle_user_input(call):
    """Mahsulot kiritish"""
    bot.edit_message_text(
        MESSAGES["user_add_product"],
        call.message.chat.id,
        call.message.message_id,
        reply_markup=branches_menu_user("input")
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("user_input_branch:"))
def handle_user_input_branch(call):
    """Kiritish uchun filial tanlash"""
    branch = call.data.split(":")[1]
    if branch == "common":
        branch = None
    
    user_id = call.from_user.id
    user_states[user_id] = {"action": "selecting_input_product", "branch": branch}
    
    bot.edit_message_text(
        "📦 Mahsulotlarni tanlang:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=products_menu_user(branch, "input"),
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("user_input_product:"))
def handle_user_input_product(call):
    """Mahsulot tanlash va miqdor kiritish"""
    product_name = call.data.split(":")[1]
    user_id = call.from_user.id
    
    data = user_states.get(user_id, {})
    data["action"] = "entering_input_quantity"
    data["product_name"] = product_name
    user_states[user_id] = data
    
    bot.send_message(
        call.message.chat.id,
        f"📦 <b>{product_name}</b>\n\n{MESSAGES['user_enter_quantity']}",
        parse_mode="HTML",
        reply_markup=back_button("user_input")
    )

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("action") == "entering_input_quantity")
def process_input_quantity(message):
    """Kiritilish miqdorini qabul qilish"""
    try:
        quantity = int(message.text)
        if quantity <= 0:
            bot.send_message(message.chat.id, MESSAGES["error_invalid_quantity"])
            return
        
        user_id = message.from_user.id
        data = user_states.get(user_id, {})
        product_name = data.get("product_name")
        branch = data.get("branch")
        
        db = get_db()
        new_qty = db.add_inventory(product_name, branch, quantity)
        
        bot.send_message(
            message.chat.id,
            MESSAGES["user_product_added"].format(product_name, quantity, new_qty),
            reply_markup=products_menu_user(branch, "input")
        )
        
        user_states.pop(user_id, None)
    except ValueError:
        bot.send_message(message.chat.id, MESSAGES["error_invalid_quantity"])

# ==================== USER REMOVE HANDLERS ====================

@bot.callback_query_handler(func=lambda call: call.data == "user_remove")
def handle_user_remove(call):
    """Mahsulot chiqarish"""
    bot.edit_message_text(
        MESSAGES["user_remove_product"],
        call.message.chat.id,
        call.message.message_id,
        reply_markup=branches_menu_user("remove")
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("user_remove_branch:"))
def handle_user_remove_branch(call):
    """Chiqarish uchun filial tanlash"""
    branch = call.data.split(":")[1]
    if branch == "common":
        branch = None
    
    user_id = call.from_user.id
    user_states[user_id] = {"action": "selecting_remove_product", "branch": branch}
    
    bot.edit_message_text(
        "📦 Mahsulotlarni tanlang:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=products_menu_user(branch, "remove"),
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("user_remove_product:"))
def handle_user_remove_product(call):
    """Mahsulot tanlash va miqdor kiritish"""
    product_name = call.data.split(":")[1]
    user_id = call.from_user.id
    
    data = user_states.get(user_id, {})
    data["action"] = "entering_remove_quantity"
    data["product_name"] = product_name
    user_states[user_id] = data
    
    bot.send_message(
        call.message.chat.id,
        f"📦 <b>{product_name}</b>\n\n{MESSAGES['user_enter_quantity']}",
        parse_mode="HTML",
        reply_markup=back_button("user_remove")
    )

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("action") == "entering_remove_quantity")
def process_remove_quantity(message):
    """Chiqarilish miqdorini qabul qilish"""
    try:
        quantity = int(message.text)
        if quantity <= 0:
            bot.send_message(message.chat.id, MESSAGES["error_invalid_quantity"])
            return
        
        user_id = message.from_user.id
        data = user_states.get(user_id, {})
        product_name = data.get("product_name")
        branch = data.get("branch")
        
        db = get_db()
        new_qty = db.remove_inventory(product_name, branch, quantity)
        
        bot.send_message(
            message.chat.id,
            MESSAGES["user_product_removed"].format(product_name, quantity, new_qty),
            reply_markup=products_menu_user(branch, "remove")
        )
        
        user_states.pop(user_id, None)
    except ValueError:
        bot.send_message(message.chat.id, MESSAGES["error_invalid_quantity"])

# ==================== USER LIST HANDLERS ====================

@bot.callback_query_handler(func=lambda call: call.data == "user_list")
def handle_user_list(call):
    """Mahsulotlar ro'yxati"""
    bot.edit_message_text(
        "📋 Ro'yxat\n\nFilial tanlang:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=list_branches_menu()
    )

# ==================== REQUEST HANDLERS ====================

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

# ==================== BACK HANDLERS ====================

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

@bot.callback_query_handler(func=lambda call: call.data == "product_branch_back")
def handle_product_branch_back(call):
    """Mahsulot turi tanlashga qaytish"""
    bot.edit_message_text(
        MESSAGES["product_management"],
        call.message.chat.id,
        call.message.message_id,
        reply_markup=product_type_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data == "product_type_back")
def handle_product_type_back(call):
    """Mahsulot turidan orqaga"""
    bot.edit_message_text(
        MESSAGES["product_management"],
        call.message.chat.id,
        call.message.message_id,
        reply_markup=product_type_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_branch")
def handle_admin_branch_back(call):
    """Admin branch menyuga qaytish"""
    bot.edit_message_text(
        MESSAGES["branch_management"],
        call.message.chat.id,
        call.message.message_id,
        reply_markup=branches_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data == "user_input_back")
def handle_user_input_back(call):
    """Kiritishdan orqaga"""
    user_id = call.from_user.id
    data = user_states.get(user_id, {})
    branch = data.get("branch")
    
    bot.edit_message_text(
        MESSAGES["user_add_product"],
        call.message.chat.id,
        call.message.message_id,
        reply_markup=branches_menu_user("input")
    )
    user_states.pop(user_id, None)

@bot.callback_query_handler(func=lambda call: call.data == "user_remove_back")
def handle_user_remove_back(call):
    """Chiqarishdan orqaga"""
    user_id = call.from_user.id
    user_states.pop(user_id, None)
    
    bot.edit_message_text(
        MESSAGES["user_remove_product"],
        call.message.chat.id,
        call.message.message_id,
        reply_markup=branches_menu_user("remove")
    )

# ==================== WEBHOOK (FLASK) ====================

@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    """Webhook endpoint"""
    try:
        json_str = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        logger.info("✅ Webhook received")
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
    return "ok", 200

@app.route('/')
def index():
    """Health check"""
    return "Bot is running", 200

# ==================== MAIN ====================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🤖 Bot ishga tushdi! Webhook path: /{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=port, debug=False)