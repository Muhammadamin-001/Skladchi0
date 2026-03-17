import telebot
import logging
import os
import time
from flask import Flask, request
from config.settings import BOT_TOKEN, ADMIN_ID, MESSAGES
from database.mongodb import init_db, get_db
from keyboards.telebot_keyboards import (
    admin_main_menu,
    warehouse_list_menu,
    warehouse_actions_menu,
    branches_menu,
    back_button,
    product_types_menu,
    products_by_type_menu,
    product_type_actions_menu,
    branches_selection_menu,
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

def _show_product_types_message(chat_id, message_id, warehouse, branch):
    """Mahsulot turlari oynasini rasm bo'lsa caption orqali, bo'lmasa text orqali yangilash"""
    branch_display = branch if branch != "common" else "🌍 Umumiy Bo'lim"
    text = f"📦 {branch_display}\n\nMahsulot turini tanlang yoki yangi qo'shish:"
    markup = product_types_menu(warehouse, branch)

    db = get_db()
    types = db.get_all_product_types(warehouse, branch)
    image_id = next((ptype.get("image_id") for ptype in types if ptype.get("image_id")), None)

    if image_id:
        try:
            bot.edit_message_caption(
                caption=text,
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=markup,
                parse_mode="HTML",
            )
            return
        except Exception:
            pass

        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass

        bot.send_photo(chat_id, image_id, caption=text, reply_markup=markup, parse_mode="HTML")
        return

    try:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="HTML")
    except Exception:
        try:
            bot.edit_message_caption(caption=text, chat_id=chat_id, message_id=message_id, reply_markup=markup, parse_mode="HTML")
        except Exception:
            bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")


def _show_products_by_type_message(chat_id, message_id, warehouse, branch, product_type):
    """Mahsulot ro'yxatini tur rasmi bilan doim qayta ko'rsatish"""
    db = get_db()
    ptype = db.get_product_type_by_name(product_type, warehouse, branch)
    text = f"📦 {product_type}\n\nMahsulot tanlang yoki yangi qo'shish:"
    markup = products_by_type_menu(warehouse, branch, product_type)

    if ptype and ptype.get("image_id"):
        try:
            bot.edit_message_media(
                media=telebot.types.InputMediaPhoto(ptype["image_id"], caption=text, parse_mode="HTML"),
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=markup,
            )
            return
        except Exception:
            pass

        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass

        bot.send_photo(chat_id, ptype["image_id"], caption=text, reply_markup=markup, parse_mode="HTML")
        return

    try:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="HTML")
    except Exception:
        try:
            bot.edit_message_caption(caption=text, chat_id=chat_id, message_id=message_id, reply_markup=markup, parse_mode="HTML")
        except Exception:
            bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")


def _show_product_details_message(chat_id, message_id, warehouse, branch, product_type, product_name):
    """Mahsulot detali: yuqorida tur rasmi, pastda nom va amallar"""
    db = get_db()
    ptype = db.get_product_type_by_name(product_type, warehouse, branch)
    product = db.get_product_by_name(product_name, warehouse, branch, product_type)
    product_code = product.get("code") if product else "-"

    text = (
        f"📦 <b>{product_name}</b>\n"
        f"🔢 Kod: <b>{product_code}</b>\n\n"
        "Amalni tanlang:"
    )

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton(
            "✏️ Tahrirlash",
            callback_data=f"product_edit:{warehouse}:{branch}:{product_type}:{product_name}",
        ),
        telebot.types.InlineKeyboardButton(
            "🗑️ O'chirish",
            callback_data=f"product_delete:{warehouse}:{branch}:{product_type}:{product_name}",
        ),
    )
    markup.add(
        telebot.types.InlineKeyboardButton(
            MESSAGES["button_back"], callback_data=f"product_list_back:{warehouse}:{branch}:{product_type}"
        )
    )

    if ptype and ptype.get("image_id"):
        try:
            bot.edit_message_media(
                media=telebot.types.InputMediaPhoto(ptype["image_id"], caption=text, parse_mode="HTML"),
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=markup,
            )
            return
        except Exception:
            pass

        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass
        bot.send_photo(chat_id, ptype["image_id"], caption=text, reply_markup=markup, parse_mode="HTML")
        return

    try:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="HTML")
    except Exception:
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
        
        
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
        logger.info(f"🗑️ /start: {user_id} ning state o'chirildi")
    
    db = get_db()
    user = db.get_user(user_id)
    
    if user_id == ADMIN_ID:
        # ✅ ADMIN: SKLAD RO'YXATI BIRINCHI!
        bot.send_message(
            user_id,
            "👤 Salom, Administrator!\n\nIshlash uchun skladni tanlang:",
            reply_markup=warehouse_list_menu()
        )
    elif user and user.get("approved"):
        bot.send_message(user_id, MESSAGES["start_user_approved"].format(first_name), reply_markup=user_main_menu())
    else:
        if not user:
            db.add_user(user_id, username, first_name, approved=False)
        bot.send_message(user_id, MESSAGES["start_user_unapproved"], reply_markup=user_request_menu())

# ==================== WAREHOUSE HANDLERS ====================

@bot.callback_query_handler(func=lambda call: call.data == "warehouse_list")
def handle_warehouse_list(call):
    """Sklad ro'yxati"""
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, MESSAGES["error_access_denied"], show_alert=True)
        return
    
    user_id = call.from_user.id
    user_states.pop(user_id, None)
    
    bot.edit_message_text(
        "🏭 Skladlar ro'yxati:\n\nSklad tanlang yoki yangi qo'shish:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=warehouse_list_menu()
    )

