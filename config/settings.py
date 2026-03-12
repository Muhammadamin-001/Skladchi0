import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# MongoDB
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "inventory_bot"
WAREHOUSE_NAME = "Umumiy sklad"
# Settings
ITEMS_PER_PAGE = 5

# O'zbek Tilida Matnlar
MESSAGES = {
    "start_admin": "👤 Salom, Administrator!\n\nIshlash uchun tugmani tanlang:",
    "start_user_approved": "👋 Salom, {}!\n\nKo'proq tanlovlar uchun tugma bosing:",
    "start_user_unapproved": "❌ Siz botdan foydalanish uchun admin tasdiqlashi kerak.\n\nTasdiqlash so'rovini yuborasizmi?",
    
    "branch_management": "🏢 Filiallarni Boshqarish:\n\nFilial tanlang yoki yangi qo'shish:",
    "branch_add_prompt": "✍️ Filial nomini kiriting:",
    "branch_added": "✅ Filial '{}' qo'shildi",
    "branch_exists": "❌ Bunday nomli filial allaqachon mavjud",
    "branch_renamed": "✅ Filial '{}' ga o'zgartirildi",
    "branch_deleted": "🗑️ Filial o'chirildi",
    
    "product_management": "📦 Mahsulotlarni Boshqarish:\n\nMahsulot turini tanlang:",
    "product_add_name": "✍️ Mahsulot nomini kiriting:",
    "product_add_image": "🖼️ Rasm zarurmi?",
    "product_send_image": "📷 Mahsulot rasmini yuboring:",
    "product_added": "✅ Mahsulot '{}' qo'shildi",
    "product_deleted": "🗑️ Mahsulot o'chirildi",
    
    "user_add_product": "📥 Mahsulot Kiritamiz\n\nMahsulotlar avtomatik ravishda Umumiy skladga qo'shiladi.",
    "user_remove_product": "📤 Mahsulot Chiqaramiz\n\nQaysi filialga yuborilishini tanlang:",
    "user_enter_quantity": "💬 Miqdorni kiriting:",
    "user_product_added": "✅ Mahsulot qo'shildi!\n\n📦 {}\n➕ +{} dona\n📊 Jami: {} dona",
    "user_product_removed": "✅ Mahsulot chiqarildi!\n\n📦 {}\n🏢 Filial: {}\n➖ -{} dona\n📊 Skladda qoldi: {} dona",
    
    "list_title": "📋 Mahsulotlar Ro'yxati",
    "list_empty": "📋 Mahsulotlar yo'q",
    
    "request_sent": "✅ So'rov yuborildi!\n\nAdmin tez orada javob beradi...",
    "user_approved": "✅ Siz tasdiqlandingiz!\n\n/start bosib davom eting",
    "user_rejected": "❌ Sizning so'rovingiz rad qilindi.",
    
    "button_branch": "🏢 Filial",
    "button_product": "📦 Mahsulot",
    "button_list": "📋 Ro'yxat",
    "button_add": "➕ Qo'shish",
    "button_edit": "✏️ Tahrirlash",
    "button_delete": "🗑️ O'chirish",
    "button_back": "⬅️ Ortga",
    "button_yes": "✅ Ha",
    "button_no": "❌ Yo'q",
    "button_add_product": "📥 Mahsulot Kiritish",
    "button_remove_product": "📤 Mahsulot Chiqarish",
    "button_send_request": "📧 So'rov Yuborish",
    
    "error_invalid_quantity": "❌ Iltimos, raqam kiriting",
    "error_access_denied": "❌ Sizda ruxsat yo'q",
}