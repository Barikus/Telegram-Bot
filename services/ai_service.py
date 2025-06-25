import os
import threading
from pathlib import Path
from llama_cpp import Llama
import logging
from config.settings import AI_ENABLED

logger = logging.getLogger(__name__)

class AIService:
    _lock = threading.Lock()
    
    def __init__(self):
        self.llm = None
        self.model_loaded = False

    def _load_model(self):
        with self._lock:
            if self.llm or self.model_loaded:
                return
                
            try:
                if not AI_ENABLED:
                    logger.info("AI отключен в настройках")
                    return
                
                model_path = "models/saiga_llama3_8b_ggml-model-q8_0.gguf"
                if not Path(model_path).exists():
                    logger.error("Файл модели не найден")
                    return

                logger.info("Загрузка AI модели...")
                self.llm = Llama(
                    model_path=model_path,
                    n_ctx=4096,
                    n_threads=8,
                    chat_format="llama-3",
                    n_gpu_layers=50,
                    verbose=False
                )
                self.model_loaded = True
                logger.info("Модель успешно загружена!")
            except Exception as e:
                logger.error(f"Ошибка загрузки модели: {str(e)}", exc_info=True)

    def generate_response(self, prompt: str) -> str:
        if not AI_ENABLED or not prompt.strip():
            return ""
            
        if not self.model_loaded:
            self._load_model()
            
        if not self.llm:
            return ""
            
        try:
            system_prompt = (
                "Ты Квартирка — профессиональный, дружелюбный консультант по недвижимости.\n"
                "ПРАВИЛА:\n"
                "1. Отвечай кратко (1-2 предложения)\n"
                "2. Используй эмодзи для выразительности 😊\n"
                "3. Задавай вопросы о предпочтениях клиента\n"
                "4. Каждые 3-5 реплик предлагай квартиры\n"
                "5. Начинай каждое предложение с большой буквы\n\n"
                "Пример диалога:\n"
                "User: Привет\n"
                "You: Привет! 😊 Готов помочь найти идеальное жильё! Что интересует?"
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            response = self.llm.create_chat_completion(
                messages=messages,
                max_tokens=384,
                temperature=0.7,
                top_p=0.9,
                stop=["<|end_of_text|>"]
            )
            
            content = response['choices'][0]['message']['content'].strip()
            
            # Гарантируем первую заглавную букву
            if content and content[0].islower():
                content = content[0].upper() + content[1:]
                
            return content
        except Exception as e:
            logger.error(f"Ошибка генерации: {str(e)}", exc_info=True)
            return ""
