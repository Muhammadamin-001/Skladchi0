import logging
from telebot import types
from config.settings import BOT_TOKEN, ADMIN_ID, MESSAGES
from database.mongodb import get_db
from keyboards.telebot_keyboards import (
    back_button,
    branches_menu,
    product_types_menu,
    products_by_type_menu,
    products_by_type_menu_user
)

# Import bot from main (will be set by main.py)
bot = None
user_states = {}

logger = logging.getLogger(__name__)

def set_bot(telegram_bot):
    """Bot instanceni set qilish"""
    global bot
    bot = telegram_bot

def set_user_states(states):
    """User states referenceini set qilish"""
    global user_states
    user_states = states

# ==================== MESSAGE HANDLERS ====================

def register_message_handlers(telegram_bot, states_dict):
    """Barcha message handlerlarni ro'yxatla"""
    global bot, user_states
    bot = telegram_bot
    user_states = states_dict

    # ============ BRANCH HANDLERS ============

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
            bot.send_message(message.chat.id, MESSAGES["branch_added"].format(name), reply_markup=branches_menu())
        else:
            bot.send_message(message.chat.id, MESSAGES["branch_exists"], reply_markup=back_button("admin_branch"))
            user_states.pop(user_id, None)

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
            bot.send_message(message.chat.id, MESSAGES["branch_renamed"].format(new_name), reply_markup=branches_menu())
        else:
            bot.send_message(message.chat.id, "❌ Xato yuz berdi", reply_markup=back_button("admin_branch"))
            user_states.pop(user_id, None)

    # ============ PRODUCT TYPE HANDLERS ============
    # ✅ ASOSIY HANDLER - BU YERDA!

    @bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "waiting_product_type_name")
    def process_product_type_add(message):
        """Mahsulot turi nomini saqlash"""
        user_id = message.from_user.id
        name = message.text.strip()
        
        logger.info(f"🔴 PRODUCT TYPE HANDLER ISHLAMOQDA: user_id={user_id}, text='{name}', state={user_states.get(user_id)}")
        
        # State tekshir
        if user_states.get(user_id) != "waiting_product_type_name":
            logger.warning(f"❌ State noto'g'ri: {user_states.get(user_id)}")
            bot.send_message(message.chat.id, "❌ Avval /start bosing yoki Qo'shish tugmasini bosing")
            return
        
        if not name:
            logger.warning("❌ Bo'sh nom")
            bot.send_message(message.chat.id, "❌ Tur nomi bo'sh bo'lishi mumkin emas")
            return
        
        db = get_db()
        
        if db.add_product_type(name):
            user_states.pop(user_id, None)
            logger.info(f"✅✅✅ TUR QO'SHILDI: {name}")
            
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
            bot.send_message(message.chat.id, "❌ Xato yuz berdi", reply_markup=back_button("admin_product"))
            user_states.pop(user_id, None)

    # ============ PRODUCT HANDLERS ============

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
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Ha", callback_data="product_add_image_yes"),
            types.InlineKeyboardButton("❌ Yo'q", callback_data="product_add_image_no")
        )
        
        bot.send_message(message.chat.id, MESSAGES["product_add_image"], reply_markup=markup)

    # ============ IMAGE HANDLER ============

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

    # ============ QUANTITY HANDLERS ============

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