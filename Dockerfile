FROM python:3.10-slim

WORKDIR /app

# Копируем зависимости и исходники
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bpn_teletime/ .

CMD ["python", "main.py"]
