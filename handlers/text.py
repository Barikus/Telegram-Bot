from telegram import Message, Update
from telegram.ext import ContextTypes
from services.ai_service import AIService
from services.voice_service import voice_service
from services.intent_classifier import IntentClassifier
from services.response_generator import ResponseGenerator
from config.settings import user_settings
import logging
import os

logger = logging.getLogger(__name__)
intent_classifier = IntentClassifier()
response_generator = ResponseGenerator()
ai_service = AIService()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏠 Бот по поиску недвижимости\n\n"
        "Команды:\n"
        "/search - Поиск квартир\n"
        "/ai_mode - AI режим\n"
        "/voice_mode - Голосовой режим"
    )

async def toggle_ai_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    current = user_settings.get_user_settings(user_id).get("ai_mode", False)
    user_settings.save_user_setting(user_id, "ai_mode", not current)
    await update.message.reply_text(f"AI режим {'включен' if not current else 'выключен'}")

async def toggle_voice_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    current = user_settings.get_user_settings(user_id).get("voice_mode", False)
    user_settings.save_user_setting(user_id, "voice_mode", not current)
    await update.message.reply_text(f"Голосовой режим {'включен' if not current else 'выключен'}")

async def search_apartments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    responses = response_generator.generate_response("apartment")
    for response in responses:
        await send_response(update, response, user_id)

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    text = update.message.text.strip()
    if not text:  # Защита от пустого сообщения
        return

    settings = user_settings.get_user_settings(user_id)

    if settings.get("ai_mode", False) and ai_service.llm:
        ai_response = ai_service.generate_response(text)
        if ai_response:
            await send_response(update, ai_response, user_id)
            return
        await update.message.reply_text("Не удалось получить ответ от ИИ")
        return

    intent, dialogue_answer = intent_classifier.process(text)
    
    if dialogue_answer:
        await send_response(update, dialogue_answer, user_id)
        return
        
    responses = response_generator.generate_response(intent)
    if not responses:
        responses = ["Я не понял вашего вопроса"]
        
    for response in responses:
        await send_response(update, response, user_id)

async def send_response(update: Update, response: str, user_id: int):
    if user_settings.get_user_settings(user_id).get("voice_mode", False):
        voice_path = voice_service.text_to_voice(response, user_id)
        if voice_path:
            try:
                with open(voice_path, 'rb') as voice_file:
                    await update.message.reply_voice(voice=voice_file)
            finally:
                try:
                    os.remove(voice_path)
                except Exception as e:
                    logger.error(f"Ошибка удаления голосового файла: {e}")
    await update.message.reply_text(response)

async def process_text_content(text: str, original_update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстового контента (для использования из других обработчиков)"""
    fake_update = Update(
        update_id=original_update.update_id + 1,
        message=Message(
            message_id=original_update.message.message_id + 1,
            date=original_update.message.date,
            chat=original_update.message.chat,
            from_user=original_update.message.from_user,
            text=text
        )
    )
    await handle_text_message(fake_update, context)