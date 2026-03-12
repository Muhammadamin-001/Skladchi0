import telebot
import logging
import os
import time
from flask import Flask, request
from config.settings import BOT_TOKEN, ADMIN_ID, MESSAGES
from database.mongodb import init_db, get_db
from keyboards.telebot_keyboards import (
    admin_main_menu,
    branches_menu,
    back_button,
    product_types_menu,
    products_by_type_menu,
    product_type_actions_menu,
    user_main_menu,
    user_request_menu,
    product_types_menu_user,
    products_by_type_menu_user,
    branches_menu_user,
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
user_states = {}

# ==================== /START ====================

@bot.message_handler(commands=['start'])
def handle_start(message):
    """Bot /start qilish"""
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"
    first_name = message.from_user.first_name or "Foydalanuvchi"
    
    # ✅ STATE O'CHIRISH
    if user_id in user_states:
        old_state = user_states.pop(user_id)
        logger.info(f"🗑️ /start: {user_id} ning state o'chirildi: {old_state}")
    
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

# ==================== BRANCH MESSAGE HANDLERS ====================

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "waiting_branch_name")
def process_branch_add(message):
    """Filial nomini saqlash"""
    db = get_db()
    name = message.text.strip()
    user_id = message.from_user.id
    
    logger.info(f"📝 Branch handler: user_id={user_id}, text='{name}'")
    
    if not name:
        bot.send_message(message.chat.id, "❌ Filial nomi bo'sh bo'lishi mumkin emas")
        return
    
    if db.add_branch(name):
        user_states.pop(user_id, None)
        logger.info(f"✅ Filial qo'shildi: {name}")
        bot.send_message(message.chat.id, MESSAGES["branch_added"].format(name), reply_markup=branches_menu())
    else:
        user_states.pop(user_id, None)
        bot.send_message(message.chat.id, MESSAGES["branch_exists"], reply_markup=back_button("admin_branch"))

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("action") == "editing_branch")
def process_branch_edit(message):
    """Filial nomini o'zgartirish"""
    user_id = message.from_user.id
    data = user_states.get(user_id, {})
    old_name = data.get("old_name")
    new_name = message.text.strip()
    
    if not new_name:
        bot.send_message(message.chat.id, "❌ Filial nomi bo'sh bo'lishi mumkin emas")
        return
    
    db = get_db()
    if db.update_branch(old_name, new_name):
        user_states.pop(user_id, None)
        logger.info(f"✅ Filial tahrirlandi: {old_name} -> {new_name}")
        bot.send_message(message.chat.id, MESSAGES["branch_renamed"].format(new_name), reply_markup=branches_menu())
    else:
        user_states.pop(user_id, None)
        bot.send_message(message.chat.id, "❌ Xato yuz berdi", reply_markup=back_button("admin_branch"))

# ==================== PRODUCT TYPE MESSAGE HANDLERS ============
# ⚠️ PRIORITY: Bu handlers callback-lardan OLDIN baholanadi!

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "waiting_product_type_name")
def process_product_type_add(message):
    """Mahsulot turi nomini saqlash"""
    user_id = message.from_user.id
    name = message.text.strip()
    
    # ✅ STATE DOUBLE CHECK
    current_state = user_states.get(user_id)
    logger.info(f"🔴 PRODUCT TYPE MESSAGE: user_id={user_id}, text='{name}', current_state={current_state}, time={time.time()}")
    
    if current_state != "waiting_product_type_name":
        logger.warning(f"❌ State mismatch: expected 'waiting_product_type_name', got '{current_state}'")
        bot.send_message(message.chat.id, "❌ Avval /start bosing yoki Qo'shish tugmasini bosing")
        return
    
    if not name:
        logger.warning("❌ Bo'sh nom kiritildi")
        bot.send_message(message.chat.id, "❌ Tur nomi bo'sh bo'lishi mumkin emas")
        return
    
    db = get_db()
    
    try:
        if db.add_product_type(name):
            user_states.pop(user_id, None)
            logger.info(f"✅✅✅ TUR QO'SHILDI: '{name}'")
            
            bot.send_message(
                message.chat.id,
                f"✅ '{name}' turi qo'shildi!",
                reply_markup=product_types_menu()
            )
        else:
            logger.warning(f"❌ Tur mavjud: {name}")
            user_states.pop(user_id, None)
            
            bot.send_message(
                message.chat.id,
                f"❌ '{name}' turi allaqachon mavjud!",
                reply_markup=back_button("admin_product")
            )
    except Exception as e:
        logger.error(f"❌ Error adding product type: {e}")
        user_states.pop(user_id, None)
        bot.send_message(message.chat.id, f"❌ Xato yuz berdi: {e}")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("action") == "editing_product_type")
