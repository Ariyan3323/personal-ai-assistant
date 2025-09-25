"""
هسته مرکزی چندگانه هوش مصنوعی
ترکیب چندین مدل AI برای قابلیت‌های مختلف
"""

import asyncio
import openai
import google.generativeai as genai
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum
import json
import random
from dataclasses import dataclass

from config.settings import settings


class AIModel(Enum):
    """انواع مدل‌های هوش مصنوعی"""
    GPT4 = "gpt-4"
    GPT35_TURBO = "gpt-3.5-turbo"
    GEMINI_PRO = "gemini-pro"
    CLAUDE = "claude-3"
    LLAMA2 = "llama-2-70b"
    T5 = "t5-large"


class TaskType(Enum):
    """انواع وظایف"""
    CONVERSATION = "conversation"
    CONTENT_GENERATION = "content_generation"
    FINANCIAL_ADVICE = "financial_advice"
    PSYCHOLOGICAL_SUPPORT = "psychological_support"
    CREATIVE_WRITING = "creative_writing"
    TECHNICAL_ANALYSIS = "technical_analysis"
    TRANSLATION = "translation"
    RESEARCH = "research"
    MEDITATION = "meditation"
    COMPANIONSHIP = "companionship"


@dataclass
class PersonalityProfile:
    """پروفایل شخصیت دستیار"""
    gender: str  # "male", "female", "neutral"
    name: str
    personality_traits: List[str]
    communication_style: str
    expertise_areas: List[str]
    emotional_intelligence: float
    humor_level: float
    formality_level: float
    empathy_level: float


