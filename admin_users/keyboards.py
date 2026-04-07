import telebot
from database.mongodb import get_db

def users_list_menu():
    """Foydalanuvchilar ro'yxati"""
    db = get_db()
    users = db.get_all_users()
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🗑️ O'chirish", callback_data="users_delete_prompt"))
    markup.add(telebot.types.InlineKeyboardButton("⬅️ Ortga", callback_data="admin_settings"))
    return markup


def back_button(callback_data):
    """Ortga tugmasi"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("⬅️ Ortga", callback_data=callback_data))
    return markup