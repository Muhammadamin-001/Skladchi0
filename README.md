# 🏪 Ombor Mahsulotlarini Boshqarish Boti

Telegram bot orqali ombor mahsulotlarini boshqarish tizimi.

## ⚡ Xususiyatlar

### 👨‍💼 Administrator Uchun
- 🏢 Filiallarni boshqarish (qo'shish, o'zgaritirsh, o'chirish)
- 📦 Mahsulotlarni boshqarish (qo'shish, rasm yuklash, o'zgaritirsh, o'chirish)
- 👤 Foydalanuvchilarni tasdiqlash/rad qilish
- 📋 To'liq inventar ro'yxatini ko'rish

### 👥 Foydalanuvchi Uchun
- 📥 Mahsulot kiritish (inventarga qo'shish)
- 📤 Mahsulot chiqarish (inventardan ayirish)
- 📋 Mahsulotlar ro'yxatini ko'rish
- 🔒 Ro'yxatga olib qo'yilish tizimi

## 📋 Talablar

```bash
- Python 3.8+
- MongoDB Atlas (bepul akkaunt)
- Telegram Bot Token (@BotFather orqali)
```

## 🚀 O'rnatish

### 1. Repositoryni klonlash
```bash
git clone <repo_url>
cd inventory_bot
```

### 2. Paket o'rnatish
```bash
pip install -r requirements.txt
```

### 3. .env fayl yaratish
```bash
cp .env.example .env
```

### 4. .env fayl parametrlarini to'ldirish

**BOT_TOKEN:** @BotFather dan olib qo'ying
**ADMIN_ID:** `/id` komandasini botga yuboring
**MONGO_URI:** MongoDB Atlas ulanish satri

### 5. Botni ishga tushirish

```bash
# Lokal ishlatish uchun
python main.py

# Production uchun (Render.com)
gunicorn main:app
```

## 📱 Foydalanish

### Admin Uchun

1. **Bot /start qilish**
2. **Filiallarni boshqarish:**
   - 🏢 Filial tugmasi
   - Yangi filial qo'shish
   - Nomlini o'zgaritirsh/o'chirish

3. **Mahsulotlarni boshqarish:**
   - 📦 Mahsulot tugmasi
   - Umumiy yoki filialga xos tanlash
   - Rasm orqali mahsulot qo'shish

4. **Ro'yxatni ko'rish:**
   - 📋 Ro'yxat tugmasi
   - Filiallar bo'yicha inventar ko'rish

### Foydalanuvchi Uchun

1. **/start bilan bot ishga tushirish**
2. **Tasdiqlash so'rovini yuborish**
3. **Admin tasdiqlash vaqt kutish**
4. **Mahsulot kiritish/chiqarish** ishlamalarini bajarib ko'rish

## 🏗️ Loyiha Tuzilishi

```
inventory_bot/
├── config/              # Konfiguratsiya
│   └── settings.py
├── database/            # MongoDB
│   └── mongodb.py
├── handlers/            # Xandalangi
│   ├── admin_handlers.py
│   ├── user_handlers.py
│   └── common_handlers.py
├── keyboards/           # Tugmalar
│   ├── admin_keyboards.py
│   └── user_keyboards.py
├── states/              # FSM holatlari
│   ├── admin_states.py
│   └── user_states.py
├── main.py              # Asosiy fayl
└── requirements.txt     # Kutubxonalar
```

## 💾 MongoDB To'plamlar

- **users** - Foydalanuvchilar
- **branches** - Filiallar
- **products** - Mahsulotlar
- **inventory** - Inventar
- **requests** - Tasdiqlash so'rovlari

## 🔒 Xavfsizlik

- Admin paneli faqat ADMIN_ID dan mavjud
- Foydalanuvchilar tasdiqlanmaguncha ishlay olmaydi
- Barcha operatsiyalar MongoDB da saqlannadi

## 🌐 Deployment (Render.com)

1. GitHub'da repositoryni yaratish
2. Render.com'da yangi Web Service qo'shish
3. Environment variables o'rnatish
4. Deploy qilish

## 🐛 Debugging

```python
# Logging ko'rish
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📞 Support

Muammolar bo'lsa issue ochib qo'ying yoki admin bilan bog'laning.

---

**Muvaffaqiyatli foydalanish!** ✨