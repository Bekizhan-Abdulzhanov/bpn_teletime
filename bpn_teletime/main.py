from telebot import TeleBot
from flask import Flask
from waitress import serve
import threading
from apscheduler.schedulers.background import BackgroundScheduler
import warnings
import os
from dotenv import load_dotenv
from bpn_teletime.config import TOKEN, PORT

# Загрузить переменные окружения
load_dotenv()

# ⚠️ Получаем токен и порт
TOKEN = os.getenv("TOKEN")
PORT = int(os.getenv("PORT", 8080))  # обязательно int

# Проверка на наличие токена
if not TOKEN:
    raise ValueError("❌ Переменная окружения TOKEN не установлена.")

bot = TeleBot(TOKEN)

# Импорты хендлеров
from handlers import register_handlers
from schedulers import setup_scheduler
from notifier import setup_notifications

warnings.filterwarnings("ignore", message="Timezone offset does not match system offset")

# Инициализация Flask-приложения
app = Flask(__name__)

@app.route('/')
def index():
    return "🤖 BPN Telegram bot is running!"

# Функция для запуска Flask в отдельном потоке
def run_flask():
    serve(app, host='0.0.0.0', port=PORT)

if __name__ == '__main__':
    # Запуск Flask-сервера
    threading.Thread(target=run_flask).start()

    # Регистрация всех хендлеров
    register_handlers(bot)

    # Планировщик задач
    scheduler = BackgroundScheduler()
    setup_scheduler(scheduler, bot)         # Автоматические отметки
    setup_notifications(scheduler, bot)     # Напоминания
    scheduler.start()

    print("✅ Бот запущен и слушает команды...")
    bot.infinity_polling()
