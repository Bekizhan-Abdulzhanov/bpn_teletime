import os
import threading
import warnings
from flask import Flask
from waitress import serve
from telebot import TeleBot
from apscheduler.schedulers.background import BackgroundScheduler

from config import TOKEN, PORT
from handlers import register_handlers
from admin_handlers import register_admin_handlers
from schedulers import setup_scheduler
from notifier import setup_notifications

# 🔕 Игнорируем предупреждение про таймзону
warnings.filterwarnings("ignore", message="Timezone offset does not match system offset")

# 🛑 Проверка: токен должен быть задан
if not TOKEN:
    raise ValueError("❌ Переменная окружения TOKEN не установлена. Добавь её в Railway Variables или .env файл.")

# 🤖 Инициализация бота
bot = TeleBot(TOKEN)

# 🌐 Flask-сервер для Railway ping или healthcheck
app = Flask(__name__)

@app.route('/')
def index():
    return "✅ BPN Teletime бот работает."

def run_flask():
    serve(app, host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    # 🔁 Запускаем Flask-сервер в фоне (для Railway)
    threading.Thread(target=run_flask).start()

    # 📦 Регистрируем хендлеры
    register_handlers(bot)
    register_admin_handlers(bot)

    # 🗓 Планировщик задач
    scheduler = BackgroundScheduler()
    setup_scheduler(scheduler, bot)
    setup_notifications(scheduler, bot)
    scheduler.start()

    print("🤖 Бот запущен. Ожидаем команды...")

    # 🧹 Удаляем старый webhook на всякий случай
    bot.remove_webhook()

    # 🚀 Запускаем polling (основной режим работы)
    bot.infinity_polling(skip_pending=True)
