from llama_cpp import Llama
import logging
from typing import Optional
import os
from config.settings import AI_ENABLED

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.llm = None
        if AI_ENABLED:
            self._load_model()

    def _load_model(self):
        try:
            model_path = "models/Meta-Llama-3-8B-Q8_0.gguf"
            if os.path.exists(model_path):
                logger.info("🔄 Loading AI model...")
                self.llm = Llama(
                    model_path=model_path,
                    n_ctx=2048,
                    n_threads=4,
                    verbose=False
                )
                logger.info("✅ AI model loaded successfully!")
            else:
                logger.warning("Model file not found, AI will be disabled")
        except Exception as e:
            logger.error(f"❌ Model loading error: {e}")

    def generate_response(self, prompt: str) -> Optional[str]:
        if not self.llm:
            return None

        try:
            system_prompt = (
                "Ты профессиональный консультант по недвижимости. "
                "Отвечай четко и по делу (1-3 предложения). "
                "Если вопрос не о недвижимости, вежливо перенаправь на тему."
            )
            full_prompt = f"{system_prompt}\nВопрос: {prompt}\nОтвет:"

            response = self.llm(
                full_prompt,  # Используем исправленную переменную
                max_tokens=150,
                temperature=0.6,
                stop=["\n", "Вопрос:", "Ответ:"],
                echo=False
            )
            return response['choices'][0]['text'].strip()
        except Exception as e:
            logger.error(f"Generation error: {e}")
            return None

ai_service = AIService()