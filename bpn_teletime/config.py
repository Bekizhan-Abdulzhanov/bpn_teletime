import os
from dotenv import load_dotenv

load_dotenv()
TOKEN ='8095424374:AAHn_OFwmipNXfHqpadBd1Rq6h6bcWFLk2c'

TOKEN = os.getenv("TOKEN")  # ⚠️ Важно: переменная должна быть установлена в Railway
PORT = int(os.getenv("PORT", 8080))
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

WORKTIME_FILE = 'work_time.csv'
EXCEL_REPORT_DIR = 'work_reports'
USERS_FILE = 'users.csv'

TIMEZONE = 'Asia/Bishkek'

