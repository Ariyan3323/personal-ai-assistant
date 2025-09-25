"""
تنظیمات اصلی دستیار هوش مصنوعی شخصی
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """تنظیمات اصلی برنامه"""
    
    # تنظیمات عمومی
    app_name: str = Field(default="Sam.AI", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    
    # تنظیمات سرور
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # تنظیمات پایگاه داده
    database_url: str = Field(
        default="postgresql://user:password@localhost:5432/personal_ai_assistant",
        env="DATABASE_URL"
    )
    
    # تنظیمات Redis
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # تنظیمات امنیتی
    secret_key: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # تنظیمات OpenAI
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")
    
    # تنظیمات Hugging Face
    huggingface_api_key: Optional[str] = Field(default=None, env="HUGGINGFACE_API_KEY")
    
    # تنظیمات لاگ
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/app.log", env="LOG_FILE")
    
    # تنظیمات شخصی‌سازی
    personalization_enabled: bool = Field(default=True, env="PERSONALIZATION_ENABLED")
    learning_rate: float = Field(default=0.01, env="LEARNING_RATE")
    
    # تنظیمات تحقیق
    research_enabled: bool = Field(default=True, env="RESEARCH_ENABLED")
    max_search_results: int = Field(default=10, env="MAX_SEARCH_RESULTS")
    
    # تنظیمات کش
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")  # 1 ساعت
    
    # تنظیمات فایل
    upload_dir: str = Field(default="uploads", env="UPLOAD_DIR")
    max_file_size: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class DevelopmentSettings(Settings):
    """تنظیمات محیط توسعه"""
    debug: bool = True
    log_level: str = "DEBUG"


class ProductionSettings(Settings):
    """تنظیمات محیط تولید"""
    debug: bool = False
    log_level: str = "WARNING"


class TestSettings(Settings):
    """تنظیمات محیط تست"""
    database_url: str = "sqlite:///./test.db"
    redis_url: str = "redis://localhost:6379/1"


def get_settings() -> Settings:
    """دریافت تنظیمات بر اساس محیط"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "test":
        return TestSettings()
    else:
        return DevelopmentSettings()


# نمونه سراسری تنظیمات
settings = get_settings()
