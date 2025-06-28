import os
import telebot
from flask import Flask, request
from config import TOKEN, PORT
from handlers import register_handlers
from admin_handlers import register_admin_handlers
from schedulers import setup_scheduler
from notifier import setup_notifications
from apscheduler.schedulers.background import BackgroundScheduler

# ✅ Инициализация
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ✅ Регистрация команд
register_handlers(bot)
register_admin_handlers(bot)

# ✅ Запуск задач по расписанию
scheduler = BackgroundScheduler()
setup_scheduler(scheduler, bot)
setup_notifications(scheduler, bot)
scheduler.start()

# ✅ Webhook URL (замени на свой домен Railway)
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Пример: https://bpn-bot-production.up.railway.app

@app.route("/", methods=["GET"])
def index():
    return "🤖 BPN Teletime работает (Webhook)."

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_data = request.get_json()
    if json_data:
        bot.process_new_updates([telebot.types.Update.de_json(json_data)])
    return "", 200

if __name__ == "__main__":
    # ✅ Установка webhook перед запуском Flask
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
    app.run(host="0.0.0.0", port=PORT)

