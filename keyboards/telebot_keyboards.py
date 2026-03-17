import telebot
from database.mongodb import get_db
from config.settings import MESSAGES
import logging

logger = logging.getLogger(__name__)

# ==================== WAREHOUSE KEYBOARDS ====================

def warehouse_list_menu():
    """✅ Sklad ro'yxati - BIRINCHI BO'LIM"""
    try:
        db = get_db()
        warehouses = db.get_all_warehouses()
        
        markup = telebot.types.InlineKeyboardMarkup()
        
        for warehouse in warehouses:
            row = [
                telebot.types.InlineKeyboardButton(
                    text=warehouse["name"],
                    callback_data=f"warehouse_select:{warehouse['name']}"
                ),
                telebot.types.InlineKeyboardButton(
                    text="⚙️",
                    callback_data=f"warehouse_actions:{warehouse['name']}"
                )
            ]
            markup.add(*row)
        
        markup.add(telebot.types.InlineKeyboardButton(
            MESSAGES["button_add"],
            callback_data="warehouse_add"
        ))
        
        return markup
    except Exception as e:
        logger.error(f"❌ Error in warehouse_list_menu: {e}")
        return telebot.types.InlineKeyboardMarkup()

def warehouse_actions_menu(warehouse):
    """Sklad faoliyatlari"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton(
            "✏️ Tahrirlash",
            callback_data=f"warehouse_edit:{warehouse}"
        ),
        telebot.types.InlineKeyboardButton(
            "🗑️ O'chirish",
            callback_data=f"warehouse_delete:{warehouse}"
        )
    )
    markup.add(telebot.types.InlineKeyboardButton(
        MESSAGES["button_back"],
        callback_data="warehouse_list"
    ))
    return markup

# ==================== ADMIN MAIN MENU ====================

def admin_main_menu(warehouse):
    """✅ ADMIN ASOSIY MENYU - SKLAD BO'LIMIGA KIRIB"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton(
            "🏢 Filial",
            callback_data=f"admin_branch:{warehouse}"
        ),
        telebot.types.InlineKeyboardButton(
            "📦 Mahsulot",
            callback_data=f"admin_product:{warehouse}"
        ),
        telebot.types.InlineKeyboardButton(
            "📋 Ro'yxat",
            callback_data=f"admin_list:{warehouse}"
        )
    )
    markup.add(telebot.types.InlineKeyboardButton(
        "⬅️ Skladlar",
        callback_data="warehouse_list"
    ))
    return markup

# ==================== BRANCH KEYBOARDS ====================

def branches_menu(warehouse):
    """Filiallar ro'yxati"""
    try:
        db = get_db()
        branches = db.get_all_branches(warehouse)
        markup = telebot.types.InlineKeyboardMarkup()
        
        for branch in branches:
            markup.add(telebot.types.InlineKeyboardButton(
                text=branch["name"],
                callback_data=f"branch_select:{warehouse}:{branch['name']}"
            ))
        
        markup.add(telebot.types.InlineKeyboardButton(
            MESSAGES["button_add"],
            callback_data=f"branch_add:{warehouse}"
        ))
        markup.add(telebot.types.InlineKeyboardButton(
            MESSAGES["button_back"],
            callback_data=f"admin_back:{warehouse}"
        ))
        
        return markup
    except Exception as e:
        logger.error(f"❌ Error in branches_menu: {e}")
        return telebot.types.InlineKeyboardMarkup()

# ==================== PRODUCT TYPE KEYBOARDS ====================

def branches_selection_menu(warehouse):
    """✅ FILIALLAR - MAHSULOT TURI TANLASHDAN OLDIN"""
    try:
        db = get_db()
        branches = db.get_all_branches(warehouse)
        markup = telebot.types.InlineKeyboardMarkup()
        
        for branch in branches:
            markup.add(telebot.types.InlineKeyboardButton(
                text=branch["name"],
                callback_data=f"product_branch_select:{warehouse}:{branch['name']}"
            ))
        
        markup.add(telebot.types.InlineKeyboardButton(
            "🌍 Umumiy",
            callback_data=f"product_branch_select:{warehouse}:common"
        ))
        markup.add(telebot.types.InlineKeyboardButton(
            MESSAGES["button_back"],
            callback_data=f"admin_back:{warehouse}"
        ))
        
        return markup
    except Exception as e:
        logger.error(f"❌ Error in branches_selection_menu: {e}")
        return telebot.types.InlineKeyboardMarkup()

