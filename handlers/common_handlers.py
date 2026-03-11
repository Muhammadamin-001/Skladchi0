from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from config.settings import ADMIN_ID, MESSAGES, BOT_TOKEN
from database.mongodb import get_db
from keyboards.admin_keyboards import admin_main_menu
from keyboards.user_keyboards import user_main_menu, user_request_menu
from aiogram import Bot
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Bot /start komandasini ishlatish"""
    await state.clear()
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"
    first_name = message.from_user.first_name or "Foydalanuvchi"
    
    db = get_db()
    user = db.get_user(user_id)
    
    if user_id == ADMIN_ID:
        # Admin uchun
        await message.answer(
            MESSAGES["start_admin"],
            reply_markup=admin_main_menu()
        )
    elif user and user.get("approved"):
        # Tasdiqlanmagan foydalanuvchi
        await message.answer(
            MESSAGES["start_user_approved"].format(first_name),
            reply_markup=user_main_menu()
        )
    else:
        # Yangi foydalanuvchi
        if not user:
            db.add_user(user_id, username, first_name, approved=False)
        
        await message.answer(
            MESSAGES["start_user_unapproved"],
            reply_markup=user_request_menu()
        )

@router.callback_query(F.data == "send_request")
async def send_request(callback: CallbackQuery):
    """Foydalanuvchi tasdiqlash so'rovini yuborish"""
    user_id = callback.from_user.id
    username = callback.from_user.username or "NoUsername"
    
    db = get_db()
    db.add_request(user_id, username)
    
    await callback.answer()
    await callback.message.edit_text(
        MESSAGES["request_sent"]
    )
    
    # Adminni bilgilash
    admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=MESSAGES["button_approve"],
                callback_data=f"approve_user:{user_id}"
            ),
            InlineKeyboardButton(
                text=MESSAGES["button_reject"],
                callback_data=f"reject_user:{user_id}"
            )
        ]
    ])
    
    bot = Bot(token=BOT_TOKEN)
    
    await bot.send_message(
        chat_id=ADMIN_ID,
        text=MESSAGES["request_received"].format(username, user_id),
        reply_markup=admin_keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("approve_user:"))
async def approve_user_handler(callback: CallbackQuery):
    """Foydalanuvchini tasdiqlash"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer(MESSAGES["error_access_denied"], show_alert=True)
        return
    
    user_id = int(callback.data.split(":")[1])
    db = get_db()
    db.approve_user(user_id)
    db.delete_request(user_id)
    
    await callback.answer("✅ Foydalanuvchi tasdiqlandı")
    await callback.message.edit_text(
        f"✅ Foydalanuvchi {user_id} tasdiqlandı"
    )
    
    # Foydalanuvchini xabardor qilish
    bot = Bot(token=BOT_TOKEN)
    
    await bot.send_message(
        chat_id=user_id,
        text=MESSAGES["user_approved"]
    )

@router.callback_query(F.data.startswith("reject_user:"))
async def reject_user_handler(callback: CallbackQuery):
    """Foydalanuvchini rad qilish"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer(MESSAGES["error_access_denied"], show_alert=True)
        return
    
    user_id = int(callback.data.split(":")[1])
    db = get_db()
    db.reject_user(user_id)
    db.delete_request(user_id)
    
    await callback.answer("❌ Foydalanuvchi rad qilindi")
    await callback.message.edit_text(
        f"❌ Foydalanuvchi {user_id} rad qilindi"
    )
    
    # Foydalanuvchini xabardor qilish
    bot = Bot(token=BOT_TOKEN)
    
    await bot.send_message(
        chat_id=user_id,
        text=MESSAGES["user_rejected"]
    )

@router.callback_query(F.data == "close_menu")
async def close_menu(callback: CallbackQuery):
    """Menyu yopish"""
    await callback.message.delete()
    await callback.answer()

@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery, state: FSMContext):
    """Admin bosh menyuga qaytish"""
    await state.clear()
    await callback.message.edit_text(
        MESSAGES["start_admin"],
        reply_markup=admin_main_menu()
    )

@router.callback_query(F.data == "user_main")
async def user_main(callback: CallbackQuery, state: FSMContext):
    """Foydalanuvchi bosh menyuga qaytish"""
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "👋 Asosiy Menyu",
        reply_markup=user_main_menu()
    )

# Xatoda o'chko'z berish
@router.message()
async def echo(message: Message):
    """Xabar qabul qilish"""
    pass