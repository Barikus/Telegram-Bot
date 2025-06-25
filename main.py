import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config.settings import TELEGRAM_TOKEN
from handlers.text_handler import start, toggle_ai_mode, toggle_voice_mode, search_apartments, handle_text
from handlers.voice_handler import handle_voice
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main() -> None:
    logger.info("Starting bot initialization...")
    
    # Создаем папки для временных файлов
    Path("temp/voices").mkdir(parents=True, exist_ok=True)
    Path("temp/audio").mkdir(parents=True, exist_ok=True)
    Path("temp/downloads").mkdir(parents=True, exist_ok=True)
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ai_mode", toggle_ai_mode))
    application.add_handler(CommandHandler("voice_mode", toggle_voice_mode))
    application.add_handler(CommandHandler("search", search_apartments))
    
    # Регистрируем обработчики сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    
    logger.info("All handlers registered. Starting polling...")
    application.run_polling()

if __name__ == "__main__":
    main()