# ✅ WAREHOUSE ADD
@bot.callback_query_handler(func=lambda call: call.data == "warehouse_add")
def handle_warehouse_add(call):
    """Yangi sklad qo'shish"""
    user_id = call.from_user.id
    
    logger.info(f"🟡 CALLBACK: warehouse_add for user {user_id}")
    
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    
    user_states[user_id] = "waiting_warehouse_name"
    logger.info(f"✅ State set: waiting_warehouse_name")
    
    bot.send_message(
        call.message.chat.id,
        "✍️ Sklad nomini kiriting:",
        reply_markup=back_button("warehouse_list")
    )

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "waiting_warehouse_name")
def process_warehouse_add(message):
    """Sklad nomini saqlash"""
    user_id = message.from_user.id
    name = message.text.strip()
    
    logger.info(f"🔴 WAREHOUSE MESSAGE: user_id={user_id}, text='{name}', state={user_states.get(user_id)}")
    
    if user_states.get(user_id) != "waiting_warehouse_name":
        logger.warning(f"❌ State mismatch")
        bot.send_message(message.chat.id, "❌ Avval /start bosing")
        return
    
    if not name:
        bot.send_message(message.chat.id, "❌ Sklad nomi bo'sh bo'lishi mumkin emas")
        return
    
    db = get_db()
    
    if db.add_warehouse(name):
        user_states.pop(user_id, None)
        logger.info(f"✅ Warehouse added: '{name}'")
        
        bot.send_message(
            message.chat.id,
            f"✅ '{name}' skladi qo'shildi!",
            reply_markup=warehouse_list_menu()
        )
    else:
        user_states.pop(user_id, None)
        logger.warning(f"❌ Warehouse already exists: '{name}'")
        
        bot.send_message(
            message.chat.id,
            f"❌ '{name}' skladi allaqachon mavjud!",
            reply_markup=back_button("warehouse_list")
        )

# ✅ WAREHOUSE SELECT
@bot.callback_query_handler(func=lambda call: call.data.startswith("warehouse_select:"))
def handle_warehouse_select(call):
    """Skladni tanlash"""
    warehouse_name = call.data.split(":")[1]
    user_id = call.from_user.id
    
    user_states[user_id] = {"action": "viewing_warehouse", "warehouse": warehouse_name}
    
    bot.edit_message_text(
        f"👤 Salom, Administrator!\n\n🏭 Sklad: <b>{warehouse_name}</b>\n\nIshlash uchun tugmani tanlang:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=admin_main_menu(warehouse_name),
        parse_mode="HTML"
    )

# ✅ WAREHOUSE ACTIONS
@bot.callback_query_handler(func=lambda call: call.data.startswith("warehouse_actions:"))
def handle_warehouse_actions(call):
    """Sklad faoliyatlari"""
    warehouse_name = call.data.split(":")[1]
    user_id = call.from_user.id
    
    user_states[user_id] = {"action": "viewing_warehouse", "warehouse": warehouse_name}
    
    bot.edit_message_text(
        f"🏭 <b>{warehouse_name}</b>\n\nFaoliyatni tanlang:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=warehouse_actions_menu(warehouse_name),
        parse_mode="HTML"
    )

# ✅ WAREHOUSE EDIT
@bot.callback_query_handler(func=lambda call: call.data.startswith("warehouse_edit:"))
def handle_warehouse_edit(call):
    """Sklad tahrirlash"""
    warehouse_name = call.data.split(":")[1]
    user_id = call.from_user.id
    
    user_states[user_id] = {"action": "editing_warehouse", "old_name": warehouse_name}
    
    bot.send_message(
        call.message.chat.id,
        "✍️ Yangi sklad nomini kiriting:",
        reply_markup=back_button("warehouse_list")
    )

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("action") == "editing_warehouse")
def process_warehouse_edit(message):
    """Sklad nomini o'zgartirish"""
    user_id = message.from_user.id
    data = user_states.get(user_id, {})
    old_name = data.get("old_name")
    new_name = message.text.strip()
    
    if not new_name:
        bot.send_message(message.chat.id, "❌ Sklad nomi bo'sh bo'lishi mumkin emas")
        return
    
    db = get_db()
    if db.update_warehouse(old_name, new_name):
        user_states.pop(user_id, None)
        logger.info(f"✅ Warehouse renamed: {old_name} -> {new_name}")
        bot.send_message(
            message.chat.id,
            f"✅ '{new_name}' nomiga o'zgartirildi!",
            reply_markup=warehouse_list_menu()
        )
    else:
        user_states.pop(user_id, None)
        bot.send_message(message.chat.id, "❌ Xato yuz berdi", reply_markup=back_button("warehouse_list"))

# ✅ WAREHOUSE DELETE
@bot.callback_query_handler(func=lambda call: call.data.startswith("warehouse_delete:"))
def handle_warehouse_delete(call):
    """Sklad o'chirish"""
    warehouse_name = call.data.split(":")[1]
    user_id = call.from_user.id
    
    user_states[user_id] = {"action": "confirming_delete", "warehouse": warehouse_name}
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("✅ Ha", callback_data=f"warehouse_delete_confirm:{warehouse_name}"),
        telebot.types.InlineKeyboardButton("❌ Yo'q", callback_data="warehouse_list")
    )
    
    bot.send_message(
        call.message.chat.id,
        f"⚠️ '{warehouse_name}' skladini o'chirasizmi?\n\nBu amalni qaytarib bo'lmaydi!",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("warehouse_delete_confirm:"))
