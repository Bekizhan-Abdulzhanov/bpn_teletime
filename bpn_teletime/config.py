import os
from dotenv import load_dotenv


TOKEN = os.getenv("TOKEN")  # ← ВАЖНО
ADMIN_ID = 557174721
PORT = int(os.getenv("PORT", 8080))  # если используешь PORT

WORKTIME_FILE = 'work_time.csv'
EXCEL_REPORT_DIR = 'work_reports'
USERS_FILE = 'users.csv'

TIMEZONE = 'Asia/Bishkek'