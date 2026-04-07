import telebot

def group_menu():
    """Guruh boshqarish asosiy menyu"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("➕ Guruh Qo'shish", callback_data="group_add_start"),
        telebot.types.InlineKeyboardButton("🗑️ Guruh O'chirish", callback_data="group_remove_start"),
    )
    markup.add(telebot.types.InlineKeyboardButton("⬅️ Ortga", callback_data="admin_settings"))
    return markup

def group_actions_menu():
    """Guruh qo'shish/o'chirish faoliyatlari"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("➕ Qo'shish", callback_data="group_add"),
        telebot.types.InlineKeyboardButton("🗑️ O'chirish", callback_data="group_remove"),
    )
    markup.add(telebot.types.InlineKeyboardButton("⬅️ Ortga", callback_data="groups_menu"))
    return markup

def group_select_menu(warehouse, action):
    """Sklad ro'yxatini tugmalar ko'rinishida"""
    db_data = __import__('database.mongodb', fromlist=['get_db']).get_db()
    warehouses = db_data.get_all_warehouses()
    
    markup = telebot.types.InlineKeyboardMarkup()
    for warehouse_doc in warehouses:
        warehouse_name = warehouse_doc["name"]
        markup.add(
            telebot.types.InlineKeyboardButton(
                f"📦 {warehouse_name}",
                callback_data=f"group_select_warehouse:{warehouse_name}:{action}"
            )
        )
    markup.add(telebot.types.InlineKeyboardButton("⬅️ Ortga", callback_data="groups_menu"))
    return markup

def group_confirm_menu(warehouse, group_link, action):
    """Guruh linki kiritgandan so'ng tasdiqlash"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("✅ Ha", callback_data=f"group_confirm:{warehouse}:{action}"),
        telebot.types.InlineKeyboardButton("⬅️ Ortga", callback_data=f"group_select_warehouse:{warehouse}:{action}"),
    )
    return markup

def group_list_menu(warehouse):
    """Skladga qo'shilgan guruhlar ro'yxati"""
    db_data = __import__('database.mongodb', fromlist=['get_db']).get_db()
    groups = db_data.get_warehouse_groups(warehouse)
    
    markup = telebot.types.InlineKeyboardMarkup()
    for group in groups:
        group_name = group.get('group_name', 'Noma\'lum')
        markup.add(
            telebot.types.InlineKeyboardButton(
                f"❌ {group_name}",
                callback_data=f"group_delete_select:{warehouse}:{group['group_id']}"
            )
        )
    markup.add(telebot.types.InlineKeyboardButton("⬅️ Ortga", callback_data="group_remove_start"))
    return markup

def back_button(callback_data):
    """Ortga tugmasi"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("⬅️ Ortga", callback_data=callback_data))
    return markup