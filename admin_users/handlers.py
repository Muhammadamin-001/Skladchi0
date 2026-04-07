import telebot
import logging
from database.mongodb import get_db
from .keyboards import (
    users_list_menu,
    back_button,
)

logger = logging.getLogger(__name__)

def register_admin_users_handlers(bot, user_states, ADMIN_ID):
    """Foydalanuvchilar boshqarish handlerlari"""
    
    def _users_text():
        db = get_db()
        users = db.get_all_users()
        if not users:
            return "👥 Foydalanuvchilar ro'yxati bo'sh."
        lines = ["👥 <b>Foydalanuvchilar ro'yxati:</b>\n"]
        for i, user in enumerate(users, 1):
            username = user.get("username") or "NoUsername"
            lines.append(f"{i}. @{username}, <blockquote>{user.get('user_id')}</blockquote>")
        return "\n".join(lines)
    
    @bot.callback_query_handler(func=lambda call: call.data == "users_list_menu")
    def handle_users_list(call):
        """Foydalanuvchilar ro'yxati"""
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "Ruxsati yo'q", show_alert=True)
            return
        
        user_states.pop(call.from_user.id, None)
        
        bot.edit_message_text(
            _users_text(),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=users_list_menu(),
            parse_mode="HTML",
        )
    
    @bot.callback_query_handler(func=lambda call: call.data == "users_delete_prompt")
    def handle_users_delete_prompt(call):
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "Ruxsati yo'q", show_alert=True)
            return
        user_states[call.from_user.id] = {"action": "waiting_user_id_for_delete"}
        bot.send_message(
            call.message.chat.id,
            "🗑️ Foydalanuvchini o'chirish uchun user_id yuboring:",
            reply_markup=back_button("users_list_menu"),
        )
    
    @bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("action") == "waiting_user_id_for_delete")
    def process_user_delete_id(message):
        user_id = message.from_user.id
        
        try:
            target_user_id = int(message.text.strip())
        except ValueError:
            bot.send_message(
                message.chat.id,
                "❌ ID raqam bo'lishi kerak.",
                reply_markup=back_button("users_list_menu"),
            )
            return
        
        
        db = get_db()
        user = db.get_user(target_user_id)
        
        if not user:
            bot.send_message(
                message.chat.id,
                "❌ Foydalanuvchi topilmadi.",
                reply_markup=back_button("users_list_menu"),
            )
            return
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("✅ Ha", callback_data=f"user_delete_confirm:{target_user_id}"))
        markup.add(telebot.types.InlineKeyboardButton("⬅️ Ortga", callback_data="users_list_menu"))
        
        username = user.get('username', 'NoUsername')
        bot.send_message(
            message.chat.id,
            f"👤 Username: <b>@{username}</b>\n🆔 ID: <b>{target_user_id}</b>\n\nO'chirasizmi?",
            reply_markup=markup,
            parse_mode="HTML",
        )
        
        user_states.pop(user_id, None)
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("user_delete_confirm:"))
    def handle_user_delete_confirm(call):
        """Foydalanuvchini bazadan o'chirish"""
        target_user_id = int(call.data.split(":")[1])
        db = get_db()
        
        db.delete_user(target_user_id)
        
        bot.edit_message_text(
            f"✅ Foydalanuvchi <b>{target_user_id}</b> o'chirildi.\n\n{_users_text()}",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=users_list_menu(),
            parse_mode="HTML",
        )