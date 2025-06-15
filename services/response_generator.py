import random
from pathlib import Path
from typing import List, Dict
import json
import logging

logger = logging.getLogger(__name__)

class ResponseGenerator:
    def __init__(self):
        self.styles = {
            "luxury": "💎 Премиум предложение",
            "standard": "🏡 Хороший вариант",
            "budget": "💰 Экономичный выбор"
        }
        self.apartments = []
        self._load_apartments()

    def _load_apartments(self):
        try:
            apartments_path = Path(__file__).parent.parent / "data" / "apartments.json"
            with open(apartments_path, 'r', encoding='utf-8') as f:
                self.apartments = json.load(f)
        except Exception as e:
            logger.error(f"Error loading apartments: {e}")
            self.apartments = []

    def _format_apartment(self, apt: Dict) -> str:
        style = self.styles.get(apt.get("style", "standard"))
        features = "\n".join(f"• {f}" for f in apt["features"])

        return (
            f"{style}\n"
            f"🏢 {apt['address']}\n"
            f"📐 {apt['area']} м² | {apt['rooms']} комнаты\n"
            f"🏷️ {apt['price']:,} руб.\n"
            f"\n✨ Особенности:\n{features}\n"
            f"\n📌 {apt['description']}\n"
            f"\n☎ Контакт: {apt.get('contact', '+7 (XXX) XXX-XX-XX')}"
        )

    def generate_response(self, intent: str) -> List[str]:
        """Генерирует ответы ТОЛЬКО для обычного режима"""
        if intent == "ai_question":
            return []  # В AI-режиме этот метод не используется
        if intent == "dialogue_answer": # Ответ уже сформирован в intent_classifier
            return []

        responses = []
        
        if intent == "greeting":
            responses.append(random.choice([
                "Привет! Я ваш гид по недвижимости.",
                "Здравствуйте! Готов помочь с поиском жилья.",
                "Приветствую!"
            ]))
        elif intent == "self_info":
            responses.append(random.choice([
                "Я бот-консультант по недвижимости. Могу помочь подобрать квартиру!",
                "Ваш виртуальный помощник по аренде и покупке жилья!",
                "Я специализируюсь на подборе недвижимости!"
            ]))
        elif intent == "mood":
            responses.append(random.choice([
                "Всё отлично! Готов вам помочь.",
                "Работаю в штатном режиме! Ищу лучшие варианты для вас.",
                "Как в сказке! Чем могу помочь?",
                "Прекрасно!"
            ]))
        elif intent == "goodbye":
            responses.append(random.choice([
                "До свидания! Возвращайтесь за новыми предложениями!",
                "Хорошего дня! Если нужна будет недвижимость — обращайтесь.",
                "Всего доброго!",
            ]))
        elif intent == "apartment":
            responses.append(random.choice([
                "Вот несколько вариантов квартир:",
                "Подобрал для вас лучшие актуальные предложения:",
                "Актуальные варианты жилья для вас:"
            ]))
            if self.apartments:
                for apt in random.sample(self.apartments, min(3, len(self.apartments))):
                    responses.append(self._format_apartment(apt))
        else:
            responses.append(random.choice([
                "Не понял вашего вопроса. Можете уточнить?",
                "Извините, я не совсем понял. Переформулируйте, пожалуйста.",
                "Кажется, я не распознал ваш запрос. Попробуйте сказать иначе."
            ]))

        return responses if intent in ["apartment", "unknown"] else responses[:1]