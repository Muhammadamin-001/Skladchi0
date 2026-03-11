from aiogram.fsm.state import State, StatesGroup

class AdminFilialHolati(StatesGroup):
    asosiy_menyusi = State()
    filiallarni_ko_rish = State()
    filial_qosh = State()
    filialni_tahrir_qilish = State()
    filialni_o_chirish = State()

class AdminMahsulotHolati(StatesGroup):
    asosiy_menyusi = State()
    turini_tanlash = State()
    filialni_tanlash = State()
    mahsulotlarni_ko_rish = State()
    mahsulot_qosh = State()
    mahsulot_nomini_qosh = State()
    mahsulotga_rasm_qosh = State()
    mahsulotni_tahrir_qilish = State()
    mahsulotni_o_chirish = State()

class AdminRo_yxatHolati(StatesGroup):
    asosiy_menyusi = State()
    ro_yxatni_ko_rish = State()
    filialni_tanlash = State()