from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database.mongodb import get_db
from keyboards.user_keyboards import *
from states.user_states import *
from config.settings import MESSAGES
import logging

logger = logging.getLogger(__name__)
router = Router()

# ==================== MAHSULOT KIRITISH ====================

@router.callback_query(F.data == "user_input")
async def user_input(callback: CallbackQuery, state: FSMContext):
    """Mahsulot kiritish boshlash"""
    await state.set_state(UserInputStates.choosing_branch)
    
    await callback.message.edit_text(
        MESSAGES["user_add_product"],
        reply_markup=branches_menu_user("input")
    )

@router.callback_query(F.data.startswith("user_input_branch:"), UserInputStates.choosing_branch)
async def user_input_branch(callback: CallbackQuery, state: FSMContext):
    """Kiritish uchun filial tanlash"""
    branch = callback.data.split(":")[1]
    if branch == "common":
        branch = None
    
    await state.update_data(current_branch=branch)
    await state.set_state(UserInputStates.choosing_product)
    
    branch_name = branch or "Umumiy bo'lim"
    
    await callback.message.edit_text(
        f"📦 {branch_name}\n\n{MESSAGES['user_select_product']}",
        reply_markup=products_menu_user(branch, "input")
    )

@router.callback_query(F.data.startswith("user_input_product:"), UserInputStates.choosing_product)
async def user_input_product(callback: CallbackQuery, state: FSMContext):
    """Kiritish uchun mahsulot tanlash"""
    product_name = callback.data.split(":")[1]
    db = get_db()
    product = db.get_product_by_name(product_name)
    data = await state.get_data()
    branch = data.get("current_branch")
    
    await state.update_data(current_product=product_name)
    await state.set_state(UserInputStates.entering_quantity)
    
    text = f"📦 <b>{product_name}</b>\n\n{MESSAGES['user_enter_quantity']}"
    
    if product.get("image_id"):
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=product["image_id"],
            caption=text,
            reply_markup=back_button_user("user_input_back"),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            text,
            reply_markup=back_button_user("user_input_back"),
            parse_mode="HTML"
        )

@router.message(UserInputStates.entering_quantity)
async def user_input_quantity(message: Message, state: FSMContext):
    """Kiritilish miqdorini olish"""
    try:
        quantity = int(message.text)
        if quantity <= 0:
            await message.answer(MESSAGES["error_invalid_number"])
            return
        
        db = get_db()
        data = await state.get_data()
        product_name = data.get("current_product")
        branch = data.get("current_branch")
        
        new_quantity = db.add_inventory(product_name, branch, quantity)
        
        await message.answer(
            MESSAGES["user_product_added"].format(
                product_name,
                quantity,
                new_quantity
            ),
            reply_markup=products_menu_user(branch, "input")
        )
        
        await state.set_state(UserInputStates.choosing_product)
    except ValueError:
        await message.answer(MESSAGES["error_invalid_quantity"])

@router.callback_query(F.data == "user_input_back")
async def user_input_back(callback: CallbackQuery, state: FSMContext):
    """Kiritishdan orqaga"""
    data = await state.get_data()
    branch = data.get("current_branch")
    
    await state.set_state(UserInputStates.choosing_product)
    
    branch_name = branch or "Umumiy bo'lim"
    
    await callback.message.edit_text(
        f"📦 {branch_name}\n\n{MESSAGES['user_select_product']}",
        reply_markup=products_menu_user(branch, "input")
    )

# ==================== MAHSULOT CHIQARISH ====================

@router.callback_query(F.data == "user_remove")
async def user_remove(callback: CallbackQuery, state: FSMContext):
    """Mahsulot chiqarish boshlash"""
    await state.set_state(UserRemoveStates.choosing_branch)
    
    await callback.message.edit_text(
        MESSAGES["user_remove_product"],
        reply_markup=branches_menu_user("remove")
    )

@router.callback_query(F.data.startswith("user_remove_branch:"), UserRemoveStates.choosing_branch)
async def user_remove_branch(callback: CallbackQuery, state: FSMContext):
    """Chiqarish uchun filial tanlash"""
    branch = callback.data.split(":")[1]
    if branch == "common":
        branch = None
    
    await state.update_data(current_branch=branch)
    await state.set_state(UserRemoveStates.choosing_product)
    
    branch_name = branch or "Umumiy bo'lim"
    
    await callback.message.edit_text(
        f"📦 {branch_name}\n\n{MESSAGES['user_select_product']}",
        reply_markup=products_menu_user(branch, "remove")
    )

