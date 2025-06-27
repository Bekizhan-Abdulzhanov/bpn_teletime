import os
import threading
import warnings
from dotenv import load_dotenv
from flask import Flask
from waitress import serve
from telebot import TeleBot
from apscheduler.schedulers.background import BackgroundScheduler
from handlers import register_handlers

# Загружаем переменные из .env или из Railway → Variables
load_dotenv()

TOKEN = os.getenv("TOKEN")
PORT = int(os.getenv("PORT", 8080))

if not TOKEN:
    raise ValueError("❌ Переменная окружения TOKEN не найдена. Убедись, что она задана в .env или Railway → Variables")

warnings.filterwarnings("ignore", message="Timezone offset does not match system offset")

# Создаем экземпляр бота
bot = TeleBot(TOKEN)

# Импортируем функции после создания бота
from handlers import register_handlers
from schedulers import setup_scheduler
from notifier import setup_notifications

# Flask-приложение
app = Flask(__name__)

@app.route("/")
def index():
    return "🤖 BPN Teletime Bot работает."

# Функция для запуска Flask-сервера
def run_flask():
    serve(app, host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    # 1. Запуск Flask в отдельном потоке
    threading.Thread(target=run_flask).start()

    # 2. Регистрация всех хендлеров
    register_handlers(bot)

    # 3. Настройка планировщика
    scheduler = BackgroundScheduler()
    setup_scheduler(scheduler, bot)
    setup_notifications(scheduler, bot)
    scheduler.start()

    print("✅ Бот запущен. Ожидаем команды...")
    bot.infinity_polling()


