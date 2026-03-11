from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.mongodb import get_db
from config.settings import MESSAGES

def admin_main_menu():
    """Admin bosh menyu"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=MESSAGES["button_branch"],
                callback_data="admin_branch"
            ),
            InlineKeyboardButton(
                text=MESSAGES["button_product"],
                callback_data="admin_product"
            ),
            InlineKeyboardButton(
                text=MESSAGES["button_list"],
                callback_data="admin_list"
            )
        ]
    ])

def branches_menu():
    """Filiallar ro'yxati"""
    db = get_db()
    branches = db.get_all_branches()
    keyboard = []
    
    for branch in branches:
        keyboard.append([
            InlineKeyboardButton(
                text=branch["name"],
                callback_data=f"branch_select:{branch['name']}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(
            text=MESSAGES["button_add"],
            callback_data="branch_add"
        )
    ])
    
    keyboard.append([
        InlineKeyboardButton(
            text="❌ Yopish",
            callback_data="close_menu"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def branch_action_menu():
    """Filial faoliyatlari"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=MESSAGES["button_edit"],
                callback_data="branch_edit"
            ),
            InlineKeyboardButton(
                text=MESSAGES["button_delete"],
                callback_data="branch_delete"
            )
        ],
        [
            InlineKeyboardButton(
                text=MESSAGES["button_back"],
                callback_data="branch_back"
            )
        ]
    ])

def back_button(callback_data="back"):
    """Orqaga tugmasi"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=MESSAGES["button_back"],
                callback_data=callback_data
            )
        ]
    ])

def product_type_menu():
    """Mahsulot turi"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📋 Umumiy",
                callback_data="product_common"
            ),
            InlineKeyboardButton(
                text="🏢 Filialga Xos",
                callback_data="product_branch"
            )
        ],
        [
            InlineKeyboardButton(
                text=MESSAGES["button_back"],
                callback_data="admin_back"
            )
        ]
    ])

def branches_for_products_menu():
    """Mahsulot uchun filiallar"""
    db = get_db()
    branches = db.get_all_branches()
    keyboard = []
    
    for branch in branches:
        keyboard.append([
            InlineKeyboardButton(
                text=branch["name"],
                callback_data=f"product_branch_select:{branch['name']}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(
            text=MESSAGES["button_back"],
            callback_data="product_type_back"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def products_menu(branch=None):
    """Mahsulotlar ro'yxati"""
    db = get_db()
    products = db.get_products_by_branch(branch)
    keyboard = []
    
    for i in range(0, len(products), 2):
        row = []
        for j in range(2):
            if i + j < len(products):
                product = products[i + j]
                row.append(
                    InlineKeyboardButton(
                        text=product["name"],
                        callback_data=f"product_select:{product['name']}"
                    )
                )
        keyboard.append(row)
    
    branch_key = branch if branch else "common"
    keyboard.append([
        InlineKeyboardButton(
            text=MESSAGES["button_add"],
            callback_data=f"product_add:{branch_key}"
        )
    ])
    
    keyboard.append([
        InlineKeyboardButton(
            text=MESSAGES["button_back"],
            callback_data="product_branch_back"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def product_action_menu():
    """Mahsulot faoliyatlari"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=MESSAGES["button_edit"],
                callback_data="product_edit"
            ),
            InlineKeyboardButton(
                text=MESSAGES["button_delete"],
                callback_data="product_delete"
            )
        ],
        [
            InlineKeyboardButton(
                text=MESSAGES["button_back"],
                callback_data="product_back"
            )
        ]
    ])

def yes_no_menu(callback_prefix="answer"):
    """Ha/Yo'q tugmalari"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=MESSAGES["button_yes"],
                callback_data=f"{callback_prefix}_yes"
            ),
            InlineKeyboardButton(
                text=MESSAGES["button_no"],
                callback_data=f"{callback_prefix}_no"
            )
        ]
    ])