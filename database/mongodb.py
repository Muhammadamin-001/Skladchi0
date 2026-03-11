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
            
            if "products" not in self.db.list_collection_names():
                self.db.create_collection("products")
                self.db["products"].create_index("name", unique=True)
            
            if "inventory" not in self.db.list_collection_names():
                self.db.create_collection("inventory")
                self.db["inventory"].create_index([("product_name", 1), ("branch", 1)], unique=True)
            
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

    def is_user_approved(self, user_id):
        user = self.get_user(user_id)
        return user and user.get("approved", False)

    # ==================== FILIALLAR ====================
    
    def add_branch(self, name):
        try:
            self.db["branches"].insert_one({
                "name": name,
                "created_at": datetime.utcnow()
            })
            return True
        except DuplicateKeyError:
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

    # ==================== MAHSULOTLAR ====================
    
    def add_product(self, name, branch=None, image_id=None):
        try:
            self.db["products"].insert_one({
                "name": name,
                "branch": branch,
                "image_id": image_id,
                "created_at": datetime.utcnow()
            })
            return True
        except DuplicateKeyError:
            return False

    def get_products_by_branch(self, branch=None):
        query = {"branch": branch}
        return list(self.db["products"].find(query).sort("name", 1))

    def get_product_by_name(self, name):
        return self.db["products"].find_one({"name": name})

    def update_product(self, name, new_name=None, new_image_id=None):
        update_data = {}
        if new_name:
            update_data["name"] = new_name
        if new_image_id:
            update_data["image_id"] = new_image_id
        
        self.db["products"].update_one(
            {"name": name},
            {"$set": update_data}
        )

    def delete_product(self, name):
        self.db["products"].delete_one({"name": name})

    # ==================== INVENTAR ====================
    
    def get_inventory(self, product_name, branch=None):
        query = {"product_name": product_name, "branch": branch}
        result = self.db["inventory"].find_one(query)
        return result if result else {"quantity": 0}

    def add_inventory(self, product_name, branch, quantity):
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
        return new_quantity

    def remove_inventory(self, product_name, branch, quantity):
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
        return new_quantity

    # ==================== SO'ROVLAR ====================
    
    def add_request(self, user_id, username):
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

    def get_pending_requests(self):
        return list(self.db["requests"].find({"status": "pending"}))

    def complete_request(self, user_id):
        self.db["requests"].update_one(
            {"user_id": user_id},
            {"$set": {"status": "completed"}}
        )

    def delete_request(self, user_id):
        self.db["requests"].delete_one({"user_id": user_id})


# Global
db_manager = None

def init_db():
    global db_manager
    db_manager = MongoDBManager()
    return db_manager

def get_db():
    return db_manager