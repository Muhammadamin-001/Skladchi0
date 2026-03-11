from aiogram.fsm.state import State, StatesGroup

class FoydalanuvchiQoshHolati(StatesGroup):
    harakat_tanlash = State()
    filialni_tanlash = State()
    mahsulotni_tanlash = State()
    miqdorni_kiritish = State()

class FoydalanuvchiAyirishHolati(StatesGroup):
    harakat_tanlash = State()
    filialni_tanlash = State()
    mahsulotni_tanlash = State()
    miqdorni_kiritish = State()

class FoydalanuvchiRo_yxatHolati(StatesGroup):
    ro_yxatni_ko_rish = State()
    filialni_tanlash = State()
    sahifa = State()