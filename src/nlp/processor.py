"""
ماژول پردازش زبان طبیعی (NLP)
"""

import re
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import spacy
from transformers import pipeline, AutoTokenizer, AutoModel
import torch
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings

from config.settings import settings


class NLPProcessor:
    """کلاس اصلی پردازش زبان طبیعی"""
    
    def __init__(self):
        self.sentiment_analyzer = None
        self.embeddings_model = None
        self.spacy_model = None
        self.text_splitter = None
        self._initialize_models()
    
    def _initialize_models(self):
        """راه‌اندازی مدل‌های NLP"""
        try:
            # مدل تحلیل احساسات
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                return_all_scores=True
            )
            
            # مدل embeddings برای فارسی و انگلیسی
            self.embeddings_model = HuggingFaceEmbeddings(
                model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            )
            
            # مدل spaCy برای پردازش متن
            try:
                self.spacy_model = spacy.load("en_core_web_sm")
            except OSError:
                # در صورت عدم وجود مدل، از مدل پایه استفاده می‌کنیم
                self.spacy_model = None
            
            # تقسیم‌کننده متن
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
            )
            
        except Exception as e:
            print(f"خطا در راه‌اندازی مدل‌های NLP: {e}")
    
    async def process_message(
        self, 
        message: str, 
        user_id: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """پردازش کامل یک پیام"""
        
        result = {
            "original_text": message,
            "processed_at": datetime.now().isoformat(),
            "user_id": user_id,
            "context": context or {}
        }
        
        # پاکسازی متن
        cleaned_text = self._clean_text(message)
        result["cleaned_text"] = cleaned_text
        
        # تشخیص زبان
        language = self._detect_language(cleaned_text)
        result["language"] = language
        
        # تحلیل احساسات
        sentiment = await self._analyze_sentiment(cleaned_text)
        result["sentiment"] = sentiment
        
        # استخراج موجودیت‌ها
        entities = self._extract_entities(cleaned_text)
        result["entities"] = entities
        
        # تشخیص قصد (Intent Detection)
        intent = self._detect_intent(cleaned_text)
        result["intent"] = intent
        
        # استخراج کلمات کلیدی
        keywords = self._extract_keywords(cleaned_text)
        result["keywords"] = keywords
        
        # تولید embedding
        embedding = await self._generate_embedding(cleaned_text)
        result["embedding"] = embedding
        
        # تحلیل پیچیدگی
        complexity = self._analyze_complexity(cleaned_text)
        result["complexity"] = complexity
        
        return result
    
    def _clean_text(self, text: str) -> str:
        """پاکسازی متن از کاراکترهای غیرضروری"""
        # حذف کاراکترهای اضافی
        text = re.sub(r'\s+', ' ', text)  # چندین فاصله به یک فاصله
        text = re.sub(r'[^\w\s\u0600-\u06FF\u200C\u200D]', ' ', text)  # حفظ فارسی و انگلیسی
        text = text.strip()
        
        return text
    
    def _detect_language(self, text: str) -> str:
        """تشخیص زبان متن"""
        # تشخیص ساده بر اساس کاراکترهای فارسی
        persian_chars = len(re.findall(r'[\u0600-\u06FF]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        
        if persian_chars > english_chars:
            return "persian"
        elif english_chars > persian_chars:
            return "english"
        else:
            return "mixed"
    
    async def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """تحلیل احساسات متن"""
        try:
            if self.sentiment_analyzer:
                results = self.sentiment_analyzer(text)
                
                # پردازش نتایج
                sentiment_scores = {}
                for result in results[0]:
                    sentiment_scores[result['label'].lower()] = result['score']
                
                # تعیین احساس غالب
                dominant_sentiment = max(sentiment_scores, key=sentiment_scores.get)
                confidence = sentiment_scores[dominant_sentiment]
                
                return {
                    "dominant": dominant_sentiment,
                    "confidence": confidence,
                    "scores": sentiment_scores
                }
            else:
                return {"dominant": "neutral", "confidence": 0.5, "scores": {}}
                
        except Exception as e:
            return {"error": str(e), "dominant": "neutral", "confidence": 0.0}
    
    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """استخراج موجودیت‌های نامدار"""
        entities = []
        
        try:
            if self.spacy_model:
                doc = self.spacy_model(text)
                
                for ent in doc.ents:
                    entities.append({
                        "text": ent.text,
                        "label": ent.label_,
                        "start": ent.start_char,
                        "end": ent.end_char,
                        "confidence": 1.0  # spaCy doesn't provide confidence scores by default
                    })
            
            # استخراج ساده برای فارسی (الگوهای رایج)
            persian_entities = self._extract_persian_entities(text)
            entities.extend(persian_entities)
            
        except Exception as e:
            print(f"خطا در استخراج موجودیت‌ها: {e}")
        
        return entities
    
    def _extract_persian_entities(self, text: str) -> List[Dict[str, Any]]:
        """استخراج موجودیت‌های فارسی با الگوهای ساده"""
        entities = []
        
        # الگوهای تاریخ فارسی
        date_pattern = r'\d{4}/\d{1,2}/\d{1,2}'
        dates = re.finditer(date_pattern, text)
        for match in dates:
            entities.append({
                "text": match.group(),
                "label": "DATE",
                "start": match.start(),
                "end": match.end(),
                "confidence": 0.9
            })
        
        # الگوهای شماره تلفن
        phone_pattern = r'09\d{9}'
        phones = re.finditer(phone_pattern, text)
        for match in phones:
            entities.append({
                "text": match.group(),
                "label": "PHONE",
                "start": match.start(),
                "end": match.end(),
                "confidence": 0.95
            })
        
        return entities
    
    def _detect_intent(self, text: str) -> Dict[str, Any]:
        """تشخیص قصد کاربر"""
        # الگوهای ساده برای تشخیص قصد
        intents = {
            "question": [r'\?', r'چی', r'چه', r'کی', r'کجا', r'چرا', r'چگونه', r'what', r'when', r'where', r'why', r'how'],
            "request": [r'لطفا', r'می‌توانی', r'کمک', r'please', r'can you', r'help'],
            "greeting": [r'سلام', r'درود', r'hello', r'hi', r'صبح بخیر', r'good morning'],
            "goodbye": [r'خداحافظ', r'بای', r'goodbye', r'bye', r'تا بعد'],
            "search": [r'جستجو', r'پیدا کن', r'search', r'find', r'look for'],
            "information": [r'اطلاعات', r'بگو', r'توضیح', r'information', r'tell me', r'explain']
        }
        
        text_lower = text.lower()
        detected_intents = {}
        
        for intent, patterns in intents.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower))
                score += matches
            
            if score > 0:
                detected_intents[intent] = score / len(patterns)
        
        if detected_intents:
            primary_intent = max(detected_intents, key=detected_intents.get)
            confidence = detected_intents[primary_intent]
        else:
            primary_intent = "general"
            confidence = 0.5
        
        return {
            "primary": primary_intent,
            "confidence": confidence,
            "all_intents": detected_intents
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """استخراج کلمات کلیدی"""
        keywords = []
        
        try:
            if self.spacy_model:
                doc = self.spacy_model(text)
                
                # استخراج کلمات مهم (اسم، صفت، فعل)
                for token in doc:
                    if (token.pos_ in ['NOUN', 'ADJ', 'VERB'] and 
                        not token.is_stop and 
                        not token.is_punct and 
                        len(token.text) > 2):
                        keywords.append(token.lemma_.lower())
            
            # استخراج ساده برای فارسی
            persian_keywords = self._extract_persian_keywords(text)
            keywords.extend(persian_keywords)
            
            # حذف تکراری‌ها
            keywords = list(set(keywords))
            
        except Exception as e:
            print(f"خطا در استخراج کلمات کلیدی: {e}")
        
        return keywords[:10]  # برگرداندن 10 کلمه اول
    
    def _extract_persian_keywords(self, text: str) -> List[str]:
        """استخراج کلمات کلیدی فارسی"""
        # کلمات ایست فارسی
        persian_stopwords = {
            'و', 'در', 'به', 'از', 'که', 'این', 'آن', 'را', 'با', 'برای',
            'تا', 'کرد', 'شد', 'است', 'بود', 'می', 'خواهد', 'باید'
        }
        
        # تقسیم متن به کلمات
        words = re.findall(r'[\u0600-\u06FF]+', text)
        
        # فیلتر کردن کلمات
        keywords = []
        for word in words:
            if (len(word) > 2 and 
                word not in persian_stopwords):
                keywords.append(word)
        
        return keywords
    
    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """تولید embedding برای متن"""
        try:
            if self.embeddings_model:
                embedding = self.embeddings_model.embed_query(text)
                return embedding
            return None
        except Exception as e:
            print(f"خطا در تولید embedding: {e}")
            return None
    
    def _analyze_complexity(self, text: str) -> Dict[str, Any]:
        """تحلیل پیچیدگی متن"""
        words = text.split()
        sentences = re.split(r'[.!?]', text)
        
        return {
            "word_count": len(words),
            "sentence_count": len([s for s in sentences if s.strip()]),
            "avg_word_length": sum(len(word) for word in words) / len(words) if words else 0,
            "avg_sentence_length": len(words) / len(sentences) if sentences else 0,
            "complexity_score": self._calculate_complexity_score(text)
        }
    
    def _calculate_complexity_score(self, text: str) -> float:
        """محاسبه امتیاز پیچیدگی متن"""
        words = text.split()
        sentences = re.split(r'[.!?]', text)
        
        if not words or not sentences:
            return 0.0
        
        # فاکتورهای پیچیدگی
        avg_word_length = sum(len(word) for word in words) / len(words)
        avg_sentence_length = len(words) / len(sentences)
        
        # محاسبه امتیاز (0 تا 1)
        complexity = min(1.0, (avg_word_length * 0.1 + avg_sentence_length * 0.05) / 2)
        
        return complexity
