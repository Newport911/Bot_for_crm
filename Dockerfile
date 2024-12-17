# Используем Python 3.11 как базовый образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости в контейнер
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект в контейнер
COPY . .

# Добавляем метаданные
LABEL maintainer="your-email@example.com"
LABEL version="1.0"
LABEL description="Telegram Bot for CRM"

# Настраиваем переменные окружения
ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Moscow

# Создаем непривилегированного пользователя
RUN useradd -m -u 1000 botuser
USER botuser

# Добавляем HEALTHCHECK для мониторинга
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import sys; sys.exit(0 if 'telegram_bot.py' in str(open('/proc/1/cmdline').read()) else 1)"

# Указываем команду для запуска бота
CMD ["python", "telegram_bot.py"]