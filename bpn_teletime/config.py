import os

TOKEN = os.getenv("TOKEN")  # ← будет взят из Railway → Variables
ADMIN_ID = 557174721
PORT = int(os.getenv("PORT", 8080))

WORKTIME_FILE = 'work_time.csv'
EXCEL_REPORT_DIR = 'work_reports'
USERS_FILE = 'users.csv'

TIMEZONE = 'Asia/Bishkek'
