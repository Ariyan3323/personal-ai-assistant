"""
ماژول تحلیل روانشناختی و شخصیت‌شناسی
تشخیص شخصیت از گفتار و نوشتار، مشاوره روحی و آرامش‌بخش
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import openai
import re
from collections import Counter
from textblob import TextBlob

from config.settings import settings
from src.core.multi_ai_engine import TaskType


class PersonalityAnalyzer:
    """تحلیلگر شخصیت از متن و گفتار"""
    
    def __init__(self):
        self.openai_available = bool(settings.openai_api_key)
        if self.openai_available:
            openai.api_key = settings.openai_api_key
        self.personality_traits = [
            "Openness", "Conscientiousness", "Extraversion", 
            "Agreeableness", "Neuroticism"
        ] # Big Five personality traits
        self.sentiment_history = []
    
    async def analyze_text_personality(
        self, 
        text: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """تحلیل شخصیت از متن"""
        
        try:
            if not self.openai_available:
                return {
                    "success": False,
                    "error": "OpenAI API key not configured for personality analysis."
                }
            
            prompt = f"""
            متن زیر را تحلیل کنید و ویژگی‌های شخصیتی نویسنده را بر اساس مدل Big Five (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism) تخمین بزنید.
            همچنین، لحن (tone) و احساسات (sentiment) کلی متن را مشخص کنید.
            در نهایت، یک ارزیابی کلی از شخصیت نویسنده ارائه دهید و اگر به نظر می‌رسد نویسنده دروغ می‌گوید یا قصد فریب دارد، آن را ذکر کنید.
            
            متن: {text}
            
            فرمت پاسخ:
            {{ "personality_traits": {{ "Openness": float (0-1), ... }}, "tone": "string", "sentiment": "string", "deception_risk": float (0-1), "overall_assessment": "string" }}
            """
            
            messages = [
                {"role": "system", "content": "شما یک روانشناس و تحلیلگر شخصیت حرفه‌ای هستید."},
                {"role": "user", "content": prompt}
            ]
            
            response = await openai.ChatCompletion.acreate(
                model=settings.openai_model,
                messages=messages,
                max_tokens=1000,
                temperature=0.3
            )
            
            analysis_str = response.choices[0].message.content.strip()
            
            try:
                analysis_json = json.loads(analysis_str)
                success = True
            except json.JSONDecodeError:
                analysis_json = {"overall_assessment": analysis_str}
                success = False
            
            # تحلیل احساسات با TextBlob به عنوان پشتیبان
            blob = TextBlob(text)
            sentiment_polarity = blob.sentiment.polarity
            sentiment_subjectivity = blob.sentiment.subjectivity
            
            sentiment_label = "neutral"
            if sentiment_polarity > 0.1:
                sentiment_label = "positive"
            elif sentiment_polarity < -0.1:
                sentiment_label = "negative"
            
            # ذخیره در تاریخچه احساسات
            self.sentiment_history.append({
                "timestamp": datetime.now().isoformat(),
                "text": text,
                "polarity": sentiment_polarity,
                "subjectivity": sentiment_subjectivity,
                "label": sentiment_label
            })
            
            return {
                "success": success,
                "analysis": analysis_json,
                "text_sentiment": {
                    "polarity": sentiment_polarity,
                    "subjectivity": sentiment_subjectivity,
                    "label": sentiment_label
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Personality analysis error: {str(e)}",
                "text": text
            }
    
    async def analyze_voice_personality(
        self, 
        audio_file_path: str
    ) -> Dict[str, Any]:
        """تحلیل شخصیت از گفتار (نیاز به تبدیل گفتار به متن)"""
        
        # این تابع نیاز به ماژول SpeechRecognizer دارد تا صوت را به متن تبدیل کند
        # سپس متن به analyze_text_personality ارسال می‌شود
        
        return {
            "success": False,
            "error": "Voice personality analysis requires speech-to-text conversion first."
        }
    
    async def provide_psychological_consultation(
        self, 
        user_concern: str,
        conversation_history: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """ارائه مشاوره روانشناختی"""
        
        try:
            if not self.openai_available:
                return {
                    "success": False,
                    "error": "OpenAI API key not configured for psychological consultation."
                }
            
            system_prompt = """
            شما یک مشاور روانشناس بسیار دلسوز، همدل و با تجربه هستید.
            هدف شما کمک به کاربر برای مدیریت احساسات، کاهش استرس، و بهبود سلامت روان است.
            با دقت به نگرانی‌های کاربر گوش دهید، همدلی نشان دهید، و راهکارهای عملی و آرامش‌بخش ارائه دهید.
            همیشه به یاد داشته باشید که شما یک هوش مصنوعی هستید و نمی‌توانید جایگزین درمانگر انسانی شوید، اما می‌توانید حمایت و راهنمایی اولیه ارائه دهید.
            """
            
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            if conversation_history:
                for entry in conversation_history:
                    messages.append({"role": "user", "content": entry["user_input"]})
                    messages.append({"role": "assistant", "content": entry["response"]["content"]})
            
            messages.append({"role": "user", "content": user_concern})
            
            response = await openai.ChatCompletion.acreate(
                model=settings.openai_model,
                messages=messages,
                max_tokens=1500,
                temperature=0.7
            )
            
            consultation_text = response.choices[0].message.content.strip()
            
            return {
                "success": True,
                "consultation": consultation_text,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Psychological consultation error: {str(e)}",
                "user_concern": user_concern
            }
    
    async def provide_calming_session(
        self, 
        session_type: str = "breathing",
        duration_minutes: int = 5
    ) -> Dict[str, Any]:
        """ارائه جلسه آرامش‌بخش (مدیتیشن، تنفس)"""
        
        try:
            if not self.openai_available:
                return {
                    "success": False,
                    "error": "OpenAI API key not configured for calming sessions."
                }
            
            prompts = {
                "breathing": f"""
                یک اسکریپت 5 دقیقه‌ای برای تمرین تنفس عمیق و آرامش‌بخش بنویسید.
                شامل دستورالعمل‌های واضح برای دم و بازدم، و تمرکز بر لحظه حال باشد.
                با لحنی آرام و دلنشین صحبت کنید.
                """,
                "mindfulness": f"""
                یک اسکریپت 5 دقیقه‌ای برای تمرین ذهن‌آگاهی (mindfulness) بنویسید.
                کاربر را به تمرکز بر حواس پنج‌گانه و مشاهده افکار بدون قضاوت هدایت کنید.
                با لحنی آرام و دلنشین صحبت کنید.
                """,
                "guided_meditation": f"""
                یک اسکریپت 5 دقیقه‌ای برای مدیتیشن هدایت‌شده بنویسید.
                کاربر را به مکانی آرام و امن در ذهن خود هدایت کنید.
                با لحنی آرام و دلنشین صحبت کنید.
                """
            }
            
            selected_prompt = prompts.get(session_type, prompts["breathing"])
            
            messages = [
                {"role": "system", "content": "شما یک مربی مدیتیشن و آرامش هستید که اسکریپت‌های آرامش‌بخش تولید می‌کنید."},
                {"role": "user", "content": selected_prompt}
            ]
            
            response = await openai.ChatCompletion.acreate(
                model=settings.openai_model,
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            session_script = response.choices[0].message.content.strip()
            
            return {
                "success": True,
                "session_type": session_type,
                "duration_minutes": duration_minutes,
                "script": session_script,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Calming session error: {str(e)}",
                "session_type": session_type
            }
    
    def get_sentiment_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """دریافت تاریخچه تحلیل احساسات"""
        return self.sentiment_history[-limit:]
    
    def get_personality_traits_description(self) -> Dict[str, str]:
        """توضیح ویژگی‌های شخصیتی Big Five"""
        return {
            "Openness": "میزان کنجکاوی، خلاقیت و تمایل به تجربیات جدید.",
            "Conscientiousness": "میزان سازمان‌یافتگی، مسئولیت‌پذیری و خودانضباطی.",
            "Extraversion": "میزان برون‌گرایی، اجتماعی بودن و انرژی.",
            "Agreeableness": "میزان همکاری، همدلی و مهربانی.",
            "Neuroticism": "میزان ثبات عاطفی، اضطراب و حساسیت."
        }
