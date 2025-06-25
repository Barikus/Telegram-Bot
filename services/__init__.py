from .ai_service import AIService
from .voice_service import VoiceService
from .intent_classifier import IntentClassifier
from .response_generator import ResponseGenerator

# Создаем экземпляры сервисов
ai_service = AIService()
voice_service = VoiceService()
intent_classifier = IntentClassifier()  
response_generator = ResponseGenerator()
