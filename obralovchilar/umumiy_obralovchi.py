from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from konfiguratsiya.sozlamalar import ADMIN_ID
from bazasidata.mongodb import bazani_olish
from tugmalar.admin_tugmalar import admin_asosiy_menyusi
from tugmalar.foydalanuvchi_tugmalar import foydalanuvchi_asosiy_menyusi, foydalanuvchi_so_rov_menyusi
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("start"))
async def cmd_boshlash(message: Message, state: FSMContext):
    await state.clear()
    foydalanuvchi_id = message.from_user.id
    username = message.from_user.username or "NoUsername"
    ismi = message.from_user.first_name or "Foydalanuvchi"
    
    bazasi = bazani_olish()
    foydalanuvchi = bazasi.foydalanuvchini_olish(foydalanuvchi_id)
    
    if foydalanuvchi_id == ADMIN_ID:
        # Administrator
        await message.answer(
            "👤 Assalomu alaykum, Administrator!\n\n"
            "Harakatni tanlang:",
            reply_markup=admin_asosiy_menyusi()
        )
    elif foydalanuvchi and foydalanuvchi.get("tasdiqlangan"):
        # Tasdiqlangan foydalanuvchi
        await message.answer(
            f"👋 Assalomu alaykum, {ismi}!\n\n"
            "Harakatni tanlang:",
            reply_markup=foydalanuvchi_asosiy_menyusi()
        )
    else:
        # Yangi foydalanuvchi - tasdiq kerak
        if not foydalanuvchi:
            bazasi.foydalanuvchi_qosh(foydalanuvchi_id, username, ismi, tasdiqlangan=False)
        
        await message.answer(
            "❌ Siz botdan foydalanish uchun admin tasdiqlashingizni kutmoqdasiz.\n"
            "Administrator qabul qilganidan so'ng, yana bir marta /start bosing.\n\n"
            "So'rov yubormoqchimisiz?",
            reply_markup=foydalanuvchi_so_rov_menyusi()
        )

@router.callback_query(F.data == "sorov_yubor")
async def sorov_yuborish(callback: CallbackQuery):
    foydalanuvchi_id = callback.from_user.id
    username = callback.from_user.username or "NoUsername"
    
    bazasi = bazani_olish()
    bazasi.so_rov_qosh(foydalanuvchi_id, username)
    
    await callback.answer()
    await callback.message.edit_text(
        "✅ So'rov yuborildi!\n"
        "Admin tasdiqlashi kutilmoqda..."
    )
    
    # Adminга xabar yuborish
    admin_tugmasi = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"foy_tasdiqlash:{foydalanuvchi_id}"),
            InlineKeyboardButton(text="❌ Rad qilish", callback_data=f"foy_rad:{foydalanuvchi_id}")
        ]
    ])
    
    from aiogram import Bot
    from konfiguratsiya.sozlamalar import BOT_TOKENI
    bot = Bot(token=BOT_TOKENI)
    
    await bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📩 Yangi foydalanuvchi so'rovi:\n\n"
             f"👤 Username: @{username}\n"
             f"🆔 Foydalanuvchi ID: `{foydalanuvchi_id}`",
        reply_markup=admin_tugmasi,
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("foy_tasdiqlash:"))
async def foydalanuvchini_tasdiqlash(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Sizda huquq yo'q", show_alert=True)
        return
    
    foydalanuvchi_id = int(callback.data.split(":")[1])
    bazasi = bazani_olish()
    bazasi.foydalanuvchini_tasdiqlash(foydalanuvchi_id)
    
    await callback.answer("✅ Foydalanuvchi tasdiqlandi")
    await callback.message.edit_text(
        f"✅ Foydalanuvchi {foydalanuvchi_id} tasdiqlandi"
    )
    
    # Foydalanuvchiga xabar yuborish
    from aiogram import Bot
    from konfiguratsiya.sozlamalar import BOT_TOKENI
    bot = Bot(token=BOT_TOKENI)
    
    await bot.send_message(
        chat_id=foydalanuvchi_id,
        text="✅ Sizning akkauntingiz tasdiqlandi!\n"
             "/start bosib yana ishga tushiring"
    )

@router.callback_query(F.data.startswith("foy_rad:"))
async def foydalanuvchini_rad_qilish(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Sizda huquq yo'q", show_alert=True)
        return
    
    foydalanuvchi_id = int(callback.data.split(":")[1])
    bazasi = bazani_olish()
    bazasi.foydalanuvchini_rad_qilish(foydalanuvchi_id)
    
    await callback.answer("❌ Foydalanuvchi rad qilindi")
    await callback.message.edit_text(
        f"❌ Foydalanuvchi {foydalanuvchi_id} rad qilindi"
    )
    
    # Foydalanuvchiga xabar yuborish
    from aiogram import Bot
    from konfiguratsiya.sozlamalar import BOT_TOKENI
    bot = Bot(token=BOT_TOKENI)
    
    await bot.send_message(
        chat_id=foydalanuvchi_id,
        text="❌ Sizning so'rovingiz rad qilindi.\n"
             "Keyinroq yana urinib ko'ring"
    )

@router.callback_query(F.data == "menyuni_yopish")
async def menyuni_yopish(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()

@router.callback_query(F.data == "admin_orqaga")
async def admin_orqaga(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "👤 Admin Menyusi:",
        reply_markup=admin_asosiy_menyusi()
    )

@router.callback_query(F.data == "foy_asosiy")
async def foy_asosiy(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "👋 Bosh Menyusi:",
        reply_markup=foydalanuvchi_asosiy_menyusi()
    )