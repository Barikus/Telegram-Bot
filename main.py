import logging
from telegram.ext import Application, MessageHandler, CommandHandler, filters
from config.settings import TELEGRAM_TOKEN
from config.logger import setup_logging
from handlers.voice import handle_voice_message
from handlers.text import (
    start,
    toggle_ai_mode,
    toggle_voice_mode,
    search_apartments,
    handle_text_message
)

def main():
    setup_logging()
    logging.info("Starting bot...")

    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Явная регистрация всех обработчиков с логгированием
    handlers = [
        CommandHandler("start", start),
        CommandHandler("ai_mode", toggle_ai_mode),
        CommandHandler("voice_mode", toggle_voice_mode),
        CommandHandler("search", search_apartments),
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message),
        MessageHandler(filters.VOICE, handle_voice_message)
    ]
    
    for handler in handlers:
        application.add_handler(handler)
        logging.info(f"Registered handler: {type(handler).__name__}")
    
    logging.info("All handlers registered successfully")
    application.run_polling()

if __name__ == "__main__":
    main()