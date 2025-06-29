# --- config.py ---
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
PORT = int(os.getenv("PORT", 8443))
TIMEZONE = os.getenv("TIMEZONE", "Asia/Bishkek")

ADMIN_IDS = [
    557174721,  # BekizhanAbdulzhanov
    378268765,  # ErlanNasiev
]

AUTO_APPROVED_USERS = {
    378268765: "ErlanNasiev",
    557174721: "BekizhanAbdulzhanov",
}

# 🔽 Добавь эти переменные ниже — это устраняет ошибку:
WORKTIME_FILE = "data/work_time.csv"
USERS_FILE = "data/users.csv"
AUTO_ENABLED_FILE = "data/auto_enabled.csv"
