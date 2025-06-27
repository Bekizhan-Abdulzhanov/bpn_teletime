import os
from dotenv import load_dotenv

load_dotenv()  # Загружает переменные из .env, если запущено локально

# Получаем токен из переменных окружения
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("❌ Переменная TOKEN не установлена в окружении.")

# Получаем и валидируем PORT
try:
    PORT = int(os.getenv("PORT", "8080"))  # По умолчанию — 8080
    if not (0 < PORT < 65536):
        raise ValueError
except ValueError:
    raise ValueError("❌ PORT variable must be integer between 0 and 65535")

# Пароль администратора (опционально, если не захочешь жёстко задавать)
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "BPN123")

# Пути к рабочим файлам
WORKTIME_FILE = 'work_time.csv'
EXCEL_REPORT_DIR = 'work_reports'
USERS_FILE = 'users.csv'
ADMINS_FILE = 'admins.csv'

# Часовой пояс
TIMEZONE = 'Asia/Bishkek'


