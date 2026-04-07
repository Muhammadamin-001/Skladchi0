import telebot
from database.mongodb import get_db

def users_list_menu():
    """Foydalanuvchilar ro'yxati"""
    db = get_db()
    users = db.get_all_users()
    
    markup = telebot.types.InlineKeyboardMarkup()
    for user in users:
        username = user.get('username', 'NoUsername')
        user_id = user.get('user_id')
        status = "✅" if user.get('approved') else "⏳"
        
        markup.add(
            telebot.types.InlineKeyboardButton(
                f"{status} @{username}",
                callback_data=f"user_info:{user_id}",
            )
        )
    
    markup.add(telebot.types.InlineKeyboardButton("⬅️ Ortga", callback_data="admin_settings"))
    return markup

def user_confirm_delete_menu(user_id, username):
    """Foydalanuvchini o'chirish tasdiqlash"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("✅ Ha, o'chirish", callback_data=f"user_delete_confirm:{user_id}"),
        telebot.types.InlineKeyboardButton("❌ Yo'q", callback_data="users_list_menu"),
    )
    return markup

def back_button(callback_data):
    """Ortga tugmasi"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("⬅️ Ortga", callback_data=callback_data))
    return markup