class MultiAIEngine:
    """موتور چندگانه هوش مصنوعی"""
    
    def __init__(self):
        self.models = {}
        self.personality = None
        self.conversation_history = []
        self.user_preferences = {}
        self.model_performance = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """راه‌اندازی مدل‌های مختلف"""
        
        # OpenAI GPT Models
        if settings.openai_api_key:
            openai.api_key = settings.openai_api_key
            self.models[AIModel.GPT4] = {
                "client": openai,
                "available": True,
                "specialties": [TaskType.CONVERSATION, TaskType.CONTENT_GENERATION, TaskType.RESEARCH],
                "performance_score": 0.95
            }
            self.models[AIModel.GPT35_TURBO] = {
                "client": openai,
                "available": True,
                "specialties": [TaskType.CONVERSATION, TaskType.TRANSLATION],
                "performance_score": 0.85
            }
        
        # Google Gemini
        if hasattr(settings, 'google_api_key') and settings.google_api_key:
            genai.configure(api_key=settings.google_api_key)
            self.models[AIModel.GEMINI_PRO] = {
                "client": genai,
                "available": True,
                "specialties": [TaskType.CREATIVE_WRITING, TaskType.TECHNICAL_ANALYSIS],
                "performance_score": 0.90
            }
        
        # مدل‌های محلی (شبیه‌سازی)
        self.models[AIModel.LLAMA2] = {
            "client": None,  # باید با Ollama یا HuggingFace پیاده‌سازی شود
            "available": False,
            "specialties": [TaskType.CONVERSATION, TaskType.RESEARCH],
            "performance_score": 0.80
        }
        
        self.models[AIModel.T5] = {
            "client": None,
            "available": False,
            "specialties": [TaskType.TRANSLATION, TaskType.CONTENT_GENERATION],
            "performance_score": 0.75
        }
    
    def setup_personality(
        self, 
        gender: str = "neutral",
        name: str = None,
        personality_type: str = "friendly"
    ) -> PersonalityProfile:
        """تنظیم شخصیت دستیار"""
        
        # انتخاب نام بر اساس جنسیت
        if not name:
            if gender == "female":
                names = ["آریا", "نیلا", "سارا", "مهرناز", "الهام", "Aria", "Luna", "Sophie"]
            elif gender == "male":
                names = ["آرش", "کیان", "امیر", "پویا", "سینا", "Alex", "Max", "David"]
            else:
                names = ["آی", "هوشیار", "دانا", "AI", "Assistant", "Helper"]
            
            name = random.choice(names)
        
        # تعریف ویژگی‌های شخصیتی
        personality_configs = {
            "friendly": {
                "traits": ["دوستانه", "مهربان", "صبور", "کمک‌کار"],
                "communication_style": "گرم و صمیمی",
                "empathy_level": 0.9,
                "humor_level": 0.7,
                "formality_level": 0.3
            },
            "professional": {
                "traits": ["حرفه‌ای", "دقیق", "قابل اعتماد", "کارآمد"],
                "communication_style": "رسمی و مؤدبانه",
                "empathy_level": 0.6,
                "humor_level": 0.3,
                "formality_level": 0.8
            },
            "companion": {
                "traits": ["رفیق", "درک‌کننده", "حمایت‌گر", "آرام‌بخش"],
                "communication_style": "صمیمی و حمایت‌کننده",
                "empathy_level": 0.95,
                "humor_level": 0.8,
                "formality_level": 0.2
            }
        }
        
        config = personality_configs.get(personality_type, personality_configs["friendly"])
        
        self.personality = PersonalityProfile(
            gender=gender,
            name=name,
            personality_traits=config["traits"],
            communication_style=config["communication_style"],
            expertise_areas=[
                "مکالمه عمومی", "مشاوره", "تولید محتوا", "تحلیل مالی",
                "حمایت روانی", "آموزش", "سرگرمی"
            ],
            emotional_intelligence=config["empathy_level"],
            humor_level=config["humor_level"],
            formality_level=config["formality_level"],
            empathy_level=config["empathy_level"]
        )
        
        return self.personality
    
    async def process_request(
        self, 
        user_input: str, 
        task_type: TaskType = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """پردازش درخواست کاربر"""
        
        # تشخیص نوع وظیفه در صورت عدم مشخص بودن
        if not task_type:
            task_type = await self._detect_task_type(user_input)
        
        # انتخاب بهترین مدل برای وظیفه
        selected_model = self._select_best_model(task_type)
        
        # پردازش با مدل انتخاب شده
        result = await self._process_with_model(
            selected_model, 
            user_input, 
            task_type, 
            context
        )
        
        # اعمال شخصیت به پاسخ
        personalized_result = await self._apply_personality(result, task_type)
        
        # ذخیره در تاریخچه
        self._save_to_history(user_input, personalized_result, task_type, selected_model)
        
        return personalized_result
    
    async def _detect_task_type(self, user_input: str) -> TaskType:
        """تشخیص نوع وظیفه از ورودی کاربر"""
        
        input_lower = user_input.lower()
        
        # کلمات کلیدی برای هر نوع وظیفه
        task_keywords = {
            TaskType.FINANCIAL_ADVICE: [
                'سهام', 'بورس', 'ارز', 'بیت کوین', 'تریدینگ', 'سرمایه‌گذاری',
                'stock', 'crypto', 'bitcoin', 'trading', 'investment'
            ],
            TaskType.PSYCHOLOGICAL_SUPPORT: [
                'غمگین', 'استرس', 'اضطراب', 'مشکل', 'نگران', 'افسرده',
                'sad', 'stress', 'anxiety', 'worried', 'depressed', 'help me'
            ],
            TaskType.CREATIVE_WRITING: [
                'داستان', 'شعر', 'نوشتن', 'خلاقیت', 'متن',
                'story', 'poem', 'write', 'creative', 'content'
            ],
            TaskType.TRANSLATION: [
                'ترجمه', 'translate', 'معنی', 'meaning'
            ],
            TaskType.MEDITATION: [
                'آرامش', 'مدیتیشن', 'تنفس', 'آرام', 'استراحت',
                'meditation', 'relax', 'calm', 'peace', 'breathe'
            ],
            TaskType.RESEARCH: [
                'تحقیق', 'جستجو', 'اطلاعات', 'یاد بگیر', 'بگو',
                'research', 'search', 'information', 'learn', 'tell me'
            ]
        }
        
        # امتیازدهی به هر نوع وظیفه
        task_scores = {}
        for task_type, keywords in task_keywords.items():
            score = sum(1 for keyword in keywords if keyword in input_lower)
            if score > 0:
                task_scores[task_type] = score
        
        # انتخاب وظیفه با بالاترین امتیاز
        if task_scores:
            return max(task_scores, key=task_scores.get)
        
        # پیش‌فرض: مکالمه عمومی
        return TaskType.CONVERSATION
    
    def _select_best_model(self, task_type: TaskType) -> AIModel:
        """انتخاب بهترین مدل برای وظیفه"""
        
        # مدل‌های مناسب برای هر وظیفه
        suitable_models = []
        
        for model, info in self.models.items():
            if (info["available"] and 
                task_type in info["specialties"]):
                suitable_models.append((model, info["performance_score"]))
        
        if suitable_models:
            # انتخاب مدل با بالاترین عملکرد
            return max(suitable_models, key=lambda x: x[1])[0]
        
        # اگر مدل مناسبی یافت نشد، از GPT-3.5 استفاده کن
        return AIModel.GPT35_TURBO if AIModel.GPT35_TURBO in self.models else list(self.models.keys())[0]
    
    async def _process_with_model(
        self, 
        model: AIModel, 
        user_input: str, 
        task_type: TaskType,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """پردازش با مدل مشخص"""
        
        try:
            if model in [AIModel.GPT4, AIModel.GPT35_TURBO]:
                return await self._process_with_openai(model, user_input, task_type, context)
            
            elif model == AIModel.GEMINI_PRO:
                return await self._process_with_gemini(user_input, task_type, context)
            
            else:
                # برای مدل‌های دیگر، از GPT استفاده کن
                return await self._process_with_openai(AIModel.GPT35_TURBO, user_input, task_type, context)
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "fallback_response": "متأسفم، در حال حاضر مشکلی در پردازش درخواست شما وجود دارد."
            }
    
    async def _process_with_openai(
        self, 
        model: AIModel, 
        user_input: str, 
        task_type: TaskType,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """پردازش با مدل‌های OpenAI"""
        
        # تنظیم system prompt بر اساس نوع وظیفه
        system_prompts = {
            TaskType.CONVERSATION: "شما یک دستیار هوشمند و دوستانه هستید که با کاربران به صورت طبیعی گفتگو می‌کنید.",
            TaskType.FINANCIAL_ADVICE: "شما یک مشاور مالی حرفه‌ای هستید که در زمینه سرمایه‌گذاری، بورس و ارزهای دیجیتال تخصص دارید.",
            TaskType.PSYCHOLOGICAL_SUPPORT: "شما یک مشاور روانی دلسوز و درک‌کننده هستید که به افراد کمک می‌کنید احساسات خود را مدیریت کنند.",
            TaskType.CREATIVE_WRITING: "شما یک نویسنده خلاق و با تجربه هستید که در تولید محتوای جذاب و خلاقانه مهارت دارید.",
            TaskType.MEDITATION: "شما یک مربی مدیتیشن و آرامش هستید که به افراد کمک می‌کنید آرامش پیدا کنند.",
            TaskType.RESEARCH: "شما یک محقق دقیق و کارآمد هستید که اطلاعات جامع و قابل اعتماد ارائه می‌دهید."
        }
        
        system_prompt = system_prompts.get(task_type, system_prompts[TaskType.CONVERSATION])
        
        # اضافه کردن اطلاعات شخصیت
        if self.personality:
            personality_info = f"""
            نام شما {self.personality.name} است و جنسیت شما {self.personality.gender} است.
            ویژگی‌های شخصیتی شما: {', '.join(self.personality.personality_traits)}
            سبک ارتباطی شما: {self.personality.communication_style}
            """
            system_prompt += personality_info
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        # اضافه کردن تاریخچه مکالمه
        if len(self.conversation_history) > 0:
            recent_history = self.conversation_history[-5:]  # 5 پیام آخر
            for entry in recent_history:
                messages.insert(-1, {"role": "user", "content": entry["user_input"]})
                messages.insert(-1, {"role": "assistant", "content": entry["response"]["content"]})
        
        response = await openai.ChatCompletion.acreate(
            model=model.value,
            messages=messages,
            max_tokens=1000,
            temperature=0.7 if task_type == TaskType.CREATIVE_WRITING else 0.5,
            top_p=0.9
        )
        
        return {
            "success": True,
            "content": response.choices[0].message.content,
            "model_used": model.value,
            "task_type": task_type.value,
            "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else 0
        }
    
    async def _process_with_gemini(
        self, 
        user_input: str, 
        task_type: TaskType,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """پردازش با Gemini"""
        
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = await model.generate_content_async(user_input)
            
            return {
                "success": True,
                "content": response.text,
                "model_used": "gemini-pro",
                "task_type": task_type.value
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Gemini error: {str(e)}"
            }
    
    async def _apply_personality(
        self, 
        result: Dict[str, Any], 
        task_type: TaskType
    ) -> Dict[str, Any]:
        """اعمال شخصیت به پاسخ"""
        
        if not result.get("success") or not self.personality:
            return result
        
        content = result["content"]
        
        # تنظیم سبک بر اساس شخصیت
        if self.personality.formality_level < 0.5:
            # سبک غیررسمی و دوستانه
            if not any(greeting in content.lower() for greeting in ["سلام", "hello", "hi"]):
                if random.random() < 0.3:  # 30% احتمال
                    friendly_starters = ["راستش", "ببین", "خب", "Well", "So"]
                    content = f"{random.choice(friendly_starters)}, {content}"
        
        # اضافه کردن عناصر احساسی
        if (task_type == TaskType.PSYCHOLOGICAL_SUPPORT and 
            self.personality.empathy_level > 0.8):
            empathy_phrases = [
                "درکت می‌کنم", "حست رو می‌فهمم", "I understand how you feel",
                "این واقعاً سخته", "You're not alone in this"
            ]
            if random.random() < 0.4:
                content = f"{random.choice(empathy_phrases)}. {content}"
        
        # اضافه کردن طنز (در صورت مناسب بودن)
        if (self.personality.humor_level > 0.6 and 
            task_type in [TaskType.CONVERSATION, TaskType.CREATIVE_WRITING] and
            random.random() < 0.2):
            # اضافه کردن عنصر طنز ملایم
            pass  # پیاده‌سازی در آینده
        
        result["content"] = content
        result["personality_applied"] = True
        result["personality_name"] = self.personality.name
        
        return result
    
    def _save_to_history(
        self, 
        user_input: str, 
        response: Dict[str, Any], 
        task_type: TaskType, 
        model_used: AIModel
    ):
        """ذخیره در تاریخچه مکالمه"""
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "response": response,
            "task_type": task_type.value,
            "model_used": model_used.value,
            "success": response.get("success", False)
        }
        
        self.conversation_history.append(entry)
        
        # حفظ فقط 100 مکالمه آخر
        if len(self.conversation_history) > 100:
            self.conversation_history = self.conversation_history[-100:]
    
    async def get_specialized_response(
        self, 
        specialty: str, 
        query: str,
        additional_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """دریافت پاسخ تخصصی"""
        
        specialty_configs = {
            "financial_advisor": {
                "task_type": TaskType.FINANCIAL_ADVICE,
                "system_prompt": """شما یک مشاور مالی حرفه‌ای با 10 سال تجربه هستید.
                تخصص شما در تحلیل بازار سهام، ارزهای دیجیتال، و استراتژی‌های سرمایه‌گذاری است.
                همیشه ریسک‌ها را توضیح دهید و توصیه‌های محافظه‌کارانه ارائه دهید."""
            },
            "therapist": {
                "task_type": TaskType.PSYCHOLOGICAL_SUPPORT,
                "system_prompt": """شما یک روانشناس مجرب و دلسوز هستید.
                با همدلی و درک عمیق به مشکلات افراد گوش می‌دهید.
                تکنیک‌های عملی برای مدیریت استرس و بهبود سلامت روان ارائه می‌دهید."""
            },
            "creative_writer": {
                "task_type": TaskType.CREATIVE_WRITING,
                "system_prompt": """شما یک نویسنده خلاق و با تجربه هستید.
                در تولید داستان، شعر، و محتوای جذاب مهارت فوق‌العاده‌ای دارید.
                از زبان زیبا و تصاویر قوی استفاده می‌کنید."""
            },
            "meditation_guide": {
                "task_type": TaskType.MEDITATION,
                "system_prompt": """شما یک مربی مدیتیشن و mindfulness هستید.
                تکنیک‌های آرام‌سازی، تنفس، و تمرینات ذهن‌آگاهی را آموزش می‌دهید.
                صدای آرام و دلنشینی دارید که به آرامش افراد کمک می‌کند."""
            }
        }
        
        config = specialty_configs.get(specialty)
        if not config:
            return {"success": False, "error": "Specialty not found"}
        
        return await self.process_request(query, config["task_type"], additional_context)
    
    def get_personality_info(self) -> Dict[str, Any]:
        """دریافت اطلاعات شخصیت"""
        if not self.personality:
            return {"error": "No personality configured"}
        
        return {
            "name": self.personality.name,
            "gender": self.personality.gender,
            "traits": self.personality.personality_traits,
            "communication_style": self.personality.communication_style,
            "expertise_areas": self.personality.expertise_areas,
            "emotional_intelligence": self.personality.emotional_intelligence,
            "humor_level": self.personality.humor_level,
            "formality_level": self.personality.formality_level
        }
    
    def get_available_models(self) -> Dict[str, Any]:
        """دریافت لیست مدل‌های در دسترس"""
        return {
            model.value: {
                "available": info["available"],
                "specialties": [s.value for s in info["specialties"]],
                "performance_score": info["performance_score"]
            }
            for model, info in self.models.items()
        }
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """آمار مکالمات"""
        if not self.conversation_history:
            return {"total_conversations": 0}
        
        task_counts = {}
        model_usage = {}
        success_rate = 0
        
        for entry in self.conversation_history:
            task_type = entry["task_type"]
            model_used = entry["model_used"]
            
            task_counts[task_type] = task_counts.get(task_type, 0) + 1
            model_usage[model_used] = model_usage.get(model_used, 0) + 1
            
            if entry["success"]:
                success_rate += 1
        
        success_rate = success_rate / len(self.conversation_history) * 100
        
        return {
            "total_conversations": len(self.conversation_history),
            "task_distribution": task_counts,
            "model_usage": model_usage,
            "success_rate": f"{success_rate:.1f}%",
            "most_used_task": max(task_counts, key=task_counts.get) if task_counts else None,
            "most_used_model": max(model_usage, key=model_usage.get) if model_usage else None
        }
