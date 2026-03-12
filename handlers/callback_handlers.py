import logging
from telebot import types
from config.settings import BOT_TOKEN, ADMIN_ID, MESSAGES
from database.mongodb import get_db
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

logger = logging.getLogger(__name__)
bot = None
user_states = {}

def set_bot(telegram_bot):
    """Bot instanceni set qilish"""
    global bot
    bot = telegram_bot

def set_user_states(states):
    """User states referenceini set qilish"""
    global user_states
    user_states = states

def register_callback_handlers(telegram_bot, states_dict):
    """Barcha callback handlerlarni ro'yxatla"""
    global bot, user_states
    bot = telegram_bot
    user_states = states_dict

    # ============ START ============

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

    # ============ BRANCH CALLBACKS ============

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

    @bot.callback_query_handler(func=lambda call: call.data.startswith("branch_select:"))
    def handle_branch_select(call):
        """Filial tanlash"""
        branch_name = call.data.split(":")[1]
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(MESSAGES["button_edit"], callback_data=f"branch_edit:{branch_name}"),
            types.InlineKeyboardButton(MESSAGES["button_delete"], callback_data=f"branch_delete:{branch_name}")
        )
        markup.add(types.InlineKeyboardButton(MESSAGES["button_back"], callback_data="admin_branch"))
        
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
        db = get_db()
        db.delete_branch(branch_name)
        
        bot.edit_message_text(
            MESSAGES["branch_deleted"],
            call.message.chat.id,
            call.message.message_id,
            reply_markup=branches_menu()
        )

    # ============ PRODUCT TYPE CALLBACKS ============

    @bot.callback_query_handler(func=lambda call: call.data == "admin_product")
    def handle_admin_product(call):
        """Admin mahsulotlarni boshqarish - TUR tanlash"""
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, MESSAGES["error_access_denied"], show_alert=True)
            return
        
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

    @bot.callback_query_handler(func=lambda call: call.data == "product_type_add")
    def handle_product_type_add(call):
        """Yangi mahsulot turi qo'shish"""
        user_id = call.from_user.id
        
        logger.info(f"🟡 CALLBACK: product_type_add chaqirildi, user_id={user_id}")
        
        # ✅ XABAR O'CHIRISH
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
            logger.info(f"✅ Callback xabari o'chirildi")
        except Exception as e:
            logger.warning(f"⚠️ Xabarni o'chirishda xato: {e}")
        
        # ✅ STATE BELGILASH
        user_states[user_id] = "waiting_product_type_name"
        logger.info(f"✅ State belgilandi: waiting_product_type_name")
        
        # ✅ XABAR YUBORISH
        bot.send_message(
            call.message.chat.id,
            "✍️ Mahsulot turi (brend) nomini kiriting:",
            reply_markup=back_button("admin_product")
        )
        
        logger.info(f"✅ Message handler uchun xabar yuborildi")

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

    # ============ PRODUCT CALLBACKS ============

    @bot.callback_query_handler(func=lambda call: call.data.startswith("product_select:"))
    def handle_product_select(call):
        """Mahsulotni tanlash"""
        product_name = call.data.split(":")[1]
        user_id = call.from_user.id
        data = user_states.get(user_id, {})
        product_type = data.get("product_type")
        
        db = get_db()
        product = db.get_product_by_name(product_name)
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(MESSAGES["button_edit"], callback_data=f"product_edit:{product_name}"),
            types.InlineKeyboardButton(MESSAGES["button_delete"], callback_data=f"product_delete:{product_name}")
        )
        markup.add(types.InlineKeyboardButton(MESSAGES["button_back"], callback_data="product_type_back"))
        
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
        db = get_db()
        db.delete_product(product_name)
        
        user_id = call.from_user.id
        data = user_states.get(user_id, {})
        product_type = data.get("product_type")
        
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

    # ============ LIST CALLBACKS ============

    @bot.callback_query_handler(func=lambda call: call.data == "admin_list")
    def handle_admin_list(call):
        """Admin ro'yxat"""
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, MESSAGES["error_access_denied"], show_alert=True)
            return
        
        db = get_db()
        branches = db.get_all_branches()
        
        markup = types.InlineKeyboardMarkup()
        for branch in branches:
            markup.add(types.InlineKeyboardButton(
                text=branch["name"],
                callback_data=f"admin_list_branch:{branch['name']}"
            ))
        markup.add(types.InlineKeyboardButton(MESSAGES["button_back"], callback_data="admin_back"))
        
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

    # ============ USER INPUT CALLBACKS ============

    @bot.callback_query_handler(func=lambda call: call.data == "user_input")
    def handle_user_input(call):
        """Mahsulot kiritish"""
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

    # ============ USER REMOVE CALLBACKS ============

    @bot.callback_query_handler(func=lambda call: call.data == "user_remove")
    def handle_user_remove(call):
        """Mahsulot chiqarish"""
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

    # ============ USER LIST CALLBACKS ============

    @bot.callback_query_handler(func=lambda call: call.data == "user_list")
    def handle_user_list(call):
        """Mahsulotlar ro'yxati"""
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

    # ============ REQUEST CALLBACKS ============

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
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_user:{user_id}"),
            types.InlineKeyboardButton("❌ Rad Qilish", callback_data=f"reject_user:{user_id}")
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

    # ============ BACK CALLBACKS ============

    @bot.callback_query_handler(func=lambda call: call.data == "close_menu")
    def handle_close_menu(call):
        """Menyu yopish"""
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
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