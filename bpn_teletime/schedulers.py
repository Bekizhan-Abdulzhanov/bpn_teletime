from apscheduler.schedulers.background import BackgroundScheduler
from storage import save_work_time, get_all_users, is_auto_enabled
from reports import generate_excel_report_by_months
from datetime import datetime
from telebot.types import InputFile
from config import ADMIN_IDS
from zoneinfo import ZoneInfo
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler

TS_ZONE = ZoneInfo("Asia/Bishkek")
scheduler = BackgroundScheduler(timezone=TS_ZONE)
AUTO_USERS = {
    378268765: "ErlanNasiev",
    557174721: "BekizhanAbdulzhanov",
}

def setup_scheduler(scheduler, bot):
    # Автоматические метки
    schedule_actions = [
        ("mon,wed", 8, 29, "Пришел на работу"),
        ("mon,wed", 12, 0, "Вышел на обед"),
        ("mon,wed", 13, 0, "Вернулся с обеда"),
        ("mon,wed", 17, 30, "Ушел с работы"),
        ("tue,thu", 8, 28, "Пришел на работу"),
        ("tue,thu", 12, 1, "Вышел на обед"),
        ("tue,thu", 13, 0, "Вернулся с обеда"),
        ("tue,thu", 17, 30, "Ушел с работы"),
        ("fri", 8, 27, "Пришел на работу"),
        ("fri", 12, 0, "Вышел на обед"),
        ("fri", 13, 0, "Вернулся с обеда"),
        ("fri", 17, 30, "Ушел с работы"),
    ]
    for uid, name in AUTO_USERS.items():
        if not is_auto_enabled(uid):
            continue
        for dow, h, m, act in schedule_actions:
            scheduler.add_job(
                save_work_time,
                trigger="cron",
                day_of_week=dow,
                hour=h,
                minute=m,
                args=[uid, name, act]
            )

    # Ежемесячные отчёты админам
    scheduler.add_job(
        send_monthly_reports_to_admins,
        "cron",
        day="29,30",
        month="1-12",
        hour=8,
        minute=30,
        args=[bot],
        id="send_monthly_reports_default"
    )
    scheduler.add_job(
        send_monthly_reports_to_admins,
        "cron",
        day="27",
        month="2",
        hour=8,
        minute=30,
        args=[bot],
        id="send_monthly_reports_feb"
    )

def send_monthly_reports_to_admins(bot):
    month_name = datetime.now().strftime('%B')
    users = get_all_users()
    for admin in ADMIN_IDS:
        bot.send_message(admin, f"Ежемесячные отчёты за {month_name}:")
        for uid, name in users.items():
            try:
                report = generate_excel_report_by_months(uid, name)
                if report:
                    fn = f"Отчет_{name}_{month_name}.xlsx"
                    bot.send_document(admin, InputFile(report, fn))
                else:
                    bot.send_message(admin, f"⚠️ Нет данных для {name}.")
            except Exception as e:
                bot.send_message(admin, f"❌ Ошибка для {name}: {e}")
