from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ServerSelectionTimeoutError
from konfiguratsiya.sozlamalar import MONGO_URI, BazaImi, KOLLEKSIYALAR
import logging

logger = logging.getLogger(__name__)

class MongoDBBoshqaruvchi:
    def __init__(self):
        try:
            self.client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            self.client.admin.command('ping')
            self.db = self.client[BazaImi]
            self._kolleksiyalar_yasash()
            logger.info("✅ MongoDB muvaffaqiyatli ulangli")
        except Exception as e:
            logger.error(f"❌ MongoDB ulanish xatosi: {e}")
            raise

    def _kolleksiyalar_yasash(self):
        """Birinchi ishga tushishda kolleksiyalarni yaratish"""
        try:
            # Foydalanuvchilar kolleksiyasi
            if KOLLEKSIYALAR["foydalanuvchilar"] not in self.db.list_collection_names():
                self.db.create_collection(KOLLEKSIYALAR["foydalanuvchilar"])
                self.db[KOLLEKSIYALAR["foydalanuvchilar"]].create_index("foydalanuvchi_id", unique=True)
            
            # Filiallar kolleksiyasi
            if KOLLEKSIYALAR["filiallar"] not in self.db.list_collection_names():
                self.db.create_collection(KOLLEKSIYALAR["filiallar"])
                self.db[KOLLEKSIYALAR["filiallar"]].create_index("nomi", unique=True)
            
            # Mahsulotlar kolleksiyasi
            if KOLLEKSIYALAR["mahsulotlar"] not in self.db.list_collection_names():
                self.db.create_collection(KOLLEKSIYALAR["mahsulotlar"])
                self.db[KOLLEKSIYALAR["mahsulotlar"]].create_index("nomi", unique=True)
            
            # Inventar kolleksiyasi
            if KOLLEKSIYALAR["inventar"] not in self.db.list_collection_names():
                self.db.create_collection(KOLLEKSIYALAR["inventar"])
            
            # So'rovlar kolleksiyasi
            if KOLLEKSIYALAR["so_rovlar"] not in self.db.list_collection_names():
                self.db.create_collection(KOLLEKSIYALAR["so_rovlar"])
            
            logger.info("✅ Kolleksiyalar tayyor")
        except Exception as e:
            logger.error(f"❌ Kolleksiyalarni yaratishda xato: {e}")

    # ==================== FOYDALANUVCHILAR ====================
    def foydalanuvchi_qosh(self, foydalanuvchi_id, username, ismi, tasdiqlangan=False):
        try:
            self.db[KOLLEKSIYALAR["foydalanuvchilar"]].insert_one({
                "foydalanuvchi_id": foydalanuvchi_id,
                "username": username,
                "ismi": ismi,
                "tasdiqlangan": tasdiqlangan,
                "vaqti": self._vaqt_olish()
            })
            return True
        except DuplicateKeyError:
            return False

    def foydalanuvchini_olish(self, foydalanuvchi_id):
        return self.db[KOLLEKSIYALAR["foydalanuvchilar"]].find_one({"foydalanuvchi_id": foydalanuvchi_id})

    def foydalanuvchini_tasdiqlash(self, foydalanuvchi_id):
        self.db[KOLLEKSIYALAR["foydalanuvchilar"]].update_one(
            {"foydalanuvchi_id": foydalanuvchi_id},
            {"$set": {"tasdiqlangan": True}}
        )

    def foydalanuvchini_rad_qilish(self, foydalanuvchi_id):
        self.db[KOLLEKSIYALAR["foydalanuvchilar"]].delete_one({"foydalanuvchi_id": foydalanuvchi_id})

    def foydalanuvchi_tasdiqlangami(self, foydalanuvchi_id):
        foydalanuvchi = self.foydalanuvchini_olish(foydalanuvchi_id)
        return foydalanuvchi and foydalanuvchi.get("tasdiqlangan", False)

    # ==================== FILIALLAR ====================
    def filial_qosh(self, nomi):
        try:
            self.db[KOLLEKSIYALAR["filiallar"]].insert_one({
                "nomi": nomi,
                "vaqti": self._vaqt_olish()
            })
            return True
        except DuplicateKeyError:
            return False

    def barcha_filiallarni_olish(self):
        return list(self.db[KOLLEKSIYALAR["filiallar"]].find())

    def filialni_olish(self, nomi):
        return self.db[KOLLEKSIYALAR["filiallar"]].find_one({"nomi": nomi})

    def filialni_yangilash(self, eski_nomi, yangi_nomi):
        try:
            natija = self.db[KOLLEKSIYALAR["filiallar"]].update_one(
                {"nomi": eski_nomi},
                {"$set": {"nomi": yangi_nomi}}
            )
            return natija.modified_count > 0
        except DuplicateKeyError:
            return False

    def filialni_ochirib_tashlash(self, nomi):
        self.db[KOLLEKSIYALAR["filiallar"]].delete_one({"nomi": nomi})

    # ==================== MAHSULOTLAR ====================
    def mahsulot_qosh(self, nomi, filial=None, rasm_id=None):
        try:
            self.db[KOLLEKSIYALAR["mahsulotlar"]].insert_one({
                "nomi": nomi,
                "filial": filial,  # None = UMUMIY mahsulot
                "rasm_id": rasm_id,
                "vaqti": self._vaqt_olish()
            })
            return True
        except DuplicateKeyError:
            return False

    def mahsulotlarni_filial_bo_yicha_olish(self, filial=None):
        so_rov = {"filial": filial}
        return list(self.db[KOLLEKSIYALAR["mahsulotlar"]].find(so_rov))

    def mahsulotni_olish(self, nomi):
        return self.db[KOLLEKSIYALAR["mahsulotlar"]].find_one({"nomi": nomi})

    def mahsulotni_yangilash(self, nomi, yangi_nomi=None, yangi_rasm_id=None):
        yangilash_malumoti = {}
        if yangi_nomi:
            yangilash_malumoti["nomi"] = yangi_nomi
        if yangi_rasm_id:
            yangilash_malumoti["rasm_id"] = yangi_rasm_id
        
        self.db[KOLLEKSIYALAR["mahsulotlar"]].update_one(
            {"nomi": nomi},
            {"$set": yangilash_malumoti}
        )

    def mahsulotni_ochirib_tashlash(self, nomi):
        self.db[KOLLEKSIYALAR["mahsulotlar"]].delete_one({"nomi": nomi})

    # ==================== INVENTAR ====================
    def inventarni_olish(self, mahsulot_nomi, filial=None):
        so_rov = {"mahsulot_nomi": mahsulot_nomi, "filial": filial}
        natija = self.db[KOLLEKSIYALAR["inventar"]].find_one(so_rov)
        return natija if natija else {"miqdori": 0}

    def inventarga_qosh(self, mahsulot_nomi, filial, miqdori):
        joriy = self.inventarni_olish(mahsulot_nomi, filial)
        yangi_miqdor = joriy.get("miqdori", 0) + miqdori
        
        self.db[KOLLEKSIYALAR["inventar"]].update_one(
            {"mahsulot_nomi": mahsulot_nomi, "filial": filial},
            {"$set": {
                "mahsulot_nomi": mahsulot_nomi,
                "filial": filial,
                "miqdori": yangi_miqdor,
                "yangilanish_vaqti": self._vaqt_olish()
            }},
            upsert=True
        )
        return yangi_miqdor

    def inventardan_ayirish(self, mahsulot_nomi, filial, miqdori):
        joriy = self.inventarni_olish(mahsulot_nomi, filial)
        yangi_miqdor = max(0, joriy.get("miqdori", 0) - miqdori)
        
        self.db[KOLLEKSIYALAR["inventar"]].update_one(
            {"mahsulot_nomi": mahsulot_nomi, "filial": filial},
            {"$set": {
                "mahsulot_nomi": mahsulot_nomi,
                "filial": filial,
                "miqdori": yangi_miqdor,
                "yangilanish_vaqti": self._vaqt_olish()
            }},
            upsert=True
        )
        return yangi_miqdor

    # ==================== SO'ROVLAR ====================
    def so_rov_qosh(self, foydalanuvchi_id, username):
        self.db[KOLLEKSIYALAR["so_rovlar"]].insert_one({
            "foydalanuvchi_id": foydalanuvchi_id,
            "username": username,
            "holati": "kutilmoqda",
            "vaqti": self._vaqt_olish()
        })

    def kutilayotgan_so_rovlarni_olish(self):
        return list(self.db[KOLLEKSIYALAR["so_rovlar"]].find({"holati": "kutilmoqda"}))

    def so_rovni_yakunlash(self, foydalanuvchi_id):
        self.db[KOLLEKSIYALAR["so_rovlar"]].update_one(
            {"foydalanuvchi_id": foydalanuvchi_id},
            {"$set": {"holati": "yakunlangan"}}
        )

    @staticmethod
    def _vaqt_olish():
        from datetime import datetime
        return datetime.utcnow()

# Global nusxasi
db_boshqaruvchi = None

def bazasini_boshlash():
    global db_boshqaruvchi
    db_boshqaruvchi = MongoDBBoshqaruvchi()
    return db_boshqaruvchi

def bazani_olish():
    return db_boshqaruvchi