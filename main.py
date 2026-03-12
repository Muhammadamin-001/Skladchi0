import telebot
import logging
import os
from flask import Flask, request
from config.settings import BOT_TOKEN, ADMIN_ID, MESSAGES
from database.mongodb import init_db, get_db
from handlers.message_handlers import register_message_handlers
from handlers.callback_handlers import register_callback_handlers

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

logger.info("🔌 MongoDB baza Ishga Tushirilmoqda...")
try:
    init_db()
    logger.info("✅ MongoDB baza tayyor")
except Exception as e:
    logger.error(f"❌ MongoDB xatosi: {e}")

# ==================== USER STATE STORAGE ====================
user_states = {}

# ==================== REGISTER HANDLERS ====================

# ✅ MESSAGE HANDLERLARNI AVVALIGA RO'YXATLA
logger.info("📝 Message handlerlarni ro'yxatlamoqda...")
register_message_handlers(bot, user_states)

# ✅ CALLBACK HANDLERLARNI KEYIN RO'YXATLA
logger.info("📝 Callback handlerlarni ro'yxatlamoqda...")
register_callback_handlers(bot, user_states)

# ==================== WEBHOOK (FLASK) ====================

@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    """Webhook endpoint"""
    try:
        json_str = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        logger.info("✅ Webhook received")
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
    return "ok", 200

@app.route('/')
def index():
    """Health check"""
    return "Bot is running", 200

# ==================== MAIN ====================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🤖 Bot ishga tushdi! Webhook path: /{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=port, debug=False)