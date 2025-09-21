"""
فایل اصلی دستیار هوش مصنوعی شخصی
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from config.settings import settings
from src.core.app import create_app
from src.core.database import init_db
from src.core.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """مدیریت چرخه حیات برنامه"""
    # راه‌اندازی اولیه
    setup_logging()
    await init_db()
    
    yield
    
    # تمیزکاری پایانی
    pass


def main():
    """تابع اصلی برای اجرای برنامه"""
    
    # ایجاد برنامه FastAPI
    app = create_app(lifespan=lifespan)
    
    # اجرای سرور
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()
