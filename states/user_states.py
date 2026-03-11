from aiogram.fsm.state import State, StatesGroup

class UserInputStates(StatesGroup):
    """Foydalanuvchi mahsulot kiritish holatlari"""
    choosing_branch = State()
    choosing_product = State()
    entering_quantity = State()

class UserRemoveStates(StatesGroup):
    """Foydalanuvchi mahsulot chiqarish holatlari"""
    choosing_branch = State()
    choosing_product = State()
    entering_quantity = State()

class UserListStates(StatesGroup):
    """Foydalanuvchi ro'yxat ko'rish holatlari"""
    choosing_branch = State()
    viewing_page = State()