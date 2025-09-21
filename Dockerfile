# استفاده از Python 3.11 به عنوان base image
FROM python:3.11-slim

# تنظیم متغیرهای محیطی
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# تنظیم دایرکتوری کاری
WORKDIR /app

# نصب وابستگی‌های سیستم
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# کپی فایل‌های requirements
COPY requirements.txt .

# نصب وابستگی‌های Python
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# کپی کد برنامه
COPY . .

# ایجاد دایرکتوری‌های مورد نیاز
RUN mkdir -p logs uploads static

# تنظیم مجوزها
RUN chmod +x main.py

# ایجاد کاربر غیر root برای امنیت
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# expose کردن پورت
EXPOSE 8000

# دستور اجرای برنامه
CMD ["python", "main.py"]

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
