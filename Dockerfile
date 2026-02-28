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
COPY run.py .

# Статические файлы
COPY static/ ./static/

# Директории для логов и кэша (файловый бэкенд не используется, но директория нужна)
RUN mkdir -p logs cache

# Конфигурация передаётся через env_file в docker-compose.yml
CMD ["python", "run.py"]
