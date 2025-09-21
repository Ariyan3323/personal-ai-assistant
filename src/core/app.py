"""
ماژول اصلی برنامه FastAPI
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from typing import Optional

from config.settings import settings
from src.core.middleware import setup_middleware
from src.core.routes import setup_routes


def create_app(lifespan: Optional[asynccontextmanager] = None) -> FastAPI:
    """ایجاد و پیکربندی برنامه FastAPI"""
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="یک دستیار هوش مصنوعی شخصی با قابلیت‌های پیشرفته",
        debug=settings.debug,
        lifespan=lifespan
    )
    
    # تنظیم middleware ها
    setup_middleware(app)
    
    # تنظیم مسیرها
    setup_routes(app)
    
    # سرو فایل‌های استاتیک
    try:
        app.mount("/static", StaticFiles(directory="static"), name="static")
    except RuntimeError:
        # دایرکتوری static وجود ندارد
        pass
    
    return app
