import telebot
from database.mongodb import get_db
from config.settings import MESSAGES
import logging

logger = logging.getLogger(__name__)

# ==================== WAREHOUSE KEYBOARDS ====================

def warehouse_list_menu():
    """✅ Sklad ro'yxati - PLUS TUGMA BILAN!"""
    try:
        db = get_db()
        warehouses = db.get_all_warehouses()
        
        markup = telebot.types.InlineKeyboardMarkup()
        
        # ✅ BARCHA SKLADLAR
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
        
        # ✅ PLUS TUGMA - SKLAD QO'SHISH
        markup.add(telebot.types.InlineKeyboardButton(
            MESSAGES["button_add"],
            callback_data="warehouse_add"
        ))
        markup.add(telebot.types.InlineKeyboardButton(
            "⚙️ Boshqarish",
            callback_data="admin_settings"
        ))
        return markup
    except Exception as e:
        logger.error(f"❌ Error in warehouse_list_menu: {e}")
        return telebot.types.InlineKeyboardMarkup()

def warehouse_actions_menu(warehouse):
    """Sklad faoliyatlari - tahrirlash va o'chirish"""
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
        "⬅️ Qaytish",
        callback_data="warehouse_list"
    ))
    return markup

def admin_settings_menu():
    """Admin sozlamalari"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("📏 Birliklar", callback_data="units_menu"))
    markup.add(telebot.types.InlineKeyboardButton("⬅️ Qaytish", callback_data="warehouse_list"))
    return markup

def units_menu():
    """Birliklar ro'yxati"""
    markup = telebot.types.InlineKeyboardMarkup()
    db = get_db()
    units = db.get_all_units()
    for unit in units:
        markup.add(
            telebot.types.InlineKeyboardButton(
                text=f"📏 {unit['name']}",
                callback_data=f"unit_select:{unit['name']}"
            )
        )
    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_add"], callback_data="unit_add"))
    markup.add(telebot.types.InlineKeyboardButton(MESSAGES["button_back"], callback_data="admin_settings"))
    return markup

def units_choose_menu(callback_prefix="product_unit_select"):
    """Mahsulot uchun birlik tanlash tugmalari"""
    markup = telebot.types.InlineKeyboardMarkup()
    db = get_db()
    units = db.get_all_units()
    for unit in units:
        markup.add(
            telebot.types.InlineKeyboardButton(
                text=f"📏 {unit['name']}",
                callback_data=f"{callback_prefix}:{unit['name']}"
            )
        )
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
        
        if types:
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
        
        # ✅ PLUS TUGMA - TUR QO'SHISH
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
        
        if products:
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
        
        # ✅ PLUS TUGMA - MAHSULOT QO'SHISH
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

def user_main_menu(warehouse):
    """Foydalanuvchi bosh menyu"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(
        MESSAGES["button_add_product"],
        callback_data=f"user_input:{warehouse}"
    ))
    markup.add(telebot.types.InlineKeyboardButton(
        MESSAGES["button_remove_product"],
        callback_data=f"user_remove:{warehouse}"
    ))
    markup.add(telebot.types.InlineKeyboardButton(
        MESSAGES["button_list"],
        callback_data=f"user_list:{warehouse}"
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

def user_warehouse_menu():
    """Tasdiqlangan foydalanuvchi uchun sklad tanlash"""
    try:
        db = get_db()
        warehouses = db.get_all_warehouses()
        markup = telebot.types.InlineKeyboardMarkup()
        
        for warehouse in warehouses:
            markup.add(telebot.types.InlineKeyboardButton(
                text=f"🏭 {warehouse['name']}",
                callback_data=f"user_warehouse:{warehouse['name']}"
            ))
        return markup
    except Exception as e:
        logger.error(f"❌ Error in user_warehouse_menu: {e}")
        return telebot.types.InlineKeyboardMarkup()

def branches_menu_user(warehouse, action="input"):
    """Foydalanuvchi uchun bo'limlar ro'yxati"""
    try:
        db = get_db()
        branches = db.get_all_branches(warehouse)
        markup = telebot.types.InlineKeyboardMarkup()

        for branch in branches:
            markup.add(telebot.types.InlineKeyboardButton(
                text=f"🏢 {branch['name']}",
                callback_data=f"user_{action}_branch:{warehouse}:{branch['name']}"
            ))

        markup.add(telebot.types.InlineKeyboardButton(
            "🌍 Umumiy",
            callback_data=f"user_{action}_branch:{warehouse}:common"
        ))
        
        markup.add(telebot.types.InlineKeyboardButton(
            MESSAGES["button_back"],
            callback_data=f"user_main:{warehouse}"
        ))
        return markup
    except Exception as e:
        logger.error(f"❌ Error in branches_menu_user: {e}")
        return telebot.types.InlineKeyboardMarkup()

def product_types_menu_user(warehouse, branch, action="input"):
    """Foydalanuvchi uchun mahsulot turlari"""
    try:
        db = get_db()
        types = db.get_all_product_types(warehouse, branch)
        markup = telebot.types.InlineKeyboardMarkup()
        
        for i in range(0, len(types), 2):
            row = []
            for j in range(2):
                if i + j < len(types):
                    ptype = types[i + j]
                    row.append(telebot.types.InlineKeyboardButton(
                        text=f"📦 {ptype['name']}",
                        callback_data=f"user_{action}_type:{warehouse}:{branch}:{ptype['name']}"
                    ))
            if row:
                markup.add(*row)
        
        markup.add(telebot.types.InlineKeyboardButton(
            MESSAGES["button_back"],
            callback_data=f"user_{action}_branches:{warehouse}"
        ))
        return markup
    except Exception as e:
        logger.error(f"❌ Error in product_types_menu_user: {e}")
        return telebot.types.InlineKeyboardMarkup()

def products_by_type_menu_user(warehouse, branch, product_type, action="input", include_back=True):
    """Foydalanuvchi uchun mahsulotlar turiga ko'ra"""
    try:
        db = get_db()
        products = db.get_products_by_type(warehouse, branch, product_type)
        markup = telebot.types.InlineKeyboardMarkup()
        
        for i in range(0, len(products), 2):
            row = []
            for j in range(2):
                if i + j < len(products):
                    product = products[i + j]
                    row.append(telebot.types.InlineKeyboardButton(
                        text=f"📦 {product['name']}",
                        callback_data=f"user_{action}_product:{warehouse}:{branch}:{product_type}:{product['name']}"
                    ))
            if row:
                markup.add(*row)

        if include_back:
            markup.add(telebot.types.InlineKeyboardButton(
                MESSAGES["button_back"],
                callback_data=f"user_{action}_types:{warehouse}:{branch}"
            ))
        return markup
    except Exception as e:
        logger.error(f"❌ Error in products_by_type_menu_user: {e}")
        return telebot.types.InlineKeyboardMarkup()

