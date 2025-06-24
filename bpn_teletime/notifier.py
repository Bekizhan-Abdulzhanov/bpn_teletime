from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from config import ADMIN_ID
from storage import get_all_users

# ✅ Уведомления для всех пользователей
def setup_notifications(scheduler, bot):
    def send_reminder_all_users(text):
        for user_id in get_all_users().keys():
            try:
                bot.send_message(user_id, text)
            except Exception as e:
                print(f"[ERROR] Не удалось отправить сообщение пользователю {user_id}: {e}")

    scheduler.add_job(send_reminder_all_users, CronTrigger(hour=8, minute=28), args=["🌞 Вы уже в пути на работу? Не забудьте меня отметить 🙂"])
    scheduler.add_job(send_reminder_all_users, CronTrigger(hour=11, minute=58), args=["🍽 Приятного аппетита! Не забудьте меня отметить 🙂"])
    scheduler.add_job(send_reminder_all_users, CronTrigger(hour=13, minute=58), args=["💼 Желаю вам продуктивной работы! Не забудьте меня отметить 🙂"])
    scheduler.add_job(send_reminder_all_users, CronTrigger(hour=17, minute=28), args=["✅ Вы сегодня хорошо поработали! Не забудьте меня отметить 🙂"])

    print("[SCHEDULER] Уведомления настроены.")

