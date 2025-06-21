from telebot import TeleBot
from flask import Flask
from waitress import serve
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import os
from config import TOKEN, PORT
from schedulers import setup_scheduler
from handlers import register_handlers

load_dotenv()

bot = TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running."

def run_flask():
    serve(app, host='0.0.0.0', port=PORT)

if __name__ == '__main__':
    # Запуск Flask-сервера
    threading.Thread(target=run_flask).start()

    # Регистрация хендлеров
    register_handlers(bot)

    # Планировщик
    scheduler = BackgroundScheduler()
    setup_scheduler(scheduler)
    scheduler.start()

    print("Bot is running...")
    bot.infinity_polling()
