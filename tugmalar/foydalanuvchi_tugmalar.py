from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bazasidata.mongodb import bazani_olish

def foydalanuvchi_asosiy_menyusi():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📥 Mahsulot qoshish", callback_data="foy_qosh"),
            InlineKeyboardButton(text="📤 Mahsulot ayirish", callback_data="foy_ayir")
        ],
        [InlineKeyboardButton(text="📋 Ro'yxat", callback_data="foy_royxat")]
    ])

def foydalanuvchi_so_rov_menyusi():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📧 So'rov yuborish", callback_data="sorov_yubor")]
    ])

def filiallar_menyusi_foydalanuvchi(harakat="qosh"):
    bazasi = bazani_olish()
    filiallar = bazasi.barcha_filiallarni_olish()
    tugmalar = []
    
    for filial in filiallar:
        tugmalar.append([InlineKeyboardButton(text=filial["nomi"], callback_data=f"foy_{harakat}_filial:{filial['nomi']}")])
    
    tugmalar.append([InlineKeyboardButton(text="🌍 Umumiy", callback_data=f"foy_{harakat}_filial:umumiy")])
    tugmalar.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="foy_asosiy")])
    
    return InlineKeyboardMarkup(inline_keyboard=tugmalar)

def mahsulotlar_menyusi_foydalanuvchi(filial=None, harakat="qosh"):
    bazasi = bazani_olish()
    mahsulotlar = bazasi.mahsulotlarni_filial_bo_yicha_olish(filial)
    tugmalar = []
    
    # 2 mahsulot bitta qatorga
    for i in range(0, len(mahsulotlar), 2):
        qator = []
        for j in range(2):
            if i + j < len(mahsulotlar):
                mahsulot = mahsulotlar[i + j]
                qator.append(InlineKeyboardButton(text=mahsulot["nomi"], callback_data=f"foy_{harakat}_mahsulot:{mahsulot['nomi']}"))
        tugmalar.append(qator)
    
    tugmalar.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"foy_{harakat}_orqaga")])
    
    return InlineKeyboardMarkup(inline_keyboard=tugmalar)

def orqaga_tugmasi(callback="foy_asosiy"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=callback)]
    ])

def royxat_filiallar_menyusi():
    bazasi = bazani_olish()
    filiallar = bazasi.barcha_filiallarni_olish()
    tugmalar = []
    
    for filial in filiallar:
        tugmalar.append([InlineKeyboardButton(text=filial["nomi"], callback_data=f"royxat_filial:{filial['nomi']}")])
    
    tugmalar.append([InlineKeyboardButton(text="🌍 Umumiy", callback_data="royxat_filial:umumiy")])
    tugmalar.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="foy_asosiy")])
    
    return InlineKeyboardMarkup(inline_keyboard=tugmalar)

def sahifalash_menyusi(sahifa, jami_sahifalar, filial, callback_prefiksi="royxat_sahifa"):
    tugmalar = []
    
    if sahifa > 0:
        tugmalar.append([InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"{callback_prefiksi}:{sahifa-1}:{filial}")])
    
    if sahifa < jami_sahifalar - 1:
        tugmalar.append([InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"{callback_prefiksi}:{sahifa+1}:{filial}")])
    
    tugmalar.append([InlineKeyboardButton(text="🏠 Asosiy", callback_data="foy_asosiy")])
    
    return InlineKeyboardMarkup(inline_keyboard=tugmalar)