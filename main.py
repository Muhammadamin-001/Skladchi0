import asyncio
import logging
import sys
from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.memory import MemoryStorage
from config.settings import BOT_TOKEN
from database.mongodb import init_db
from handlers import admin_handlers, user_handlers, common_handlers

# Logging konfiguratsiyasi
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Botni ishga tushirish"""
    
    # Bazani ishga tushirish
    logger.info("🔌 MongoDB baza Ishga Tushirilmoqda...")
    try:
        init_db()
        logger.info("✅ MongoDB baza tayyor")
    except Exception as e:
        logger.error(f"❌ MongoDB xatosi: {e}")
        sys.exit(1)
    
    # Botni ishga tushirish
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Routers ro'yxatga olib qo'shish
    logger.info("📝 Obrabotchiklari ro'yxatga olib qo'shilmoqda...")
    dp.include_router(common_handlers.router)
    dp.include_router(admin_handlers.router)
    dp.include_router(user_handlers.router)
    logger.info("✅ Obrabotchiklari ro'yxatga qo'shildi")
    
    try:
        logger.info("🤖 Bot ishga tushdi!")
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("⛔ Bot to'xtatildi")
    finally:
        await bot.session.close()
        logger.info("🔌 Bot yopildi")

if __name__ == "__main__":
    asyncio.run(main())