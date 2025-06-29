from telebot import TeleBot
from flask import Flask
from waitress import serve
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import os
import warnings

from config import TOKEN, PORT
from handlers import register_handlers
from admin_handlers import register_admin_handlers
from schedulers import setup_scheduler
from notifier import setup_notifications

warnings.filterwarnings("ignore", message="Timezone offset does not match system offset")
load_dotenv()

bot = TeleBot(TOKEN)
app = Flask(__name__)

# Регистрация обработчиков
register_handlers(bot)
register_admin_handlers(bot)

# Планировщик
scheduler = BackgroundScheduler()
setup_scheduler(scheduler, bot)
setup_notifications(scheduler, bot)
scheduler.start()

@app.route("/")
def index():
    return "🤖 BPN TeleTime бот работает!"

if __name__ == "__main__":
    # Запуск Flask + Telegram Polling
    print("[SCHEDULER] Уведомления и ежедневные отчёты настроены.\n")
    print("🤖 Бот запущен. Ожидаем команды...")

    if os.getenv("RAILWAY_ENVIRONMENT"):  # Railway
        serve(app, host="0.0.0.0", port=PORT)
    else:
        app.run(host="0.0.0.0", port=PORT)
    
    bot.infinity_polling(skip_pending=True)
