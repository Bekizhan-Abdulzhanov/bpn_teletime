WORKDIR /app
COPY bpn_teletime/ /app
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
