import os
from dotenv import load_dotenv

load_dotenv()

# 🔐 Основные переменные
TOKEN = os.getenv("TOKEN")
PORT = int(os.getenv("PORT", 8443))
TIMEZONE = os.getenv("TIMEZONE", "Asia/Bishkek")

# 👮‍♂️ ID админов
ADMIN_IDS = [
    557174721,  # BekizhanAbdulzhanov
    378268765,  # ErlanNasiev
]

# 👑 Автоматически одобренные пользователи
AUTO_APPROVED_USERS = {
    378268765: "ErlanNasiev",
    557174721: "BekizhanAbdulzhanov",
}

# 📁 Пути к CSV-файлам (в корне проекта)
WORKTIME_FILE = "work_time.csv"
USERS_FILE = "users.csv"
AUTO_ENABLED_FILE = "auto_enabled.csv"
