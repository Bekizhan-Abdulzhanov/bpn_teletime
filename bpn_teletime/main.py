from telebot import TeleBot
from flask import Flask
from waitress import serve
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import os
import warnings

from config import TOKEN, PORT
from handlers import register_handlers
from schedulers import setup_scheduler
from notifier import setup_notifications

warnings.filterwarnings("ignore", message="Timezone offset does not match system offset")

load_dotenv()
if not TOKEN:
    raise ValueError("❌ Переменная TOKEN не установлена. Проверь .env или Railway Variables.")


bot = TeleBot(TOKEN)
app = Flask(__name__)


@app.route('/')
def index():
    return "Bot is running."


def run_flask():
    serve(app, host='0.0.0.0', port=PORT)


if __name__ == '__main__':
    # Запуск Flask-сервера в отдельном потоке
    threading.Thread(target=run_flask).start()

    # Регистрация всех хендлеров (всё внутри handlers.py)
    register_handlers(bot)

    print("🤖 Бот запущен. Ждём команды...")

    # Планировщик: автосохранения и уведомления
    scheduler = BackgroundScheduler()
    setup_scheduler(scheduler, bot)
    setup_notifications(scheduler, bot)
    scheduler.start()

    print("Bot is running...")
    bot.infinity_polling()

