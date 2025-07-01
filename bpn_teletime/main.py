import os
import threading
from zoneinfo import ZoneInfo

from telebot import TeleBot
from flask import Flask
from waitress import serve
from apscheduler.schedulers.background import BackgroundScheduler

from config import TOKEN, PORT
from handlers import register_handlers
from admin_handlers import register_admin_handlers
from schedulers import setup_scheduler
from notifier import setup_notifications

bot = TeleBot(TOKEN)
app = Flask(__name__)

# Регистрируем хендлеры
register_handlers(bot)
register_admin_handlers(bot)

# Создаём планировщик в часовом поясе Asia/Bishkek (UTC+6)
scheduler = BackgroundScheduler(timezone=ZoneInfo("Asia/Bishkek"))
setup_scheduler(scheduler, bot)
setup_notifications(scheduler, bot)
scheduler.start()
print("[SCHEDULER] Уведомления и ежедневные отчёты настроены (Asia/Bishkek).")

@app.route("/")
def index():
    return "Bot is running!"

def run_flask():
    serve(app, host="0.0.0.0", port=int(PORT))

if __name__ == "__main__":
    bot.remove_webhook()
    threading.Thread(target=run_flask, daemon=True).start()
    print(f"Веб-сервер запущен на порту {PORT}")
    print("Запускаем polling бота…")
    bot.infinity_polling(skip_pending=True)