def remove_description_menu(warehouse, branch, product_type, product_name, quantity):
    """Chiqarish uchun tavsif so'rash tugmalari"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton(
            MESSAGES["button_yes"],
            callback_data=f"user_remove_desc_yes:{warehouse}:{branch}:{product_type}:{product_name}:{quantity}"
        ),
        telebot.types.InlineKeyboardButton(
            MESSAGES["button_no"],
            callback_data=f"user_remove_desc_no:{warehouse}:{branch}:{product_type}:{product_name}:{quantity}"
        ),
    )
    markup.add(telebot.types.InlineKeyboardButton(
        MESSAGES["button_back"],
        callback_data=f"user_remove_product:{warehouse}:{branch}:{product_type}:{product_name}"
    ))
    return markup

def remove_target_branch_menu(warehouse, product_type, product_name, quantity):
    """Umumiy bo'limdan chiqarilganda mahsulot qaysi bo'limga chiqqanini tanlash."""
    markup = telebot.types.InlineKeyboardMarkup()
    db = get_db()
    branches = db.get_all_branches(warehouse)
    for branch in branches:
        markup.add(
            telebot.types.InlineKeyboardButton(
                text=f"🏢 {branch['name']}",
                callback_data=f"user_remove_target_branch:{warehouse}:{branch['name']}:{product_type}:{product_name}:{quantity}",
            )
        )
    markup.add(
        telebot.types.InlineKeyboardButton(
            "🌍 Umumiy bo'lim",
            callback_data=f"user_remove_target_branch:{warehouse}:common:{product_type}:{product_name}:{quantity}",
        )
    )
    markup.add(
        telebot.types.InlineKeyboardButton(
            MESSAGES["button_back"],
            callback_data=f"user_remove_product:{warehouse}:common:{product_type}:{product_name}",
        )
    )
    return markup

def input_quantity_back_menu(warehouse, branch, product_type):
    """Kiritish miqdori oynasi uchun ortga tugmasi"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(
        MESSAGES["button_back"],
        callback_data=f"user_input_products:{warehouse}:{branch}:{product_type}"
    ))
    return markup

def remove_quantity_back_menu(warehouse, branch, product_type):
    """Chiqarish miqdori oynasi uchun ortga tugmasi"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(
        MESSAGES["button_back"],
        callback_data=f"user_remove_products:{warehouse}:{branch}:{product_type}"
    ))
    return markup

def list_branches_menu(warehouse):
    """Ro'yxat uchun bo'limlar"""
    try:
        db = get_db()
        branches = db.get_all_branches(warehouse)
        markup = telebot.types.InlineKeyboardMarkup()
        
        for branch in branches:
            markup.add(telebot.types.InlineKeyboardButton(
                text=f"🏢 {branch['name']}",
                callback_data=f"list_branch:{warehouse}:{branch['name']}"
            ))
            
        markup.add(telebot.types.InlineKeyboardButton(
            "🌍 Umumiy",
            callback_data=f"list_branch:{warehouse}:common"
        ))
        markup.add(telebot.types.InlineKeyboardButton(
            MESSAGES["button_back"],
            callback_data=f"user_main:{warehouse}"
        ))
        return markup
    except Exception as e:
        logger.error(f"❌ Error in list_branches_menu: {e}")
        return telebot.types.InlineKeyboardMarkup()