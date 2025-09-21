"""
تنظیم middleware های برنامه
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import time
from loguru import logger

from config.settings import settings


def setup_middleware(app: FastAPI) -> None:
    """تنظیم تمام middleware های برنامه"""
    
    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # در محیط تولید باید محدود شود
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Trusted Host Middleware (برای امنیت)
    if not settings.debug:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
        )
    
    # Custom Logging Middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """لاگ کردن درخواست‌ها"""
        start_time = time.time()
        
        # اطلاعات درخواست
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        url = str(request.url)
        
        logger.info(f"درخواست دریافت شد: {method} {url} از {client_ip}")
        
        # پردازش درخواست
        response = await call_next(request)
        
        # محاسبه زمان پردازش
        process_time = time.time() - start_time
        
        # لاگ پاسخ
        logger.info(
            f"پاسخ ارسال شد: {response.status_code} - "
            f"زمان پردازش: {process_time:.4f}s"
        )
        
        # اضافه کردن هدر زمان پردازش
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    
    # Rate Limiting Middleware (ساده)
    @app.middleware("http")
    async def rate_limit(request: Request, call_next):
        """محدودیت نرخ درخواست (پیاده‌سازی ساده)"""
        # در پیاده‌سازی واقعی باید از Redis یا ابزار مشابه استفاده کرد
        response = await call_next(request)
        return response