def product_types_menu(warehouse, branch):
    """✅ MAHSULOT TURLARI - RASIMLI!"""
    try:
        db = get_db()
        types = db.get_all_product_types(warehouse, branch)
        
        markup = telebot.types.InlineKeyboardMarkup()
        
        if not types:
            markup.add(telebot.types.InlineKeyboardButton(
                MESSAGES["button_add"],
                callback_data=f"product_type_add:{warehouse}:{branch}"
            ))
        else:
            for ptype in types:
                row = [
                    telebot.types.InlineKeyboardButton(
                        text=f"📦 {ptype['name']}",
                        callback_data=f"product_type_select:{warehouse}:{branch}:{ptype['name']}"
                    ),
                    telebot.types.InlineKeyboardButton(
                        text="⚙️",
                        callback_data=f"product_type_actions:{warehouse}:{branch}:{ptype['name']}"
                    )
                ]
                markup.add(*row)
            
            markup.add(telebot.types.InlineKeyboardButton(
                MESSAGES["button_add"],
                callback_data=f"product_type_add:{warehouse}:{branch}"
            ))
        
        markup.add(telebot.types.InlineKeyboardButton(
            MESSAGES["button_back"],
            callback_data=f"product_branch_back:{warehouse}:{branch}"
        ))
        
        return markup
    except Exception as e:
        logger.error(f"❌ Error in product_types_menu: {e}")
        return telebot.types.InlineKeyboardMarkup()

def product_type_actions_menu(warehouse, branch, product_type):
    """Mahsulot turi faoliyatlari"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton(
            "✏️ Tahrirlash",
            callback_data=f"product_type_edit:{warehouse}:{branch}:{product_type}"
        ),
        telebot.types.InlineKeyboardButton(
            "🗑️ O'chirish",
            callback_data=f"product_type_delete:{warehouse}:{branch}:{product_type}"
        )
    )
    markup.add(telebot.types.InlineKeyboardButton(
        MESSAGES["button_back"],
        callback_data=f"product_type_back:{warehouse}:{branch}"
    ))
    return markup

def products_by_type_menu(warehouse, branch, product_type):
    """✅ MAHSULOTLAR - 2 QATORDAN + KOD"""
    try:
        db = get_db()
        products = db.get_products_by_type(warehouse, branch, product_type)
        
        markup = telebot.types.InlineKeyboardMarkup()
        
        if not products:
            markup.add(telebot.types.InlineKeyboardButton(
                MESSAGES["button_add"],
                callback_data=f"product_add:{warehouse}:{branch}:{product_type}"
            ))
        else:
            for i in range(0, len(products), 2):
                row = []
                for j in range(2):
                    if i + j < len(products):
                        product = products[i + j]
                        row.append(telebot.types.InlineKeyboardButton(
                            text=f"📦 {product['name']}",
                            callback_data=f"product_select:{warehouse}:{branch}:{product_type}:{product['name']}"
                        ))
                if row:
                    markup.add(*row)
            
            markup.add(telebot.types.InlineKeyboardButton(
                MESSAGES["button_add"],
                callback_data=f"product_add:{warehouse}:{branch}:{product_type}"
            ))
        
        markup.add(telebot.types.InlineKeyboardButton(
            MESSAGES["button_back"],
            callback_data=f"product_type_back:{warehouse}:{branch}"
        ))
        
        return markup
    except Exception as e:
        logger.error(f"❌ Error in products_by_type_menu: {e}")
        return telebot.types.InlineKeyboardMarkup()

# ==================== UTILITY KEYBOARDS ====================

def back_button(callback_data="back"):
    """Orqaga tugmasi"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(
        MESSAGES["button_back"],
        callback_data=callback_data
    ))
    return markup