def process_product_type_edit(message):
    """Mahsulot turi nomini o'zgartirish"""
    user_id = message.from_user.id
    data = user_states.get(user_id, {})
    old_name = data.get("old_name")
    new_name = message.text.strip()
    
    if not new_name:
        bot.send_message(message.chat.id, "❌ Tur nomi bo'sh bo'lishi mumkin emas")
        return
    
    db = get_db()
    if db.update_product_type(old_name, new_name):
        user_states.pop(user_id, None)
        logger.info(f"✅ Tur tahrirlandi: {old_name} -> {new_name}")
        bot.send_message(message.chat.id, f"✅ '{new_name}' turi saqlandi!", reply_markup=product_types_menu())
    else:
        logger.warning(f"❌ Tur tahrirlashda xato: {old_name}")
        user_states.pop(user_id, None)
        bot.send_message(message.chat.id, "❌ Xato yuz berdi", reply_markup=back_button("admin_product"))

# ==================== PRODUCT MESSAGE HANDLERS ====================

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("action") == "editing_product")
def process_product_edit(message):
    """Mahsulot nomini o'zgartirish"""
    user_id = message.from_user.id
    data = user_states.get(user_id, {})
    old_name = data.get("old_name")
    new_name = message.text.strip()
    
    if not new_name:
        bot.send_message(message.chat.id, "❌ Mahsulot nomi bo'sh bo'lishi mumkin emas")
        return
    
    db = get_db()
    db.update_product(old_name, new_name)
    
    product_type = data.get("product_type")
    user_states.pop(user_id, None)
    
    bot.send_message(message.chat.id, MESSAGES["product_added"].format(new_name), reply_markup=products_by_type_menu(product_type))

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("action") == "adding_product")
def process_product_add_name(message):
    """Mahsulot nomini qabul qilish"""
    user_id = message.from_user.id
    data = user_states.get(user_id, {})
    product_name = message.text.strip()
    
    if not product_name:
        bot.send_message(message.chat.id, "❌ Mahsulot nomi bo'sh bo'lishi mumkin emas")
        return
    
    data["product_name"] = product_name
    data["action"] = "adding_product_image"
    user_states[user_id] = data
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("✅ Ha", callback_data="product_add_image_yes"),
        telebot.types.InlineKeyboardButton("❌ Yo'q", callback_data="product_add_image_no")
    )
    
    bot.send_message(message.chat.id, MESSAGES["product_add_image"], reply_markup=markup)

@bot.message_handler(content_types=['photo'], func=lambda message: user_states.get(message.from_user.id, {}).get("action") == "uploading_product_image")
def process_product_image(message):
    """Mahsulot rasmi qabul qilish"""
    user_id = message.from_user.id
    data = user_states.get(user_id, {})
    
    image_id = message.photo[-1].file_id
    
    db = get_db()
    db.add_product(data.get("product_name"), data.get("product_type"), image_id)
    
    product_type = data.get("product_type")
    user_states.pop(user_id, None)
    
    bot.send_message(
        message.chat.id,
        MESSAGES["product_added"].format(data.get("product_name")),
        reply_markup=products_by_type_menu(product_type)
    )

