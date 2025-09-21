"""
تنظیم مسیرهای API
"""

from fastapi import FastAPI, APIRouter
from src.api.chat import router as chat_router
from src.api.user import router as user_router
from src.api.research import router as research_router
from src.api.personalization import router as personalization_router


def setup_routes(app: FastAPI) -> None:
    """تنظیم تمام مسیرهای API"""
    
    # مسیر اصلی API
    api_router = APIRouter(prefix="/api/v1")
    
    # اضافه کردن مسیرهای مختلف
    api_router.include_router(chat_router, prefix="/chat", tags=["چت"])
    api_router.include_router(user_router, prefix="/user", tags=["کاربر"])
    api_router.include_router(research_router, prefix="/research", tags=["تحقیق"])
    api_router.include_router(personalization_router, prefix="/personalization", tags=["شخصی‌سازی"])
    
    # اضافه کردن router اصلی به برنامه
    app.include_router(api_router)
    
    # مسیر سلامتی سیستم
    @app.get("/health")
    async def health_check():
        """بررسی سلامت سیستم"""
        return {
            "status": "healthy",
            "app_name": "Personal AI Assistant",
            "version": "1.0.0"
        }
    
    # مسیر اصلی
    @app.get("/")
    async def root():
        """صفحه اصلی"""
        return {
            "message": "به دستیار هوش مصنوعی شخصی خوش آمدید!",
            "docs": "/docs",
            "health": "/health"
        }
