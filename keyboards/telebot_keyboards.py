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

# ✅ PRODUCT TYPES MENU - YANGI!
def product_types_menu():
    """Mahsulot turlari menyu"""
    db = get_db()
    types = db.get_all_product_types()  # ✅ DATABASE DAN OLISH
    markup = telebot.types.InlineKeyboardMarkup()
    
    if not types:
        markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_add"], callback_data="product_type_add"))
        markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data="admin_back"))
        return markup
    
    # Har bir tur uchun - tanlash va sozlash
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

# ✅ PRODUCT TYPE ACTIONS MENU - YANGI!
def product_type_actions_menu(product_type):
    """Mahsulot turi faoliyatlari"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("✏️ Tahrirlash", callback_data=f"product_type_edit:{product_type}"),
        telebot.types.InlineKeyboardButton("🗑️ O'chirish", callback_data=f"product_type_delete:{product_type}")
    )
    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data="product_type_back"))
    return markup

# ✅ PRODUCTS BY TYPE MENU - YANGI!
def products_by_type_menu(product_type):
    """Mahsulot turiga ko'ra mahsulotlar"""
    db = get_db()
    products = db.get_products_by_type(product_type)  # ✅ PRODUCT_TYPE BO'YICHA
    markup = telebot.types.InlineKeyboardMarkup()
    
    if not products:
        markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_add"], callback_data=f"product_add:{product_type}"))
        markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data="product_type_back"))
        return markup
    
    # 2 qatordan
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

# ✅ USER PRODUCT TYPES MENU - YANGI!
def product_types_menu_user(action="input"):
    """Foydalanuvchi uchun mahsulot turlari"""
    db = get_db()
    types = db.get_all_product_types()
    markup = telebot.types.InlineKeyboardMarkup()
    
    # 2 tadan bir qatorda chiqsin
    for i in range(0, len(types), 2):
        row = []
        for j in range(2):
            if i + j < len(types):
                ptype = types[i + j]
                row.append(telebot.types.InlineKeyboardButton(
                    text=ptype["name"],
                    callback_data=f"user_{action}_type:{ptype['name']}"
                ))
        if row:
            markup.add(*row)
    
    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data="user_main"))
    return markup

# ✅ USER PRODUCTS BY TYPE MENU - YANGI!
def products_by_type_menu_user(product_type, action="input", back_callback=None):
    """Foydalanuvchi uchun mahsulot turiga ko'ra mahsulotlar"""
    db = get_db()
    products = db.get_products_by_type(product_type)  # ✅ PRODUCT_TYPE BO'YICHA
    markup = telebot.types.InlineKeyboardMarkup()
    
    back_data = back_callback or f"user_{action}_back"

    if not products:
        markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data=back_data))
        return markup
    
    # 2 qatordan
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
    
    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data=back_data))
    return markup

def branches_menu_user(action="input", back_callback=None):
    """Foydalanuvchi uchun filiallar"""
    db = get_db()
    branches = db.get_all_branches()
    markup = telebot.types.InlineKeyboardMarkup()
    
    for branch in branches:
        markup.add(telebot.types.InlineKeyboardButton(
            text=branch["name"],
            callback_data=f"user_{action}_branch:{branch['name']}"
        ))
        
    back_data = back_callback or f"user_{action}_back"
    
    markup.add(
       telebot.types.InlineKeyboardButton(
           MESSAGES["button_back"],
           callback_data=back_data
       )
   )
    return markup

def list_branches_menu():
    """Ro'yxat uchun mahsulot turlari"""
    db = get_db()
    types = db.get_all_product_types()
    markup = telebot.types.InlineKeyboardMarkup()
    
    for i in range(0, len(types), 2):
       row = []
       for j in range(2):
           if i + j < len(types):
               ptype = types[i + j]
               row.append(telebot.types.InlineKeyboardButton(
                   text=ptype["name"],
                   callback_data=f"list_type:{ptype['name']}"
               ))
       if row:
           markup.add(*row)
    
    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data="user_main"))
    return markup

def list_products_by_type_menu(product_type):
    """Ro'yxat uchun mahsulotlar (type bo'yicha)"""
    db = get_db()
    products = db.get_products_by_type(product_type)
    markup = telebot.types.InlineKeyboardMarkup()

    for i in range(0, len(products), 2):
        row = []
        for j in range(2):
            if i + j < len(products):
                product = products[i + j]
                row.append(telebot.types.InlineKeyboardButton(
                    text=product["name"],
                    callback_data=f"list_product:{product['name']}"
                ))
        if row:
            markup.add(*row)

    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data="user_list"))
    return markup


def admin_list_types_menu():
    """Admin ro'yxati uchun mahsulot turlari"""
    db = get_db()
    types = db.get_all_product_types()
    markup = telebot.types.InlineKeyboardMarkup()

    for i in range(0, len(types), 2):
        row = []
        for j in range(2):
            if i + j < len(types):
                ptype = types[i + j]
                row.append(telebot.types.InlineKeyboardButton(
                    text=ptype["name"],
                    callback_data=f"admin_list_type:{ptype['name']}"
                ))
        if row:
            markup.add(*row)

    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data="admin_back"))
    return markup


def admin_list_products_by_type_menu(product_type):
    """Admin ro'yxati uchun mahsulotlar (type bo'yicha)"""
    db = get_db()
    products = db.get_products_by_type(product_type)
    markup = telebot.types.InlineKeyboardMarkup()

    for i in range(0, len(products), 2):
        row = []
        for j in range(2):
            if i + j < len(products):
                product = products[i + j]
                row.append(telebot.types.InlineKeyboardButton(
                    text=product["name"],
                    callback_data=f"admin_list_product:{product['name']}"
                ))
        if row:
            markup.add(*row)

    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data="admin_list_types_back"))
    return markup

