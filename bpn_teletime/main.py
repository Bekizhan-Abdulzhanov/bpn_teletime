import os
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from telebot import TeleBot, apihelper
from flask import Flask
from waitress import serve
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import SchedulerAlreadyRunningError

from config import TOKEN, PORT
from handlers import register_handlers
from admin_handlers import register_admin_handlers
from schedulers import setup_scheduler
from notifier import setup_notifications

# --- Инициализация ---
TS_ZONE = ZoneInfo("Asia/Bishkek")
bot = TeleBot(TOKEN)
app = Flask(__name__)

# Сброс webhook перед polling
bot.remove_webhook()

# Регистрируем хендлеры
register_handlers(bot)
register_admin_handlers(bot)

# Настраиваем планировщик
scheduler = BackgroundScheduler(timezone=TS_ZONE)
setup_scheduler(scheduler, bot)
setup_notifications(scheduler, bot)
# Старт планировщика (если ещё не запущен)
try:
    if not scheduler.running:
        scheduler.start()
except SchedulerAlreadyRunningError:
    print(f"[{datetime.now(TS_ZONE)}] [WARN] Планировщик уже запущен")

print(f"[{datetime.now(TS_ZONE)}] [SCHEDULER] Запущен (Asia/Bishkek)")

# --- Веб-сервер для health check ---
@app.route("/")
def index():
    return "Bot is running!"

def run_flask():
    serve(app, host="0.0.0.0", port=int(PORT))

if __name__ == "__main__":
    # Запускаем Flask в фоне
    threading.Thread(target=run_flask, daemon=True).start()
    print(f"[{datetime.now(TS_ZONE)}] Веб-сервер запущен на порту {PORT}")

    # Основной цикл polling с обработкой конфликта 409
    print(f"[{datetime.now(TS_ZONE)}] Запускаем polling бота…")
    while True:
        try:
            bot.infinity_polling(skip_pending=True)
        except apihelper.ApiTelegramException as e:
            if e.error_code == 409 and "Conflict" in e.result_json.get("description", ""):
                print(f"[{datetime.now(TS_ZONE)}] [WARN] Conflict 409, сброс webhook и retry")
                bot.remove_webhook()
                time.sleep(1)
                continue
            raise

