import os
import threading
import warnings
from flask import Flask
from waitress import serve
from telebot import TeleBot
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные окружения

from config import TOKEN, PORT
from handlers import register_handlers
from schedulers import setup_scheduler
from notifier import setup_notifications

warnings.filterwarnings("ignore", message="Timezone offset does not match system offset")

# Проверка токена
if not TOKEN:
    raise ValueError("❌ Переменная окружения TOKEN не найдена. Установи её в .env или Railway → Variables")

bot = TeleBot(TOKEN)
app = Flask(__name__)

@app.route("/")
def index():
    return "🤖 BPN Time Bot is running!"

def run_flask():
    serve(app, host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    # Flask сервер
    threading.Thread(target=run_flask).start()

    # Регистрация всех обработчиков
    register_handlers(bot)

    # Планировщик задач
    scheduler = BackgroundScheduler()
    setup_scheduler(scheduler, bot)
    setup_notifications(scheduler, bot)
    scheduler.start()

    print("🤖 Бот запущен и ждёт команды...")
    bot.infinity_polling()

