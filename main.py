import asyncio
import logging
import sys
import os
from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.memory import MemoryStorage
from config.settings import BOT_TOKEN
from database.mongodb import init_db
from handlers import admin_handlers, user_handlers, common_handlers

# Logging - Render uchun
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

async def main():
    """Botni ishga tushirish"""
    
    logger.info("🔌 MongoDB baza Ishga Tushirilmoqda...")
    try:
        init_db()
        logger.info("✅ MongoDB baza tayyor")
    except Exception as e:
        logger.error(f"❌ MongoDB xatosi: {e}")
        sys.exit(1)
    
    try:
        bot = Bot(token=BOT_TOKEN)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        logger.info("📝 Obrabotchiklari ro'yxatga olib qo'shilmoqda...")
        dp.include_router(common_handlers.router)
        dp.include_router(admin_handlers.router)
        dp.include_router(user_handlers.router)
        logger.info("✅ Obrabotchiklari ro'yxatga qo'shildi")
        
        logger.info("🤖 Bot ishga tushdi! Polling boshlandi...")
        
        # Long polling
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            relax_timeout=10,
            timeout=30
        )
        
    except KeyboardInterrupt:
        logger.info("⛔ Bot to'xtatildi")
    except Exception as e:
        logger.error(f"❌ Xatolik: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await bot.session.close()
        logger.info("🔌 Bot yopildi")


if __name__ == "__main__":
    asyncio.run(main())