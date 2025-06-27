from telebot import TeleBot
from flask import Flask
from waitress import serve
import threading
from apscheduler.schedulers.background import BackgroundScheduler
import warnings

from config import TOKEN, PORT
from handlers import register_handlers
from schedulers import setup_scheduler
from notifier import setup_notifications

warnings.filterwarnings("ignore", message="Timezone offset does not match system offset")

# Проверка на наличие токена
if not TOKEN:
    raise ValueError("❌ Переменная окружения TOKEN не установлена. Добавь её в Railway Variables или .env файл.")

# Инициализация бота
bot = TeleBot(TOKEN)

# Flask-сервер
app = Flask(__name__)

@app.route('/')
def index():
    return "✅ BPN Teletime бот работает."

def run_flask():
    serve(app, host='0.0.0.0', port=PORT)

if __name__ == '__main__':
    # Запуск Flask в отдельном потоке
    threading.Thread(target=run_flask).start()

    # Регистрация всех хендлеров
    register_handlers(bot)

    # Настройка планировщика
    scheduler = BackgroundScheduler()
    setup_scheduler(scheduler, bot)
    setup_notifications(scheduler, bot)
    scheduler.start()

    print("🤖 Бот запущен. Ожидаем команды...")
    bot.infinity_polling()
