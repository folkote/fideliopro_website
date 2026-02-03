FROM python:3.11-slim

WORKDIR /app

# Установить зависимости системы и UV
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Установить UV
RUN pip install --no-cache-dir uv

# Установить Python зависимости через UV (в системное окружение)
COPY requirements.txt .
RUN uv pip install --system --no-cache-dir -r requirements.txt

# Копировать приложение
COPY app/ ./app/
COPY run.py .
COPY .env .

# Копировать статические файлы
COPY static/ ./static/

# Создать директорию для данных (кэш и логи будут использоваться через volume)
RUN mkdir -p data

# Запустить приложение
CMD ["python", "run.py"]
