from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.mongodb import get_db
from config.settings import MESSAGES

def user_main_menu():
    """Foydalanuvchi bosh menyu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=MESSAGES["button_add_product"],
                callback_data="user_input"
            )
        ],
        [
            InlineKeyboardButton(
                text=MESSAGES["button_remove_product"],
                callback_data="user_remove"
            )
        ],
        [
            InlineKeyboardButton(
                text=MESSAGES["button_list"],
                callback_data="user_list"
            )
        ]
    ])

def user_request_menu():
    """Foydalanuvchi so'rov menyu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=MESSAGES["button_send_request"],
                callback_data="send_request"
            )
        ]
    ])

def branches_menu_user(action="input"):
    """Foydalanuvchi uchun filial menyu"""
    db = get_db()
    branches = db.get_all_branches()
    keyboard = []
    
    for branch in branches:
        keyboard.append([
            InlineKeyboardButton(
                text=branch["name"],
                callback_data=f"user_{action}_branch:{branch['name']}"
            )
        ])
    
    # Umumiy mahsulotlar
    keyboard.append([
        InlineKeyboardButton(
            text=MESSAGES["button_common"],
            callback_data=f"user_{action}_branch:common"
        )
    ])
    
    # Orqaga
    keyboard.append([
        InlineKeyboardButton(
            text=MESSAGES["button_back"],
            callback_data="user_main"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def products_menu_user(branch=None, action="input"):
    """Foydalanuvchi uchun mahsulot menyu"""
    db = get_db()
    products = db.get_products_by_branch(branch)
    keyboard = []
    
    # 2 ta mahsulot bir qatorda
    for i in range(0, len(products), 2):
        row = []
        for j in range(2):
            if i + j < len(products):
                product = products[i + j]
                row.append(
                    InlineKeyboardButton(
                        text=product["name"],
                        callback_data=f"user_{action}_product:{product['name']}"
                    )
                )
        keyboard.append(row)
    
    # Orqaga
    keyboard.append([
        InlineKeyboardButton(
            text=MESSAGES["button_back"],
            callback_data=f"user_{action}_back"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def back_button_user(callback_data="user_main"):
    """Foydalanuvchi uchun orqaga tugmasi"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=MESSAGES["button_back"],
                callback_data=callback_data
            )
        ]
    ])

def list_branches_menu():
    """Ro'yxat uchun filial menyu"""
    db = get_db()
    branches = db.get_all_branches()
    keyboard = []
    
    for branch in branches:
        keyboard.append([
            InlineKeyboardButton(
                text=branch["name"],
                callback_data=f"list_branch:{branch['name']}"
            )
        ])
    
    # Umumiy mahsulotlar
    keyboard.append([
        InlineKeyboardButton(
            text=MESSAGES["button_common"],
            callback_data="list_branch:common"
        )
    ])
    
    # Orqaga
    keyboard.append([
        InlineKeyboardButton(
            text=MESSAGES["button_back"],
            callback_data="user_main"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def pagination_menu(page, total_pages, branch, callback_prefix="list_page"):
    """Sahifalar orasida harakat"""
    keyboard = []
    
    if page > 0:
        keyboard.append([
            InlineKeyboardButton(
                text=MESSAGES["button_prev"],
                callback_data=f"{callback_prefix}:{page-1}:{branch}"
            )
        ])
    
    if page < total_pages - 1:
        keyboard.append([
            InlineKeyboardButton(
                text=MESSAGES["button_next"],
                callback_data=f"{callback_prefix}:{page+1}:{branch}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(
            text=MESSAGES["button_home"],
            callback_data="user_main"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)