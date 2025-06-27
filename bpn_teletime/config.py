import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# Приводим PORT к целому числу, обрабатываем ошибку, если невалиден
try:
    PORT = int(os.getenv("PORT"))
    if not (0 <= PORT <= 65535):
        raise ValueError("PORT must be between 0 and 65535")
except (TypeError, ValueError):
    PORT = 8080  # Значение по умолчанию


# Пути к рабочим файлам
WORKTIME_FILE = 'work_time.csv'
EXCEL_REPORT_DIR = 'work_reports'
USERS_FILE = 'users.csv'
ADMINS_FILE = 'admins.csv'

# Часовой пояс
TIMEZONE = 'Asia/Bishkek'