# ==================== USER KEYBOARDS ====================

def user_main_menu():
    """Foydalanuvchi bosh menyu"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(
        MESSAGES["button_add_product"],
        callback_data="user_input"
    ))
    markup.add(telebot.types.InlineKeyboardButton(
        MESSAGES["button_remove_product"],
        callback_data="user_remove"
    ))
    markup.add(telebot.types.InlineKeyboardButton(
        MESSAGES["button_list"],
        callback_data="user_list"
    ))
    return markup

def user_request_menu():
    """So'rov menyu"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(
        MESSAGES["button_send_request"],
        callback_data="send_request"
    ))
    return markup

def product_types_menu_user(action="input"):
    """Foydalanuvchi uchun mahsulot turlari"""
    try:
        db = get_db()
        types = db.get_all_product_types()
        markup = telebot.types.InlineKeyboardMarkup()
        
        for ptype in types:
            markup.add(telebot.types.InlineKeyboardButton(
                text=ptype["name"],
                callback_data=f"user_{action}_type:{ptype['name']}"
            ))
        
        markup.add(telebot.types.InlineKeyboardButton(
            MESSAGES["button_back"],
            callback_data="user_main"
        ))
        return markup
    except Exception as e:
        logger.error(f"❌ Error in product_types_menu_user: {e}")
        return telebot.types.InlineKeyboardMarkup()

def products_by_type_menu_user(product_type, action="input"):
    """Foydalanuvchi uchun mahsulotlar turiga ko'ra"""
    try:
        db = get_db()
        products = db.get_products_by_type_all(product_type)
        markup = telebot.types.InlineKeyboardMarkup()
        
        if not products:
            markup.add(telebot.types.InlineKeyboardButton(
                MESSAGES["button_back"],
                callback_data=f"user_{action}_back"
            ))
            return markup
        
        for i in range(0, len(products), 2):
            row = []
            for j in range(2):
                if i + j < len(products):
                    product = products[i + j]
                    row.append(telebot.types.InlineKeyboardButton(
                        text=f"📦 {product['name']}",
                        callback_data=f"user_{action}_product:{product['name']}"
                    ))
            if row:
                markup.add(*row)
        
        markup.add(telebot.types.InlineKeyboardButton(
            MESSAGES["button_back"],
            callback_data=f"user_{action}_back"
        ))
        return markup
    except Exception as e:
        logger.error(f"❌ Error in products_by_type_menu_user: {e}")
        return telebot.types.InlineKeyboardMarkup()

def branches_menu_user(action="input"):
    """Foydalanuvchi uchun filiallar"""
    try:
        db = get_db()
        branches = db.get_all_branches()  # ALL WAREHOUSES
        markup = telebot.types.InlineKeyboardMarkup()
        
        for branch in branches:
            markup.add(telebot.types.InlineKeyboardButton(
                text=branch["name"],
                callback_data=f"user_{action}_branch:{branch['name']}"
            ))
        
        markup.add(telebot.types.InlineKeyboardButton(
            MESSAGES["button_back"],
            callback_data="user_main"
        ))
        return markup
    except Exception as e:
        logger.error(f"❌ Error in branches_menu_user: {e}")
        return telebot.types.InlineKeyboardMarkup()

def list_branches_menu():
    """Ro'yxat uchun filiallar"""
    try:
        db = get_db()
        branches = db.get_all_branches()
        markup = telebot.types.InlineKeyboardMarkup()
        
        for branch in branches:
            markup.add(telebot.types.InlineKeyboardButton(
                text=branch["name"],
                callback_data=f"list_branch:{branch['name']}"
            ))
        
        markup.add(telebot.types.InlineKeyboardButton(
            MESSAGES["button_back"],
            callback_data="user_main"
        ))
        return markup
    except Exception as e:
        logger.error(f"❌ Error in list_branches_menu: {e}")
        return telebot.types.InlineKeyboardMarkup()