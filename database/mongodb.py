from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from config.settings import MONGO_URI, DB_NAME
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MongoDBManager:
    """MongoDB bilan ishlash uchun asosiy klass"""
    
    def __init__(self):
        """MongoDB ulanishini boshlang"""
        try:
            self.client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            self.client.admin.command('ping')
            self.db = self.client[DB_NAME]
            self._create_collections()
            logger.info("✅ MongoDB ulanishi muvaffaqiyatli")
        except Exception as e:
            logger.error(f"❌ MongoDB ulanish xatosi: {e}")
            raise

    def _create_collections(self):
        """Birinchi ishga tushirilganda to'plamlarni yarating"""
        try:
            if "users" not in self.db.list_collection_names():
                self.db.create_collection("users")
                self.db["users"].create_index("user_id", unique=True)
            
            if "branches" not in self.db.list_collection_names():
                self.db.create_collection("branches")
                self.db["branches"].create_index("name", unique=True)
            
            # ✅ PRODUCT_TYPES COLLECTION YARATISH
            if "product_types" not in self.db.list_collection_names():
                self.db.create_collection("product_types")
                self.db["product_types"].create_index("name", unique=True)
                logger.info("✅ product_types collection yaratildi")
            
            if "products" not in self.db.list_collection_names():
                self.db.create_collection("products")
                self.db["products"].create_index("name", unique=True)
            
            if "inventory" not in self.db.list_collection_names():
                self.db.create_collection("inventory")
                self.db["inventory"].create_index([("product_name", 1), ("branch", 1)], unique=True)
            
            if "requests" not in self.db.list_collection_names():
                self.db.create_collection("requests")
                self.db["requests"].create_index("user_id", unique=True)
            
            logger.info("✅ Barcha to'plamlar tayyor")
        except Exception as e:
            logger.error(f"❌ To'plamlarni yaratishda xato: {e}")

    # ==================== USERS ====================
    
    def add_user(self, user_id, username, first_name, approved=False):
        try:
            self.db["users"].insert_one({
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "approved": approved,
                "created_at": datetime.utcnow()
            })
            return True
        except DuplicateKeyError:
            return False

    def get_user(self, user_id):
        return self.db["users"].find_one({"user_id": user_id})

    def approve_user(self, user_id):
        self.db["users"].update_one(
            {"user_id": user_id},
            {"$set": {"approved": True}}
        )

    def reject_user(self, user_id):
        self.db["users"].delete_one({"user_id": user_id})

    # ==================== BRANCHES ====================
    
    def add_branch(self, name):
        try:
            self.db["branches"].insert_one({
                "name": name,
                "created_at": datetime.utcnow()
            })
            logger.info(f"✅ Branch qo'shildi: {name}")
            return True
        except DuplicateKeyError:
            logger.warning(f"❌ Branch mavjud: {name}")
            return False

    def get_all_branches(self):
        return list(self.db["branches"].find({}))

    def get_branch_by_name(self, name):
        return self.db["branches"].find_one({"name": name})

    def update_branch(self, old_name, new_name):
        try:
            result = self.db["branches"].update_one(
                {"name": old_name},
                {"$set": {"name": new_name}}
            )
            return result.modified_count > 0
        except DuplicateKeyError:
            return False

    def delete_branch(self, name):
        self.db["branches"].delete_one({"name": name})

    # ==================== PRODUCT TYPES (YANGI!) ====================
    # ✅ BU KRITIK - OLDINROQ BU JOYDA!

    def add_product_type(self, name):
        """Mahsulot turi qo'shish"""
        try:
            result = self.db["product_types"].insert_one({
                "name": name,
                "created_at": datetime.utcnow()
            })
            logger.info(f"✅ Product type qo'shildi: {name}, ID: {result.inserted_id}")
            return True
        except DuplicateKeyError:
            logger.warning(f"❌ Product type mavjud: {name}")
            return False
        except Exception as e:
            logger.error(f"❌ Product type qo'shishda xato: {e}")
            return False

    def get_all_product_types(self):
        """Barcha mahsulot turlarini olish"""
        try:
            types = list(self.db["product_types"].find({}))
            logger.info(f"✅ Product types olindi: {len(types)} ta")
            return types
        except Exception as e:
            logger.error(f"❌ Product types olishda xato: {e}")
            return []

    def get_product_type_by_name(self, name):
        """Mahsulot turini nomga ko'ra olish"""
        return self.db["product_types"].find_one({"name": name})

    def update_product_type(self, old_name, new_name):
        """Mahsulot turini tahrirlash"""
        try:
            result = self.db["product_types"].update_one(
                {"name": old_name},
                {"$set": {"name": new_name}}
            )
            logger.info(f"✅ Product type tahrirlandi: {old_name} -> {new_name}")
            return result.modified_count > 0
        except DuplicateKeyError:
            logger.warning(f"❌ Product type already exists: {new_name}")
            return False
        except Exception as e:
            logger.error(f"❌ Product type tahrirlashda xato: {e}")
            return False

    def delete_product_type(self, name):
        """Mahsulot turini o'chirish"""
        try:
            result = self.db["product_types"].delete_one({"name": name})
            logger.info(f"✅ Product type o'chirildi: {name}")
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"❌ Product type o'chirishda xato: {e}")
            return False

    # ==================== PRODUCTS ====================
    
    def add_product(self, name, product_type, image_id=None):
        """Mahsulot qo'shish"""
        try:
            result = self.db["products"].insert_one({
                "name": name,
                "product_type": product_type,  # ✅ PRODUCT TYPE REFERENCE
                "image_id": image_id,
                "created_at": datetime.utcnow()
            })
            logger.info(f"✅ Product qo'shildi: {name} (type: {product_type})")
            return True
        except DuplicateKeyError:
            logger.warning(f"❌ Product mavjud: {name}")
            return False
        except Exception as e:
            logger.error(f"❌ Product qo'shishda xato: {e}")
            return False

    def get_products_by_type(self, product_type):
        """Mahsulot turiga ko'ra mahsulotlar olish"""
        try:
            products = list(self.db["products"].find({"product_type": product_type}).sort("name", 1))
            logger.info(f"✅ Products olindi (type: {product_type}): {len(products)} ta")
            return products
        except Exception as e:
            logger.error(f"❌ Products olishda xato: {e}")
            return []

    def get_all_products(self):
        """Barcha mahsulotlarni olish"""
        try:
            products = list(self.db["products"].find({}).sort("name", 1))
            return products
        except Exception as e:
            logger.error(f"❌ All products olishda xato: {e}")
            return []

    def get_product_by_name(self, name):
        """Mahsulotni nomga ko'ra olish"""
        return self.db["products"].find_one({"name": name})

    def update_product(self, name, new_name=None, product_type=None):
        """Mahsulotni tahrirlash"""
        try:
            update_data = {}
            if new_name:
                update_data["name"] = new_name
            if product_type:
                update_data["product_type"] = product_type
            
            if update_data:
                result = self.db["products"].update_one(
                    {"name": name},
                    {"$set": update_data}
                )
                logger.info(f"✅ Product tahrirlandi: {name}")
                return result.modified_count > 0
            return False
        except Exception as e:
            logger.error(f"❌ Product tahrirlashda xato: {e}")
            return False

    def delete_product(self, name):
        """Mahsulotni o'chirish"""
        try:
            result = self.db["products"].delete_one({"name": name})
            logger.info(f"✅ Product o'chirildi: {name}")
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"❌ Product o'chirishda xato: {e}")
            return False

    # ==================== INVENTORY ====================
    
    def get_inventory(self, product_name, branch=None):
        """Inventarni olish"""
        query = {"product_name": product_name, "branch": branch}
        result = self.db["inventory"].find_one(query)
        return result if result else {"quantity": 0}

    def get_inventory_by_branch(self, branch):
        """Filial bo'yicha inventarni olish"""
        try:
            inventory = list(self.db["inventory"].find({"branch": branch}))
            return inventory
        except Exception as e:
            logger.error(f"❌ Inventory olishda xato: {e}")
            return []

    def add_inventory(self, product_name, branch, quantity):
        """Inventarga qo'shish"""
        try:
            current = self.get_inventory(product_name, branch)
            new_quantity = current.get("quantity", 0) + quantity
            
            result = self.db["inventory"].update_one(
                {"product_name": product_name, "branch": branch},
                {"$set": {
                    "product_name": product_name,
                    "branch": branch,
                    "quantity": new_quantity,
                    "updated_at": datetime.utcnow()
                }},
                upsert=True
            )
            logger.info(f"✅ Inventory qo'shildi: {product_name} (+{quantity})")
            return new_quantity
        except Exception as e:
            logger.error(f"❌ Inventory qo'shishda xato: {e}")
            return 0

    def remove_inventory(self, product_name, branch, quantity):
        """Inventardan ayirish"""
        try:
            current = self.get_inventory(product_name, branch)
            new_quantity = max(0, current.get("quantity", 0) - quantity)
            
            result = self.db["inventory"].update_one(
                {"product_name": product_name, "branch": branch},
                {"$set": {
                    "product_name": product_name,
                    "branch": branch,
                    "quantity": new_quantity,
                    "updated_at": datetime.utcnow()
                }},
                upsert=True
            )
            logger.info(f"✅ Inventory ayirildi: {product_name} (-{quantity})")
            return new_quantity
        except Exception as e:
            logger.error(f"❌ Inventory ayirishda xato: {e}")
            return 0

    # ==================== REQUESTS ====================
    
    def add_request(self, user_id, username):
        """So'rov qo'shish"""
        try:
            self.db["requests"].insert_one({
                "user_id": user_id,
                "username": username,
                "status": "pending",
                "created_at": datetime.utcnow()
            })
            return True
        except DuplicateKeyError:
            return False

    def delete_request(self, user_id):
        """So'rovni o'chirish"""
        self.db["requests"].delete_one({"user_id": user_id})


# Global
db_manager = None

def init_db():
    global db_manager
    db_manager = MongoDBManager()
    return db_manager

def get_db():
    return db_manager