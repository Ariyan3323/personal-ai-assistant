"""
ماژول پردازش صوت و گفتار (مانند Bixby و Google Assistant)
"""

import asyncio
import io
import wave
import pyaudio
import speech_recognition as sr
import pyttsx3
from gtts import gTTS
import pygame
from typing import Dict, Any, Optional, List
import tempfile
import os
from datetime import datetime
import threading
import queue

from config.settings import settings


class VoiceProcessor:
    """پردازشگر اصلی صوت و گفتار"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.tts_engine = None
        self.is_listening = False
        self.audio_queue = queue.Queue()
        self.wake_words = ["سلام دستیار", "hey assistant", "ok assistant"]
        self._initialize_components()
    
    def _initialize_components(self):
        """راه‌اندازی اجزای صوتی"""
        try:
            # راه‌اندازی میکروفون
            self.microphone = sr.Microphone()
            
            # تنظیم میکروفون
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            # راه‌اندازی TTS
            self.tts_engine = pyttsx3.init()
            self._configure_tts()
            
            # راه‌اندازی pygame برای پخش صوت
            pygame.mixer.init()
            
        except Exception as e:
            print(f"خطا در راه‌اندازی اجزای صوتی: {e}")
    
    def _configure_tts(self):
        """پیکربندی موتور TTS"""
        if self.tts_engine:
            # تنظیم سرعت گفتار
            self.tts_engine.setProperty('rate', 150)
            
            # تنظیم صدا (در صورت وجود صدای زنانه/مردانه)
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # انتخاب صدای اول (معمولاً زنانه)
                self.tts_engine.setProperty('voice', voices[0].id)
            
            # تنظیم حجم صدا
            self.tts_engine.setProperty('volume', 0.8)


class SpeechRecognizer(VoiceProcessor):
    """تشخیص گفتار"""
    
    async def listen_once(self, timeout: int = 5, phrase_timeout: int = 1) -> Dict[str, Any]:
        """گوش دادن یک بار به صدا"""
        try:
            with self.microphone as source:
                print("در حال گوش دادن...")
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_timeout
                )
            
            return await self._process_audio(audio)
            
        except sr.WaitTimeoutError:
            return {"success": False, "error": "Timeout - no speech detected"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def continuous_listen(self, callback_func=None):
        """گوش دادن مداوم"""
        self.is_listening = True
        
        def listen_thread():
            while self.is_listening:
                try:
                    with self.microphone as source:
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                        self.audio_queue.put(audio)
                except sr.WaitTimeoutError:
                    continue
                except Exception as e:
                    print(f"خطا در گوش دادن مداوم: {e}")
        
        # شروع thread گوش دادن
        listen_thread = threading.Thread(target=listen_thread, daemon=True)
        listen_thread.start()
        
        # پردازش صداهای دریافتی
        while self.is_listening:
            try:
                if not self.audio_queue.empty():
                    audio = self.audio_queue.get_nowait()
                    result = await self._process_audio(audio)
                    
                    if result["success"] and callback_func:
                        await callback_func(result)
                
                await asyncio.sleep(0.1)  # جلوگیری از CPU usage بالا
                
            except Exception as e:
                print(f"خطا در پردازش صدای مداوم: {e}")
    
    def stop_listening(self):
        """توقف گوش دادن مداوم"""
        self.is_listening = False
    
    async def _process_audio(self, audio) -> Dict[str, Any]:
        """پردازش صدای دریافتی"""
        results = {}
        
        # تشخیص گفتار فارسی
        persian_result = await self._recognize_persian(audio)
        results["persian"] = persian_result
        
        # تشخیص گفتار انگلیسی
        english_result = await self._recognize_english(audio)
        results["english"] = english_result
        
        # انتخاب بهترین نتیجه
        best_result = self._select_best_result(results)
        
        return {
            "success": best_result is not None,
            "text": best_result["text"] if best_result else "",
            "language": best_result["language"] if best_result else "unknown",
            "confidence": best_result["confidence"] if best_result else 0.0,
            "all_results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _recognize_persian(self, audio) -> Dict[str, Any]:
        """تشخیص گفتار فارسی"""
        try:
            # استفاده از Google Speech Recognition برای فارسی
            text = self.recognizer.recognize_google(audio, language="fa-IR")
            
            return {
                "text": text,
                "language": "persian",
                "confidence": 0.8,  # Google API confidence نمی‌دهد
                "engine": "google"
            }
            
        except sr.UnknownValueError:
            return {"error": "Could not understand Persian audio"}
        except sr.RequestError as e:
            return {"error": f"Persian recognition service error: {e}"}
        except Exception as e:
            return {"error": f"Persian recognition error: {e}"}
    
    async def _recognize_english(self, audio) -> Dict[str, Any]:
        """تشخیص گفتار انگلیسی"""
        try:
            # استفاده از Google Speech Recognition برای انگلیسی
            text = self.recognizer.recognize_google(audio, language="en-US")
            
            return {
                "text": text,
                "language": "english",
                "confidence": 0.8,
                "engine": "google"
            }
            
        except sr.UnknownValueError:
            return {"error": "Could not understand English audio"}
        except sr.RequestError as e:
            return {"error": f"English recognition service error: {e}"}
        except Exception as e:
            return {"error": f"English recognition error: {e}"}
    
    def _select_best_result(self, results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """انتخاب بهترین نتیجه تشخیص"""
        valid_results = []
        
        for lang, result in results.items():
            if "text" in result and result["text"]:
                valid_results.append(result)
        
        if not valid_results:
            return None
        
        # انتخاب نتیجه با بالاترین confidence
        best_result = max(valid_results, key=lambda x: x.get("confidence", 0))
        
        return best_result
    
    def detect_wake_word(self, text: str) -> bool:
        """تشخیص کلمه بیدارکننده"""
        text_lower = text.lower()
        
        for wake_word in self.wake_words:
            if wake_word.lower() in text_lower:
                return True
        
        return False


class TextToSpeech(VoiceProcessor):
    """تبدیل متن به گفتار"""
    
    async def speak_text(self, text: str, language: str = "auto") -> Dict[str, Any]:
        """تبدیل متن به گفتار و پخش"""
        try:
            # تشخیص زبان خودکار
            if language == "auto":
                language = self._detect_text_language(text)
            
            # انتخاب روش TTS بر اساس زبان
            if language == "persian":
                return await self._speak_persian(text)
            else:
                return await self._speak_english(text)
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _detect_text_language(self, text: str) -> str:
        """تشخیص زبان متن"""
        import re
        
        # شمارش کاراکترهای فارسی
        persian_chars = len(re.findall(r'[\u0600-\u06FF]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        
        if persian_chars > english_chars:
            return "persian"
        else:
            return "english"
    
    async def _speak_persian(self, text: str) -> Dict[str, Any]:
        """گفتار فارسی"""
        try:
            # استفاده از gTTS برای فارسی
            tts = gTTS(text=text, lang='fa', slow=False)
            
            # ذخیره در فایل موقت
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                tts.save(tmp_file.name)
                
                # پخش فایل
                pygame.mixer.music.load(tmp_file.name)
                pygame.mixer.music.play()
                
                # انتظار تا پایان پخش
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.1)
                
                # پاک کردن فایل موقت
                os.unlink(tmp_file.name)
            
            return {"success": True, "language": "persian", "engine": "gtts"}
            
        except Exception as e:
            # در صورت خطا، استفاده از pyttsx3
            return await self._speak_with_pyttsx3(text)
    
    async def _speak_english(self, text: str) -> Dict[str, Any]:
        """گفتار انگلیسی"""
        try:
            # استفاده از gTTS برای انگلیسی
            tts = gTTS(text=text, lang='en', slow=False)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                tts.save(tmp_file.name)
                
                pygame.mixer.music.load(tmp_file.name)
                pygame.mixer.music.play()
                
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.1)
                
                os.unlink(tmp_file.name)
            
            return {"success": True, "language": "english", "engine": "gtts"}
            
        except Exception as e:
            # در صورت خطا، استفاده از pyttsx3
            return await self._speak_with_pyttsx3(text)
    
    async def _speak_with_pyttsx3(self, text: str) -> Dict[str, Any]:
        """گفتار با pyttsx3 (آفلاین)"""
        try:
            if self.tts_engine:
                # اجرای TTS در thread جداگانه
                def speak():
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                
                speak_thread = threading.Thread(target=speak)
                speak_thread.start()
                speak_thread.join()
                
                return {"success": True, "engine": "pyttsx3"}
            else:
                return {"success": False, "error": "TTS engine not available"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}


class VoiceAssistant:
    """دستیار صوتی کامل (مانند Bixby و Google Assistant)"""
    
    def __init__(self):
        self.speech_recognizer = SpeechRecognizer()
        self.tts = TextToSpeech()
        self.is_active = False
        self.conversation_history = []
    
    async def start_voice_assistant(self):
        """شروع دستیار صوتی"""
        self.is_active = True
        
        # پیام خوشامدگویی
        await self.tts.speak_text("سلام! من دستیار صوتی شما هستم. چطور می‌توانم کمک کنم؟")
        
        # شروع گوش دادن مداوم
        await self.speech_recognizer.continuous_listen(self._handle_voice_command)
    
    def stop_voice_assistant(self):
        """توقف دستیار صوتی"""
        self.is_active = False
        self.speech_recognizer.stop_listening()
    
    async def _handle_voice_command(self, recognition_result: Dict[str, Any]):
        """پردازش دستور صوتی"""
        if not recognition_result["success"]:
            return
        
        text = recognition_result["text"]
        language = recognition_result["language"]
        
        # بررسی کلمه بیدارکننده
        if not self.speech_recognizer.detect_wake_word(text):
            return
        
        print(f"دستور دریافت شد: {text} ({language})")
        
        # پردازش دستور
        response = await self._process_voice_command(text, language)
        
        # پاسخ صوتی
        if response:
            await self.tts.speak_text(response, language)
        
        # ذخیره در تاریخچه
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "user_input": text,
            "language": language,
            "response": response
        })
    
    async def _process_voice_command(self, text: str, language: str) -> str:
        """پردازش دستور صوتی و تولید پاسخ"""
        text_lower = text.lower()
        
        # دستورات سیستمی
        if any(word in text_lower for word in ["خاموش", "shutdown", "قفل", "lock"]):
            return "در حال اجرای دستور سیستمی..."
        
        # دستورات اپلیکیشن
        elif any(word in text_lower for word in ["باز کن", "open", "اجرا کن", "start"]):
            return "در حال باز کردن اپلیکیشن..."
        
        # سوالات عمومی
        elif any(word in text_lower for word in ["چی", "what", "چه", "کی", "when"]):
            return "در حال جستجو برای پاسخ شما..."
        
        # دستورات ترجمه
        elif any(word in text_lower for word in ["ترجمه", "translate"]):
            return "در حال ترجمه..."
        
        # پاسخ پیش‌فرض
        else:
            return "متوجه نشدم. می‌توانید دوباره بگویید؟"
    
    async def process_single_command(self, audio_file_path: str = None) -> Dict[str, Any]:
        """پردازش یک دستور صوتی از فایل یا میکروفون"""
        if audio_file_path:
            # پردازش از فایل صوتی
            return await self._process_audio_file(audio_file_path)
        else:
            # پردازش از میکروفون
            return await self.speech_recognizer.listen_once()
    
    async def _process_audio_file(self, file_path: str) -> Dict[str, Any]:
        """پردازش فایل صوتی"""
        try:
            with sr.AudioFile(file_path) as source:
                audio = self.speech_recognizer.recognizer.record(source)
            
            return await self.speech_recognizer._process_audio(audio)
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """دریافت تاریخچه مکالمات"""
        return self.conversation_history
    
    def clear_conversation_history(self):
        """پاک کردن تاریخچه مکالمات"""
        self.conversation_history.clear()