def handle_warehouse_delete_confirm(call):
    """Sklad o'chirishni tasdiqlash"""
    warehouse_name = call.data.split(":")[1]
    user_id = call.from_user.id
    
    db = get_db()
    db.delete_warehouse(warehouse_name)
    
    user_states.pop(user_id, None)
    
    bot.edit_message_text(
        f"🗑️ '{warehouse_name}' skladi o'chirildi",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=warehouse_list_menu()
    )

# ==================== BRANCH HANDLERS ====================

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_branch:"))
def handle_admin_branch(call):
    """Admin filial boshqarish"""
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, MESSAGES["error_access_denied"], show_alert=True)
        return
    
    warehouse = call.data.split(":")[1]
    user_id = call.from_user.id
    user_states[user_id] = {"warehouse": warehouse}
    
    bot.edit_message_text(
        MESSAGES["branch_management"],
        call.message.chat.id,
        call.message.message_id,
        reply_markup=branches_menu(warehouse)
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("branch_add:"))
def handle_branch_add(call):
    """Filial qo'shish"""
    warehouse = call.data.split(":")[1]
    user_id = call.from_user.id
    
    user_states[user_id] = {"warehouse": warehouse}
    
    bot.send_message(
        call.message.chat.id,
        MESSAGES["branch_add_prompt"],
        reply_markup=back_button(f"admin_branch:{warehouse}")
    )
    user_states[user_id] = {"warehouse": warehouse, "state": "waiting_branch_name"}

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("state") == "waiting_branch_name")
def process_branch_add(message):
    """Filial nomini saqlash"""
    db = get_db()
    name = message.text.strip()
    user_id = message.from_user.id
    
    warehouse = user_states.get(user_id, {}).get("warehouse")
    
    logger.info(f"📝 Branch handler: user_id={user_id}, text='{name}', warehouse='{warehouse}'")
    
    if not name:
        bot.send_message(message.chat.id, "❌ Filial nomi bo'sh bo'lishi mumkin emas")
        return
    
    if db.add_branch(name, warehouse):
        user_states.pop(user_id, None)
        logger.info(f"✅ Filial qo'shildi: {name}")
        bot.send_message(
            message.chat.id,
            MESSAGES["branch_added"].format(name),
            reply_markup=branches_menu(warehouse)
        )
    else:
        user_states.pop(user_id, None)
        bot.send_message(
            message.chat.id,
            MESSAGES["branch_exists"],
            reply_markup=back_button(f"admin_branch:{warehouse}")
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("branch_select:"))
def handle_branch_select(call):
    """Filial tanlash"""
    parts = call.data.split(":")
    warehouse = parts[1]
    branch_name = parts[2]
    
    user_id = call.from_user.id
    user_states[user_id] = {"warehouse": warehouse, "branch": branch_name}
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton(MESSAGES["button_edit"], callback_data=f"branch_edit:{warehouse}:{branch_name}"),
        telebot.types.InlineKeyboardButton(MESSAGES["button_delete"], callback_data=f"branch_delete:{warehouse}:{branch_name}")
    )
    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data=f"admin_branch:{warehouse}"))
    
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
    parts = call.data.split(":")
    warehouse = parts[1]
    branch_name = parts[2]
    
    user_id = call.from_user.id
    user_states[user_id] = {"action": "editing_branch", "warehouse": warehouse, "old_name": branch_name}
    
    bot.send_message(
        call.message.chat.id,
        "✍️ Yangi filial nomini kiriting:",
        reply_markup=back_button(f"admin_branch:{warehouse}")
    )

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("action") == "editing_branch")
def process_branch_edit(message):
    """Filial nomini o'zgartirish"""
    user_id = message.from_user.id
    data = user_states.get(user_id, {})
    warehouse = data.get("warehouse")
    old_name = data.get("old_name")
    new_name = message.text.strip()
    
    if not new_name:
        bot.send_message(message.chat.id, "❌ Filial nomi bo'sh bo'lishi mumkin emas")
        return
    
    db = get_db()
    if db.update_branch(old_name, new_name, warehouse):
        user_states.pop(user_id, None)
        logger.info(f"✅ Filial tahrirlandi: {old_name} -> {new_name}")
        bot.send_message(
            message.chat.id,
            MESSAGES["branch_renamed"].format(new_name),
            reply_markup=branches_menu(warehouse)
        )
    else:
        user_states.pop(user_id, None)
        bot.send_message(message.chat.id, "❌ Xato yuz berdi", reply_markup=back_button(f"admin_branch:{warehouse}"))

@bot.callback_query_handler(func=lambda call: call.data.startswith("branch_delete:"))
def handle_branch_delete(call):
    """Filial o'chirish"""
    parts = call.data.split(":")
    warehouse = parts[1]
    branch_name = parts[2]
    
    db = get_db()
    db.delete_branch(branch_name, warehouse)
    
    user_id = call.from_user.id
    user_states.pop(user_id, None)
    
    bot.edit_message_text(
        MESSAGES["branch_deleted"],
        call.message.chat.id,
        call.message.message_id,
        reply_markup=branches_menu(warehouse)
    )

