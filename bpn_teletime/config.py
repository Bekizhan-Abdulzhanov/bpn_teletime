import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")  # ⚠️ Важно: переменная должна быть установлена в Railway
PORT = int(os.getenv("PORT", 8080))
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))  # Поддержка Railway переменной

WORKTIME_FILE = 'work_time.csv'
EXCEL_REPORT_DIR = 'work_reports'
USERS_FILE = 'users.csv'

TIMEZONE = 'Asia/Bishkek'

