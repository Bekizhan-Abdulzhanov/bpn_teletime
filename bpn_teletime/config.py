import os
from dotenv import load_dotenv


load_dotenv()

TOKEN = os.getenv("TOKEN")

PORT = int(os.getenv("PORT", 8080))


ADMIN_IDS = [
    557174721,  
    987654321
]

# 📁 Пути к файлам хранения
WORKTIME_FILE = 'work_time.csv'
EXCEL_REPORT_DIR = 'work_reports'
USERS_FILE = 'users.csv'

# 🌍 Часовой пояс
TIMEZONE = 'Asia/Bishkek'



