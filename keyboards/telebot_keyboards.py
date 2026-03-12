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

def product_types_menu():
    """Mahsulot turlari menyu - 2 qatordan + sozlash tugmasi"""
    db = get_db()
    types = db.get_all_product_types()
    markup = telebot.types.InlineKeyboardMarkup()
    
    if not types:
        markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_add"], callback_data="product_type_add"))
        markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data="admin_back"))
        return markup
    
    # 2 qatordan qo'shish + sozlash tugmasi
    for ptype in types:
        row = []
        row.append(telebot.types.InlineKeyboardButton(
            text=ptype["name"],
            callback_data=f"product_type_select:{ptype['name']}"
        ))
        row.append(telebot.types.InlineKeyboardButton(
            text="⚙️",
            callback_data=f"product_type_actions:{ptype['name']}"
        ))
        markup.add(*row)
    
    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_add"], callback_data="product_type_add"))
    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data="admin_back"))
    
    return markup

def product_type_actions_menu(product_type):
    """Mahsulot turi faoliyatlari - tahrirlash va o'chirish"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("✏️ Tahrirlash", callback_data=f"product_type_edit:{product_type}"),
        telebot.types.InlineKeyboardButton("🗑️ O'chirish", callback_data=f"product_type_delete:{product_type}")
    )
    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data="product_type_back"))
    return markup

def products_by_type_menu(product_type):
    """Mahsulot turiga ko'ra mahsulotlar - 2 qatordan"""
    db = get_db()
    products = db.get_products_by_type(product_type)
    markup = telebot.types.InlineKeyboardMarkup()
    
    if not products:
        markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_add"], callback_data=f"product_add:{product_type}"))
        markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data="product_type_back"))
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
    
    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_add"], callback_data=f"product_add:{product_type}"))
    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data="product_type_back"))
    
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

def product_types_menu_user(action="input"):
    """Foydalanuvchi uchun mahsulot turlari"""
    db = get_db()
    types = db.get_all_product_types()
    markup = telebot.types.InlineKeyboardMarkup()
    
    for ptype in types:
        markup.add(telebot.types.InlineKeyboardButton(
            text=ptype["name"],
            callback_data=f"user_{action}_type:{ptype['name']}"
        ))
    
    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data="user_main"))
    return markup

def products_by_type_menu_user(product_type, action="input"):
    """Foydalanuvchi uchun mahsulotlar turiga ko'ra - 2 qatordan"""
    db = get_db()
    products = db.get_products_by_type(product_type)
    markup = telebot.types.InlineKeyboardMarkup()
    
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

def branches_menu_user(action="input"):
    """Foydalanuvchi uchun filiallar (kiritish/chiqarish uchun)"""
    db = get_db()
    branches = db.get_all_branches()
    markup = telebot.types.InlineKeyboardMarkup()
    
    for branch in branches:
        markup.add(telebot.types.InlineKeyboardButton(
            text=branch["name"],
            callback_data=f"user_{action}_branch:{branch['name']}"
        ))
    
    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data="user_main"))
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
    
    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data="user_main"))
    return markup