@router.callback_query(F.data.startswith("user_remove_product:"), UserRemoveStates.choosing_product)
async def user_remove_product(callback: CallbackQuery, state: FSMContext):
    """Chiqarish uchun mahsulot tanlash"""
    product_name = callback.data.split(":")[1]
    db = get_db()
    product = db.get_product_by_name(product_name)
    data = await state.get_data()
    branch = data.get("current_branch")
    inventory = db.get_inventory(product_name, branch)
    current_qty = inventory.get("quantity", 0)
    
    await state.update_data(current_product=product_name)
    await state.set_state(UserRemoveStates.entering_quantity)
    
    text = f"📦 <b>{product_name}</b>\n" \
           f"📊 Mavjud: <b>{current_qty}</b> dona\n\n" \
           f"{MESSAGES['user_enter_remove_qty']}"
    
    if product.get("image_id"):
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=product["image_id"],
            caption=text,
            reply_markup=back_button_user("user_remove_back"),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            text,
            reply_markup=back_button_user("user_remove_back"),
            parse_mode="HTML"
        )

@router.message(UserRemoveStates.entering_quantity)
async def user_remove_quantity(message: Message, state: FSMContext):
    """Chiqarilish miqdorini olish"""
    try:
        quantity = int(message.text)
        if quantity <= 0:
            await message.answer(MESSAGES["error_invalid_number"])
            return
        
        db = get_db()
        data = await state.get_data()
        product_name = data.get("current_product")
        branch = data.get("current_branch")
        
        new_quantity = db.remove_inventory(product_name, branch, quantity)
        
        await message.answer(
            MESSAGES["user_product_removed"].format(
                product_name,
                quantity,
                new_quantity
            ),
            reply_markup=products_menu_user(branch, "remove")
        )
        
        await state.set_state(UserRemoveStates.choosing_product)
    except ValueError:
        await message.answer(MESSAGES["error_invalid_quantity"])

@router.callback_query(F.data == "user_remove_back")
async def user_remove_back(callback: CallbackQuery, state: FSMContext):
    """Chiqarishdan orqaga"""
    data = await state.get_data()
    branch = data.get("current_branch")
    
    await state.set_state(UserRemoveStates.choosing_product)
    
    branch_name = branch or "Umumiy bo'lim"
    
    await callback.message.edit_text(
        f"📦 {branch_name}\n\n{MESSAGES['user_select_product']}",
        reply_markup=products_menu_user(branch, "remove")
    )

# ==================== RO'YXAT ====================

@router.callback_query(F.data == "user_list")
async def user_list(callback: CallbackQuery, state: FSMContext):
    """Foydalanuvchi ro'yxat ko'rish"""
    await state.clear()
    await state.set_state(UserListStates.choosing_branch)
    
    await callback.message.edit_text(
        MESSAGES["list_select_branch"],
        reply_markup=list_branches_menu()
    )

@router.callback_query(F.data.startswith("list_branch:"), UserListStates.choosing_branch)
async def list_branch(callback: CallbackQuery, state: FSMContext):
    """Filial ro'yxati"""
    branch = callback.data.split(":")[1]
    if branch == "common":
        branch = None
    
    await state.update_data(list_branch=branch, list_page=0)
    await state.set_state(UserListStates.viewing_page)
    await show_inventory_list(callback, branch, 0)

@router.callback_query(F.data.startswith("list_page:"))
async def list_pagination(callback: CallbackQuery, state: FSMContext):
    """Ro'yxat sahifalanishi"""
    parts = callback.data.split(":")
    page = int(parts[1])
    branch = parts[2] if parts[2] != "common" else None
    
    await show_inventory_list(callback, branch, page)

async def show_inventory_list(callback, branch, page):
    """Inventar ro'yxatini ko'rsatish"""
    db = get_db()
    products = db.get_products_by_branch(branch)
    
    from config.settings import ITEMS_PER_PAGE
    total_pages = (len(products) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    
    if total_pages == 0:
        await callback.message.edit_text(
            MESSAGES["list_empty"],
            reply_markup=back_button_user("user_main")
        )
        return
    
    start_idx = page * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    page_products = products[start_idx:end_idx]
    
    text = MESSAGES["list_title"] + "\n\n"
    
    for idx, product in enumerate(page_products, start_idx + 1):
        inventory = db.get_inventory(product["name"], branch)
        quantity = inventory.get("quantity", 0)
        
        if product.get("image_id"):
            text += MESSAGES["list_item"].format(idx, product['name'], quantity) + " 📷\n"
        else:
            text += MESSAGES["list_item"].format(idx, product['name'], quantity) + "\n"
    
    text += MESSAGES["list_page_info"].format(page + 1, total_pages)
    
    await callback.message.edit_text(
        text,
        reply_markup=pagination_menu(page, total_pages, branch or "common", "list_page"),
        parse_mode="HTML"
    )