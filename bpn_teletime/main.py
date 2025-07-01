import os
import threading

from telebot import TeleBot
from flask import Flask
from waitress import serve
from apscheduler.schedulers.background import BackgroundScheduler

from config import TOKEN, PORT
from handlers import register_handlers
from admin_handlers import register_admin_handlers
from schedulers import setup_scheduler
from notifier import setup_notifications

# --- Инициализация бота и веб-сервера ---
bot = TeleBot(TOKEN)
app = Flask(__name__)

# Регистрируем обработчики команд
register_handlers(bot)
register_admin_handlers(bot)

# --- Настройка и запуск планировщика ---
scheduler = BackgroundScheduler()
# Передаём в функции сам экземпляр планировщика и объект бота
setup_scheduler(scheduler, bot)
setup_notifications(scheduler, bot)
scheduler.start()

# --- Простая HTTP-страница для проверки работоспособности ---
@app.route("/")
def index():
    return "Bot is running!"

def run_flask():
    # PORT из .env может быть строкой, приводим к int
    serve(app, host="0.0.0.0", port=int(PORT))

if __name__ == "__main__":
    # Запускаем Flask в отдельном потоке
    threading.Thread(target=run_flask, daemon=True).start()
    print("Бот и веб-сервер запущены.")
    # Запускаем бота
    bot.infinity_polling(skip_pending=True)