# ==================== ADMIN PRODUCT HANDLERS ====================

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_product:"))
def handle_admin_product(call):
    """Admin mahsulot tanlash - FILIALLAR RO'YXATI BIRINCHI"""
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, MESSAGES["error_access_denied"], show_alert=True)
        return
    
    warehouse = call.data.split(":")[1]
    user_id = call.from_user.id
    user_states[user_id] = {"warehouse": warehouse}
    
    bot.edit_message_text(
        "🏢 Filial tanlang yoki Umumiy:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=branches_selection_menu(warehouse),
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("product_branch_select:"))
def handle_product_branch_select(call):
    """Mahsulot turi tanlash uchun filial tanlandi"""
    parts = call.data.split(":")
    warehouse = parts[1]
    branch = parts[2] if len(parts) > 2 else "common"
    
    user_id = call.from_user.id
    user_states[user_id] = {"warehouse": warehouse, "branch": branch}
    
    branch_display = branch if branch != "common" else "🌍 Umumiy Bo'lim"
    
    bot.edit_message_text(
        f"📦 {branch_display}\n\nMahsulot turini tanlang yoki yangi qo'shish:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=product_types_menu(warehouse, branch),
        parse_mode="HTML"
    )

# ✅ PRODUCT TYPE ADD - RASM BILAN!
@bot.callback_query_handler(func=lambda call: call.data.startswith("product_type_add:"))
def handle_product_type_add(call):
    """Yangi mahsulot turi qo'shish"""
    parts = call.data.split(":")
    warehouse = parts[1]
    branch = parts[2] if len(parts) > 2 else "common"
    
    user_id = call.from_user.id
    
    logger.info(f"🟡 CALLBACK: product_type_add for warehouse={warehouse}, branch={branch}")
    
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    
    user_states[user_id] = {
        "action": "waiting_product_type_name",
        "warehouse": warehouse,
        "branch": branch
    }
    
    bot.send_message(
        call.message.chat.id,
        "✍️ Mahsulot turi (brend) nomini kiriting:",
        reply_markup=back_button(f"product_branch_select:{warehouse}:{branch}")
    )

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("action") == "waiting_product_type_name")
def process_product_type_add(message):
    """Mahsulot turi nomini saqlash"""
    user_id = message.from_user.id
    name = message.text.strip()
    
    current_state = user_states.get(user_id, {})
    logger.info(f"🔴 PRODUCT TYPE MESSAGE: user_id={user_id}, text='{name}', state={current_state}")
    
    if current_state.get("action") != "waiting_product_type_name":
        logger.warning(f"❌ State mismatch")
        bot.send_message(message.chat.id, "❌ Avval /start bosing")
        return
    
    if not name:
        bot.send_message(message.chat.id, "❌ Tur nomi bo'sh bo'lishi mumkin emas")
        return
    
    # ✅ RASM KERAK MI DEB SO'RASH!
    user_states[user_id] = {
        "action": "adding_product_type",
        "product_type_name": name,
        "warehouse": current_state.get("warehouse"),
        "branch": current_state.get("branch", "common")
    }
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("✅ Ha", callback_data="product_type_image_yes"),
        telebot.types.InlineKeyboardButton("❌ Yo'q", callback_data="product_type_image_no")
    )
    
    bot.send_message(
        message.chat.id,
        f"Mahsulot turi: <b>{name}</b>\n\n🖼️ Rasm kerakmi?",
        reply_markup=markup,
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "product_type_image_yes")
def handle_product_type_image_yes(call):
    """Rasm yuklash kerak"""
    user_id = call.from_user.id
    if user_id not in user_states or not isinstance(user_states[user_id], dict):
        bot.answer_callback_query(call.id, "Holat topilmadi, qayta urinib ko'ring", show_alert=True)
        return

    user_states[user_id]["action"] = "uploading_product_type_image"
    
    bot.send_message(
        call.message.chat.id,
        "📷 Mahsulot turi uchun rasm yuboring:",
        reply_markup=back_button("product_type_image_cancel")
    )

@bot.message_handler(content_types=['photo'], func=lambda message: user_states.get(message.from_user.id, {}).get("action") == "uploading_product_type_image")
def process_product_type_image(message):
    """Mahsulot turi rasmi qabul qilish"""
    user_id = message.from_user.id
    data = user_states.get(user_id, {})
    
    image_id = message.photo[-1].file_id
    
    db = get_db()
    db.add_product_type(
        data.get("product_type_name"),
        image_id,
        data.get("warehouse"),
        data.get("branch", "common")
    )
    
    logger.info(f"✅ Product type saved with image: '{data.get('product_type_name')}'")
    
    # ✅ ESKI STATELNI RESTORE QILISH
    user_states[user_id] = data
    warehouse = data.get("warehouse")
    branch = data.get("branch", "common")
    
    user_states.pop(user_id, None)
    
    bot.send_message(
        message.chat.id,
        f"✅ '{data.get('product_type_name')}' turi qo'shildi!",
        reply_markup=product_types_menu(warehouse, branch)
    )

