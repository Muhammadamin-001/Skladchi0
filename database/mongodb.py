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
            
            if "product_types" not in self.db.list_collection_names():
                self.db.create_collection("product_types")
                self.db["product_types"].create_index("name", unique=True)
            
            if "products" not in self.db.list_collection_names():
                self.db.create_collection("products")
                self.db["products"].create_index([("name", 1), ("type", 1)], unique=True)
            
            if "branches" not in self.db.list_collection_names():
                self.db.create_collection("branches")
                self.db["branches"].create_index("name", unique=True)
            
            if "inventory" not in self.db.list_collection_names():
                self.db.create_collection("inventory")
                self.db["inventory"].create_index([("product_id", 1), ("branch", 1)], unique=True)
            
            if "requests" not in self.db.list_collection_names():
                self.db.create_collection("requests")
                self.db["requests"].create_index("user_id", unique=True)
            
            logger.info("✅ To'plamlar tayyor")
        except Exception as e:
            logger.error(f"❌ To'plamlarni yaratishda xato: {e}")

    # ==================== FOYDALANUVCHILAR ====================
    
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

    # ==================== MAHSULOT TURLARI (BREND) ====================
    
    def add_product_type(self, name):
        """Yangi mahsulot turi (brend) qo'shish"""
        try:
            self.db["product_types"].insert_one({
                "name": name,
                "created_at": datetime.utcnow()
            })
            return True
        except DuplicateKeyError:
            return False

    def get_all_product_types(self):
        """Barcha mahsulot turlarini olish"""
        return list(self.db["product_types"].find({}).sort("name", 1))

    def get_product_type_by_name(self, name):
        """Mahsulot turini nomiga ko'ra olish"""
        return self.db["product_types"].find_one({"name": name})

    def update_product_type(self, old_name, new_name):
        """Mahsulot turi nomini o'zgartirish"""
        try:
            result = self.db["product_types"].update_one(
                {"name": old_name},
                {"$set": {"name": new_name}}
            )
            return result.modified_count > 0
        except DuplicateKeyError:
            return False

    def delete_product_type(self, name):
        """Mahsulot turini o'chirish"""
        self.db["product_types"].delete_one({"name": name})
        # Tegishli mahsulotlarni ham o'chirish
        self.db["products"].delete_many({"type": name})

    # ==================== MAHSULOTLAR ====================
    
    def add_product(self, name, product_type, image_id=None):
        """Yangi mahsulot qo'shish
        
        Args:
            name: Mahsulot nomi
            product_type: Mahsulot turi (brend)
            image_id: Telegram rasm ID
        """
        try:
            self.db["products"].insert_one({
                "name": name,
                "type": product_type,
                "image_id": image_id,
                "created_at": datetime.utcnow()
            })
            return True
        except DuplicateKeyError:
            return False

    def get_products_by_type(self, product_type):
        """Mahsulot turiga ko'ra mahsulotlarni olish"""
        query = {"type": product_type}
        return list(self.db["products"].find(query).sort("name", 1))

    def get_product_by_name(self, name):
        """Mahsulot nomiga ko'ra olish"""
        return self.db["products"].find_one({"name": name})

    def get_product_by_name_and_type(self, name, product_type):
        """Mahsulot nomiga va turiga ko'ra olish"""
        return self.db["products"].find_one({"name": name, "type": product_type})

    def update_product(self, old_name, new_name=None, product_type=None):
        """Mahsulotni tahrirlash"""
        update_data = {}
        if new_name:
            update_data["name"] = new_name
        if product_type:
            update_data["type"] = product_type
        
        if update_data:
            self.db["products"].update_one(
                {"name": old_name},
                {"$set": update_data}
            )

    def delete_product(self, name):
        """Mahsulot o'chirish"""
        self.db["products"].delete_one({"name": name})
        # Tegishli inventarni ham o'chirish
        self.db["inventory"].delete_many({"product_name": name})

    # ==================== FILIALLAR ====================
    
    def add_branch(self, name):
        """Yangi filial qo'shish"""
        try:
            self.db["branches"].insert_one({
                "name": name,
                "created_at": datetime.utcnow()
            })
            return True
        except DuplicateKeyError:
            return False

    def get_all_branches(self):
        """Barcha filiallarni olish"""
        return list(self.db["branches"].find({}).sort("name", 1))

    def get_branch_by_name(self, name):
        """Filialni nomiga ko'ra olish"""
        return self.db["branches"].find_one({"name": name})

    def update_branch(self, old_name, new_name):
        """Filial nomini o'zgartirish"""
        try:
            result = self.db["branches"].update_one(
                {"name": old_name},
                {"$set": {"name": new_name}}
            )
            return result.modified_count > 0
        except DuplicateKeyError:
            return False

    def delete_branch(self, name):
        """Filial o'chirish"""
        self.db["branches"].delete_one({"name": name})

    # ==================== INVENTAR ====================
    
    def get_inventory(self, product_name, branch):
        """Mahsulot inventarini olish (filialga xos)"""
        query = {"product_name": product_name, "branch": branch}
        result = self.db["inventory"].find_one(query)
        return result if result else {"quantity": 0}

    def add_inventory(self, product_name, branch, quantity):
        """Inventarga mahsulot qo'shish"""
        current = self.get_inventory(product_name, branch)
        new_quantity = current.get("quantity", 0) + quantity
        
        self.db["inventory"].update_one(
            {"product_name": product_name, "branch": branch},
            {"$set": {
                "product_name": product_name,
                "branch": branch,
                "quantity": new_quantity,
                "updated_at": datetime.utcnow()
            }},
            upsert=True
        )
        
        # Tarix qidiruviga qo'shish (filial qaysi mahsulotdan qancha olgani)
        self.db["inventory"].update_one(
            {"product_name": product_name, "branch": branch},
            {
                "$push": {
                    "history": {
                        "action": "add",
                        "quantity": quantity,
                        "timestamp": datetime.utcnow()
                    }
                }
            }
        )
        
        return new_quantity

    def remove_inventory(self, product_name, branch, quantity):
        """Inventardan mahsulot chiqarish"""
        current = self.get_inventory(product_name, branch)
        new_quantity = max(0, current.get("quantity", 0) - quantity)
        
        self.db["inventory"].update_one(
            {"product_name": product_name, "branch": branch},
            {"$set": {
                "product_name": product_name,
                "branch": branch,
                "quantity": new_quantity,
                "updated_at": datetime.utcnow()
            }},
            upsert=True
        )
        
        # Tarix qidiruviga qo'shish (filial qaysi mahsulotdan qancha chiqargan)
        self.db["inventory"].update_one(
            {"product_name": product_name, "branch": branch},
            {
                "$push": {
                    "history": {
                        "action": "remove",
                        "quantity": quantity,
                        "timestamp": datetime.utcnow()
                    }
                }
            }
        )
        
        return new_quantity

    def get_inventory_by_branch(self, branch):
        """Filialning to'liq inventarini olish"""
        return list(self.db["inventory"].find({"branch": branch}))

    def get_inventory_by_product(self, product_name):
        """Mahsulotning barcha filiallardagi inventarini olish"""
        return list(self.db["inventory"].find({"product_name": product_name}))

    # ==================== SO'ROVLAR ====================
    
    def add_request(self, user_id, username):
        """Yangi so'rov qo'shish"""
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