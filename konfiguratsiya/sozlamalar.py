import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Sozlamalari
BOT_TOKENI = os.getenv("BOT_TOKENI")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

# MongoDB Sozlamalari
MONGO_URI = os.getenv("MONGO_URI")
BazaImi = "ombor_boti"
KOLLEKSIYALAR = {
    "foydalanuvchilar": "foydalanuvchilar",
    "filiallar": "filiallar",
    "mahsulotlar": "mahsulotlar",
    "inventar": "inventar",
    "so_rovlar": "so_rovlar"
}

# Bot Sozlamalari
BIR_SAHIFADAGI_MAHSULOT = 5