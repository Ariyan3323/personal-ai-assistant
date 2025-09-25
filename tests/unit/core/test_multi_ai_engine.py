"""
تست‌های واحد برای ماژول multi_ai_engine
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from src.core.multi_ai_engine import MultiAIEngine, AIModel, TaskType, PersonalityProfile
from config.settings import settings


@pytest.fixture
def multi_ai_engine():
    """فیکسچر برای نمونه MultiAIEngine"""
    engine = MultiAIEngine()
    # Mock کردن OpenAI و Gemini برای جلوگیری از فراخوانی API واقعی در تست‌ها
    with patch("openai.ChatCompletion.acreate", new_callable=AsyncMock) as mock_openai_chat:
        with patch("google.generativeai.GenerativeModel") as mock_gemini_model:
            mock_openai_chat.return_value = AsyncMock(choices=[AsyncMock(message=AsyncMock(content="Test response from GPT"))], usage=AsyncMock(total_tokens=10))
            mock_gemini_model.return_value.generate_content_async.return_value = AsyncMock(text="Test response from Gemini")
        
        yield engine


@pytest.mark.asyncio
async def test_initialize_models(multi_ai_engine):
    """تست راه‌اندازی مدل‌ها"""
    assert len(multi_ai_engine.models) > 0
    if settings.openai_api_key:
        assert multi_ai_engine.models[AIModel.GPT4]["available"]
        assert multi_ai_engine.models[AIModel.GPT35_TURBO]["available"]
    if hasattr(settings, 'google_api_key') and settings.google_api_key:
        assert multi_ai_engine.models[AIModel.GEMINI_PRO]["available"]


def test_setup_personality(multi_ai_engine):
    """تست تنظیم شخصیت"""
    personality = multi_ai_engine.setup_personality(gender="female", personality_type="friendly")
    assert isinstance(personality, PersonalityProfile)
    assert personality.gender == "female"
    assert personality.name is not None
    assert "دوستانه" in personality.personality_traits

    personality = multi_ai_engine.setup_personality(gender="male", name="Robert", personality_type="professional")
    assert personality.gender == "male"
    assert personality.name == "Robert"
    assert "حرفه‌ای" in personality.personality_traits


@pytest.mark.asyncio
async def test_detect_task_type(multi_ai_engine):
    """تست تشخیص نوع وظیفه"""
    assert await multi_ai_engine._detect_task_type("چگونه سهام بخرم؟") == TaskType.FINANCIAL_ADVICE
    assert await multi_ai_engine._detect_task_type("احساس غمگینی می‌کنم") == TaskType.PSYCHOLOGICAL_SUPPORT
    assert await multi_ai_engine._detect_task_type("یک داستان کوتاه بنویس") == TaskType.CREATIVE_WRITING
    assert await multi_ai_engine._detect_task_type("ترجمه کن") == TaskType.TRANSLATION
    assert await multi_ai_engine._detect_task_type("درباره هوش مصنوعی تحقیق کن") == TaskType.RESEARCH
    assert await multi_ai_engine._detect_task_type("سلام حالت چطوره؟") == TaskType.CONVERSATION


@pytest.mark.asyncio
async def test_select_best_model(multi_ai_engine):
    """تست انتخاب بهترین مدل"""
    # فرض می‌کنیم GPT-4 و Gemini در دسترس هستند
    if AIModel.GPT4 in multi_ai_engine.models and multi_ai_engine.models[AIModel.GPT4]["available"]:
        assert multi_ai_engine._select_best_model(TaskType.CONTENT_GENERATION) == AIModel.GPT4
    elif AIModel.GEMINI_PRO in multi_ai_engine.models and multi_ai_engine.models[AIModel.GEMINI_PRO]["available"]:
        assert multi_ai_engine._select_best_model(TaskType.CREATIVE_WRITING) == AIModel.GEMINI_PRO
    else:
        assert multi_ai_engine._select_best_model(TaskType.CONVERSATION) == AIModel.GPT35_TURBO


@pytest.mark.asyncio
async def test_process_request_conversation(multi_ai_engine):
    """تست پردازش درخواست مکالمه"""
    multi_ai_engine.setup_personality(gender="female", name="آریا")
    response = await multi_ai_engine.process_request("سلام چطوری؟")
    assert response["success"]
    assert "Test response from GPT" in response["content"]
    assert response["model_used"] in [AIModel.GPT35_TURBO.value, AIModel.GPT4.value]
    assert response["task_type"] == TaskType.CONVERSATION.value
    assert multi_ai_engine.conversation_history[-1]["user_input"] == "سلام چطوری؟"


@pytest.mark.asyncio
async def test_process_request_financial_advice(multi_ai_engine):
    """تست پردازش درخواست مشاوره مالی"""
    multi_ai_engine.setup_personality(gender="male", name="آرش", personality_type="professional")
    response = await multi_ai_engine.process_request("تحلیل بیت کوین را می‌خواهم", task_type=TaskType.FINANCIAL_ADVICE)
    assert response["success"]
    assert "Test response from GPT" in response["content"]
    assert response["task_type"] == TaskType.FINANCIAL_ADVICE.value


@pytest.mark.asyncio
async def test_apply_personality(multi_ai_engine):
    """تست اعمال شخصیت به پاسخ"""
    multi_ai_engine.setup_personality(gender="female", name="نیلا", personality_type="companion")
    mock_result = {"success": True, "content": "امروز هوا خوب است."}
    personalized_response = await multi_ai_engine._apply_personality(mock_result, TaskType.CONVERSATION)
    assert personalized_response["success"]
    assert personalized_response["personality_applied"]
    assert personalized_response["personality_name"] == "نیلا"
    # بررسی اینکه آیا عناصر شخصیتی اضافه شده‌اند (مثلاً با کلمات همدلانه)
    # این بخش نیاز به تطابق دقیق با منطق _apply_personality دارد


@pytest.mark.asyncio
async def test_get_specialized_response(multi_ai_engine):
    """تست دریافت پاسخ تخصصی"""
    multi_ai_engine.setup_personality(gender="male", name="مشاور")
    response = await multi_ai_engine.get_specialized_response("financial_advisor", "بهترین سهام برای سرمایه‌گذاری چیست؟")
    assert response["success"]
    assert response["task_type"] == TaskType.FINANCIAL_ADVICE.value
    assert "Test response from GPT" in response["content"]


@pytest.mark.asyncio
async def test_get_conversation_stats(multi_ai_engine):
    """تست آمار مکالمات"""
    multi_ai_engine.setup_personality(gender="neutral", name="دستیار")
    await multi_ai_engine.process_request("سلام")
    await multi_ai_engine.process_request("یک شعر بنویس", task_type=TaskType.CREATIVE_WRITING)
    stats = multi_ai_engine.get_conversation_stats()
    assert stats["total_conversations"] == 2
    assert stats["task_distribution"][TaskType.CONVERSATION.value] == 1
    assert stats["task_distribution"][TaskType.CREATIVE_WRITING.value] == 1
    assert "%" in stats["success_rate"]
