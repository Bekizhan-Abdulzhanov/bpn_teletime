from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from config import ADMIN_IDS
from storage import get_all_users
from reports import generate_excel_report_by_months
from telebot.types import InputFile

REMINDERS = [
    ("Вы уже в пути на работу? Не забудьте отметить!", 8, 28),
    ("Приятного аппетита! Не забудьте отметить!", 11, 58),
    ("Желаю вам продуктивной работы! Не забудьте отметить!", 13, 58),
    ("✅ Вы сегодня отлично поработали! Не забудьте отметить!", 17, 28),
]

def setup_notifications(scheduler, bot):
    def notify_all(text):
        for uid in get_all_users():
            try:
                bot.send_message(uid, text)
            except Exception as e:
                print(f"[ERROR] Не удалось уведомить {uid}: {e}")

    # Уведомления будние дни
    for text, h, m in REMINDERS:
        scheduler.add_job(
            notify_all,
            CronTrigger(day_of_week='mon-fri', hour=h, minute=m),
            args=[text]
        )

    # Ежедневный отчёт в 18:00
    def daily_report():
        for uid, name in get_all_users().items():
            try:
                rep = generate_excel_report_by_months(uid, name)
                if rep:
                    fn = f"Отчёт_{name}_{datetime.now():%d.%m.%Y}.xlsx"
                    bot.send_document(uid, InputFile(rep, fn))
                else:
                    bot.send_message(uid, "⚠️ Сегодняшний отчёт не найден.")
            except Exception as e:
                print(f"[ERROR] Не удалось отправить отчёт {uid}: {e}")

    scheduler.add_job(
        daily_report,
        CronTrigger(day_of_week='mon-fri', hour=18, minute=0)
    )

    print("[SCHEDULER] Уведомления и ежедневные отчёты настроены.")

