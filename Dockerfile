FROM python:3.10-slim

# Установка рабочей директории
WORKDIR /app

# Копируем зависимости и устанавливаем
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Устанавливаем переменные окружения, если нужно (Railway использует .env или Variables UI)
ENV PYTHONUNBUFFERED=1

# Запуск основного файла
CMD ["python", "bpn_teletime/main.py"]