@bot.callback_query_handler(func=lambda call: call.data == "product_type_image_no")
def handle_product_type_image_no(call):
    """Rasm talab qilinmadi"""
    user_id = call.from_user.id
    data = user_states.get(user_id, {})
    
    db = get_db()
    db.add_product_type(
        data.get("product_type_name"),
        None,
        data.get("warehouse"),
        data.get("branch", "common")
    )
    
    logger.info(f"✅ Product type saved without image: '{data.get('product_type_name')}'")
    
    warehouse = data.get("warehouse")
    branch = data.get("branch", "common")
    
    user_states.pop(user_id, None)
    
    bot.edit_message_text(
        f"✅ '{data.get('product_type_name')}' turi qo'shildi!",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=product_types_menu(warehouse, branch)
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("product_type_actions:"))
def handle_product_type_actions(call):
    """Mahsulot turi sozlamalari (tahrirlash/o'chirish/back)"""
    parts = call.data.split(":")
    warehouse = parts[1]
    branch = parts[2] if len(parts) > 2 else "common"
    product_type = parts[3] if len(parts) > 3 else ""

    user_states[call.from_user.id] = {"warehouse": warehouse, "branch": branch, "product_type": product_type}

    text = f"📦 <b>{product_type}</b>\n\nAmalni tanlang:"
    db = get_db()
    ptype = db.get_product_type_by_name(product_type, warehouse, branch)
    markup = product_type_actions_menu(warehouse, branch, product_type)

    if ptype and ptype.get("image_id"):
        try:
            bot.edit_message_media(
                media=telebot.types.InputMediaPhoto(ptype["image_id"], caption=text, parse_mode="HTML"),
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=markup,
            )
            return
        except Exception:
            pass

        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass

        bot.send_photo(call.message.chat.id, ptype["image_id"], caption=text, reply_markup=markup, parse_mode="HTML")
        return

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")


# ✅ PRODUCT TYPE SELECT - MAHSULOTLAR BO'LIMI
@bot.callback_query_handler(func=lambda call: call.data.startswith("product_type_select:"))
def handle_product_type_select(call):
    """Mahsulot turini tanlash"""
    parts = call.data.split(":")
    warehouse = parts[1]
    branch = parts[2] if len(parts) > 2 else "common"
    product_type = parts[3] if len(parts) > 3 else ""
    
    user_id = call.from_user.id
    user_states[user_id] = {"warehouse": warehouse, "branch": branch, "product_type": product_type}
    
    _show_products_by_type_message(call.message.chat.id, call.message.message_id, warehouse, branch, product_type)

# ✅ PRODUCT TYPE EDIT
@bot.callback_query_handler(func=lambda call: call.data.startswith("product_type_edit:"))
def handle_product_type_edit(call):
    """Mahsulot turini tahrirlash"""
    parts = call.data.split(":")
    warehouse = parts[1]
    branch = parts[2] if len(parts) > 2 else "common"
    product_type = parts[3] if len(parts) > 3 else ""
    
    user_id = call.from_user.id
    user_states[user_id] = {
        "action": "editing_product_type",
        "old_name": product_type,
        "warehouse": warehouse,
        "branch": branch
    }
    
    bot.send_message(
        call.message.chat.id,
        "✍️ Yangi tur nomini kiriting:",
        reply_markup=back_button(f"product_type_back:{warehouse}:{branch}")
    )

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("action") == "editing_product_type")
def process_product_type_edit(message):
    """Mahsulot turi nomini o'zgartirish"""
    user_id = message.from_user.id
    data = user_states.get(user_id, {})
    old_name = data.get("old_name")
    new_name = message.text.strip()
    warehouse = data.get("warehouse")
    branch = data.get("branch")
    
    if not new_name:
        bot.send_message(message.chat.id, "❌ Tur nomi bo'sh bo'lishi mumkin emas")
        return
    
    db = get_db()
    ptype = db.get_product_type_by_name(old_name, warehouse, branch)
    
    if ptype and ptype.get("image_id"):
        # ✅ RASM MAVJUD - YANGILAYSIZMI DEB SO'RASH
        user_states[user_id]["action"] = "awaiting_image_update"
        user_states[user_id]["new_name"] = new_name
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("✅ Yangilash", callback_data="product_type_update_image_yes"),
            telebot.types.InlineKeyboardButton("❌ Qoldirish", callback_data="product_type_update_image_no")
        )
        
        bot.send_message(
            message.chat.id,
            f"📷 Rasimni yangilayman?\n\n<b>{old_name}</b> → <b>{new_name}</b>",
            reply_markup=markup,
            parse_mode="HTML"
        )
    else:
        # ✅ RASM YO'Q - RASM QO'SHISH SO'RASH
        user_states[user_id]["action"] = "awaiting_image_add"
        user_states[user_id]["new_name"] = new_name
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("✅ Qo'shish", callback_data="product_type_add_image_yes"),
            telebot.types.InlineKeyboardButton("❌ Yo'q", callback_data="product_type_add_image_no")
        )
        
        bot.send_message(
            message.chat.id,
            f"🖼️ Rasm qo'shaman?\n\n<b>{old_name}</b> → <b>{new_name}</b>",
            reply_markup=markup,
            parse_mode="HTML"
        )

@bot.callback_query_handler(func=lambda call: call.data == "product_type_update_image_yes")
def handle_product_type_update_image_yes(call):
    """Rasm yangilash"""
    user_id = call.from_user.id
    user_states[user_id]["action"] = "uploading_product_type_new_image"
    
    bot.send_message(
        call.message.chat.id,
        "📷 Yangi rasm yuboring:",
        reply_markup=back_button("product_type_cancel_edit")
    )

