import telebot
import logging
from database.mongodb import get_db
from .keyboards import group_menu, group_select_menu, group_list_menu, back_button

logger = logging.getLogger(__name__)

def register_group_handlers(bot, user_states, ADMIN_ID):
    """Guruh boshqarish handlerlari"""
    
    @bot.callback_query_handler(func=lambda call: call.data == "groups_menu")
    def handle_groups_menu(call):
        """Guruh menyu"""
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "Ruxsati yo'q", show_alert=True)
            return
        
        user_states.pop(call.from_user.id, None)
        bot.edit_message_text(
            "👥 Guruhlar Boshqarishi\n\nAmalni tanlang:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=group_menu(),
        )
    
    @bot.callback_query_handler(func=lambda call: call.data == "group_add_start")
    def handle_group_add_start(call):
        """Guruh qo'shish boshlash"""
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "Ruxsati yo'q", show_alert=True)
            return
        
        user_id = call.from_user.id
        user_states[user_id] = {"action": "group_add_select_warehouse"}
        
        bot.edit_message_text(
            "📦 Sklad tanlang:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=group_select_menu(None, "add"),
        )
    
    @bot.callback_query_handler(func=lambda call: call.data == "group_remove_start")
    def handle_group_remove_start(call):
        """Guruh o'chirish boshlash"""
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "Ruxsati yo'q", show_alert=True)
            return
        
        user_id = call.from_user.id
        user_states[user_id] = {"action": "group_remove_select_warehouse"}
        
        bot.edit_message_text(
            "📦 Sklad tanlang o'chirish uchun:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=group_select_menu(None, "remove"),
        )
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("group_select_warehouse:"))
    def handle_group_select_warehouse(call):
        """Skladni tanlash"""
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "Ruxsati yo'q", show_alert=True)
            return
        
        parts = call.data.split(":")
        warehouse = parts[1]
        action = parts[2]
        
        user_id = call.from_user.id
        user_states[user_id] = {"warehouse": warehouse, "action": f"group_{action}"}
        
        if action == "add":
            bot.edit_message_text(
                f"📦 <b>{warehouse}</b>\n\nGuruh linkini kiriting:\n\n(Masalan: https://t.me/+abcdefg123)",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=back_button("group_add_start"),
                parse_mode="HTML",
            )
            user_states[user_id]["action"] = "waiting_group_link"
        else:
            bot.edit_message_text(
                f"📦 <b>{warehouse}</b>\n\nGuruhlari:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=group_list_menu(warehouse),
            )
    
    @bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("action") == "waiting_group_link")
    def process_group_link(message):
        """Guruh link qabul qilish"""
        if message.from_user.id != ADMIN_ID:
            return
        user_id = message.from_user.id
        data = user_states.get(user_id, {})
        group_link = message.text.strip()
        warehouse = data.get("warehouse")
        
        if not group_link or "t.me" not in group_link:
            bot.send_message(
                message.chat.id,
                "❌ Noto'g'ri guruh linki. Iltimos, to'g'ri link kiriting.",
                reply_markup=back_button("group_add_start"),
            )
            return
        
        data["group_link"] = group_link
        data["action"] = "waiting_group_id"
        user_states[user_id] = data
        
        bot.send_message(
            message.chat.id,
            f"✍️ Guruh ID sini @username_to_id_bot orqali olib, yuboring:\n(Masalan: -1001234567890)\n\n⚠️ Bot guruhga Admin bo'lishi kerak!",
            reply_markup=back_button("group_add_start"),
        )
    
    @bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("action") == "waiting_group_id")
    def process_group_id(message):
        """Guruh ID qabul qilish"""
        if message.from_user.id != ADMIN_ID:
            return
        user_id = message.from_user.id
        data = user_states.get(user_id, {})
        
        try:
            group_id = int(message.text.strip())
        except ValueError:
            bot.send_message(
                message.chat.id,
                "❌ ID raqam bo'lishi kerak.",
                reply_markup=back_button("group_add_start"),
            )
            return
        
        data["group_id"] = group_id
        data["action"] = "confirming_group"
        user_states[user_id] = data
        
        db = get_db()
        try:
            group_info = bot.get_chat(group_id)
            group_name = group_info.title or "Noma'lum"
            data["group_name"] = group_name
            user_states[user_id] = data
            
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(
                telebot.types.InlineKeyboardButton("✅ Ha", callback_data="group_add_confirm"),
                telebot.types.InlineKeyboardButton("❌ Yo'q", callback_data="group_add_cancel"),
            )
            
            bot.send_message(
                message.chat.id,
                f"✅ Tasdiqlang:\n\n📌 Guruh: <b>{group_name}</b>\n🔗 ID: <b>{group_id}</b>\n🔗 Link: {data.get('group_link')}",
                reply_markup=markup,
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Guruh topilmadi: {e}")
            bot.send_message(
                message.chat.id,
                f"❌ Guruh topilmadi. Bot admin bo'lishi kerak.\n\nXato: {str(e)}",
                reply_markup=back_button("group_add_start"),
            )
    
    @bot.callback_query_handler(func=lambda call: call.data == "group_add_confirm")
    def handle_group_add_confirm(call):
        """Guruh qo'shishni tasdiqlash"""
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "Ruxsati yo'q", show_alert=True)
            return
        user_id = call.from_user.id
        data = user_states.get(user_id, {})
        db = get_db()
        
        db.add_group(
            data.get("warehouse"),
            data.get("group_id"),
            data.get("group_link"),
            data.get("group_name"),
        )
        
        user_states.pop(user_id, None)
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("➕ Yana qo'shish", callback_data="group_add_start"),
            telebot.types.InlineKeyboardButton("🗑️ O'chirish", callback_data="group_remove_start"),
        )
        markup.add(telebot.types.InlineKeyboardButton("⬅️ Ortga", callback_data="groups_menu"))
        
        bot.edit_message_text(
            "✅ Guruh qabul qilindi va biriktirildi.\n\nAmalni davom ettiring:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
        )
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("group_delete_select:"))
    def handle_group_delete_select(call):
        """Guruh o'chirish uchun tanlash"""
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "Ruxsati yo'q", show_alert=True)
            return
        parts = call.data.split(":")
        warehouse = parts[1]
        group_id = int(parts[2])
        
        db = get_db()
        group = db.get_group(warehouse, group_id)
        
        if not group:
            bot.answer_callback_query(call.id, "Guruh topilmadi", show_alert=True)
            return
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🗑️ O'chirish", callback_data=f"group_delete_confirm:{warehouse}:{group_id}"))
        markup.add(telebot.types.InlineKeyboardButton("⬅️ Ortga", callback_data="group_remove_start"))
        
        group_name = group.get("group_name", "Noma'lum")
        bot.edit_message_text(
            f"📦 Sklad: <b>{warehouse}</b>\n"
            f"👥 Guruh: <b>{group_name}</b>\n"
            f"🔗 Link: {group.get('group_link', '-')}\n\n"
            "O'chirasizmi?",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML",
        )
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("group_delete_confirm:"))
    def handle_group_delete_confirm(call):
        """Guruh o'chirishni tasdiqlash"""
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "Ruxsati yo'q", show_alert=True)
            return
        parts = call.data.split(":")
        warehouse = parts[1]
        group_id = int(parts[2])
        
        db = get_db()
        db.delete_group(warehouse, group_id)
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("➕ Qo'shish", callback_data="group_add_start"),
            telebot.types.InlineKeyboardButton("🗑️ Yana o'chirish", callback_data="group_remove_start"),
        )
        markup.add(telebot.types.InlineKeyboardButton("⬅️ Ortga", callback_data="groups_menu"))
        
        bot.edit_message_text(
            f"🗑️ Guruh o'chirildi. Jarayon haqida xabar olib turish uchun <b>{warehouse}</b>ga guruh qo'shishingiz kerak",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML",
        )