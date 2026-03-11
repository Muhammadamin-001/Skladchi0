import asyncio
import logging
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from config.settings import BOT_TOKEN
from database.mongodb import init_db

# Logging
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
        # Bot o'rnatish
        app = Application.builder().token(BOT_TOKEN).build()
        
        logger.info("🤖 Bot ishga tushdi!")
        
        # Polling boshlash
        await app.run_polling()
        
    except KeyboardInterrupt:
        logger.info("⛔ Bot to'xtatildi")
    except Exception as e:
        logger.error(f"❌ Xatolik: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())