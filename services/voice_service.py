import os
from datetime import datetime
import asyncio
from pathlib import Path
import speech_recognition as sr
from gtts import gTTS
import logging
from concurrent.futures import ThreadPoolExecutor
import subprocess
import re

logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor(max_workers=4)

class VoiceService:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.audio_dir = Path(__file__).parent.parent / "data" / "audio"
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols
            "\U0001F680-\U0001F6FF"  # transport
            "\U0001F1E0-\U0001F1FF"  # flags
            "]+", 
            flags=re.UNICODE
        )

    async def voice_to_text(self, ogg_path: str) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, self._sync_voice_to_text, ogg_path)

    def _sync_voice_to_text(self, ogg_path: str) -> str:
        wav_path = ogg_path.replace('.ogg', '.wav')
        try:
            # Конвертируем OGG в WAV
            subprocess.run(
                ['ffmpeg', '-y', '-i', ogg_path, '-ar', '16000', '-ac', '1', wav_path],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            with sr.AudioFile(wav_path) as source:
                audio = self.recognizer.record(source)
                return self.recognizer.recognize_google(audio, language="ru-RU")
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка конвертации аудио: {e.stderr.decode()}")
            return ""
        except sr.UnknownValueError:
            logger.error("Google Speech Recognition не смог распознать аудио")
            return ""
        except sr.RequestError as e:
            logger.error(f"Ошибка сервиса распознавания: {str(e)}")
            return ""
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {str(e)}")
            return ""
        finally:
            # Удаляем временные файлы
            for path in [wav_path]:
                try:
                    if path and os.path.exists(path):
                        os.remove(path)
                except Exception as e:
                    logger.error(f"Ошибка удаления файла {path}: {str(e)}")

    def text_to_voice(self, text: str, user_id: int) -> str:
        if not text or not text.strip():
            logger.error("Пустой текст для озвучки")
            return ""

        try:
            # Очистка текста от эмодзи и лишних символов
            clean_text = self.emoji_pattern.sub('', text)
            if not clean_text.strip():
                logger.error("Текст содержит только эмодзи/спецсимволы")
                return ""

            # Создаем уникальное имя файла с timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            voice_path = str(self.audio_dir / f"voice_{user_id}_{timestamp}.ogg")
            
            # Ограничиваем длину текста для gTTS (максимум 500 символов)
            clean_text = clean_text[:500]
            
            # Генерация голоса
            tts = gTTS(text=clean_text, lang='ru', slow=False)
            tts.save(voice_path)
            
            # Проверка что файл создан
            if not os.path.exists(voice_path):
                logger.error(f"Файл {voice_path} не создан")
                return ""
                
            return voice_path
            
        except Exception as e:
            logger.error(f"Ошибка генерации голоса: {str(e)}", exc_info=True)
            return ""

voice_service = VoiceService()  