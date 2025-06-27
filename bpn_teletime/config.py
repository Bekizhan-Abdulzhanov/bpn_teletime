import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
PORT = int(os.getenv("PORT", 8080))
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "BPN123")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))  # 👈 ДОБАВЬ ЭТУ СТРОКУ

WORKTIME_FILE = 'work_time.csv'
EXCEL_REPORT_DIR = 'work_reports'
USERS_FILE = 'users.csv'

TIMEZONE = 'Asia/Bishkek'


