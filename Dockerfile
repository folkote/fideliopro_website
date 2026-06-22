FROM python:3.11-slim

WORKDIR /app

# Системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Установить UV
RUN pip install --no-cache-dir uv

# Python зависимости
COPY requirements.txt .
RUN uv pip install --system --no-cache-dir -r requirements.txt

# Приложение
COPY app/ ./app/
COPY scripts/ ./scripts/
COPY run.py .

# Статические файлы
COPY static/ ./static/

# Создать директории для runtime-данных; .env не копируется в image
RUN mkdir -p logs data

# Конфигурация передаётся через env_file/environment в docker-compose.yml
CMD ["python", "run.py"]
