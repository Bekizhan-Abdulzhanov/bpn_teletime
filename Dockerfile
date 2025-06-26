FROM python:3.10-slim

WORKDIR /app

# Установим зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Запуск main.py из поддиректории (обрати внимание на путь)
CMD ["python", "bpn_teletime/main.py"]

