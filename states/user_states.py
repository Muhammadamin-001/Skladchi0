from aiogram.fsm.state import State, StatesGroup

class UserInputStates(StatesGroup):
    """Mahsulot kiritish holatlari"""
    choosing_branch = State()
    choosing_product = State()
    entering_quantity = State()

class UserRemoveStates(StatesGroup):
    """Mahsulot chiqarish holatlari"""
    choosing_branch = State()
    choosing_product = State()
    entering_quantity = State()

class UserListStates(StatesGroup):
    """Ro'yxat ko'rish holatlari"""
    choosing_branch = State()
    viewing_page = State()