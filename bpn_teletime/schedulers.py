from datetime import datetime
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from telebot.types import InputFile

from storage import save_work_time, is_auto_enabled
from reports import generate_excel_report_by_months
from config import ADMIN_IDS

TS_ZONE = ZoneInfo("Asia/Bishkek")
AUTO_USERS = {
    378268765: "ErlanNasiev",
    557174721: "BekizhanAbdulzhanov",
}
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

def auto_mark(action: str):
    ts = datetime.now(TS_ZONE).strftime("%Y-%m-%d %H:%M:%S")
    for uid in AUTO_USERS:
        if is_auto_enabled(uid):
            save_work_time(uid, action, ts)

def send_reports(bot):
    month = datetime.now(TS_ZONE).strftime("%Y-%m")
    for admin in ADMIN_IDS:
        bot.send_message(admin, f"📊 Отчёты за {month}:")
        for uid, name in AUTO_USERS.items():
            buf = generate_excel_report_by_months(uid, name)
            if buf:
                bot.send_document(admin, InputFile(buf, f"Report_{name}_{month}.xlsx"))
            else:
                bot.send_message(admin, f"⚠️ Нет данных для {name}.")

def setup_scheduler(scheduler: BackgroundScheduler, bot):
    scheduler.remove_all_jobs()
    for dow, hr, mn, act in SCHEDULE_ACTIONS:
        scheduler.add_job(
            auto_mark,
            CronTrigger(day_of_week=dow, hour=hr, minute=mn, timezone=TS_ZONE),
            args=[act],
            id=f"auto_{dow}_{act.replace(' ', '_')}"
        )
    scheduler.add_job(
        send_reports,
        CronTrigger(day="29,30", hour=8, minute=30, timezone=TS_ZONE),
        args=[bot],
        id="monthly_reports"
    )
    scheduler.start()