@bot.message_handler(content_types=['photo'], func=lambda message: user_states.get(message.from_user.id, {}).get("action") == "uploading_product_type_new_image")
def process_product_type_new_image(message):
    """Yangi rasm saqlash va turi tahrirlash"""
    user_id = message.from_user.id
    data = user_states.get(user_id, {})
    
    image_id = message.photo[-1].file_id
    
    db = get_db()
    db.update_product_type(
        data.get("old_name"),
        data.get("new_name"),
        image_id,
        data.get("warehouse"),
        data.get("branch")
    )
    
    warehouse = data.get("warehouse")
    branch = data.get("branch")
    
    user_states.pop(user_id, None)
    
    bot.send_message(
        message.chat.id,
        f"✅ '{data.get('new_name')}' turi yangilandi!",
        reply_markup=product_types_menu(warehouse, branch)
    )

@bot.callback_query_handler(func=lambda call: call.data == "product_type_update_image_no")
def handle_product_type_update_image_no(call):
    """Rasim qoldirish"""
    user_id = call.from_user.id
    data = user_states.get(user_id, {})
    
    db = get_db()
    db.update_product_type(
        data.get("old_name"),
        data.get("new_name"),
        None,
        data.get("warehouse"),
        data.get("branch")
    )
    
    warehouse = data.get("warehouse")
    branch = data.get("branch")
    
    user_states.pop(user_id, None)
    
    bot.edit_message_text(
        f"✅ '{data.get('new_name')}' nomiga o'zgartirildi!",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=product_types_menu(warehouse, branch)
    )

@bot.callback_query_handler(func=lambda call: call.data == "product_type_add_image_yes")
def handle_product_type_add_image_yes(call):
    """Rasm qo'shish"""
    user_id = call.from_user.id
    user_states[user_id]["action"] = "uploading_product_type_add_image"
    
    bot.send_message(
        call.message.chat.id,
        "📷 Rasm yuboring:",
        reply_markup=back_button("product_type_cancel_edit")
    )

@bot.message_handler(content_types=['photo'], func=lambda message: user_states.get(message.from_user.id, {}).get("action") == "uploading_product_type_add_image")
def process_product_type_add_image(message):
    """Rasm qo'shib turi tahrirlash"""
    user_id = message.from_user.id
    data = user_states.get(user_id, {})
    
    image_id = message.photo[-1].file_id
    
    db = get_db()
    db.update_product_type(
        data.get("old_name"),
        data.get("new_name"),
        image_id,
        data.get("warehouse"),
        data.get("branch")
    )
    
    warehouse = data.get("warehouse")
    branch = data.get("branch")
    
    user_states.pop(user_id, None)
    
    bot.send_message(
        message.chat.id,
        f"✅ '{data.get('new_name')}' turi rasmli yangilandi!",
        reply_markup=product_types_menu(warehouse, branch)
    )

@bot.callback_query_handler(func=lambda call: call.data == "product_type_add_image_no")
def handle_product_type_add_image_no(call):
    """Rasm qo'shmasdan tahrirlash"""
    user_id = call.from_user.id
    data = user_states.get(user_id, {})
    
    db = get_db()
    db.update_product_type(
        data.get("old_name"),
        data.get("new_name"),
        None,
        data.get("warehouse"),
        data.get("branch")
    )
    
    warehouse = data.get("warehouse")
    branch = data.get("branch")
    
    user_states.pop(user_id, None)
    
    bot.edit_message_text(
        f"✅ '{data.get('new_name')}' nomiga o'zgartirildi!",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=product_types_menu(warehouse, branch)
    )

# ✅ PRODUCT TYPE DELETE
@bot.callback_query_handler(func=lambda call: call.data.startswith("product_type_delete:"))
def handle_product_type_delete(call):
    """Mahsulot turini o'chirish"""
    parts = call.data.split(":")
    warehouse = parts[1]
    branch = parts[2] if len(parts) > 2 else "common"
    product_type = parts[3] if len(parts) > 3 else ""
    
    user_id = call.from_user.id
    user_states.pop(user_id, None)
    
    db = get_db()
    db.delete_product_type(product_type, warehouse, branch)
    
    bot.edit_message_text(
        f"🗑️ '{product_type}' turi o'chirildi",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=product_types_menu(warehouse, branch)
    )

# ==================== PRODUCT HANDLERS ====================