# ==================== QUANTITY MESSAGE HANDLERS ====================

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("action") == "entering_input_quantity")
def process_input_quantity(message):
    """Kiritilish miqdorini qabul qilish"""
    user_id = message.from_user.id
    
    try:
        quantity = int(message.text)
        if quantity <= 0:
            bot.send_message(message.chat.id, MESSAGES["error_invalid_quantity"])
            return
        
        data = user_states.get(user_id, {})
        product_name = data.get("product_name")
        branch = data.get("branch")
        product_type = data.get("product_type")
        
        db = get_db()
        new_qty = db.add_inventory(product_name, branch, quantity)
        
        user_states.pop(user_id, None)
        
        bot.send_message(
            message.chat.id,
            MESSAGES["user_product_added"].format(product_name, quantity, new_qty),
            reply_markup=products_by_type_menu_user(product_type, "input")
        )
    except ValueError:
        bot.send_message(message.chat.id, MESSAGES["error_invalid_quantity"])

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("action") == "entering_remove_quantity")
def process_remove_quantity(message):
    """Chiqarilish miqdorini qabul qilish"""
    user_id = message.from_user.id
    
    try:
        quantity = int(message.text)
        if quantity <= 0:
            bot.send_message(message.chat.id, MESSAGES["error_invalid_quantity"])
            return
        
        data = user_states.get(user_id, {})
        product_name = data.get("product_name")
        branch = data.get("branch")
        product_type = data.get("product_type")
        
        db = get_db()
        new_qty = db.remove_inventory(product_name, branch, quantity)
        
        user_states.pop(user_id, None)
        
        bot.send_message(
            message.chat.id,
            MESSAGES["user_product_removed"].format(product_name, quantity, new_qty),
            reply_markup=products_by_type_menu_user(product_type, "remove")
        )
    except ValueError:
        bot.send_message(message.chat.id, MESSAGES["error_invalid_quantity"])

# ==================== CALLBACK HANDLERS ====================

@bot.callback_query_handler(func=lambda call: call.data == "admin_branch")
def handle_admin_branch(call):
    """Admin filial boshqarish"""
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, MESSAGES["error_access_denied"], show_alert=True)
        return
    
    user_id = call.from_user.id
    user_states.pop(user_id, None)
    
    bot.edit_message_text(
        MESSAGES["branch_management"],
        call.message.chat.id,
        call.message.message_id,
        reply_markup=branches_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data == "branch_add")
def handle_branch_add(call):
    """Filial qo'shish"""
    user_id = call.from_user.id
    user_states[user_id] = "waiting_branch_name"
    logger.info(f"🟡 CALLBACK: branch_add, user_id={user_id}, state set to waiting_branch_name")
    
    bot.send_message(
        call.message.chat.id,
        MESSAGES["branch_add_prompt"],
        reply_markup=back_button("admin_branch")
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("branch_select:"))
def handle_branch_select(call):
    """Filial tanlash"""
    branch_name = call.data.split(":")[1]
    user_id = call.from_user.id
    user_states.pop(user_id, None)
    
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

@bot.callback_query_handler(func=lambda call: call.data.startswith("branch_edit:"))
def handle_branch_edit(call):
    """Filial tahrirlash"""
    branch_name = call.data.split(":")[1]
    user_id = call.from_user.id
    user_states[user_id] = {"action": "editing_branch", "old_name": branch_name}
    
    bot.send_message(
        call.message.chat.id,
        "✍️ Yangi filial nomini kiriting:",
        reply_markup=back_button("admin_branch")
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("branch_delete:"))
def handle_branch_delete(call):
    """Filial o'chirish"""
    branch_name = call.data.split(":")[1]
    user_id = call.from_user.id
    user_states.pop(user_id, None)
    
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
    """Admin mahsulotlarni boshqarish"""
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, MESSAGES["error_access_denied"], show_alert=True)
        return
    
    user_id = call.from_user.id
    user_states.pop(user_id, None)
    logger.info(f"🟡 CALLBACK: admin_product, user_id={user_id}, state cleared")
    
    bot.edit_message_text(
        MESSAGES["product_management"],
        call.message.chat.id,
        call.message.message_id,
        reply_markup=product_types_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("product_type_select:"))
def handle_product_type_select(call):
    """Mahsulot turini tanlash"""
    product_type = call.data.split(":")[1]
    user_id = call.from_user.id
    user_states[user_id] = {"action": "viewing_products", "product_type": product_type}
    
    bot.edit_message_text(
        f"📦 {product_type} Turidagi Mahsulotlar:\n\nMahsulot tanlang yoki yangi qo'shish:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=products_by_type_menu(product_type),
        parse_mode="HTML"
    )

