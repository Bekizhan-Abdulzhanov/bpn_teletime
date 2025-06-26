from telebot import TeleBot, types
from flask import Flask, request
from waitress import serve
import threading
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

@app.route('/')
def index():
    return "Bot is running."

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return 'ok', 200

def run_flask():
    serve(app, host='0.0.0.0', port=PORT)

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()

    register_handlers(bot)
    register_admin_handlers(bot)
    print("🤖 Хендлеры готовы.")

    scheduler = BackgroundScheduler()
    setup_scheduler(scheduler, bot)
    setup_notifications(scheduler, bot)
    scheduler.start()

    RAILWAY_DOMAIN = os.getenv("RAILWAY_PUBLIC_DOMAIN")
    if RAILWAY_DOMAIN:
        webhook_url = f"https://{RAILWAY_DOMAIN}/{TOKEN}"
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)
        print("📡 Webhook установлен:", webhook_url)
    else:
        print("❌ RAILWAY_PUBLIC_DOMAIN не задана!")

    print("Бот запущен.")

