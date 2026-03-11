from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from konfiguratsiya.sozlamalar import ADMIN_ID
from bazasidata.mongodb import bazani_olish
from tugmalar.admin_tugmalar import *
import logging

logger = logging.getLogger(__name__)
router = Router()

class FilialHolatlari(StatesGroup):
    qosh = State()
    tahrir = State()

class MahsulotHolatlari(StatesGroup):
    nomini_qosh = State()
    rasmini_qosh = State()
    nomini_tahrir = State()
    rasmini_tahrir = State()

# ==================== FILIALLAR ====================
@router.callback_query(F.data == "admin_filial")
async def admin_filial(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Sizda huquq yo'q", show_alert=True)
        return
    
    await state.clear()
    await callback.message.edit_text(
        "🏢 Filiallarni Boshqarish:\n\n"
        "Filiallardan birini tanlang yoki yangi filial qoshing:",
        reply_markup=filiallar_menyusi()
    )

@router.callback_query(F.data == "filial_qosh")
async def filial_qosh(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FilialHolatlari.qosh)
    await callback.message.edit_text(
        "✍️ Yangi filialning nomini kiriting:",
        reply_markup=orqaga_tugmasi("filial_orqaga")
    )

@router.message(FilialHolatlari.qosh)
async def filial_nomi_qosh(message: Message, state: FSMContext):
    bazasi = bazani_olish()
    nomi = message.text.strip()
    
    if bazasi.filial_qosh(nomi):
        await state.clear()
        await message.answer(
            f"✅ Filial '{nomi}' qo'shildi",
            reply_markup=filiallar_menyusi()
        )
    else:
        await message.answer(
            "❌ Bunday nomda filial allaqachon mavjud",
            reply_markup=orqaga_tugmasi("filial_orqaga")
        )

@router.callback_query(F.data.startswith("filial_tanlash:"))
async def filial_tanlash(callback: CallbackQuery, state: FSMContext):
    filial_nomi = callback.data.split(":")[1]
    await state.update_data(joriy_filial=filial_nomi)
    
    await callback.message.edit_text(
        f"🏢 Filial: <b>{filial_nomi}</b>\n\n"
        "Harakatni tanlang:",
        reply_markup=filial_harakatlari_menyusi(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "filial_tahrir")
async def filial_tahrir(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FilialHolatlari.tahrir)
    await callback.message.edit_text(
        "✍️ Filialning yangi nomini kiriting:",
        reply_markup=orqaga_tugmasi("filial_tahrir_orqaga")
    )

@router.message(FilialHolatlari.tahrir)
async def filial_nomi_tahrir(message: Message, state: FSMContext):
    bazasi = bazani_olish()
    malumot = await state.get_data()
    eski_nomi = malumot.get("joriy_filial")
    yangi_nomi = message.text.strip()
    
    if bazasi.filialni_yangilash(eski_nomi, yangi_nomi):
        await state.clear()
        await message.answer(
            f"✅ Filial '{yangi_nomi}' qilib o'zgartirildi",
            reply_markup=filiallar_menyusi()
        )
    else:
        await message.answer(
            "❌ Xato yuz berdi",
            reply_markup=orqaga_tugmasi("filial_tahrir_orqaga")
        )

@router.callback_query(F.data == "filial_ochir")
async def filial_ochir(callback: CallbackQuery, state: FSMContext):
    bazasi = bazani_olish()
    malumot = await state.get_data()
    filial_nomi = malumot.get("joriy_filial")
    
    bazasi.filialni_ochirib_tashlash(filial_nomi)
    await state.clear()
    
    await callback.message.edit_text(
        f"🗑️ Filial '{filial_nomi}' o'chirib tashlandi",
        reply_markup=filiallar_menyusi()
    )

@router.callback_query(F.data == "filial_orqaga")
async def filial_orqaga(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🏢 Filiallarni Boshqarish:\n\n"
        "Filiallardan birini tanlang yoki yangi filial qoshing:",
        reply_markup=filiallar_menyusi()
    )

# ==================== MAHSULOTLAR ====================
@router.callback_query(F.data == "admin_mahsulot")
async def admin_mahsulot(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Sizda huquq yo'q", show_alert=True)
        return
    
    await state.clear()
    await callback.message.edit_text(
        "📦 Mahsulotlarni Boshqarish:\n\n"
        "Mahsulot turini tanlang:",
        reply_markup=mahsulot_turi_menyusi()
    )

@router.callback_query(F.data == "mahsulot_umumiy")
async def mahsulot_umumiy(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.update_data(mahsulot_filiali=None)
    await callback.message.edit_text(
        "📦 Umumiy Mahsulotlar:\n\n"
        "Mahsulotlardan birini tanlang yoki yangi mahsulot qoshing:",
        reply_markup=mahsulotlar_menyusi(None)
    )

@router.callback_query(F.data == "mahsulot_filial")
async def mahsulot_filial(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🏢 Filiallardan birini tanlang:",
        reply_markup=mahsulotlar_uchun_filiallar_menyusi()
    )

@router.callback_query(F.data.startswith("mahsulot_filial_tanlash:"))
async def mahsulot_filial_tanlash(callback: CallbackQuery, state: FSMContext):
    filial_nomi = callback.data.split(":")[1]
    await state.update_data(mahsulot_filiali=filial_nomi)
    
    await callback.message.edit_text(
        f"📦 Filial: <b>{filial_nomi}</b>\n\n"
        "Mahsulotlardan birini tanlang yoki yangi mahsulot qoshing:",
        reply_markup=mahsulotlar_menyusi(filial_nomi),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("mahsulot_qosh:"))
async def mahsulot_qosh(callback: CallbackQuery, state: FSMContext):
    filial = callback.data.split(":")[1]
    if filial == "umumiy":
        filial = None
    
    await state.set_state(MahsulotHolatlari.nomini_qosh)
    await state.update_data(mahsulot_filiali=filial)
    
    await callback.message.edit_text(
        "✍️ Mahsulot nomini kiriting:",
        reply_markup=orqaga_tugmasi("mahsulot_orqaga")
    )

@router.message(MahsulotHolatlari.nomini_qosh)
async def mahsulot_nomi_qosh(message: Message, state: FSMContext):
    await state.update_data(mahsulot_nomi=message.text.strip())
    await state.set_state(MahsulotHolatlari.rasmini_qosh)
    