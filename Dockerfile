# Используем официальный образ Python с конкретной версией
FROM python:3.10-slim

# Устанавливаем зависимости для PostgreSQL и очищаем кэш
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости отдельно для кэширования
COPY requirements.txt .

# Обновляем pip и устанавливаем зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы проекта
COPY . .

# Указываем переменные окружения
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

# Команда запуска (лучше использовать список вместо строки)
CMD ["python3", "main.py"]