# ⚠️ CRITICAL CALLBACK - PRODUCT TYPE ADD
@bot.callback_query_handler(func=lambda call: call.data == "product_type_add")
def handle_product_type_add(call):
    """Yangi mahsulot turi qo'shish"""
    user_id = call.from_user.id
    
    logger.info(f"🟡 CALLBACK: product_type_add CALLED, user_id={user_id}, time={time.time()}")
    
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
        logger.info(f"✅ Callback xabari o'chirildi")
    except Exception as e:
        logger.warning(f"⚠️ Xabarni o'chirishda xato: {e}")
    
    # ✅ STATE SET
    user_states[user_id] = "waiting_product_type_name"
    logger.info(f"✅ State set: waiting_product_type_name for user {user_id}")
    
    # ✅ XABAR YUBORISH
    bot.send_message(
        call.message.chat.id,
        "✍️ Mahsulot turi (brend) nomini kiriting:",
        reply_markup=back_button("admin_product")
    )
    
    logger.info(f"✅ Message handler uchun xabar yuborildi. Now waiting for text input...")
    logger.info(f"✅ Current state: {user_states.get(user_id)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("product_type_edit:"))
def handle_product_type_edit(call):
    """Mahsulot turini tahrirlash"""
    product_type = call.data.split(":")[1]
    user_id = call.from_user.id
    user_states[user_id] = {"action": "editing_product_type", "old_name": product_type}
    
    bot.send_message(
        call.message.chat.id,
        "✍️ Yangi tur nomini kiriting:",
        reply_markup=back_button("admin_product")
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("product_type_delete:"))
def handle_product_type_delete(call):
    """Mahsulot turini o'chirish"""
    product_type = call.data.split(":")[1]
    user_id = call.from_user.id
    user_states.pop(user_id, None)
    
    db = get_db()
    db.delete_product_type(product_type)
    
    bot.edit_message_text(
        f"🗑️ '{product_type}' turi o'chirildi",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=product_types_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("product_type_actions:"))
def handle_product_type_actions(call):
    """Mahsulot turi faoliyatlari"""
    product_type = call.data.split(":")[1]
    user_id = call.from_user.id
    user_states[user_id] = {"action": "viewing_type", "product_type": product_type}
    
    bot.edit_message_text(
        f"📦 <b>{product_type}</b>\n\nFaoliyatni tanlang:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=product_type_actions_menu(product_type),
        parse_mode="HTML"
    )

# ==================== PRODUCT CALLBACKS ====================

@bot.callback_query_handler(func=lambda call: call.data.startswith("product_select:"))
def handle_product_select(call):
    """Mahsulotni tanlash"""
    product_name = call.data.split(":")[1]
    user_id = call.from_user.id
    data = user_states.get(user_id, {})
    product_type = data.get("product_type")
    
    db = get_db()
    product = db.get_product_by_name(product_name)
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton(MESSAGES["button_edit"], callback_data=f"product_edit:{product_name}"),
        telebot.types.InlineKeyboardButton(MESSAGES["button_delete"], callback_data=f"product_delete:{product_name}")
    )
    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data="product_type_back"))
    
    text = f"📦 <b>{product_name}</b>\n\nFaoliyatni tanlang:"
    
    if product and product.get("image_id"):
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_photo(
                call.message.chat.id,
                product["image_id"],
                caption=text,
                reply_markup=markup,
                parse_mode="HTML"
            )
        except:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
    else:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("product_edit:"))
