from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from config.settings import ADMIN_ID, MESSAGES
from database.mongodb import get_db
from keyboards.admin_keyboards import *
from states.admin_states import *
import logging

logger = logging.getLogger(__name__)
router = Router()

# ==================== FILIALLAR ====================

@router.callback_query(F.data == "admin_branch")
async def admin_branch(callback: CallbackQuery, state: FSMContext):
    """Admin filial boshqarish"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer(MESSAGES["error_access_denied"], show_alert=True)
        return
    
    await state.clear()
    await callback.message.edit_text(
        MESSAGES["branch_management"],
        reply_markup=branches_menu()
    )

@router.callback_query(F.data == "branch_add")
async def branch_add(callback: CallbackQuery, state: FSMContext):
    """Filial qo'shish"""
    await state.set_state(AdminBranchStates.adding_branch)
    await callback.message.edit_text(
        MESSAGES["branch_add_prompt"],
        reply_markup=back_button("branch_back")
    )

@router.message(AdminBranchStates.adding_branch)
async def branch_add_name(message: Message, state: FSMContext):
    """Filial nomini kiritish"""
    db = get_db()
    name = message.text.strip()
    
    if db.add_branch(name):
        await state.clear()
        await message.answer(
            MESSAGES["branch_added"].format(name),
            reply_markup=branches_menu()
        )
    else:
        await message.answer(
            MESSAGES["branch_exists"],
            reply_markup=back_button("branch_back")
        )

@router.callback_query(F.data.startswith("branch_select:"))
async def branch_select(callback: CallbackQuery, state: FSMContext):
    """Filial tanlash"""
    branch_name = callback.data.split(":")[1]
    await state.update_data(current_branch=branch_name)
    
    await callback.message.edit_text(
        MESSAGES["branch_action"].format(branch_name),
        reply_markup=branch_action_menu(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "branch_edit")
async def branch_edit(callback: CallbackQuery, state: FSMContext):
    """Filial tahrirlash"""
    await state.set_state(AdminBranchStates.editing_branch)
    await callback.message.edit_text(
        "✍️ Yangi filial nomini kiriting:",
        reply_markup=back_button("branch_edit_back")
    )

@router.message(AdminBranchStates.editing_branch)
async def branch_edit_name(message: Message, state: FSMContext):
    """Filial nomini o'zgartirish"""
    db = get_db()
    data = await state.get_data()
    old_name = data.get("current_branch")
    new_name = message.text.strip()
    
    if db.update_branch(old_name, new_name):
        await state.clear()
        await message.answer(
            MESSAGES["branch_renamed"].format(new_name),
            reply_markup=branches_menu()
        )
    else:
        await message.answer(
            "❌ Xato yuz berdi",
            reply_markup=back_button("branch_edit_back")
        )

@router.callback_query(F.data == "branch_delete")
async def branch_delete(callback: CallbackQuery, state: FSMContext):
    """Filial o'chirish"""
    db = get_db()
    data = await state.get_data()
    branch_name = data.get("current_branch")
    
    db.delete_branch(branch_name)
    await state.clear()
    
    await callback.message.edit_text(
        MESSAGES["branch_deleted"],
        reply_markup=branches_menu()
    )

@router.callback_query(F.data == "branch_back")
async def branch_back(callback: CallbackQuery, state: FSMContext):
    """Filial ro'yxatiga qaytish"""
    await state.clear()
    await callback.message.edit_text(
        MESSAGES["branch_management"],
        reply_markup=branches_menu()
    )

# ==================== MAHSULOTLAR ====================

@router.callback_query(F.data == "admin_product")
async def admin_product(callback: CallbackQuery, state: FSMContext):
    """Admin mahsulot boshqarish"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer(MESSAGES["error_access_denied"], show_alert=True)
        return
    
    await state.clear()
    await callback.message.edit_text(
        MESSAGES["product_management"],
        reply_markup=product_type_menu()
    )

@router.callback_query(F.data == "product_common")
async def product_common(callback: CallbackQuery, state: FSMContext):
    """Umumiy mahsulotlar"""
    await state.clear()
    await state.update_data(product_branch=None)
    await callback.message.edit_text(
        MESSAGES["product_list"].format("Umumiy"),
        reply_markup=products_menu(None),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "product_branch")
async def product_branch(callback: CallbackQuery, state: FSMContext):
    """Filialga xos mahsulotlar"""
    await callback.message.edit_text(
        MESSAGES["product_select_branch"],
        reply_markup=branches_for_products_menu()
    )

@router.callback_query(F.data.startswith("product_branch_select:"))
async def product_branch_select(callback: CallbackQuery, state: FSMContext):
    """Filial uchun mahsulotlar"""
    branch_name = callback.data.split(":")[1]
    await state.update_data(product_branch=branch_name)
    
    await callback.message.edit_text(
        MESSAGES["product_list"].format(branch_name),
        reply_markup=products_menu(branch_name),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("product_add:"))
async def product_add(callback: CallbackQuery, state: FSMContext):
    """Mahsulot qo'shish"""
    branch = callback.data.split(":")[1]
    if branch == "common":
        branch = None
    
    await state.set_state(AdminProductStates.adding_product_name)
    await state.update_data(product_branch=branch)
    
    await callback.message.edit_text(
        MESSAGES["product_add_name"],
        reply_markup=back_button("product_back")
    )

@router.message(AdminProductStates.adding_product_name)
async def product_add_name(message: Message, state: FSMContext):
    """Mahsulot nomi"""
    await state.update_data(product_name=message.text.strip())
    await state.set_state(AdminProductStates.adding_product_image)
    
    await message.answer(
        MESSAGES["product_add_image"],
        reply_markup=yes_no_menu("image_add")
    )

@router.callback_query(F.data.startswith("image_add_"))
async def product_image_question(callback: CallbackQuery, state: FSMContext):
    """Rasm zarurmi"""
    if "yes" in callback.data:
        await callback.message.edit_text(
            MESSAGES["product_send_image"],
            reply_markup=back_button("product_back")
        )
        await state.set_state(AdminProductStates.adding_product_image)
    else:
        db = get_db()
        data = await state.get_data()
        
        db.add_product(data["product_name"], data["product_branch"])
        
        await state.clear()
        branch = data["product_branch"]
        
        await callback.message.edit_text(
            MESSAGES["product_added"].format(data['product_name']),
            reply_markup=products_menu(branch)
        )

@router.message(AdminProductStates.adding_product_image)
async def product_add_image(message: Message, state: FSMContext):
    """Rasm qo'shish"""
    if message.photo:
        db = get_db()
        data = await state.get_data()
        
        image_id = message.photo[-1].file_id
        db.add_product(data["product_name"], data["product_branch"], image_id)
        
        await state.clear()
        branch = data["product_branch"]
        
        await message.answer(
            MESSAGES["product_added"].format(data['product_name']),
            reply_markup=products_menu(branch)
        )
    else:
        await message.answer(
            MESSAGES["error_not_image"],
            reply_markup=back_button("product_back")
        )

@router.callback_query(F.data.startswith("product_select:"))
async def product_select(callback: CallbackQuery, state: FSMContext):
    """Mahsulot tanlash"""
    product_name = callback.data.split(":")[1]
    db = get_db()
    product = db.get_product_by_name(product_name)
    
    await state.update_data(current_product=product_name)
    
    text = MESSAGES["product_action"].format(product_name)
    
    if product.get("image_id"):
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=product["image_id"],
            caption=text,
            reply_markup=product_action_menu(),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            text,
            reply_markup=product_action_menu(),
            parse_mode="HTML"
        )

