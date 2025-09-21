"""
ماژول تحقیق خودکار و یادگیری مداوم
"""

import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import openai
from dataclasses import dataclass
import hashlib

from config.settings import settings


@dataclass
class ResearchResult:
    """نتیجه تحقیق"""
    title: str
    content: str
    source_url: str
    relevance_score: float
    timestamp: datetime
    summary: str
    keywords: List[str]
    category: str


class WebScraper:
    """خزنده وب برای جمع‌آوری اطلاعات"""
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search_google(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """جستجو در گوگل"""
        try:
            search_url = f"https://www.google.com/search?q={query}&num={num_results}"
            
            async with self.session.get(search_url) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                results = []
                search_results = soup.find_all('div', class_='g')
                
                for result in search_results[:num_results]:
                    title_elem = result.find('h3')
                    link_elem = result.find('a')
                    snippet_elem = result.find('span', class_='aCOpRe')
                    
                    if title_elem and link_elem:
                        title = title_elem.get_text()
                        url = link_elem.get('href')
                        snippet = snippet_elem.get_text() if snippet_elem else ""
                        
                        if url.startswith('/url?q='):
                            url = url.split('/url?q=')[1].split('&')[0]
                        
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet,
                            'source': 'google'
                        })
                
                return results
                
        except Exception as e:
            print(f"خطا در جستجوی گوگل: {e}")
            return []
    
    async def scrape_webpage(self, url: str) -> Dict[str, Any]:
        """استخراج محتوای صفحه وب"""
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # حذف اسکریپت‌ها و استایل‌ها
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    # استخراج عنوان
                    title = soup.find('title')
                    title_text = title.get_text().strip() if title else ""
                    
                    # استخراج متن اصلی
                    content_selectors = [
                        'article', 'main', '.content', '.post-content',
                        '.entry-content', '.article-body', 'p'
                    ]
                    
                    content = ""
                    for selector in content_selectors:
                        elements = soup.select(selector)
                        if elements:
                            content = ' '.join([elem.get_text().strip() for elem in elements])
                            break
                    
                    if not content:
                        content = soup.get_text()
                    
                    # پاکسازی متن
                    content = re.sub(r'\s+', ' ', content).strip()
                    
                    return {
                        'success': True,
                        'title': title_text,
                        'content': content[:5000],  # محدود کردن طول
                        'url': url,
                        'word_count': len(content.split()),
                        'scraped_at': datetime.now().isoformat()
                    }
                else:
                    return {
                        'success': False,
                        'error': f'HTTP {response.status}',
                        'url': url
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url': url
            }