def handle_product_edit(call):
    """Mahsulot tahrirlash"""
    product_name = call.data.split(":")[1]
    user_id = call.from_user.id
    user_states[user_id] = {"action": "editing_product", "old_name": product_name}
    
    bot.send_message(
        call.message.chat.id,
        "✍️ Yangi mahsulot nomini kiriting:",
        reply_markup=back_button("product_type_back")
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("product_delete:"))
def handle_product_delete(call):
    """Mahsulot o'chirish"""
    product_name = call.data.split(":")[1]
    user_id = call.from_user.id
    
    db = get_db()
    db.delete_product(product_name)
    
    data = user_states.get(user_id, {})
    product_type = data.get("product_type")
    user_states.pop(user_id, None)
    
    bot.edit_message_text(
        MESSAGES["product_deleted"],
        call.message.chat.id,
        call.message.message_id,
        reply_markup=products_by_type_menu(product_type)
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("product_add:"))
def handle_product_add(call):
    """Mahsulot qo'shish"""
    product_type = call.data.split(":")[1]
    
    user_id = call.from_user.id
    user_states[user_id] = {"action": "adding_product", "product_type": product_type}
    
    bot.send_message(
        call.message.chat.id,
        MESSAGES["product_add_name"],
        reply_markup=back_button("product_type_back")
    )

@bot.callback_query_handler(func=lambda call: call.data == "product_add_image_yes")
def handle_product_image_yes(call):
    """Rasm yuklash kerak"""
    user_id = call.from_user.id
    user_states[user_id]["action"] = "uploading_product_image"
    
    bot.send_message(
        call.message.chat.id,
        MESSAGES["product_send_image"],
        reply_markup=back_button("product_type_back")
    )

@bot.callback_query_handler(func=lambda call: call.data == "product_add_image_no")
def handle_product_image_no(call):
    """Rasm talab qilinmadi"""
    user_id = call.from_user.id
    data = user_states.get(user_id, {})
    
    db = get_db()
    db.add_product(data.get("product_name"), data.get("product_type"))
    
    product_type = data.get("product_type")
    user_states.pop(user_id, None)
    
    bot.edit_message_text(
        MESSAGES["product_added"].format(data.get("product_name")),
        call.message.chat.id,
        call.message.message_id,
        reply_markup=products_by_type_menu(product_type)
    )

# ==================== LIST CALLBACKS ====================

@bot.callback_query_handler(func=lambda call: call.data == "admin_list")
def handle_admin_list(call):
    """Admin ro'yxat"""
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, MESSAGES["error_access_denied"], show_alert=True)
        return
    
    user_id = call.from_user.id
    user_states.pop(user_id, None)
    
    db = get_db()
    branches = db.get_all_branches()
    
    markup = telebot.types.InlineKeyboardMarkup()
    for branch in branches:
        markup.add(telebot.types.InlineKeyboardButton(
            text=branch["name"],
            callback_data=f"admin_list_branch:{branch['name']}"
        ))
    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data="admin_back"))
    
    bot.edit_message_text(
        "📋 Filial tanlang:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_list_branch:"))
def handle_admin_list_branch(call):
    """Admin filial ro'yxati"""
    branch = call.data.split(":")[1]
    
    db = get_db()
    inventory = db.get_inventory_by_branch(branch)
    
    text = f"📋 <b>{branch}</b> - Mahsulotlar Ro'yxati\n\n"
    
    if not inventory:
        text = f"📋 <b>{branch}</b> - Mahsulotlar Yo'q"
    else:
        for idx, item in enumerate(inventory, 1):
            quantity = item.get("quantity", 0)
            text += f"{idx}. {item['product_name']}: <b>{quantity}</b> dona\n"
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=back_button("admin_list"),
        parse_mode="HTML"
    )

# ==================== USER INPUT CALLBACKS ====================

