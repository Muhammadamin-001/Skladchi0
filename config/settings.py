import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Konfiguratsiyasi
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

# MongoDB Konfiguratsiyasi
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "inventory_bot"

# Ro'yxat Sozlamalari
ITEMS_PER_PAGE = 5

# O'zbek Tilida Matnlar
MESSAGES = {
    # Boshlang'ich Xabarlar
    "start_admin": "👤 Salom, Administrator!\n\nIshlash uchun tugmani tanlang:",
    "start_user_approved": "👋 Salom, {}!\n\nKo'proq tanlovlar uchun tugma bosing:",
    "start_user_unapproved": "❌ Siz botdan foydalanish uchun admin tasdiqlashi kerak.\n\nTasdiqlash so'rovini yuborasizmi?",
    
    # Filial Xabarlar
    "branch_management": "🏢 Filiallarni Boshqarish:\n\nFilial tanlang yoki yangi qo'shing:",
    "branch_add_prompt": "✍️ Filial nomini kiriting:",
    "branch_added": "✅ Filial '{}' qo'shildi",
    "branch_exists": "❌ Bunday nomli filial allaqachon mavjud",
    "branch_renamed": "✅ Filial '{}' ga o'zgartirildi",
    "branch_deleted": "🗑️ Filial o'chirildi",
    "branch_action": "🏢 Filial: <b>{}</b>\n\nFaoliyatni tanlang:",
    
    # Mahsulot Xabarlar
    "product_management": "📦 Mahsulotlarni Boshqarish:\n\nMahsulot turini tanlang:",
    "product_type_choice": "📦 Mahsulot turini tanlang:\n\n• <b>📋 Umumiy</b> - Barcha filiallar uchun\n• <b>🏢 Filialga Xos</b> - Bitta filial uchun",
    "product_select_branch": "🏢 Filial tanlang:",
    "product_list": "📦 Mahsulotlar:\n\n<b>{}</b> uchun mahsulot tanlang yoki yangi qo'shing:",
    "product_add_name": "✍️ Mahsulot nomini kiriting:",
    "product_add_image": "🖼️ Rasm zarurmi?",
    "product_send_image": "📷 Mahsulot rasmini yuboring:",
    "product_added": "✅ Mahsulot '{}' qo'shildi",
    "product_action": "📦 Mahsulot: <b>{}</b>\n\nFaoliyatni tanlang:",
    "product_rename": "✍️ Mahsulot uchun yangi nomi kiriting:",
    "product_renamed": "✅ Mahsulot '{}' ga o'zgartirildi",
    "product_deleted": "🗑️ Mahsulot o'chirildi",
    
    # Foydalanuvchi Xabarlar
    "user_add_product": "📥 Mahsulot Kiritamiz\n\nFilial tanlang:",
    "user_remove_product": "📤 Mahsulot Chiqaramiz\n\nFilial tanlang:",
    "user_select_product": "📦 Mahsulotlar:\n\nMahsulot tanlang:",
    "user_enter_quantity": "💬 Qo'shilishi kerak bo'lgan miqdorni kiriting:",
    "user_enter_remove_qty": "💬 Chiqarilishi kerak bo'lgan miqdorni kiriting:",
    "user_product_added": "✅ Mahsulot qo'shildi!\n\n📦 {}\n➕ +{} dona\n📊 Jami: {} dona",
    "user_product_removed": "✅ Mahsulot chiqarildi!\n\n📦 {}\n➖ -{} dona\n📊 Qoldi: {} dona",
    
    # Ro'yxat Xabarlar
    "list_title": "📋 Mahsulotlar Ro'yxati",
    "list_select_branch": "📋 Ro'yxat\n\nFilial tanlang:",
    "list_item": "{}. {} <b>{}</b> dona",
    "list_page_info": "\n[Sahifa {}/{}]",
    "list_empty": "📋 Mahsulotlar yo'q",
    
    # Muloqot Xabarlar
    "request_sent": "✅ So'rov yuborildi!\n\nAdmin tez orada javob beradi...",
    "request_received": "📩 Yangi so'rov:\n\n👤 Username: @{}\n🆔 User ID: <code>{}</code>",
    "user_approved": "✅ Siz tasdiqlandingiz!\n\n/start bosib davom eting",
    "user_rejected": "❌ Sizning so'rovingiz rad qilindi.\n\nKeyinroq urinib ko'ring",
    
    # Tugma Nomlari
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
    "button_approve": "✅ Tasdiqlash",
    "button_reject": "❌ Rad Qilish",
    "button_common": "🌍 Umumiy",
    "button_for_branch": "🏢 Filialga Xos",
    "button_general": "📋 Umumiy",
    "button_next": "Keyingi ➡️",
    "button_prev": "⬅️ Oldingi",
    "button_home": "🏠 Bosh Sahifa",
    
    # Xato Xabarlar
    "error_invalid_quantity": "❌ Iltimos, raqam kiriting",
    "error_invalid_number": "❌ Iltimos, musbat raqam kiriting",
    "error_not_image": "❌ Iltimos, rasm yuboring",
    "error_access_denied": "❌ Sizda ruxsat yo'q",
    
    # Muvaffaqiyat Xabarlar
    "success_operation": "✅ Operatsiya muvaffaqiyatli bajarildi",
}