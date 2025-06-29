from telebot import TeleBot
from flask import Flask
from waitress import serve
import threading
from apscheduler.schedulers.background import BackgroundScheduler
import warnings
from config import TOKEN, PORT
from handlers import register_handlers
from admin_handlers import register_admin_handlers
from schedulers import setup_scheduler
from notifier import setup_notifications

warnings.filterwarnings("ignore", message="Timezone offset does not match system offset")

if not TOKEN:
    raise ValueError("❌ Переменная окружения TOKEN не установлена.")

bot = TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def index():
    return "✅ BPN Teletime бот работает."

def run_flask():
    serve(app, host='0.0.0.0', port=PORT)

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    register_handlers(bot)
    register_admin_handlers(bot)

    scheduler = BackgroundScheduler()
    setup_scheduler(scheduler, bot)
    setup_notifications(scheduler, bot)
    scheduler.start()

    # ❗ Удаляем старый webhook перед polling
    bot.remove_webhook()

    print("🤖 Бот запущен. Ожидаем команды...")
    bot.infinity_polling(skip_pending=True)
