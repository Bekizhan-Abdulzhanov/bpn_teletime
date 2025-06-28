from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from config import ADMIN_IDS
from storage import get_all_users
from reports import generate_excel_report_by_months
from telebot.types import InputFile


REMINDERS = [
    ("🌞 Вы уже в пути на работу? Не забудьте меня отметить 🙂", 8, 28),
    ("🍽 Приятного аппетита! Не забудьте меня отметить 🙂", 11, 58),
    ("💼 Желаю вам продуктивной работы! Не забудьте меня отметить 🙂", 13, 58),
    ("✅ Вы сегодня хорошо поработали! Не забудьте меня отметить 🙂", 17, 28),
]

def setup_notifications(scheduler, bot):
    def notify_all_users(text):
        for uid in get_all_users():
            try:
                bot.send_message(uid, text)
            except Exception as e:
                print(f"[ERROR] Не удалось отправить {uid}: {e}")

    # Уведомления по расписанию (только по будням)
    for text, hour, minute in REMINDERS:
        scheduler.add_job(
            notify_all_users,
            CronTrigger(day_of_week='mon-fri', hour=hour, minute=minute),
            args=[text]
        )

    # Ежедневная отправка Excel-отчета в 18:00
    def send_daily_reports():
        users = get_all_users()
        for user_id, username in users.items():
            try:
                file = generate_excel_report_by_months(user_id, username)
                if file:
                    filename = f"Отчёт_{username}_{datetime.now().strftime('%d.%m.%Y')}.xlsx"
                    bot.send_document(user_id, InputFile(file, filename), caption="📊 Ваш ежедневный отчёт.")
                else:
                    bot.send_message(user_id, "⚠️ Сегодняшний отчёт не найден.")
            except Exception as e:
                print(f"[ERROR] Не удалось отправить отчёт {user_id}: {e}")

    scheduler.add_job(
        send_daily_reports,
        CronTrigger(day_of_week='mon-fri', hour=18, minute=0)
    )

    print("[SCHEDULER] Уведомления и ежедневные отчёты настроены.")