class KnowledgeBase:
    """پایگاه دانش برای ذخیره و مدیریت اطلاعات"""
    
    def __init__(self):
        self.knowledge_store = {}
        self.categories = {
            'technology': 'فناوری',
            'science': 'علم',
            'business': 'کسب‌وکار',
            'health': 'سلامت',
            'education': 'آموزش',
            'news': 'اخبار',
            'general': 'عمومی'
        }
    
    def add_knowledge(self, topic: str, content: Dict[str, Any]):
        """اضافه کردن دانش جدید"""
        topic_hash = hashlib.md5(topic.encode()).hexdigest()
        
        if topic_hash not in self.knowledge_store:
            self.knowledge_store[topic_hash] = {
                'topic': topic,
                'entries': [],
                'last_updated': datetime.now(),
                'access_count': 0
            }
        
        self.knowledge_store[topic_hash]['entries'].append({
            'content': content,
            'added_at': datetime.now(),
            'relevance_score': content.get('relevance_score', 0.5)
        })
        
        self.knowledge_store[topic_hash]['last_updated'] = datetime.now()
    
    def search_knowledge(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """جستجو در پایگاه دانش"""
        results = []
        query_lower = query.lower()
        
        for topic_hash, data in self.knowledge_store.items():
            topic = data['topic'].lower()
            
            # محاسبه امتیاز شباهت ساده
            similarity_score = 0
            query_words = query_lower.split()
            topic_words = topic.split()
            
            for q_word in query_words:
                for t_word in topic_words:
                    if q_word in t_word or t_word in q_word:
                        similarity_score += 1
            
            if similarity_score > 0:
                results.append({
                    'topic': data['topic'],
                    'similarity_score': similarity_score / len(query_words),
                    'entries': data['entries'][-3:],  # آخرین 3 ورودی
                    'last_updated': data['last_updated']
                })
        
        # مرتب‌سازی بر اساس امتیاز شباهت
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return results[:limit]
    
    def get_trending_topics(self, days: int = 7) -> List[Dict[str, Any]]:
        """دریافت موضوعات پرطرفدار"""
        cutoff_date = datetime.now() - timedelta(days=days)
        trending = []
        
        for topic_hash, data in self.knowledge_store.items():
            if data['last_updated'] > cutoff_date:
                recent_entries = [
                    entry for entry in data['entries']
                    if entry['added_at'] > cutoff_date
                ]
                
                if recent_entries:
                    trending.append({
                        'topic': data['topic'],
                        'recent_entries_count': len(recent_entries),
                        'access_count': data['access_count'],
                        'last_updated': data['last_updated']
                    })
        
        # مرتب‌سازی بر اساس تعداد ورودی‌های اخیر
        trending.sort(key=lambda x: x['recent_entries_count'], reverse=True)
        
        return trending[:10]


class AutoResearcher:
    """محقق خودکار"""
    
    def __init__(self):
        self.knowledge_base = KnowledgeBase()
        self.research_history = []
        self.active_research_topics = set()
        
        # تنظیم OpenAI
        if settings.openai_api_key:
            openai.api_key = settings.openai_api_key
    
    async def research_topic(
        self, 
        topic: str, 
        depth: str = 'medium',
        sources: List[str] = None
    ) -> Dict[str, Any]:
        """تحقیق در مورد یک موضوع"""
        
        if topic in self.active_research_topics:
            return {
                'success': False,
                'error': 'Research already in progress for this topic'
            }
        
        self.active_research_topics.add(topic)
        
        try:
            research_results = []
            
            # مرحله 1: جستجوی اولیه
            search_queries = await self._generate_search_queries(topic)
            
            async with WebScraper() as scraper:
                for query in search_queries:
                    search_results = await scraper.search_google(query, num_results=5)
                    
                    # استخراج محتوای صفحات
                    for result in search_results:
                        webpage_content = await scraper.scrape_webpage(result['url'])
                        
                        if webpage_content['success']:
                            # تحلیل و امتیازدهی محتوا
                            analysis = await self._analyze_content(
                                webpage_content['content'], 
                                topic
                            )
                            
                            research_result = ResearchResult(
                                title=webpage_content['title'],
                                content=webpage_content['content'],
                                source_url=result['url'],
                                relevance_score=analysis['relevance_score'],
                                timestamp=datetime.now(),
                                summary=analysis['summary'],
                                keywords=analysis['keywords'],
                                category=analysis['category']
                            )
                            
                            research_results.append(research_result)
            
            # مرحله 2: تحلیل و خلاصه‌سازی
            comprehensive_summary = await self._create_comprehensive_summary(
                topic, 
                research_results
            )
            
            # مرحله 3: ذخیره در پایگاه دانش
            self.knowledge_base.add_knowledge(topic, {
                'summary': comprehensive_summary,
                'sources': [r.source_url for r in research_results],
                'research_date': datetime.now().isoformat(),
                'depth': depth,
                'result_count': len(research_results)
            })
            
            # ذخیره تاریخچه
            self.research_history.append({
                'topic': topic,
                'timestamp': datetime.now(),
                'results_count': len(research_results),
                'depth': depth
            })
            
            return {
                'success': True,
                'topic': topic,
                'summary': comprehensive_summary,
                'results': [
                    {
                        'title': r.title,
                        'summary': r.summary,
                        'source': r.source_url,
                        'relevance': r.relevance_score,
                        'category': r.category
                    }
                    for r in sorted(research_results, key=lambda x: x.relevance_score, reverse=True)
                ],
                'research_metadata': {
                    'total_sources': len(research_results),
                    'research_time': datetime.now().isoformat(),
                    'depth': depth
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'topic': topic
            }
        
        finally:
            self.active_research_topics.discard(topic)
    
    async def _generate_search_queries(self, topic: str) -> List[str]:
        """تولید کوئری‌های جستجو"""
        base_queries = [
            topic,
            f"{topic} آموزش",
            f"{topic} راهنما",
            f"{topic} تحلیل",
            f"what is {topic}",
            f"{topic} tutorial",
            f"{topic} guide"
        ]
        
        # تولید کوئری‌های پیشرفته با AI
        if settings.openai_api_key:
            try:
                prompt = f"""
                برای موضوع "{topic}" لیستی از 5 کوئری جستجوی مفید و متنوع تولید کن.
                کوئری‌ها باید جنبه‌های مختلف موضوع را پوشش دهند.
                فقط کوئری‌ها را برگردان، هر کدام در یک خط.
                """
                
                response = await openai.ChatCompletion.acreate(
                    model=settings.openai_model,
                    messages=[
                        {"role": "system", "content": "شما یک متخصص تحقیق هستید."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=200,
                    temperature=0.7
                )
                
                ai_queries = response.choices[0].message.content.strip().split('\n')
                base_queries.extend([q.strip() for q in ai_queries if q.strip()])
                
            except Exception as e:
                print(f"خطا در تولید کوئری با AI: {e}")
        
        return base_queries[:10]  # محدود کردن به 10 کوئری
    
    async def _analyze_content(self, content: str, topic: str) -> Dict[str, Any]:
        """تحلیل محتوا و امتیازدهی"""
        
        # محاسبه امتیاز ربط ساده
        topic_words = topic.lower().split()
        content_lower = content.lower()
        
        relevance_score = 0
        for word in topic_words:
            relevance_score += content_lower.count(word) * 0.1
        
        relevance_score = min(relevance_score, 1.0)  # محدود کردن به 1
        
        # استخراج کلمات کلیدی ساده
        words = re.findall(r'\b\w+\b', content.lower())
        word_freq = {}
        
        for word in words:
            if len(word) > 3:  # فقط کلمات بلندتر از 3 حرف
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # برترین کلمات
        top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        keywords = [word for word, freq in top_keywords]
        
        # تعیین دسته‌بندی ساده
        category = self._categorize_content(content)
        
        # خلاصه‌سازی ساده
        sentences = content.split('.')[:3]  # 3 جمله اول
        summary = '. '.join(sentences).strip()
        
        return {
            'relevance_score': relevance_score,
            'keywords': keywords,
            'category': category,
            'summary': summary[:500]  # محدود کردن طول خلاصه
        }
    
    def _categorize_content(self, content: str) -> str:
        """دسته‌بندی محتوا"""
        content_lower = content.lower()
        
        category_keywords = {
            'technology': ['تکنولوژی', 'فناوری', 'کامپیوتر', 'نرم‌افزار', 'technology', 'software', 'computer'],
            'science': ['علم', 'تحقیق', 'دانش', 'science', 'research', 'study'],
            'business': ['کسب‌وکار', 'تجارت', 'بازار', 'business', 'market', 'company'],
            'health': ['سلامت', 'پزشکی', 'درمان', 'health', 'medical', 'treatment'],
            'education': ['آموزش', 'تعلیم', 'دانشگاه', 'education', 'learning', 'university']
        }
        
        category_scores = {}
        
        for category, keywords in category_keywords.items():
            score = 0
            for keyword in keywords:
                score += content_lower.count(keyword)
            category_scores[category] = score
        
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            if category_scores[best_category] > 0:
                return best_category
        
        return 'general'
    
    async def _create_comprehensive_summary(
        self, 
        topic: str, 
        research_results: List[ResearchResult]
    ) -> str:
        """ایجاد خلاصه جامع"""
        
        if not research_results:
            return f"اطلاعات کافی در مورد {topic} یافت نشد."
        
        # ترکیب خلاصه‌ها
        all_summaries = [r.summary for r in research_results if r.summary]
        combined_text = ' '.join(all_summaries)
        
        # خلاصه‌سازی با AI (در صورت وجود)
        if settings.openai_api_key and combined_text:
            try:
                prompt = f"""
                بر اساس اطلاعات زیر، یک خلاصه جامع و مفید در مورد "{topic}" بنویس:
                
                {combined_text[:3000]}
                
                خلاصه باید:
                - حداکثر 300 کلمه باشد
                - نکات کلیدی را پوشش دهد
                - قابل فهم و مفید باشد
                """
                
                response = await openai.ChatCompletion.acreate(
                    model=settings.openai_model,
                    messages=[
                        {"role": "system", "content": "شما یک متخصص خلاصه‌نویسی هستید."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=400,
                    temperature=0.5
                )
                
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                print(f"خطا در خلاصه‌سازی با AI: {e}")
        
        # خلاصه‌سازی ساده
        if combined_text:
            sentences = combined_text.split('.')[:5]  # 5 جمله اول
            return '. '.join(sentences).strip()
        
        return f"تحقیق در مورد {topic} انجام شد اما خلاصه مناسبی تولید نشد."
    
    async def continuous_learning(self, topics: List[str], interval_hours: int = 24):
        """یادگیری مداوم در مورد موضوعات مشخص"""
        
        while True:
            for topic in topics:
                try:
                    print(f"شروع تحقیق خودکار در مورد: {topic}")
                    result = await self.research_topic(topic, depth='light')
                    
                    if result['success']:
                        print(f"تحقیق {topic} با موفقیت انجام شد")
                    else:
                        print(f"خطا در تحقیق {topic}: {result.get('error')}")
                    
                    # تأخیر بین موضوعات
                    await asyncio.sleep(60)  # 1 دقیقه
                    
                except Exception as e:
                    print(f"خطا در یادگیری مداوم {topic}: {e}")
            
            # تأخیر تا دور بعدی
            await asyncio.sleep(interval_hours * 3600)
    
    def get_research_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """دریافت تاریخچه تحقیقات"""
        return self.research_history[-limit:]
    
    def get_knowledge_summary(self) -> Dict[str, Any]:
        """خلاصه‌ای از پایگاه دانش"""
        return {
            'total_topics': len(self.knowledge_base.knowledge_store),
            'trending_topics': self.knowledge_base.get_trending_topics(),
            'recent_research': self.get_research_history(10),
            'categories': self.knowledge_base.categories
        }