@bot.callback_query_handler(func=lambda call: call.data == "user_input")
def handle_user_input(call):
    """Mahsulot kiritish"""
    user_id = call.from_user.id
    user_states.pop(user_id, None)
    
    bot.edit_message_text(
        "📦 Mahsulot Kiritamiz\n\nMahsulot turini tanlang:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=product_types_menu_user("input")
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("user_input_type:"))
def handle_user_input_type(call):
    """Kiritish uchun mahsulot turi tanlash"""
    product_type = call.data.split(":")[1]
    
    user_id = call.from_user.id
    user_states[user_id] = {"action": "selecting_input_product", "product_type": product_type}
    
    bot.edit_message_text(
        f"📦 {product_type} - Mahsulotlarni tanlang:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=products_by_type_menu_user(product_type, "input"),
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("user_input_product:"))
def handle_user_input_product(call):
    """Mahsulot tanlash"""
    product_name = call.data.split(":")[1]
    user_id = call.from_user.id
    
    data = user_states.get(user_id, {})
    data["action"] = "selecting_input_branch"
    data["product_name"] = product_name
    user_states[user_id] = data
    
    db = get_db()
    product = db.get_product_by_name(product_name)
    
    text = f"📦 <b>{product_name}</b>\n\n🏢 Qaysi filialga kiritmoqchisiz?"
    
    if product and product.get("image_id"):
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_photo(
                call.message.chat.id,
                product["image_id"],
                caption=text,
                reply_markup=branches_menu_user("input"),
                parse_mode="HTML"
            )
        except:
            bot.send_message(
                call.message.chat.id,
                text,
                parse_mode="HTML",
                reply_markup=branches_menu_user("input")
            )
    else:
        bot.send_message(
            call.message.chat.id,
            text,
            parse_mode="HTML",
            reply_markup=branches_menu_user("input")
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("user_input_branch:"))
def handle_user_input_branch(call):
    """Kiritish filiali tanlandi"""
    branch = call.data.split(":")[1]
    user_id = call.from_user.id
    
    data = user_states.get(user_id, {})
    data["action"] = "entering_input_quantity"
    data["branch"] = branch
    user_states[user_id] = data
    
    product_name = data.get("product_name")
    
    bot.send_message(
        call.message.chat.id,
        f"📦 <b>{product_name}</b>\n🏢 <b>{branch}</b>\n\n{MESSAGES['user_enter_quantity']}",
        parse_mode="HTML",
        reply_markup=back_button("user_input_back")
    )

# ==================== USER REMOVE CALLBACKS ====================

@bot.callback_query_handler(func=lambda call: call.data == "user_remove")
def handle_user_remove(call):
    """Mahsulot chiqarish"""
    user_id = call.from_user.id
    user_states.pop(user_id, None)
    
    bot.edit_message_text(
        "📦 Mahsulot Chiqaramiz\n\nMahsulot turini tanlang:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=product_types_menu_user("remove")
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("user_remove_type:"))
def handle_user_remove_type(call):
    """Chiqarish uchun mahsulot turi tanlash"""
    product_type = call.data.split(":")[1]
    
    user_id = call.from_user.id
    user_states[user_id] = {"action": "selecting_remove_product", "product_type": product_type}
    
    bot.edit_message_text(
        f"📦 {product_type} - Mahsulotlarni tanlang:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=products_by_type_menu_user(product_type, "remove"),
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("user_remove_product:"))
def handle_user_remove_product(call):
    """Mahsulot tanlash"""
    product_name = call.data.split(":")[1]
    user_id = call.from_user.id
    
    data = user_states.get(user_id, {})
    data["action"] = "selecting_remove_branch"
    data["product_name"] = product_name
    user_states[user_id] = data
    
    db = get_db()
    product = db.get_product_by_name(product_name)
    
    text = f"📦 <b>{product_name}</b>\n\n🏢 Qaysi filialdan chiqarmoqchisiz?"
    
    if product and product.get("image_id"):
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_photo(
                call.message.chat.id,
                product["image_id"],
                caption=text,
                reply_markup=branches_menu_user("remove"),
                parse_mode="HTML"
            )
        except:
            bot.send_message(
                call.message.chat.id,
                text,
                parse_mode="HTML",
                reply_markup=branches_menu_user("remove")
            )
    else:
        bot.send_message(
            call.message.chat.id,
            text,
            parse_mode="HTML",
            reply_markup=branches_menu_user("remove")
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("user_remove_branch:"))
def handle_user_remove_branch(call):
    """Chiqarish filiali tanlandi"""
    branch = call.data.split(":")[1]
    user_id = call.from_user.id
    
    data = user_states.get(user_id, {})
    data["action"] = "entering_remove_quantity"
    data["branch"] = branch
    user_states[user_id] = data
    
    product_name = data.get("product_name")
    db = get_db()
    inventory = db.get_inventory(product_name, branch)
    current_qty = inventory.get("quantity", 0)
    
    bot.send_message(
        call.message.chat.id,
        f"📦 <b>{product_name}</b>\n🏢 <b>{branch}</b>\n📊 Mavjud: <b>{current_qty}</b> dona\n\n{MESSAGES['user_enter_quantity']}",
        parse_mode="HTML",
        reply_markup=back_button("user_remove_back")
    )

