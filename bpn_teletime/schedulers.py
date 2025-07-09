from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from telebot.types import InputFile

from storage import save_work_time, is_auto_enabled
from reports import generate_excel_report_by_months
from config import ADMIN_IDS

# Часовая зона Бишкек (UTC+6)
TS_ZONE = ZoneInfo("Asia/Bishkek")

# Пользователи, имеющие право на авто-режим
AUTO_USERS = {
    378268765: "ErlanNasiev",
    557174721: "BekizhanAbdulzhanov",
}

# Расписание автоматических меток (будни)
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


def auto_mark_all_users(action: str):
    """
    Сохраняет метку для каждого пользователя из AUTO_USERS,
    если авто-режим включён.
    """
    timestamp = datetime.now(TS_ZONE).strftime("%Y-%m-%d %H:%M:%S")
    for uid in AUTO_USERS:
        if is_auto_enabled(uid):
            save_work_time(uid, action, timestamp)


def send_monthly_reports(bot):
    """
    Отправляет всем администраторам Excel-отчёты за прошлый месяц.
    """
    month_str = datetime.now(TS_ZONE).strftime("%Y-%m")
    for admin_id in ADMIN_IDS:
        bot.send_message(admin_id, f"📊 Ежемесячные отчёты за {month_str}:")
        for uid, username in AUTO_USERS.items():
            report_buf = generate_excel_report_by_months(uid, username)
            if report_buf:
                filename = f"Report_{username}_{month_str}.xlsx"
                bot.send_document(admin_id, InputFile(report_buf, filename))
            else:
                bot.send_message(admin_id, f"⚠️ Нет данных для {username}.")


def setup_scheduler(scheduler: BackgroundScheduler, bot):
    """
    Настраивает задачи APScheduler:
    1) Автоматические метки по расписанию для AUTO_USERS.
    2) Ежемесячная рассылка Excel-отчётов 29 и 30 числа в 08:30.
    """
    # Удаляем старые задачи, чтобы избежать дублирования
    scheduler.remove_all_jobs()

    # 1) Автоматические ежедневные метки
    for dow, hour, minute, action in SCHEDULE_ACTIONS:
        scheduler.add_job(
            auto_mark_all_users,
            trigger=CronTrigger(day_of_week=dow, hour=hour, minute=minute, timezone=TS_ZONE),
            args=[action],
            id=f"auto_{action.replace(' ', '_')}"
        )

    # 2) Ежемесячная рассылка 29 и 30 числа в 08:30
    scheduler.add_job(
        send_monthly_reports,
        trigger=CronTrigger(day="29,30", hour=8, minute=30, timezone=TS_ZONE),
        args=[bot],
        id="monthly_reports"
    )

    scheduler.start()
    print(f"[{datetime.now(TS_ZONE)}] [SCHEDULER] Авто-режим и рассылка настроены (Asia/Bishkek)")
