import logging
from pathlib import Path
from telegram import Update, Message
from telegram.ext import ContextTypes
from services import voice_service
from config.settings import get_user_settings
from .text_handler import handle_text
from datetime import datetime
import random

logger = logging.getLogger(__name__)

class CustomMessage:
    """Класс-обертка для имитации объекта сообщения"""
    def __init__(self, original_message, text):
        # Копируем все важные атрибуты из оригинального сообщения
        self.text = text
        self.message_id = random.randint(-1000000000, -1)  # Отрицательный ID для фейковых сообщений
        self.date = datetime.now()
        self.chat = original_message.chat
        self.from_user = original_message.from_user
        
        # Добавляем необходимые атрибуты
        self.effective_user = original_message.from_user  # Для большинства случаев достаточно from_user
        self.effective_chat = original_message.chat  # Этим чат, в который пришло сообщение
        
        # Копируем атрибуты для совместимости
        self.forward_from = None
        self.forward_date = None
        self.reply_to_message = None
        self.voice = None
        self.caption = None
        self.entities = None
        self.caption_entities = None

    # Добавляем свойство reply, для совместимости с некоторыми обработчиками
    @property
    def reply(self):
        return self.reply_to_message

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.voice:
        return
        
    user_id = update.effective_user.id
    user_settings_data = get_user_settings(user_id)

    if not user_settings_data.get("voice_mode", False):
        await update.message.reply_text("ℹ️ Для голосового общения активируйте функцию /voice_mode")
        return

    # Создаем временные папки
    temp_dir = Path("temp") / "downloads"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Скачиваем голосовое сообщение
    voice_file = await context.bot.get_file(update.message.voice.file_id)
    audio_path = temp_dir / f"voice_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.ogg"
    await voice_file.download_to_drive(audio_path)
    
    if not audio_path.exists():
        logger.error(f"Failed to download voice: {audio_path}")
        await update.message.reply_text("❌ Не удалось обработать аудио. Попробуйте ещё раз.")
        return

    # Конвертируем в текст
    recognized_text = voice_service.speech_to_text(str(audio_path))
    
    # Удаляем временный файл
    try:
        audio_path.unlink()
    except Exception as e:
        logger.warning(f"Error deleting audio file: {str(e)}")

    if recognized_text:
        logger.info(f"Recognized text: {recognized_text}")
        
        # Создаем кастомное сообщение для обработки
        custom_message = CustomMessage(update.message, recognized_text)
        
        # Создаем кастомный update
        custom_update = Update(
            update_id=update.update_id + 1000 * int(datetime.now().timestamp()),
            message=custom_message
        )
        
        # Обрабатываем как текстовое сообщение
        await handle_text(custom_update, context)
    else:
        await update.message.reply_text("🔇 Не удалось распознать речь. Пожалуйста, повторите или пишите текстом.")
