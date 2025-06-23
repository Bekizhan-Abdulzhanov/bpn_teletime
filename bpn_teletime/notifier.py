from apscheduler.schedulers.background import BackgroundScheduler
from telebot import TeleBot
from config import TOKEN
from storage import get_all_users

bot = TeleBot(TOKEN)
scheduler = BackgroundScheduler(timezone='Asia/Bishkek')

def send_reminder_to_all_users(text):
    users = get_all_users()
    for user_id in users:
        try:
            bot.send_message(user_id, text)
        except Exception as e:
            print(f"[ERROR] Не удалось отправить сообщение {user_id}: {e}")

def setup_notifications():
    scheduler.add_job(lambda: send_reminder_to_all_users("Вы уже в пути на работу? Не забудьте меня отметить 😊"), 'cron', hour=8, minute=28)
    scheduler.add_job(lambda: send_reminder_to_all_users("Приятного аппетита! Не забудьте меня отметить 😊"), 'cron', hour=11, minute=58)
    scheduler.add_job(lambda: send_reminder_to_all_users("Желаю вам продуктивной работы! Не забудьте меня отметить 😊"), 'cron', hour=13, minute=58)
    scheduler.add_job(lambda: send_reminder_to_all_users("Вы сегодня хорошо поработали! Не забудьте меня отметить 😊"), 'cron', hour=17, minute=28)
    scheduler.start()
