import os
import threading
import time
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

# --- Инициализация бота и Flask ---
bot = TeleBot(TOKEN)
app = Flask(__name__)

# Сбрасываем все вебхуки перед любым polling (освобождаем getUpdates)
bot.remove_webhook()

# Регистрируем все обработчики
register_handlers(bot)
register_admin_handlers(bot)

# --- Планировщик в часовом поясе Asia/Bishkek (UTC+6) ---
TZ = ZoneInfo("Asia/Bishkek")
scheduler = BackgroundScheduler(timezone=TZ)
# Если у вас setup_scheduler принимает (bot) и создаёт внутри scheduler, замените вызов соответственно.
# Здесь мы передаём экземпляры обоих:
setup_scheduler(scheduler, bot)
setup_notifications(scheduler, bot)
scheduler.start()
print("[SCHEDULER] Ежедневные отметки и ежемесячные отчёты настроены (Asia/Bishkek).")

# --- Простой HTTP endpoint для проверки alive ---
@app.route("/")
def index():
    return "Bot is running!"

def run_flask():
    serve(app, host="0.0.0.0", port=int(PORT))

if __name__ == "__main__":
    # Запускаем Flask в отдельном потоке
    threading.Thread(target=run_flask, daemon=True).start()
    print(f"Веб-сервер запущен на порту {PORT}")

    # Основной цикл polling с обработкой конфликта 409
    print("Запускаем polling бота…")
    while True:
        try:
            bot.infinity_polling(skip_pending=True)
        except apihelper.ApiTelegramException as e:
            # Если конфликт вебхуков, сбрасываем и пробуем снова
            if e.error_code == 409 and "Conflict" in e.result_json.get("description", ""):
                print("[WARN] Conflict 409: другой getUpdates, сбрасываем webhook и перезапускаем polling.")
                try:
                    bot.remove_webhook()
                except Exception:
                    pass
                time.sleep(1)
                continue
            # Для любых остальных ошибок — прекращаем
            raise


