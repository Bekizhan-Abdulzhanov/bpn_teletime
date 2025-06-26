# Используем минимальный образ
FROM python:3.10-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Указываем переменные среды
ENV PYTHONUNBUFFERED=1

# Запуск бота
CMD ["python", "main.py"]