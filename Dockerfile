FROM python:3.10-slim

# 1) Устанавливаем данные по часовым поясам
RUN apt-get update \
 && apt-get install -y --no-install-recommends tzdata \
 && ln -snf /usr/share/zoneinfo/Asia/Bishkek /etc/localtime \
 && echo "Asia/Bishkek" > /etc/timezone \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "bpn_teletime/main.py"]

