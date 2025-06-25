import os
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
import speech_recognition as sr
from gtts import gTTS
import subprocess

logger = logging.getLogger(__name__)

class VoiceService:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.emoji_regex = re.compile(r"[\U00010000-\U0010ffff]", flags=re.UNICODE)
        self.clean_regex = re.compile(r'[^\w\s,.?!-]')

    def clean_text(self, text: str) -> str:
        """Удаление эмодзи и спецсимволов"""
        cleaned = re.sub(self.emoji_regex, '', text)
        return re.sub(self.clean_regex, '', cleaned)

    def text_to_speech(self, text: str, user_id: int) -> Optional[str]:
        try:
            # Создаем временную директорию
            temp_dir = Path("temp") / "voices"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Генерируем уникальное имя файла
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            voice_path = temp_dir / f"voice_{user_id}_{timestamp}.ogg"
            
            # Очищаем текст
            clean_text = self.clean_text(text)
            if not clean_text or len(clean_text) < 3:
                return None

            # Синтез речи
            tts = gTTS(text=clean_text[:300], lang='ru', slow=False)
            tts.save(str(voice_path))
            return str(voice_path)
        except Exception as e:
            logger.error(f"Ошибка синтеза речи: {str(e)}", exc_info=True)
            return None

    def speech_to_text(self, ogg_path: str) -> Optional[str]:
        try:
            # Создаем временную директорию для конвертированных файлов
            temp_dir = Path("temp") / "audio"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Конвертация в WAV (требуется для speech_recognition)
            wav_path = temp_dir / f"{Path(ogg_path).stem}.wav"
            
            # Используем ffmpeg для конвертации
            subprocess.run(
                ['ffmpeg', '-y', '-i', str(ogg_path), str(wav_path)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Распознавание речи
            with sr.AudioFile(str(wav_path)) as source:
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio, language='ru-RU')
                return text
        except sr.UnknownValueError:
            logger.warning("Не удалось распознать речь в аудио")
        except sr.RequestError as e:
            logger.error(f"Ошибка сервиса распознавания: {str(e)}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка конвертации аудио: {str(e)}")
        except Exception as e:
            logger.error(f"Необработанная ошибка в speech_to_text: {str(e)}", exc_info=True)
        finally:
            # Удаляем временные файлы
            for path in [ogg_path, wav_path]:
                if path and Path(path).exists():
                    try:
                        Path(path).unlink()
                    except:
                        pass
        return None
