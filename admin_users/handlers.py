import telebot
import logging
from database.mongodb import get_db
from .keyboards import (
    users_list_menu,
    user_confirm_delete_menu,
    back_button,
)

logger = logging.getLogger(__name__)

def register_admin_users_handlers(bot, user_states, ADMIN_ID):
    """Foydalanuvchilar boshqarish handlerlari"""
    
    @bot.callback_query_handler(func=lambda call: call.data == "users_list_menu")
    def handle_users_list(call):
        """Foydalanuvchilar ro'yxati"""
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "Ruxsati yo'q", show_alert=True)
            return
        
        user_states.pop(call.from_user.id, None)
        
        bot.edit_message_text(
            "👥 Foydalanuvchilar ro'yxati:\n\nFoydalanuvchini tanlang:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=users_list_menu(),
        )
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("user_info:"))
    def handle_user_info(call):
        """Foydalanuvchi ma'lumotlari"""
        user_id = int(call.data.split(":")[1])
        db = get_db()
        user = db.get_user(user_id)
        
        if not user:
            bot.answer_callback_query(call.id, "Foydalanuvchi topilmadi", show_alert=True)
            return
        
        username = user.get('username', 'NoUsername')
        first_name = user.get('first_name', 'Noma\'lum')
        approved = "✅ Tasdiqlangan" if user.get('approved') else "⏳ Tasdiq kutilmoqda"
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("🗑️ O'chirish", callback_data=f"user_delete_start:{user_id}"),
        )
        markup.add(telebot.types.InlineKeyboardButton("⬅️ Ortga", callback_data="users_list_menu"))
        
        bot.edit_message_text(
            f"👤 Foydalanuvchi Ma'lumotlari:\n\n"
            f"🆔 ID: <b>{user_id}</b>\n"
            f"📝 Username: <b>@{username}</b>\n"
            f"📛 Ism: <b>{first_name}</b>\n"
            f"✔️ Status: <b>{approved}</b>",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML",
        )
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("user_delete_start:"))
    def handle_user_delete_start(call):
        """Foydalanuvchi o'chirish boshlash"""
        user_id = int(call.data.split(":")[1])
        
        user_states[call.from_user.id] = {
            "action": "waiting_user_id_confirmation",
            "target_user_id": user_id,
        }
        
        bot.edit_message_text(
            f"⚠️ Foydalanuvchi <b>{user_id}</b> o'chirilsinmi?\n\n"
            f"Tasdiqlash uchun user ID sini qayta kiriting:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=back_button("users_list_menu"),
            parse_mode="HTML",
        )
    
    @bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("action") == "waiting_user_id_confirmation")
    def process_user_delete_confirmation(message):
        """Foydalanuvchi o'chirish tasdiqlash"""
        user_id = message.from_user.id
        data = user_states.get(user_id, {})
        target_user_id = data.get("target_user_id")
        
        try:
            entered_id = int(message.text.strip())
        except ValueError:
            bot.send_message(
                message.chat.id,
                "❌ ID raqam bo'lishi kerak.",
                reply_markup=back_button("users_list_menu"),
            )
            return
        
        if entered_id != target_user_id:
            bot.send_message(
                message.chat.id,
                f"❌ ID mos kelmadi. Kiritilgan ID: {entered_id}\n\nTo'g'ri ID: {target_user_id}",
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
        markup.add(
            telebot.types.InlineKeyboardButton("✅ Ha, o'chirish", callback_data=f"user_delete_confirm:{target_user_id}"),
            telebot.types.InlineKeyboardButton("❌ Yo'q", callback_data="users_list_menu"),
        )
        
        username = user.get('username', 'NoUsername')
        bot.send_message(
            message.chat.id,
            f"👤 <b>@{username}</b> o'chirilsinmi?\n\n"
            f"🆔 ID: <b>{target_user_id}</b>",
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
            f"✅ Foydalanuvchi <b>{target_user_id}</b> muvaffaqiyatli o'chirildi!",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=back_button("users_list_menu"),
            parse_mode="HTML",
        )