# ==================== USER LIST CALLBACKS ====================

@bot.callback_query_handler(func=lambda call: call.data == "user_list")
def handle_user_list(call):
    """Mahsulotlar ro'yxati"""
    user_id = call.from_user.id
    user_states.pop(user_id, None)
    
    bot.edit_message_text(
        "📋 Ro'yxat\n\nFilial tanlang:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=list_branches_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("list_branch:"))
def handle_list_branch(call):
    """Filial ro'yxati"""
    branch = call.data.split(":")[1]
    
    db = get_db()
    inventory = db.get_inventory_by_branch(branch)
    
    text = MESSAGES["list_title"] + "\n\n"
    
    if not inventory:
        text = MESSAGES["list_empty"]
    else:
        for idx, item in enumerate(inventory, 1):
            quantity = item.get("quantity", 0)
            text += f"{idx}. {item['product_name']}: <b>{quantity}</b> dona\n"
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=back_button("user_list"),
        parse_mode="HTML"
    )

# ==================== REQUEST HANDLERS ====================

@bot.callback_query_handler(func=lambda call: call.data == "send_request")
def handle_send_request(call):
    """So'rov yuborish"""
    user_id = call.from_user.id
    username = call.from_user.username or "NoUsername"
    
    user_states.pop(user_id, None)
    
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
    user_id = call.from_user.id
    user_states.pop(user_id, None)
    
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "admin_back")
def handle_admin_back(call):
    """Admin orqaga"""
    user_id = call.from_user.id
    user_states.pop(user_id, None)
    
    bot.edit_message_text(
        MESSAGES["start_admin"],
        call.message.chat.id,
        call.message.message_id,
        reply_markup=admin_main_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data == "user_main")
def handle_user_main(call):
    """Foydalanuvchi asosiy menyu"""
    user_id = call.from_user.id
    user_states.pop(user_id, None)
    
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    bot.send_message(call.message.chat.id, "👋 Asosiy Menyu", reply_markup=user_main_menu())

@bot.callback_query_handler(func=lambda call: call.data == "product_type_back")
def handle_product_type_back(call):
    """Mahsulot turiga qaytish"""
    user_id = call.from_user.id
    user_states.pop(user_id, None)
    
    bot.edit_message_text(
        MESSAGES["product_management"],
        call.message.chat.id,
        call.message.message_id,
        reply_markup=product_types_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data == "user_input_back")
def handle_user_input_back(call):
    """Kiritishdan orqaga"""
    user_id = call.from_user.id
    data = user_states.get(user_id, {})
    product_type = data.get("product_type")
    user_states.pop(user_id, None)
    
    if product_type:
        bot.edit_message_text(
            f"📦 {product_type} - Mahsulotlarni tanlang:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=products_by_type_menu_user(product_type, "input"),
            parse_mode="HTML"
        )

@bot.callback_query_handler(func=lambda call: call.data == "user_remove_back")
def handle_user_remove_back(call):
    """Chiqarishdan orqaga"""
    user_id = call.from_user.id
    data = user_states.get(user_id, {})
    product_type = data.get("product_type")
    user_states.pop(user_id, None)
    
    if product_type:
        bot.edit_message_text(
            f"📦 {product_type} - Mahsulotlarni tanlang:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=products_by_type_menu_user(product_type, "remove"),
            parse_mode="HTML"
        )

@bot.callback_query_handler(func=lambda call: call.data == "user_list_back")
def handle_user_list_back(call):
    """Ro'yxatdan orqaba"""
    user_id = call.from_user.id
    user_states.pop(user_id, None)
    
    bot.edit_message_text(
        "📋 Ro'yxat\n\nFilial tanlang:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=list_branches_menu()
    )

# ==================== WEBHOOK ====================

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