@bot.callback_query_handler(func=lambda call: call.data.startswith("product_add:"))
def handle_product_add(call):
    """Mahsulot qo'shish"""
    parts = call.data.split(":")
    warehouse = parts[1]
    branch = parts[2] if len(parts) > 2 else "common"
    product_type = parts[3] if len(parts) > 3 else ""
    
    user_id = call.from_user.id
    user_states[user_id] = {
        "action": "adding_product",
        "warehouse": warehouse,
        "branch": branch,
        "product_type": product_type
    }
    
    bot.send_message(
        call.message.chat.id,
        MESSAGES["product_add_name"],
        reply_markup=back_button(f"product_type_back:{warehouse}:{branch}")
    )

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
    data["action"] = "adding_product_code"
    user_states[user_id] = data
    
    bot.send_message(
        message.chat.id,
        f"📦 <b>{product_name}</b>\n\n🔢 Mahsulot kodini kiriting:\n(Masalan: SKL-001)",
        reply_markup=back_button(f"product_type_back:{data['warehouse']}:{data['branch']}"),
        parse_mode="HTML"
    )

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("action") == "adding_product_code")
def process_product_code(message):
    """Mahsulot kodini qabul qilish"""
    user_id = message.from_user.id
    data = user_states.get(user_id, {})
    
    code = message.text.strip()
    
    if not code:
        bot.send_message(message.chat.id, "❌ Mahsulot kodi bo'sh bo'lishi mumkin emas")
        return
    
    data["product_code"] = code
    data["action"] = "added_product_confirm"
    user_states[user_id] = data
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("✅ Tasdiq", callback_data="product_confirm_add"),
        telebot.types.InlineKeyboardButton("❌ Bekor", callback_data=f"product_type_back:{data['warehouse']}:{data['branch']}")
    )
    
    bot.send_message(
        message.chat.id,
        f"✅ Tasdiqlansinmi?\n\n📦 <b>{data['product_name']}</b>\n🔢 Kod: <b>{code}</b>",
        reply_markup=markup,
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "product_confirm_add")
def handle_product_confirm_add(call):
    """Mahsulotni qo'shish tasdiqlash"""
    user_id = call.from_user.id
    data = user_states.get(user_id, {})
    
    db = get_db()
    db.add_product(
        data.get("product_name"),
        data.get("product_code"),
        data.get("product_type"),
        data.get("warehouse"),
        data.get("branch")
    )
    
    warehouse = data.get("warehouse")
    branch = data.get("branch")
    product_type = data.get("product_type")
    
    user_states.pop(user_id, None)
    
    _show_products_by_type_message(call.message.chat.id, call.message.message_id, warehouse, branch, product_type)


@bot.callback_query_handler(func=lambda call: call.data.startswith("product_select:"))
def handle_product_select(call):
    """Mahsulot nomi bosilganda detal oynasi"""
    parts = call.data.split(":")
    warehouse = parts[1]
    branch = parts[2] if len(parts) > 2 else "common"
    product_type = parts[3] if len(parts) > 3 else ""
    product_name = parts[4] if len(parts) > 4 else ""

    user_states[call.from_user.id] = {
        "warehouse": warehouse,
        "branch": branch,
        "product_type": product_type,
        "product_name": product_name,
    }

    _show_product_details_message(call.message.chat.id, call.message.message_id, warehouse, branch, product_type, product_name)


@bot.callback_query_handler(func=lambda call: call.data.startswith("product_edit:"))
def handle_product_edit(call):
    """Mahsulotni tahrirlash jarayonini boshlash"""
    parts = call.data.split(":")
    warehouse = parts[1]
    branch = parts[2] if len(parts) > 2 else "common"
    product_type = parts[3] if len(parts) > 3 else ""
    product_name = parts[4] if len(parts) > 4 else ""

    user_states[call.from_user.id] = {
        "action": "editing_product_name",
        "warehouse": warehouse,
        "branch": branch,
        "product_type": product_type,
        "old_product_name": product_name,
    }

    bot.send_message(
        call.message.chat.id,
        f"✍️ Yangi mahsulot nomini kiriting:\n\nEski nom: <b>{product_name}</b>",
        reply_markup=back_button(f"product_select:{warehouse}:{branch}:{product_type}:{product_name}"),
        parse_mode="HTML",
    )


@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("action") == "editing_product_name")
def process_product_edit_name(message):
    """Mahsulot tahriri uchun yangi nom"""
    user_id = message.from_user.id
    data = user_states.get(user_id, {})
    new_name = message.text.strip()

    if not new_name:
        bot.send_message(message.chat.id, "❌ Mahsulot nomi bo'sh bo'lishi mumkin emas")
        return

    data["new_product_name"] = new_name
    data["action"] = "editing_product_code"
    user_states[user_id] = data

    bot.send_message(
        message.chat.id,
        f"🔢 Yangi mahsulot kodini kiriting:\n\nYangi nom: <b>{new_name}</b>",
        reply_markup=back_button(
            f"product_select:{data['warehouse']}:{data['branch']}:{data['product_type']}:{data['old_product_name']}"
        ),
        parse_mode="HTML",
    )


@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("action") == "editing_product_code")
def process_product_edit_code(message):
    """Mahsulot tahriri uchun yangi kod"""
    user_id = message.from_user.id
    data = user_states.get(user_id, {})
    new_code = message.text.strip()

    if not new_code:
        bot.send_message(message.chat.id, "❌ Mahsulot kodi bo'sh bo'lishi mumkin emas")
        return

    db = get_db()
    updated = db.update_product(
        data.get("old_product_name"),
        data.get("new_product_name"),
        new_code,
        data.get("warehouse"),
        data.get("branch"),
        data.get("product_type"),
    )
    
    warehouse = data.get("warehouse")
    branch = data.get("branch")
    product_type = data.get("product_type")
    new_name = data.get("new_product_name")

    user_states.pop(user_id, None)

    if updated:
        bot.send_message(message.chat.id, "✅ Mahsulot muvaffaqiyatli yangilandi")
        _show_product_details_message(message.chat.id, message.message_id, warehouse, branch, product_type, new_name)
    else:
        bot.send_message(message.chat.id, "❌ Tahrirlashda xatolik (nom/kod band bo'lishi mumkin)")


