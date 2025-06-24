from apscheduler.schedulers.background import BackgroundScheduler
from storage import save_work_time, get_all_users
from reports import generate_excel_report_by_months
from datetime import datetime
import os
import telebot
import dotenv
import config

# ✅ Конфигурация
dotenv.load_dotenv()
ADMIN_ID = int(os.getenv("ADMIN_ID", config.ADMIN_ID))  # Поддержка из .env или config

# ✅ Список пользователей, для которых автоматическая отметка
AUTO_USERS = {
    378268765: "ErlanNasiev",
    557174721: "BekizhanAbdulzhanov",
}

# ✅ Настройка автоматических отметок по дням недели
def setup_scheduler(scheduler, bot):
    # Автоматическая отправка отчета админу 29, 30 и 27 февраля в 8:30
    scheduler.add_job(
        send_monthly_reports_to_admin,
        "cron",
        day="29,30",
        month="1-12",
        hour=8,
        minute=30,
        args=[bot],
        id="send_monthly_reports_default"
    )
    scheduler.add_job(
        send_monthly_reports_to_admin,
        "cron",
        day="27",
        month="2",
        hour=8,
        minute=30,
        args=[bot],
        id="send_monthly_reports_feb"
    )

    for user_id, name in AUTO_USERS.items():
        # Понедельник и Среда
        scheduler.add_job(save_work_time, 'cron', day_of_week='mon,wed', hour=8, minute=29, args=[user_id, name, 'Пришел на работу'])
        scheduler.add_job(save_work_time, 'cron', day_of_week='mon,wed', hour=12, minute=0, args=[user_id, name, 'Вышел на обед'])
        scheduler.add_job(save_work_time, 'cron', day_of_week='mon,wed', hour=13, minute=0, args=[user_id, name, 'Вернулся с обеда'])
        scheduler.add_job(save_work_time, 'cron', day_of_week='mon,wed', hour=17, minute=30, args=[user_id, name, 'Ушел с работы'])

        # Вторник и Четверг
        scheduler.add_job(save_work_time, 'cron', day_of_week='tue,thu', hour=8, minute=28, args=[user_id, name, 'Пришел на работу'])
        scheduler.add_job(save_work_time, 'cron', day_of_week='tue,thu', hour=12, minute=1, args=[user_id, name, 'Вышел на обед'])
        scheduler.add_job(save_work_time, 'cron', day_of_week='tue,thu', hour=13, minute=0, args=[user_id, name, 'Вернулся с обеда'])
        scheduler.add_job(save_work_time, 'cron', day_of_week='tue,thu', hour=17, minute=30, args=[user_id, name, 'Ушел с работы'])

        # Пятница
        scheduler.add_job(save_work_time, 'cron', day_of_week='fri', hour=8, minute=27, args=[user_id, name, 'Пришел на работу'])
        scheduler.add_job(save_work_time, 'cron', day_of_week='fri', hour=12, minute=0, args=[user_id, name, 'Вышел на обед'])
        scheduler.add_job(save_work_time, 'cron', day_of_week='fri', hour=13, minute=0, args=[user_id, name, 'Вернулся с обеда'])
        scheduler.add_job(save_work_time, 'cron', day_of_week='fri', hour=17, minute=30, args=[user_id, name, 'Ушел с работы'])

# ✅ Функция отправки отчётов админу

def send_monthly_reports_to_admin(bot):
    now = datetime.now()
    month_name = now.strftime('%B')

    bot.send_message(ADMIN_ID, f"📦 Отправка отчетов за {month_name}:")

    all_users = get_all_users()
    for user_id, username in all_users.items():
        report_path = generate_excel_report_by_months(user_id, username)
        if report_path and os.path.exists(report_path):
            with open(report_path, 'rb') as file:
                bot.send_document(ADMIN_ID, file, caption=f"📎 Отчет: {username}")
        else:
            bot.send_message(ADMIN_ID, f"⚠️ Нет данных для пользователя: {username}")
