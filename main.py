import asyncio
import logging
import sys
from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.memory import MemoryStorage
from config.settings import BOT_TOKEN
from database.mongodb import init_db
from handlers import admin_handlers, user_handlers, common_handlers

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
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
        
        logger.info("🤖 Bot ishga tushdi!")
        await dp.start_polling(bot)
        
    except KeyboardInterrupt:
        logger.info("⛔ Bot to'xtatildi")
    except Exception as e:
        logger.error(f"❌ Xatolik: {e}")
        sys.exit(1)
    finally:
        await bot.session.close()
        logger.info("🔌 Bot yopildi")


@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200

# Just to test server
@app.route('/')
def index():
    return "Bot is running"

if __name__ == "__main__":

    PORT = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=PORT)




