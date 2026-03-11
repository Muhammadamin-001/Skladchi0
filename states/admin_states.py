from aiogram.fsm.state import State, StatesGroup

class AdminBranchStates(StatesGroup):
    """Admin filial boshqarish holatlari"""
    main_menu = State()
    viewing_branches = State()
    adding_branch = State()
    branch_added = State()
    editing_branch = State()
    branch_edited = State()
    deleting_branch = State()

class AdminProductStates(StatesGroup):
    """Admin mahsulot boshqarish holatlari"""
    main_menu = State()
    choosing_type = State()
    choosing_branch = State()
    viewing_products = State()
    adding_product_name = State()
    adding_product_image = State()
    product_added = State()
    editing_product_name = State()
    editing_product_image = State()
    product_edited = State()
    deleting_product = State()

class AdminListStates(StatesGroup):
    """Admin ro'yxat ko'rish holatlari"""
    viewing_list = State()
    choosing_branch = State()
    viewing_inventory = State()