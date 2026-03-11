from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bazasidata.mongodb import bazani_olish

# ==================== ASOSIY MENYUSI ====================
def admin_asosiy_menyusi():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏢 Filial", callback_data="admin_filial"),
            InlineKeyboardButton(text="📦 Mahsulot", callback_data="admin_mahsulot"),
            InlineKeyboardButton(text="📋 Ro'yxat", callback_data="admin_royxat")
        ]
    ])

# ==================== FILIALLAR ====================
def filiallar_menyusi():
    bazasi = bazani_olish()
    filiallar = bazasi.barcha_filiallarni_olish()
    tugmalar = []
    
    for filial in filiallar:
        tugmalar.append([InlineKeyboardButton(text=filial["nomi"], callback_data=f"filial_tanlash:{filial['nomi']}")])
    
    tugmalar.append([InlineKeyboardButton(text="➕ Qoshish", callback_data="filial_qosh")])
    tugmalar.append([InlineKeyboardButton(text="❌ Yopish", callback_data="menyuni_yopish")])
    
    return InlineKeyboardMarkup(inline_keyboard=tugmalar)

def filial_harakatlari_menyusi():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Tahrir qilish", callback_data="filial_tahrir"),
            InlineKeyboardButton(text="🗑️ O'chirish", callback_data="filial_ochir")
        ],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="filial_orqaga")]
    ])

def orqaga_tugmasi(callback="filial_orqaga"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=callback)]
    ])

# ==================== MAHSULOTLAR ====================
def mahsulot_turi_menyusi():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Umumiy Mahsulot", callback_data="mahsulot_umumiy"),
            InlineKeyboardButton(text="🏢 Filial uchun Mahsulot", callback_data="mahsulot_filial")
        ],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_orqaga")]
    ])

def mahsulotlar_uchun_filiallar_menyusi():
    bazasi = bazani_olish()
    filiallar = bazasi.barcha_filiallarni_olish()
    tugmalar = []
    
    for filial in filiallar:
        tugmalar.append([InlineKeyboardButton(text=filial["nomi"], callback_data=f"mahsulot_filial_tanlash:{filial['nomi']}")])
    
    tugmalar.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="mahsulot_turi_orqaga")])
    
    return InlineKeyboardMarkup(inline_keyboard=tugmalar)

def mahsulotlar_menyusi(filial=None):
    bazasi = bazani_olish()
    mahsulotlar = bazasi.mahsulotlarni_filial_bo_yicha_olish(filial)
    tugmalar = []
    
    # 2 mahsulot bitta qatorga
    for i in range(0, len(mahsulotlar), 2):
        qator = []
        for j in range(2):
            if i + j < len(mahsulotlar):
                mahsulot = mahsulotlar[i + j]
                qator.append(InlineKeyboardButton(text=mahsulot["nomi"], callback_data=f"mahsulot_tanlash:{mahsulot['nomi']}"))
        tugmalar.append(qator)
    
    tugmalar.append([InlineKeyboardButton(text="➕ Qoshish", callback_data=f"mahsulot_qosh:{filial or 'umumiy'}")])
    tugmalar.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="mahsulot_filial_orqaga")])
    
    return InlineKeyboardMarkup(inline_keyboard=tugmalar)

def mahsulot_harakatlari_menyusi():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Tahrir qilish", callback_data="mahsulot_tahrir"),
            InlineKeyboardButton(text="🗑️ O'chirish", callback_data="mahsulot_ochir")
        ],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="mahsulot_orqaga")]
    ])

def ha_yoq_menyusi(callback_prefiksi="rasm"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha", callback_data=f"{callback_prefiksi}_ha"),
            InlineKeyboardButton(text="❌ Yo'q", callback_data=f"{callback_prefiksi}_yoq")
        ]
    ])