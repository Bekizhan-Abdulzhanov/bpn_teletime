from datetime import datetime
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from telebot.types import InputFile

from storage import save_work_time, get_all_users, is_auto_enabled
from reports import generate_excel_report_by_months
from config import ADMIN_IDS

# Часовая зона Бишкека (UTC+6)
TS_ZONE = ZoneInfo("Asia/Bishkek")

# Список пользователей, участвующих в авто-режиме
AUTO_USERS = {
    378268765: "ErlanNasiev",
    557174721: "BekizhanAbdulzhanov",
}

# Расписание автоматических меток
SCHEDULE_ACTIONS = [
    ("mon,wed", 8, 29, "Пришел на работу"),
    ("mon,wed", 12,  0, "Вышел на обед"),
    ("mon,wed", 13,  0, "Вернулся с обеда"),
    ("mon,wed", 17, 30, "Ушел с работы"),
    ("tue,thu", 8, 28, "Пришел на работу"),
    ("tue,thu", 12,  1, "Вышел на обед"),
    ("tue,thu", 13,  0, "Вернулся с обеда"),
    ("tue,thu", 17, 30, "Ушел с работы"),
    ("fri",     8, 27, "Пришел на работу"),
    ("fri",    12,  0, "Вышел на обед"),
    ("fri",    13,  0, "Вернулся с обеда"),
    ("fri",    17, 30, "Ушел с работы"),
]

def setup_scheduler(scheduler: BackgroundScheduler, bot):
    # Автоматические ежедневные метки (будни)
    for uid, username in AUTO_USERS.items():
        if not is_auto_enabled(uid):
            continue
        for dow, hour, minute, action in SCHEDULE_ACTIONS:
            scheduler.add_job(
                save_work_time,
                trigger="cron",
                day_of_week=dow,
                hour=hour,
                minute=minute,
                timezone=TS_ZONE,
                args=[uid, action, datetime.now(TS_ZONE).strftime("%Y-%m-%d %H:%M:%S")],
                id=f"auto_{uid}_{action.replace(' ', '_')}"
            )
    
    # Ежемесячные отчёты администраторам
    scheduler.add_job(
        send_monthly_reports_to_admins,
        trigger="cron",
        day="29,30",
        month="1-12",
        hour=8,
        minute=30,
        timezone=TS_ZONE,
        args=[bot],
        id="send_monthly_reports_default"
    )
    scheduler.add_job(
        send_monthly_reports_to_admins,
        trigger="cron",
        day="27",
        month="2",
        hour=8,
        minute=30,
        timezone=TS_ZONE,
        args=[bot],
        id="send_monthly_reports_feb"
    )


def send_monthly_reports_to_admins(bot):
    month_name = datetime.now(TS_ZONE).strftime('%B')
    users = get_all_users()
    for admin in ADMIN_IDS:
        bot.send_message(admin, f"Ежемесячные отчёты за {month_name}:")
        for uid, username in users.items():
            try:
                report = generate_excel_report_by_months(int(uid), username)
                if report:
                    fn = f"Отчет_{username}_{month_name}.xlsx"
                    bot.send_document(admin, InputFile(report, fn))
                else:
                    bot.send_message(admin, f"⚠️ Нет данных для {username}.")
            except Exception as e:
                bot.send_message(admin, f"❌ Ошибка для {username}: {e}")
