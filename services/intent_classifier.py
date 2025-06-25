import json
from pathlib import Path
import logging
from typing import Tuple, Optional
import re

logger = logging.getLogger(__name__)

class IntentClassifier:
    def __init__(self):
        self.intents = {}
        self.dialogues = []
        self._load_data()
        logger.info(f"IntentClassifier initialized with {len(self.intents)} intents and {len(self.dialogues)} dialogues")

    def _load_data(self):
        base_path = Path(__file__).parent.parent / "data"
        
        # Загрузка intents.json
        intents_path = base_path / "intents.json"
        if intents_path.exists():
            try:
                with open(intents_path, 'r', encoding='utf-8') as f:
                    self.intents = json.load(f)
                    logger.info(f"Loaded {len(self.intents)} intents")
            except Exception as e:
                logger.error(f"Intent loading error: {str(e)}")

        # Загрузка диалогов
        dialogues_path = base_path / "my_dialogues.txt"
        if dialogues_path.exists():
            try:
                self.dialogues = []
                with open(dialogues_path, 'r', encoding='utf-8') as f:
                    current_dialog = []
                    for line in f:
                        line = line.strip()
                        if line.startswith("="*10):
                            if current_dialog:
                                self.dialogues.append(current_dialog)
                                current_dialog = []
                        elif ":" in line:
                            speaker, text = line.split(":", 1)
                            current_dialog.append((speaker.strip(), text.strip()))
                    # Добавляем последний диалог
                    if current_dialog:
                        self.dialogues.append(current_dialog)
                
                logger.info(f"💬 Loaded {len(self.dialogues)} dialogues")
            except Exception as e:
                logger.error(f"Dialogue loading error: {str(e)}")
        else:
            logger.warning("Dialogues file not found")

    def _find_in_dialogues(self, user_input: str) -> Optional[str]:
        cleaned_input = user_input.lower().strip()
        if not cleaned_input:
            return None
            
        for dialog in self.dialogues:
            for i, (speaker, line) in enumerate(dialog):
                # Конвертируем в верхний регистр для надежности
                speaker = speaker.strip().upper()
                
                # Проверяем строки пользователя только в Human репликах
                if speaker == "H":
                    # Ищем комбинации слов
                    line_text = line.lower()
                    if cleaned_input in line_text or line_text in cleaned_input:
                        # Ищем следующую реплику бота
                        if i + 1 < len(dialog):
                            next_speaker, next_line = dialog[i+1]
                            next_speaker = next_speaker.strip().upper()
                            
                            if next_speaker in ["B", "BOT"]:
                                return self.normalize_response(next_line)
        return None

    def _find_similar_in_dialogues(self, user_input: str) -> Optional[str]:
        """Поиск по основным ключевым словам"""
        keywords = ["привет", "пока", "спасибо", "кто"]
        for word in keywords:
            if word in user_input:
                result = self._find_in_dialogues(word)
                if result:
                    return result
        return None

    def normalize_response(self, text: str) -> str:
        if not text:
            return text
            
        # Простая нормализация: первая буква заглавная
        if text and text[0].isalpha() and text[0].islower():
            return text[0].upper() + text[1:]
        return text

    def classify(self, text: str, ai_mode: bool = False) -> Tuple[str, Optional[str]]:
        """Определение типа сообщения с улучшенным порядком"""
        if ai_mode:
            return "ai_direct", None
            
        cleaned_text = text.lower().strip()
        if not cleaned_text:
            return "unknown", None
        
        logger.debug(f"Classifying text: '{text}'")
        
        # 1. Сначала пробуем определить интент
        for intent, examples in self.intents.items():
            for example in examples:
                # Проверяем вхождение примеров в очищенный текст
                if example in cleaned_text:
                    logger.debug(f"Matched intent: {intent} with example: {example}")
                    return intent, None
        
        # 2. Пробуем найти ответ в диалогах
        dialog_response = self._find_in_dialogues(cleaned_text)
        if dialog_response:
            logger.debug(f"Found dialog response: {dialog_response}")
            return "dialogue_answer", dialog_response
        
        # 3. Пробуем похожие базовые фразы
        similar_response = self._find_similar_in_dialogues(cleaned_text)
        if similar_response:
            logger.debug(f"Found similar response: {similar_response}")
            return "dialogue_answer", similar_response
            
        return "unknown", None
