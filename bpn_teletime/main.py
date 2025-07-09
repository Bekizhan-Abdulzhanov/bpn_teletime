import os
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from telebot import TeleBot, apihelper
from flask import Flask
from waitress import serve
from apscheduler.schedulers.background import BackgroundScheduler

from config import TOKEN, PORT
from handlers import register_handlers
from admin_handlers import register_admin_handlers
from schedulers import setup_scheduler
from notifier import setup_notifications

# Таймзона Бишкек
TS_ZONE = ZoneInfo("Asia/Bishkek")

bot = TeleBot(TOKEN)
app = Flask(__name__)

# Перед polling сбросим вебхук
bot.remove_webhook()

# Регистрируем обычные и админские хендлеры
register_handlers(bot)
register_admin_handlers(bot)

# Планировщик в зоне TS_ZONE
scheduler = BackgroundScheduler(timezone=TS_ZONE)
setup_scheduler(scheduler, bot)
setup_notifications(scheduler, bot)
scheduler.start() 
print(f"[{datetime.now(TS_ZONE)}] [SCHEDULER] Запущен в {TS_ZONE}")

@app.route("/")
def index():
    return "Bot is running!"

def run_flask():
    serve(app, host="0.0.0.0", port=int(PORT))

if __name__ == "__main__":
    # Flask в фоне
    threading.Thread(target=run_flask, daemon=True).start()
    print(f"[{datetime.now(TS_ZONE)}] Веб-сервер запущен на порту {PORT}")

    # Запускаем polling с автоперезапуском при 409 Conflict
    print(f"[{datetime.now(TS_ZONE)}] Запускаем polling бота…")
    while True:
        try:
            bot.infinity_polling(skip_pending=True)
        except apihelper.ApiTelegramException as e:
            if e.error_code == 409 and "Conflict" in e.result_json.get("description", ""):
                print(f"[{datetime.now(TS_ZONE)}] [WARN] Conflict 409 — сброс webhook и retry")
                bot.remove_webhook()
                time.sleep(1)
                continue
            raise