@router.callback_query(F.data == "product_edit")
async def product_edit(callback: CallbackQuery, state: FSMContext):
    """Mahsulot tahrirlash"""
    await state.set_state(AdminProductStates.editing_product_name)
    await callback.message.edit_text(
        "✍️ Yangi mahsulot nomini kiriting:",
        reply_markup=back_button("product_edit_back")
    )

@router.message(AdminProductStates.editing_product_name)
async def product_edit_name(message: Message, state: FSMContext):
    """Mahsulot nomini o'zgartirish"""
    data = await state.get_data()
    old_name = data["current_product"]
    new_name = message.text.strip()
    
    await state.update_data(new_product_name=new_name)
    await state.set_state(AdminProductStates.editing_product_image)
    
    await message.answer(
        MESSAGES["product_add_image"],
        reply_markup=yes_no_menu("edit_image")
    )

@router.callback_query(F.data.startswith("edit_image_"))
async def product_edit_image_question(callback: CallbackQuery, state: FSMContext):
    """Rasm o'zgartirish"""
    db = get_db()
    data = await state.get_data()
    old_name = data["current_product"]
    new_name = data["new_product_name"]
    
    if "yes" in callback.data:
        await callback.message.edit_text(
            MESSAGES["product_send_image"],
            reply_markup=back_button("product_edit_back")
        )
        await state.set_state(AdminProductStates.editing_product_image)
    else:
        db.update_product(old_name, new_name)
        
        await state.clear()
        branch = data.get("product_branch")
        
        await callback.message.edit_text(
            MESSAGES["product_renamed"].format(new_name),
            reply_markup=products_menu(branch)
        )

