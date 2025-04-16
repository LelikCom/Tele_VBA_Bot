# Используем официальный образ Python
FROM python:3.10-slim


# Устанавливаем необходимые зависимости для работы с PostgreSQL
RUN apt-get update && apt-get install -y libpq-dev

# Обновляем pip
RUN pip install --upgrade pip

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файл зависимостей и устанавливаем их
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем переменную окружения PYTHONPATH
ENV PYTHONPATH="/app"

# Копируем весь проект в контейнер
COPY . /app/

# Проверим содержимое папки /app
RUN ls -l /app

# Указываем правильный файл для старта
CMD ["python3", "main.py"]
