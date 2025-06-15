import os
from telegram import Update
from telegram.ext import ContextTypes
from services import ai_service
from services.intent_classifier import IntentClassifier
from services.response_generator import ResponseGenerator
from services.voice_service import voice_service
from services.ai_service import AIService
from config.settings import user_settings
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
intent_classifier = IntentClassifier()
response_generator = ResponseGenerator()
ai_service = AIService()

async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.voice:
        return

    user_id = update.effective_user.id
    voice_path = f"data/audio/{user_id}_{datetime.now().timestamp()}.ogg"

    try:
        if not user_settings.get_user_settings(user_id).get("voice_mode", False):
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="ℹ Голосовой режим отключен. Включите командой /voice_mode"
            )
            return

        os.makedirs(os.path.dirname(voice_path), exist_ok=True)
        voice_file = await update.message.voice.get_file()
        await voice_file.download_to_drive(voice_path)

        text = await voice_service.voice_to_text(voice_path)
        if not text:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Не удалось распознать речь"
            )
            return

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"🔊 Вы сказали: {text}"
        )

        # Получаем ответ с проверкой на пустоту
        response = None
        if user_settings.get_user_settings(user_id).get("ai_mode", False):
            response = ai_service.generate_response(text) or "Не удалось сгенерировать ответ"
        else:
            intent, dialogue_answer = intent_classifier.process(text)
            if dialogue_answer:
                response = dialogue_answer
            else:
                responses = response_generator.generate_response(intent)
                response = "\n".join(responses) if responses else "Я не понял вашего вопроса"

        if not response or not response.strip():
            response = "Я не нашел подходящего ответа"

        # Отправка ответа
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=response
        )

        if user_settings.get_user_settings(user_id).get("voice_mode", False):
            voice_path = voice_service.text_to_voice(response, user_id)
            if voice_path and os.path.exists(voice_path):
                try:
                    with open(voice_path, 'rb') as voice_file:
                        await context.bot.send_voice(
                            chat_id=update.effective_chat.id,
                            voice=voice_file
                        )
                finally:
                    try:
                        os.remove(voice_path)
                    except Exception as e:
                        logger.error(f"Ошибка удаления голосового файла: {str(e)}")

    except Exception as e:
        logger.error(f"Ошибка обработки голосового сообщения: {str(e)}", exc_info=True)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Произошла ошибка при обработке голосового сообщения"
        )
    finally:
        try:
            if os.path.exists(voice_path):
                os.remove(voice_path)
        except Exception as e:
            logger.error(f"Ошибка при удалении временного файла: {str(e)}")

async def process_text_directly(text: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текста с учетом режимов"""
    user_id = update.effective_user.id
    settings = user_settings.get_user_settings(user_id)

    # AI-режим
    if settings.get("ai_mode", False) and ai_service.llm:
        ai_response = ai_service.generate_response(text)
        if ai_response:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=ai_response
            )
            return

    # Обычный режим
    intent, _ = intent_classifier.process(text)
    responses = response_generator.generate_response(intent)
    for response in responses:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=response
        )