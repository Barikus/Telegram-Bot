import random
from pathlib import Path
import json
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class ResponseGenerator:
    STYLE_EMOJIS = {
        "luxury": "💎 Люкс",
        "standard": "🏠 Стандарт",
        "budget": "💰 Бюджетный вариант"
    }
    
    def __init__(self):
        self.apartments = []
        self._load_apartments()
        logger.info(f"ResponseGenerator loaded {len(self.apartments)} apartments")

    def _load_apartments(self):
        apt_path = Path(__file__).parent.parent / "data" / "apartments.json"
        if apt_path.exists():
            try:
                with open(apt_path, 'r', encoding='utf-8') as f:
                    self.apartments = json.load(f)
                    logger.info(f"🏢 Loaded {len(self.apartments)} apartments")
            except Exception as e:
                logger.error(f"🚨 Apartment loading error: {str(e)}")
        else:
            logger.warning("Apartments file not found")

    def _format_apartment(self, apt: dict) -> str:
        style = self.STYLE_EMOJIS.get(apt.get("style", "standard"))
        features = "\n".join(f"• {feat}" for feat in apt.get("features", []))
        
        return (
            f"{style}\n"
            f"📍 {apt['address']}\n"
            f"📏 {apt['area']} м² | 🛏️ {apt['rooms']} комнаты\n"
            f"💵 {apt['price']:,} руб.{' в месяц' if apt.get('rental', False) else ''}\n\n"
            f"🔮 Особенности:\n{features}\n\n"
            f"📝 {apt['description']}\n\n"
            f"👤 {apt.get('contact', 'Контакты отсутствуют')}"
        )

    def get_random_apartment(self) -> Optional[str]:
        if not self.apartments:
            return None
        apt = random.choice(self.apartments)
        return self._format_apartment(apt)

    def generate(self, intent: str) -> List[str]:
        responses = []
        
        if intent == "greeting":
            responses.append(random.choice([
                "Привет! Я ваш ассистент по недвижимости. Чем могу помочь? 😊",
                "Здравствуйте! Помогу подобрать идеальное жильё для вас. 🏠",
                "Приветствую! Готов предложить вам лучшие варианты жилья! 🌆"
            ]))
            
        elif intent == "self_info":
            responses.append("Я бот-консультант по недвижимости. Специализируюсь на подборе квартир и ответах на все вопросы по этой теме! 🏡")
            
        elif intent == "mood":
            responses.append(random.choice([
                "Отлично, готов работать! 😊",
                "У меня всё чудесно, как у бота! 🤖",
                "В прекрасном настроении, помогу по любым вопросам жилья. 💪"
            ]))
            
        elif intent == "goodbye":
            responses.append("Отличного дня! Возвращайтесь, когда понадобится недвижимость. 👋")
            
        elif intent == "apartment":
            if not self.apartments:
                responses.append("⛔ К сожалению, у меня нет доступных предложений сейчас.")
                return responses
                
            responses.append("🏙️ Вот актуальные варианты:")
            # Берем максимум 3 случайных квартиры
            for apt in random.sample(self.apartments, min(3, len(self.apartments))):
                responses.append(self._format_apartment(apt))
                
        else:  # unknown intent
            return []  # Пустой ответ отправится в AI-обработчик
            
        return responses
