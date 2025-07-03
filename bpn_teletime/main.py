import os
import threading
import time
from zoneinfo import ZoneInfo
from datetime import datetime

from telebot import TeleBot, apihelper
from flask import Flask
from waitress import serve
from apscheduler.schedulers.background import BackgroundScheduler

from config import TOKEN, PORT, ADMIN_IDS
from handlers import register_handlers
from admin_handlers import register_admin_handlers
from schedulers import setup_scheduler
from notifier import setup_notifications

# --- Инициализация бота и Flask ---
bot = TeleBot(TOKEN)
app = Flask(__name__)

# Сбрасываем вебхуки перед polling
bot.remove_webhook()

# Регистрируем хендлеры
register_handlers(bot)
register_admin_handlers(bot)

# --- Планировщик в Asia/Bishkek (UTC+6) ---
TZ = ZoneInfo("Asia/Bishkek")
scheduler = BackgroundScheduler(timezone=TZ)
setup_scheduler(scheduler, bot)
setup_notifications(scheduler, bot)
scheduler.start()
print(f"[{datetime.now(TZ)}] Планировщик запущен в {TZ}")

@app.route("/")
def index():
    return "Bot is running!"

def run_flask():
    serve(app, host="0.0.0.0", port=int(PORT))

if __name__ == "__main__":
    # Flask в фоне
    threading.Thread(target=run_flask, daemon=True).start()
    print(f"Веб-сервер запущен на порту {PORT}")

    # Основной цикл polling с авто-рестартом при 409
    print("Запускаем polling бота…")
    while True:
        try:
            bot.infinity_polling(skip_pending=True)
        except apihelper.ApiTelegramException as e:
            if e.error_code == 409 and "Conflict" in e.result_json.get("description",""):
                print("[WARN] Conflict 409: сбрасываем webhook и перезапускаем polling.")
                bot.remove_webhook()
                time.sleep(1)
                continue
            raise


