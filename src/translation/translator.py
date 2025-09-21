"""
ماژول ترجمه پیشرفته (متنی و صوتی)
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
import requests
from googletrans import Translator as GoogleTranslator
import openai
from datetime import datetime
import re
import json

from config.settings import settings
from src.voice.speech_processor import VoiceAssistant


class AdvancedTranslator:
    """مترجم پیشرفته با قابلیت‌های متعدد"""
    
    def __init__(self):
        self.google_translator = GoogleTranslator()
        self.voice_assistant = VoiceAssistant()
        self.supported_languages = self._get_supported_languages()
        self.translation_history = []
        
        # تنظیم OpenAI در صورت وجود کلید
        if settings.openai_api_key:
            openai.api_key = settings.openai_api_key
    
    def _get_supported_languages(self) -> Dict[str, str]:
        """دریافت لیست زبان‌های پشتیبانی شده"""
        return {
            'fa': 'فارسی',
            'en': 'انگلیسی',
            'ar': 'عربی',
            'fr': 'فرانسوی',
            'de': 'آلمانی',
            'es': 'اسپانیایی',
            'it': 'ایتالیایی',
            'ru': 'روسی',
            'zh': 'چینی',
            'ja': 'ژاپنی',
            'ko': 'کره‌ای',
            'tr': 'ترکی',
            'ur': 'اردو',
            'hi': 'هندی'
        }
    
    async def translate_text(
        self, 
        text: str, 
        target_language: str, 
        source_language: str = 'auto',
        method: str = 'google'
    ) -> Dict[str, Any]:
        """ترجمه متن"""
        
        try:
            # تشخیص زبان مبدا در صورت نیاز
            if source_language == 'auto':
                detected_lang = await self._detect_language(text)
                source_language = detected_lang['language']
            
            # انتخاب روش ترجمه
            if method == 'google':
                result = await self._translate_with_google(text, target_language, source_language)
            elif method == 'openai' and settings.openai_api_key:
                result = await self._translate_with_openai(text, target_language, source_language)
            else:
                result = await self._translate_with_google(text, target_language, source_language)
            
            # ذخیره در تاریخچه
            self._save_translation_history(text, result, source_language, target_language, method)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "original_text": text,
                "source_language": source_language,
                "target_language": target_language
            }
    
    async def _translate_with_google(self, text: str, target_lang: str, source_lang: str) -> Dict[str, Any]:
        """ترجمه با Google Translate"""
        try:
            result = self.google_translator.translate(
                text, 
                dest=target_lang, 
                src=source_lang if source_lang != 'auto' else None
            )
            
            return {
                "success": True,
                "translated_text": result.text,
                "original_text": text,
                "source_language": result.src,
                "target_language": target_lang,
                "confidence": 0.9,  # Google doesn't provide confidence
                "method": "google",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Google Translate error: {str(e)}",
                "method": "google"
            }
    
    async def _translate_with_openai(self, text: str, target_lang: str, source_lang: str) -> Dict[str, Any]:
        """ترجمه با OpenAI GPT"""
        try:
            target_lang_name = self.supported_languages.get(target_lang, target_lang)
            source_lang_name = self.supported_languages.get(source_lang, source_lang)
            
            prompt = f"""
            لطفاً متن زیر را از {source_lang_name} به {target_lang_name} ترجمه کنید.
            فقط ترجمه را برگردانید، بدون توضیح اضافی.
            
            متن: {text}
            """
            
            response = await openai.ChatCompletion.acreate(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "شما یک مترجم حرفه‌ای هستید."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            translated_text = response.choices[0].message.content.strip()
            
            return {
                "success": True,
                "translated_text": translated_text,
                "original_text": text,
                "source_language": source_lang,
                "target_language": target_lang,
                "confidence": 0.95,
                "method": "openai",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"OpenAI translation error: {str(e)}",
                "method": "openai"
            }
    
    async def _detect_language(self, text: str) -> Dict[str, Any]:
        """تشخیص زبان متن"""
        try:
            result = self.google_translator.detect(text)
            
            return {
                "language": result.lang,
                "confidence": result.confidence,
                "language_name": self.supported_languages.get(result.lang, result.lang)
            }
            
        except Exception as e:
            # تشخیص ساده بر اساس کاراکتر
            return self._simple_language_detection(text)
    
    def _simple_language_detection(self, text: str) -> Dict[str, Any]:
        """تشخیص ساده زبان بر اساس کاراکتر"""
        persian_chars = len(re.findall(r'[\u0600-\u06FF]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        arabic_chars = len(re.findall(r'[\u0621-\u063A\u0641-\u064A]', text))
        
        total_chars = len(text.replace(' ', ''))
        
        if total_chars == 0:
            return {"language": "unknown", "confidence": 0.0}
        
        persian_ratio = persian_chars / total_chars
        english_ratio = english_chars / total_chars
        arabic_ratio = arabic_chars / total_chars
        
        if persian_ratio > 0.5:
            return {"language": "fa", "confidence": persian_ratio, "language_name": "فارسی"}
        elif english_ratio > 0.5:
            return {"language": "en", "confidence": english_ratio, "language_name": "انگلیسی"}
        elif arabic_ratio > 0.3:
            return {"language": "ar", "confidence": arabic_ratio, "language_name": "عربی"}
        else:
            return {"language": "unknown", "confidence": 0.5}
    
    async def voice_translate(
        self, 
        audio_input: str = None,  # مسیر فایل صوتی یا None برای میکروفون
        target_language: str = 'en',
        speak_result: bool = True
    ) -> Dict[str, Any]:
        """ترجمه صوتی"""
        
        try:
            # تشخیص گفتار
            if audio_input:
                speech_result = await self.voice_assistant.process_single_command(audio_input)
            else:
                speech_result = await self.voice_assistant.process_single_command()
            
            if not speech_result["success"]:
                return {
                    "success": False,
                    "error": "Speech recognition failed",
                    "speech_error": speech_result.get("error")
                }
            
            original_text = speech_result["text"]
            source_language = speech_result["language"]
            
            # ترجمه متن
            translation_result = await self.translate_text(
                original_text, 
                target_language, 
                source_language
            )
            
            if not translation_result["success"]:
                return translation_result
            
            # تبدیل به گفتار (در صورت درخواست)
            if speak_result:
                tts_result = await self.voice_assistant.tts.speak_text(
                    translation_result["translated_text"], 
                    target_language
                )
                translation_result["tts_result"] = tts_result
            
            return {
                "success": True,
                "original_speech": original_text,
                "translated_text": translation_result["translated_text"],
                "source_language": source_language,
                "target_language": target_language,
                "speech_recognition": speech_result,
                "translation": translation_result,
                "spoken": speak_result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Voice translation error: {str(e)}"
            }
    
    async def batch_translate(
        self, 
        texts: List[str], 
        target_language: str,
        source_language: str = 'auto'
    ) -> List[Dict[str, Any]]:
        """ترجمه دسته‌ای متن‌ها"""
        
        results = []
        
        for text in texts:
            result = await self.translate_text(text, target_language, source_language)
            results.append(result)
            
            # کمی تأخیر برای جلوگیری از محدودیت نرخ
            await asyncio.sleep(0.1)
        
        return results
    
    async def translate_document(
        self, 
        file_path: str, 
        target_language: str,
        output_path: str = None
    ) -> Dict[str, Any]:
        """ترجمه فایل"""
        
        try:
            # خواندن فایل
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # تقسیم به پاراگراف‌ها
            paragraphs = content.split('\n\n')
            
            # ترجمه هر پاراگراف
            translated_paragraphs = []
            
            for paragraph in paragraphs:
                if paragraph.strip():
                    result = await self.translate_text(paragraph, target_language)
                    
                    if result["success"]:
                        translated_paragraphs.append(result["translated_text"])
                    else:
                        translated_paragraphs.append(paragraph)  # حفظ متن اصلی در صورت خطا
                else:
                    translated_paragraphs.append(paragraph)
            
            # ترکیب پاراگراف‌های ترجمه شده
            translated_content = '\n\n'.join(translated_paragraphs)
            
            # ذخیره فایل ترجمه شده
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as file:
                    file.write(translated_content)
            
            return {
                "success": True,
                "original_file": file_path,
                "translated_content": translated_content,
                "output_file": output_path,
                "paragraph_count": len(paragraphs),
                "target_language": target_language
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Document translation error: {str(e)}",
                "file_path": file_path
            }
    
    def _save_translation_history(
        self, 
        original_text: str, 
        result: Dict[str, Any], 
        source_lang: str, 
        target_lang: str, 
        method: str
    ):
        """ذخیره تاریخچه ترجمه"""
        
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "original_text": original_text,
            "translated_text": result.get("translated_text", ""),
            "source_language": source_lang,
            "target_language": target_lang,
            "method": method,
            "success": result.get("success", False),
            "confidence": result.get("confidence", 0.0)
        }
        
        self.translation_history.append(history_entry)
        
        # حفظ فقط 1000 ترجمه آخر
        if len(self.translation_history) > 1000:
            self.translation_history = self.translation_history[-1000:]
    
    def get_translation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """دریافت تاریخچه ترجمه"""
        return self.translation_history[-limit:]
    
    def clear_translation_history(self):
        """پاک کردن تاریخچه ترجمه"""
        self.translation_history.clear()
    
    async def get_language_suggestions(self, text: str) -> List[Dict[str, Any]]:
        """پیشنهاد زبان‌های مناسب برای ترجمه"""
        
        # تشخیص زبان اصلی
        detected = await self._detect_language(text)
        source_lang = detected["language"]
        
        # پیشنهاد زبان‌های رایج
        common_targets = {
            'fa': ['en', 'ar', 'tr', 'ur'],  # از فارسی
            'en': ['fa', 'ar', 'es', 'fr', 'de'],  # از انگلیسی
            'ar': ['fa', 'en', 'ur', 'tr']  # از عربی
        }
        
        suggested_langs = common_targets.get(source_lang, ['en', 'fa'])
        
        suggestions = []
        for lang_code in suggested_langs:
            if lang_code != source_lang:
                suggestions.append({
                    "code": lang_code,
                    "name": self.supported_languages.get(lang_code, lang_code),
                    "confidence": 0.8
                })
        
        return suggestions
    
    async def smart_translate(self, text: str, context: str = None) -> Dict[str, Any]:
        """ترجمه هوشمند با در نظر گیری زمینه"""
        
        # تشخیص زبان
        detected = await self._detect_language(text)
        source_lang = detected["language"]
        
        # انتخاب زبان هدف بر اساس زمینه
        if source_lang == 'fa':
            target_lang = 'en'  # فارسی به انگلیسی
        elif source_lang == 'en':
            target_lang = 'fa'  # انگلیسی به فارسی
        else:
            target_lang = 'en'  # سایر زبان‌ها به انگلیسی
        
        # ترجمه با روش بهتر (OpenAI اگر موجود باشد)
        method = 'openai' if settings.openai_api_key else 'google'
        
        result = await self.translate_text(text, target_lang, source_lang, method)
        
        # اضافه کردن اطلاعات هوشمند
        result["smart_features"] = {
            "auto_detected_source": source_lang,
            "auto_selected_target": target_lang,
            "context_considered": context is not None,
            "method_used": method
        }
        
        return result
