from typing import Tuple, Optional
from pathlib import Path
import json
import logging
from services.ai_service import ai_service
from services.ml_service import ml_service

logger = logging.getLogger(__name__)

class IntentClassifier:
    def __init__(self):
        self.intents = self._load_intents()
        self.dialogues = self._load_dialogues()

    def _load_intents(self):
        try:
            intents_path = Path(__file__).parent.parent / "data" / "intents.json"
            with open(intents_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading intents: {e}")
            return {}

    def _load_dialogues(self):
        dialogues = []
        try:
            dialogues_path = Path(__file__).parent.parent / "data" / "my_dialogues.txt"
            with open(dialogues_path, 'r', encoding='utf-8') as f:
                current_dialog = []
                for line in f:
                    line = line.strip()
                    if line.startswith("=========="):
                        if current_dialog:
                            dialogues.append(current_dialog)
                            current_dialog = []
                    elif ":" in line:
                        speaker, text = line.split(":", 1)
                        current_dialog.append((speaker.strip(), text.strip()))
        except Exception as e:
            logger.error(f"Error loading dialogues: {e}")
        return dialogues

    def find_in_dialogues(self, user_input: str) -> Optional[str]:
        user_input = user_input.lower().strip()
        if not user_input:  # Защита от пустого ввода
            return None
            
        for dialog in self.dialogues:
            for i, (speaker, text) in enumerate(dialog):
                if speaker == "H" and user_input in text.lower():
                    if i + 1 < len(dialog) and dialog[i+1][0] == "B":
                        answer = dialog[i+1][1].strip()
                        return answer if answer else None  # Не возвращаем пустые ответы
        return None

    def process(self, text: str, ai_mode: bool = False) -> Tuple[str, Optional[str]]:
        if ai_mode:
            return "ai_question", None
            
        # Сначала ищем в диалогах
        dialogue_answer = self.find_in_dialogues(text)
        if dialogue_answer:
            return "dialogue_answer", dialogue_answer
            
        # Затем обычные интенты
        text_lower = text.lower()
        for intent, examples in self.intents.items():
            if any(example in text_lower for example in examples):
                return intent, None
                
        return "unknown", None

    # Старый вариант, при котором сначала ищутся ключевые слова, а если не находятся - подключается AI или бот скажет, что не понял вопроса
    # def process(self, text: str) -> Tuple[str, Optional[str]]:
    #     try:
    #         text_lower = text.lower()
            
    #         # Проверка интентов из JSON
    #         for intent, examples in self.intents.items():
    #             if any(example in text_lower for example in examples):
    #                 return intent, None
                    
    #         return "unknown", None
    #     except Exception as e:
    #         logger.error(f"Intent classification failed: {e}")
    #         return "error", None

    def get_ai_response(self, text: str) -> Optional[str]:
        """Генерирует ответ с помощью AI"""
        try:
            return ai_service.generate_response(text)
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return None
