import telebot
from database.mongodb import get_db
from config.settings import MESSAGES

# ==================== ADMIN KEYBOARDS ====================

def admin_main_menu():
    """Admin bosh menyu"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("🏢 Filial", callback_data="admin_branch"),
        telebot.types.InlineKeyboardButton("📦 Mahsulot", callback_data="admin_product"),
        telebot.types.InlineKeyboardButton("📋 Ro'yxat", callback_data="admin_list")
    )
    return markup

def branches_menu():
    """Filiallar ro'yxati"""
    db = get_db()
    branches = db.get_all_branches()
    markup = telebot.types.InlineKeyboardMarkup()
    
    for branch in branches:
        markup.add(telebot.types.InlineKeyboardButton(
            text=branch["name"],
            callback_data=f"branch_select:{branch['name']}"
        ))
    
    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_add"], callback_data="branch_add"))
    markup.add(telebot.types.InlineKeyboardButton("❌ Yopish", callback_data="close_menu"))
    
    return markup

def back_button(callback_data="back"):
    """Orqaga tugmasi"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data=callback_data))
    return markup

def product_type_menu():
    """Mahsulot turi - TUZATILDI"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("🌍 Umumiy", callback_data="product_common"),
        telebot.types.InlineKeyboardButton("🏢 Filialga Xos", callback_data="product_branch")
    )
    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data="admin_back"))
    return markup

def branches_for_products_menu():
    """Mahsulot uchun filiallar"""
    db = get_db()
    branches = db.get_all_branches()
    markup = telebot.types.InlineKeyboardMarkup()
    
    for branch in branches:
        markup.add(telebot.types.InlineKeyboardButton(
            text=branch["name"],
            callback_data=f"product_branch_select:{branch['name']}"
        ))
    
    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data="product_type_back"))
    return markup

def products_menu(branch=None):
    """Mahsulotlar ro'yxati - 2 qatordan
    
    Args:
        branch: Filial nomi yoki None (umumiy uchun)
    """
    db = get_db()
    products = db.get_products_by_branch(branch)
    markup = telebot.types.InlineKeyboardMarkup()
    
    # Agar mahsulot bo'lmasa
    if not products:
        branch_key = branch if branch else "common"
        markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_add"], callback_data=f"product_add:{branch_key}"))
        markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data="product_branch_back"))
        return markup
    
    # 2 qatordan qo'shish
    for i in range(0, len(products), 2):
        row = []
        for j in range(2):
            if i + j < len(products):
                product = products[i + j]
                row.append(telebot.types.InlineKeyboardButton(
                    text=product["name"],
                    callback_data=f"product_select:{product['name']}"
                ))
        if row:
            markup.add(*row)
    
    # Plus tugmasi va Ortga
    branch_key = branch if branch else "common"
    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_add"], callback_data=f"product_add:{branch_key}"))
    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data="product_branch_back"))
    
    return markup

# ==================== USER KEYBOARDS ====================

def user_main_menu():
    """Foydalanuvchi bosh menyu"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_add_product"], callback_data="user_input"))
    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_remove_product"], callback_data="user_remove"))
    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_list"], callback_data="user_list"))
    return markup

def user_request_menu():
    """So'rov menyu"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_send_request"], callback_data="send_request"))
    return markup

def branches_menu_user(action="input"):
    """Foydalanuvchi uchun filiallar"""
    db = get_db()
    branches = db.get_all_branches()
    markup = telebot.types.InlineKeyboardMarkup()
    
    for branch in branches:
        markup.add(telebot.types.InlineKeyboardButton(
            text=branch["name"],
            callback_data=f"user_{action}_branch:{branch['name']}"
        ))
    
    markup.add(telebot.types.InlineKeyboardButton("🌍 Umumiy", callback_data=f"user_{action}_branch:common"))
    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data="user_main"))
    return markup

def products_menu_user(branch=None, action="input"):
    """Foydalanuvchi uchun mahsulotlar - 2 qatordan
    
    Args:
        branch: Filial nomi yoki None (umumiy uchun)
        action: "input" yoki "remove"
    """
    db = get_db()
    products = db.get_products_by_branch(branch)
    markup = telebot.types.InlineKeyboardMarkup()
    
    # Agar mahsulot bo'lmasa
    if not products:
        markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data=f"user_{action}_back"))
        return markup
    
    # 2 qatordan qo'shish
    for i in range(0, len(products), 2):
        row = []
        for j in range(2):
            if i + j < len(products):
                product = products[i + j]
                row.append(telebot.types.InlineKeyboardButton(
                    text=product["name"],
                    callback_data=f"user_{action}_product:{product['name']}"
                ))
        if row:
            markup.add(*row)
    
    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data=f"user_{action}_back"))
    return markup

def list_branches_menu():
    """Ro'yxat uchun filiallar"""
    db = get_db()
    branches = db.get_all_branches()
    markup = telebot.types.InlineKeyboardMarkup()
    
    for branch in branches:
        markup.add(telebot.types.InlineKeyboardButton(
            text=branch["name"],
            callback_data=f"list_branch:{branch['name']}"
        ))
    
    markup.add(telebot.types.InlineKeyboardButton("🌍 Umumiy", callback_data="list_branch:common"))
    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data="user_main"))
    return markup