@router.message(AdminProductStates.editing_product_image)
async def product_edit_image(message: Message, state: FSMContext):
    """Rasmi o'zgartirilgan mahsulot"""
    if message.photo:
        db = get_db()
        data = await state.get_data()
        old_name = data["current_product"]
        new_name = data["new_product_name"]
        image_id = message.photo[-1].file_id
        
        db.update_product(old_name, new_name, image_id)
        
        await state.clear()
        branch = data.get("product_branch")
        
        await message.answer(
            MESSAGES["product_renamed"].format(new_name),
            reply_markup=products_menu(branch)
        )
    else:
        await message.answer(MESSAGES["error_not_image"])

@router.callback_query(F.data == "product_delete")
async def product_delete(callback: CallbackQuery, state: FSMContext):
    """Mahsulot o'chirish"""
    db = get_db()
    data = await state.get_data()
    product_name = data.get("current_product")
    branch = data.get("product_branch")
    
    db.delete_product(product_name)
    await state.clear()
    
    await callback.message.edit_text(
        MESSAGES["product_deleted"],
        reply_markup=products_menu(branch)
    )

@router.callback_query(F.data == "product_back")
async def product_back(callback: CallbackQuery, state: FSMContext):
    """Mahsulot ro'yxatiga qaytish"""
    data = await state.get_data()
    branch = data.get("product_branch")
    
    await state.clear()
    await state.update_data(product_branch=branch)
    
    await callback.message.edit_text(
        MESSAGES["product_list"].format(branch or "Umumiy"),
        reply_markup=products_menu(branch),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("product_branch_back") | F.data.startswith("product_type_back"))
async def product_branch_back(callback: CallbackQuery, state: FSMContext):
    """Mahsulot turi tanlashga qaytish"""
    await state.clear()
    await callback.message.edit_text(
        MESSAGES["product_management"],
        reply_markup=product_type_menu()
    )

# ==================== RO'YXAT ====================

@router.callback_query(F.data == "admin_list")
async def admin_list(callback: CallbackQuery, state: FSMContext):
    """Admin ro'yxatni ko'rish"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer(MESSAGES["error_access_denied"], show_alert=True)
        return
    
    await state.clear()
    
    db = get_db()
    branches = db.get_all_branches()
    keyboard = []
    
    for branch in branches:
        keyboard.append([
            InlineKeyboardButton(
                text=branch["name"],
                callback_data=f"admin_list_branch:{branch['name']}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(
            text=MESSAGES["button_common"],
            callback_data="admin_list_branch:common"
        )
    ])
    
    keyboard.append([
        InlineKeyboardButton(
            text=MESSAGES["button_back"],
            callback_data="admin_back"
        )
    ])
    
    await callback.message.edit_text(
        MESSAGES["list_title"],
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

@router.callback_query(F.data.startswith("admin_list_branch:"))
async def admin_list_branch(callback: CallbackQuery, state: FSMContext):
    """Admin filial ro'yxati"""
    branch = callback.data.split(":")[1]
    if branch == "common":
        branch = None
    
    await show_admin_inventory_list(callback.message, branch, 0, callback)

async def show_admin_inventory_list(message, branch, page, callback):
    """Admin inventar ro'yxatini ko'rsatish"""
    db = get_db()
    products = db.get_products_by_branch(branch)
    
    from config.settings import ITEMS_PER_PAGE
    total_pages = (len(products) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    
    if total_pages == 0:
        await callback.message.edit_text(
            MESSAGES["list_empty"],
            reply_markup=back_button("admin_list")
        )
        return
    
    start_idx = page * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    page_products = products[start_idx:end_idx]
    
    text = MESSAGES["list_title"] + "\n\n"
    
    for idx, product in enumerate(page_products, start_idx + 1):
        inventory = db.get_inventory(product["name"], branch)
        quantity = inventory.get("quantity", 0)
        text += MESSAGES["list_item"].format(idx, product['name'], quantity) + "\n"
    
    text += MESSAGES["list_page_info"].format(page + 1, total_pages)
    
    keyboard = []
    
    if page > 0:
        keyboard.append([
            InlineKeyboardButton(
                text=MESSAGES["button_prev"],
                callback_data=f"admin_list_page:{page-1}:{branch or 'common'}"
            )
        ])
    
    if page < total_pages - 1:
        keyboard.append([
            InlineKeyboardButton(
                text=MESSAGES["button_next"],
                callback_data=f"admin_list_page:{page+1}:{branch or 'common'}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(
            text=MESSAGES["button_back"],
            callback_data="admin_list"
        )
    ])
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

@router.callback_query(F.data.startswith("admin_list_page:"))
async def admin_list_pagination(callback: CallbackQuery):
    """Admin ro'yxat sahifalari"""
    parts = callback.data.split(":")
    page = int(parts[1])
    branch = parts[2] if len(parts) > 2 and parts[2] != "common" else None
    
    await show_admin_inventory_list(callback.message, branch, page, callback)