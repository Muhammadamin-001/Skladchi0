
from datetime import datetime
import logging

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from config.settings import DB_NAME, MONGO_URI, WAREHOUSE_NAME

logger = logging.getLogger(__name__)

class MongoDBManager:
    """MongoDB bilan ishlash uchun asosiy klass"""
    
    def __init__(self):
        try:
            self.client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            self.client.admin.command("ping")
            self.db = self.client[DB_NAME]
            self._create_collections()
            logger.info("✅ MongoDB ulanishi muvaffaqiyatli")
        except Exception as e:
            logger.error(f"❌ MongoDB ulanish xatosi: {e}")
            raise

    def _create_collections(self):
        """Kerakli kolleksiyalar va indekslarni tayyorlash."""
        collections = ["users", "warehouses", "branches", "product_types", "products", "inventory", "requests"]
        for name in collections:
            if name not in self.db.list_collection_names():
                self.db.create_collection(name)

        # Users / requests
        self.db["users"].create_index("user_id", unique=True)
        self.db["requests"].create_index("user_id", unique=True)

        # Warehouse/branch/type/product unique constraints per kontekst
        # Legacy tizimlarda branches uchun faqat `name` unique index qolib ketgan bo'lishi mumkin.
        # Bu holatda turli skladlarda bir xil filial nomi qo'shib bo'lmaydi, shuning uchun tozalaymiz.
        branch_indexes = self.db["branches"].index_information()
        for index_name, index_data in branch_indexes.items():
            if index_name == "_id_":
                continue
            if index_data.get("unique") and index_data.get("key") == [("name", 1)]:
                self.db["branches"].drop_index(index_name)

        self.db["warehouses"].create_index([("name", 1)], unique=True)
        self.db["branches"].create_index([("name", 1), ("warehouse", 1)], unique=True)
        self.db["product_types"].create_index([("name", 1), ("warehouse", 1), ("branch", 1)], unique=True)
        self.db["products"].create_index([("name", 1), ("warehouse", 1), ("branch", 1), ("product_type", 1)], unique=True)
        inventory_indexes = self.db["inventory"].index_information()
        for index_name, index_data in inventory_indexes.items():
            if index_name == "_id_":
                continue
            if index_data.get("unique") and index_data.get("key") == [("product_name", 1), ("branch", 1)]:
                self.db["inventory"].drop_index(index_name)

        self.db["inventory"].create_index(
            [("product_name", 1), ("warehouse", 1), ("branch", 1), ("product_type", 1)],
            unique=True,
        )


    # ==================== USERS ====================
    
    def add_user(self, user_id, username, first_name, approved=False):
        try:
            self.db["users"].insert_one(
                {
                    "user_id": user_id,
                    "username": username,
                    "first_name": first_name,
                    "approved": approved,
                    "created_at": datetime.utcnow(),
                }
            )
            return True
        except DuplicateKeyError:
            return False

    def get_user(self, user_id):
        return self.db["users"].find_one({"user_id": user_id})

    def approve_user(self, user_id):
        self.db["users"].update_one({"user_id": user_id}, {"$set": {"approved": True}})

    def reject_user(self, user_id):
        self.db["users"].delete_one({"user_id": user_id})

    # ==================== BRANCHES ====================
    
    # WAREHOUSES
    def add_warehouse(self, name):
        try:
            self.db["warehouses"].insert_one({"name": name, "created_at": datetime.utcnow()})
            return True
        except DuplicateKeyError:
            return False

    def get_all_warehouses(self):
        return list(self.db["warehouses"].find({}).sort("name", 1))

    def update_warehouse(self, old_name, new_name):
        try:
            result = self.db["warehouses"].update_one({"name": old_name}, {"$set": {"name": new_name}})
            if result.modified_count:
                # bog'liq hujjatlarni ham yangilash
                self.db["branches"].update_many({"warehouse": old_name}, {"$set": {"warehouse": new_name}})
                self.db["product_types"].update_many({"warehouse": old_name}, {"$set": {"warehouse": new_name}})
                self.db["products"].update_many({"warehouse": old_name}, {"$set": {"warehouse": new_name}})
            return result.modified_count > 0
        except DuplicateKeyError:
            return False

    def delete_warehouse(self, name):
        self.db["warehouses"].delete_one({"name": name})
        self.db["branches"].delete_many({"warehouse": name})
        self.db["product_types"].delete_many({"warehouse": name})
        self.db["products"].delete_many({"warehouse": name})

    # BRANCHES
    def add_branch(self, name, warehouse=None):
        try:
            self.db["branches"].insert_one(
                {"name": name, "warehouse": warehouse, "created_at": datetime.utcnow()}
            )
            return True
        except DuplicateKeyError:
            return False

    def get_all_branches(self, warehouse=None):
        query = {"warehouse": warehouse} if warehouse is not None else {}
        return list(self.db["branches"].find(query).sort("name", 1))

    def get_branch_by_name(self, name):
        return self.db["branches"].find_one({"name": name})

    def update_branch(self, old_name, new_name, warehouse=None):
        try:
            query = {"name": old_name}
            if warehouse is not None:
                query["warehouse"] = warehouse
            result = self.db["branches"].update_one(query, {"$set": {"name": new_name}})
            if result.modified_count and warehouse is not None:
                self.db["product_types"].update_many(
                    {"warehouse": warehouse, "branch": old_name}, {"$set": {"branch": new_name}}
                )
                self.db["products"].update_many(
                    {"warehouse": warehouse, "branch": old_name}, {"$set": {"branch": new_name}}
                )
            return result.modified_count > 0
        except DuplicateKeyError:
            return False

    def delete_branch(self, name, warehouse=None):
        query = {"name": name}
        if warehouse is not None:
            query["warehouse"] = warehouse
        self.db["branches"].delete_one(query)
        if warehouse is not None:
            self.db["product_types"].delete_many({"warehouse": warehouse, "branch": name})
            self.db["products"].delete_many({"warehouse": warehouse, "branch": name})

    # PRODUCT TYPES
    def add_product_type(self, name, image_id=None, warehouse=None, branch=None):
        try:
            self.db["product_types"].insert_one(
                {
                    "name": name,
                    "image_id": image_id,
                    "warehouse": warehouse,
                    "branch": branch,
                    "created_at": datetime.utcnow(),
                }
            )
            return True
        except DuplicateKeyError:
            return False

    def get_all_product_types(self, warehouse=None, branch=None):
        query = {}
        if warehouse is not None:
            query["warehouse"] = warehouse
        if branch is not None:
            query["branch"] = branch
        return list(self.db["product_types"].find(query).sort("name", 1))

    def get_product_type_by_name(self, name, warehouse=None, branch=None):
        query = {"name": name}
        if warehouse is not None:
            query["warehouse"] = warehouse
        if branch is not None:
            query["branch"] = branch
        return self.db["product_types"].find_one(query)

    def update_product_type(self, old_name, new_name, image_id=None, warehouse=None, branch=None):
        try:
            query = {"name": old_name}
            if warehouse is not None:
                query["warehouse"] = warehouse
            if branch is not None:
                query["branch"] = branch

            update_data = {"name": new_name}
            if image_id is not None:
                update_data["image_id"] = image_id

            result = self.db["product_types"].update_one(query, {"$set": update_data})
            if result.modified_count:
                self.db["products"].update_many(
                    {
                        "product_type": old_name,
                        **({"warehouse": warehouse} if warehouse is not None else {}),
                        **({"branch": branch} if branch is not None else {}),
                    },
                    {"$set": {"product_type": new_name}},
                )
            return result.modified_count > 0
        except DuplicateKeyError:
            return False

    def delete_product_type(self, name, warehouse=None, branch=None):
        query = {"name": name}
        if warehouse is not None:
            query["warehouse"] = warehouse
        if branch is not None:
            query["branch"] = branch
        self.db["product_types"].delete_one(query)
        self.db["products"].delete_many(
            {
                "product_type": name,
                **({"warehouse": warehouse} if warehouse is not None else {}),
                **({"branch": branch} if branch is not None else {}),
            }
        )

    # PRODUCTS
    def add_product(self, name, code, product_type, warehouse=None, branch=None, image_id=None):
        try:
            self.db["products"].insert_one(
                {
                    "name": name,
                    "code": code,
                    "product_type": product_type,
                    "warehouse": warehouse,
                    "branch": branch,
                    "image_id": image_id,
                    "created_at": datetime.utcnow(),
                }
            )
            return True
        except DuplicateKeyError:
            return False

    def get_products_by_type(self, warehouse, branch, product_type):
        return list(
            self.db["products"].find(
                {"warehouse": warehouse, "branch": branch, "product_type": product_type}
            ).sort("name", 1)
        )

    def get_products_by_type_all(self, product_type):
        return list(self.db["products"].find({"product_type": product_type}).sort("name", 1))

    def get_product_by_name(self, name, warehouse=None, branch=None, product_type=None):
        query = {"name": name}
        if warehouse is not None:
            query["warehouse"] = warehouse
        if branch is not None:
            query["branch"] = branch
        if product_type is not None:
            query["product_type"] = product_type
        return self.db["products"].find_one(query)

    def update_product(self, old_name, new_name, new_code, warehouse=None, branch=None, product_type=None, image_id=None):
        query = {"name": old_name}
        if warehouse is not None:
            query["warehouse"] = warehouse
        if branch is not None:
            query["branch"] = branch
        if product_type is not None:
            query["product_type"] = product_type
        try:
            update_data = {
               "name": new_name,
               "code": new_code,
           }
            if image_id is not None:
               update_data["image_id"] = image_id
               
            result = self.db["products"].update_one(
                query,
                {
                "$set": update_data
                },
            )
            return result.modified_count > 0
        except DuplicateKeyError:
            return False

    def delete_product(self, name, warehouse=None, branch=None, product_type=None):
        query = {"name": name}
        if warehouse is not None:
            query["warehouse"] = warehouse
        if branch is not None:
            query["branch"] = branch
        if product_type is not None:
            query["product_type"] = product_type
        self.db["products"].delete_one(query)
    # INVENTORY
    
    def _inventory_query(self, product_name, warehouse=None, branch=WAREHOUSE_NAME, product_type=None):
       query = {"product_name": product_name, "branch": branch}
       if warehouse is not None:
           query["warehouse"] = warehouse
       if product_type is not None:
           query["product_type"] = product_type
       return query

    def get_inventory(self, product_name, warehouse=None, branch=WAREHOUSE_NAME, product_type=None):
       result = self.db["inventory"].find_one(
           self._inventory_query(product_name, warehouse, branch, product_type)
       )
       return result if result else {"quantity": 0}

    def get_inventory_by_branch(self, warehouse=None, branch=WAREHOUSE_NAME):
        query = {"branch": branch}
        if warehouse is not None:
            query["warehouse"] = warehouse
        return list(self.db["inventory"].find(query).sort("product_name", 1))

    def get_total_inventory_by_product(self, product_name, warehouse=None, product_type=None):
        return self.get_inventory(product_name, warehouse, WAREHOUSE_NAME, product_type)

    def add_inventory(self, product_name, quantity, warehouse=None, branch=WAREHOUSE_NAME, product_type=None):
        current = self.get_inventory(product_name, warehouse, branch, product_type)
        new_quantity = current.get("quantity", 0) + quantity
        query = self._inventory_query(product_name, warehouse, branch, product_type)
        
        self.db["inventory"].update_one(
            {"product_name": product_name, "branch": WAREHOUSE_NAME},
            query,
            {
                "$set": {
                    **query,
                    "quantity": new_quantity,
                    "updated_at": datetime.utcnow(),
                }
            },
            upsert=True,
        )
        return new_quantity

    def remove_inventory(self, product_name, quantity, warehouse=None, branch=WAREHOUSE_NAME, product_type=None):
        current = self.get_inventory(product_name, warehouse, branch, product_type)
        current_qty = current.get("quantity", 0)
        if quantity > current_qty:
            return None

        new_quantity = current_qty - quantity
        query = self._inventory_query(product_name, warehouse, branch, product_type)
            
        self.db["inventory"].update_one(
            {"product_name": product_name, "branch": WAREHOUSE_NAME},
            query,
            {
                "$set": {
                    **query,
                    "quantity": new_quantity,
                    "updated_at": datetime.utcnow(),
                }
            },
            upsert=True,
        )
        return new_quantity

    # ==================== REQUESTS ====================
    
    def add_request(self, user_id, username):
        """So'rov qo'shish"""
        try:
            self.db["requests"].insert_one(
                {
                    "user_id": user_id,
                    "username": username,
                    "status": "pending",
                    "created_at": datetime.utcnow(),
                }
            )
            return True
        except DuplicateKeyError:
            return False

    def delete_request(self, user_id):
        """So'rovni o'chirish"""
        self.db["requests"].delete_one({"user_id": user_id})


# Global
_db_manager = None

def init_db():
    global _db_manager
    _db_manager = MongoDBManager()
    return _db_manager

def get_db():
    return _db_manager
