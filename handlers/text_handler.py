import random
import logging
import os
from pathlib import Path
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from services import ai_service, voice_service, intent_classifier, response_generator
from config.settings import save_user_setting, get_user_settings

logger = logging.getLogger(__name__)

APT_RECOMMEND_PROBABILITY = 0.25
GENERAL_RECOMMEND_PROBABILITY = 0.1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        f"Приветствую, {user.mention_html()}! 👋 Я твой виртуальный помощник по недвижимости.\n\n"
        "<b>🏠 Основные команды:</b>\n"
        "• /start - Начало работы\n"
        "• /search - Найти квартиры 🔎\n"
        "• /ai_mode - AI-режим\n"
        "• /voice_mode - Голосовой режим\n\n"
        "<i>Просто напиши мне о том, что ищешь, и я подберу лучшие варианты! 😊</i>",
        reply_markup=ReplyKeyboardRemove()
    )

async def toggle_ai_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    current_settings = get_user_settings(user_id)  # Исправлено
    new_mode = not current_settings.get("ai_mode", False)
    
    save_user_setting(user_id, "ai_mode", new_mode)  # Исправлено
    await update.message.reply_text(f"🤖 AI режим {'включен' if new_mode else 'выключен'}")

async def toggle_voice_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    current_settings = get_user_settings(user_id)  # Исправлено
    new_mode = not current_settings.get("voice_mode", False)
    
    save_user_setting(user_id, "voice_mode", new_mode)  # Исправлено
    await update.message.reply_text(f"🎤 Голосовой режим {'включен' if new_mode else 'выключен'}")

async def search_apartments(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    responses = response_generator.generate("apartment")  # Экземпляр из сразу сервиса
    for response in responses:
        await send_response(update, context.bot, response)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text or not update.message.text.strip():
        return
        
    user_id = update.effective_user.id
    user_settings_data = get_user_settings(user_id)
    ai_active = user_settings_data.get("ai_mode", False)
    text = update.message.text.strip()
    
    logger.info(f"Text Handler | User:{user_id} | Text: {text} | AI Active: {ai_active}")
    
    intent, prepared_response = intent_classifier.classify(text, ai_active)
    
    logger.info(f"Intent: {intent} | Prepared: {bool(prepared_response)}")
    
    if prepared_response:
        await send_response(update, context.bot, prepared_response)
        return
        
    # Обработка через AI для всех запросов в AI-режиме или неизвестных
    if ai_active or intent == "unknown":
        logger.info("Using AI processing...")
        
        # Середаем сообщение "Думаю..."
        chat_id = update.effective_chat.id
        thinking_msg = await context.bot.send_message(
            chat_id=chat_id,
            text="🤔 Думаю...",
            reply_to_message_id=update.message.message_id
        )
        
        ai_response = ai_service.generate_response(text)
        
        # Удаляем сообщение "Думаю..."
        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=thinking_msg.message_id
        )
        
        if ai_response:
            logger.info(f"AI Response: {ai_response[:50]}...")
            # Добавим рекомендацию квартиры с вероятностью 30%
            if random.random() < APT_RECOMMEND_PROBABILITY:
                apartment = response_generator.get_random_apartment()
                if apartment:
                    ai_response += f"\n\n✨ Кстати, вот отличный вариант для вас:\n\n{apartment}"
                    
            await send_response(update, context.bot, ai_response)
            return
        else:
            # Если AI не вернул ответ, отправляем уведомление
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Не удалось обработать ваш запрос. Попробуйте сформулировать иначе.",
                reply_to_message_id=update.message.message_id
            )
            return
    
    # Обычная обработка для известных intents
    responses = response_generator.generate(intent)
    
    # Добавим рекомендацию для обычных ответов
    if random.random() < GENERAL_RECOMMEND_PROBABILITY:
        apartment = response_generator.get_random_apartment()
        if apartment:
            responses.append(f"\n\n🏠 Рекомендую посмотреть этот вариант:\n\n{apartment}")
    
    for response in responses:
        await send_response(update, context.bot, response)


async def send_response(update: Update, bot, text: str) -> None:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if text:
        await bot.send_message(chat_id, text, parse_mode="HTML")
    
    user_settings_data = get_user_settings(user_id)  # Исправлено
    voice_mode_active = user_settings_data.get("voice_mode", False)
    
    if voice_mode_active and text:
        logger.info("Sending voice response...")
        if voice_path := voice_service.text_to_speech(text, user_id):
            try:
                if Path(voice_path).exists():
                    with open(voice_path, 'rb') as voice_file:
                        await bot.send_voice(chat_id, voice=voice_file)
                    logger.info("Voice sent successfully")
                else:
                    logger.error(f"Voice file not found: {voice_path}")
            except Exception as e:
                logger.error(f"Voice send error: {str(e)}", exc_info=True)
            finally:
                try:
                    if Path(voice_path).exists():
                        Path(voice_path).unlink()
                except Exception as e:
                    logger.error(f"Failed to delete voice file: {str(e)}")
