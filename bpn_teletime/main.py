from telebot import TeleBot
from flask import Flask
from waitress import serve
import threading
import os

from config import TOKEN, PORT
from handlers import register_handlers
from admin_handlers import register_admin_handlers
from schedulers import setup_scheduler
from notifier import setup_notifications

bot = TeleBot(TOKEN)
app = Flask(__name__)

# Регистрируем все хендлеры
register_handlers(bot)
register_admin_handlers(bot)

# Планировщик задач (ежедневные автоотметки)
scheduler = setup_scheduler(bot)
setup_notifications(bot)

# Фоновый поток Flask
@app.route("/")
def index():
    return "Bot is running!"

def run_flask():
    serve(app, host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    print("🤖 Бот запущен. Ожидаем команды...")
    bot.infinity_polling(skip_pending=True)