@bot.callback_query_handler(func=lambda call: call.data.startswith("product_delete:"))
def handle_product_delete(call):
    """Mahsulotni o'chirishni tasdiqlash oynasi"""
    parts = call.data.split(":")
    warehouse = parts[1]
    branch = parts[2] if len(parts) > 2 else "common"
    product_type = parts[3] if len(parts) > 3 else ""
    product_name = parts[4] if len(parts) > 4 else ""

    db = get_db()
    qty = db.get_inventory(product_name, branch).get("quantity", 0)

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("✅ Ha", callback_data=f"product_delete_confirm:{warehouse}:{branch}:{product_type}:{product_name}"),
        telebot.types.InlineKeyboardButton("❌ Yo'q", callback_data=f"product_delete_cancel:{warehouse}:{branch}:{product_type}:{product_name}"),
    )

    text = f"⚠️ <b>{product_name}</b> o'chirilsinmi?\n\nSkladdagi qoldiq: <b>{qty}</b>"
    db_ptype = db.get_product_type_by_name(product_type, warehouse, branch)

    if db_ptype and db_ptype.get("image_id"):
        try:
            bot.edit_message_media(
                media=telebot.types.InputMediaPhoto(db_ptype["image_id"], caption=text, parse_mode="HTML"),
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=markup,
            )
            return
        except Exception:
            pass

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data.startswith("product_delete_confirm:"))
def handle_product_delete_confirm(call):
    """Mahsulotni tasdiqlab o'chirish"""
    parts = call.data.split(":")
    warehouse = parts[1]
    branch = parts[2] if len(parts) > 2 else "common"
    product_type = parts[3] if len(parts) > 3 else ""
    product_name = parts[4] if len(parts) > 4 else ""

    db = get_db()
    db.delete_product(product_name, warehouse, branch, product_type)

    _show_products_by_type_message(call.message.chat.id, call.message.message_id, warehouse, branch, product_type)


@bot.callback_query_handler(func=lambda call: call.data.startswith("product_delete_cancel:"))
def handle_product_delete_cancel(call):
    """Mahsulotni o'chirish bekor qilindi"""
    parts = call.data.split(":")
    warehouse = parts[1]
    branch = parts[2] if len(parts) > 2 else "common"
    product_type = parts[3] if len(parts) > 3 else ""

    _show_products_by_type_message(call.message.chat.id, call.message.message_id, warehouse, branch, product_type)

# ==================== BACK HANDLERS ====================

@bot.callback_query_handler(func=lambda call: call.data == "warehouse_list")
def handle_warehouse_list_back(call):
    """Sklad ro'yxatiga qaytish"""
    user_id = call.from_user.id
    user_states.pop(user_id, None)
    
    bot.edit_message_text(
        "👤 Salom, Administrator!\n\nIshlash uchun skladni tanlang:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=warehouse_list_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_back:"))
def handle_admin_back(call):
    """Admin panelga qaytish"""
    warehouse = call.data.split(":")[1]
    user_id = call.from_user.id
    user_states.pop(user_id, None)
    
    bot.edit_message_text(
        f"👤 Salom, Administrator!\n\n🏭 Sklad: <b>{warehouse}</b>\n\nIshlash uchun tugmani tanlang:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=admin_main_menu(warehouse),
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("product_type_back:"))
def handle_product_type_back(call):
    """Filial tanlashga qaytish"""
    parts = call.data.split(":")
    warehouse = parts[1]
    branch = parts[2] if len(parts) > 2 else "common"
    
    user_id = call.from_user.id
    user_states.pop(user_id, None)
    
    _show_product_types_message(call.message.chat.id, call.message.message_id, warehouse, branch)


@bot.callback_query_handler(func=lambda call: call.data.startswith("product_list_back:"))
def handle_product_list_back(call):
    """Mahsulot detal oynasidan ro'yxatga qaytish"""
    parts = call.data.split(":")
    warehouse = parts[1]
    branch = parts[2] if len(parts) > 2 else "common"
    product_type = parts[3] if len(parts) > 3 else ""

    user_states.pop(call.from_user.id, None)
    _show_products_by_type_message(call.message.chat.id, call.message.message_id, warehouse, branch, product_type)


@bot.callback_query_handler(func=lambda call: call.data == "product_type_image_cancel")
def handle_product_type_image_cancel(call):
    """Tur qo'shishda rasm yuborishni bekor qilish"""
    data = user_states.get(call.from_user.id, {})
    warehouse = data.get("warehouse")
    branch = data.get("branch", "common")
    user_states.pop(call.from_user.id, None)
    _show_product_types_message(call.message.chat.id, call.message.message_id, warehouse, branch)


@bot.callback_query_handler(func=lambda call: call.data == "product_type_cancel_edit")
def handle_product_type_cancel_edit(call):
    """Tur tahrirlashda rasm bosqichini bekor qilish"""
    data = user_states.get(call.from_user.id, {})
    warehouse = data.get("warehouse")
    branch = data.get("branch", "common")
    user_states.pop(call.from_user.id, None)
    _show_product_types_message(call.message.chat.id, call.message.message_id, warehouse, branch)

@bot.callback_query_handler(func=lambda call: call.data.startswith("product_branch_back:"))
def handle_product_branch_back(call):
    """Mahsulot bo'limiga qaytish"""
    warehouse = call.data.split(":")[1]
    user_id = call.from_user.id
    user_states.pop(user_id, None)
    
    try:
        bot.edit_message_text(
            "🏢 Filial tanlang yoki Umumiy:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=branches_selection_menu(warehouse),
            parse_mode="HTML"
        )
    except Exception:
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        bot.send_message(
            call.message.chat.id,
            "🏢 Filial tanlang yoki Umumiy:",
            reply_markup=branches_selection_menu(warehouse),
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

# ==================== MISC HANDLERS ====================

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