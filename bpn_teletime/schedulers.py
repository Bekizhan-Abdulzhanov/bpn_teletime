# schedulers.py
from datetime import datetime
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from telebot.types import InputFile

from storage import save_work_time, is_auto_enabled
from reports import generate_excel_report_by_months
from config import ADMIN_IDS, TIMEZONE, AUTO_APPROVED_USERS, EMPLOYEE_USERS

TS_ZONE = ZoneInfo(TIMEZONE)

# Расписание авто-отметок:
# - Приход/уход оставлены поминутно по дням (как было у тебя).
# - ОБЕД для каждого буднего дня: 12:30 (выход) и 13:00 (возврат).
SCHEDULE_ACTIONS = [
    # Понедельник
    ("mon", 8, 29, "Пришел на работу"),
    ("mon", 12, 30, "Вышел на обед"),
    ("mon", 13,  0, "Вернулся с обеда"),
    ("mon", 17, 29, "Ушел с работы"),

    # Вторник
    ("tue", 8, 28, "Пришел на работу"),
    ("tue", 12, 30, "Вышел на обед"),
    ("tue", 13,  0, "Вернулся с обеда"),
    ("tue", 17, 30, "Ушел с работы"),

    # Среда
    ("wed", 8, 27, "Пришел на работу"),
    ("wed", 12, 30, "Вышел на обед"),
    ("wed", 13,  0, "Вернулся с обеда"),
    ("wed", 17, 28, "Ушел с работы"),

    # Четверг
    ("thu", 8, 26, "Пришел на работу"),
    ("thu", 12, 30, "Вышел на обед"),
    ("thu", 13,  0, "Вернулся с обеда"),
    ("thu", 17, 30, "Ушел с работы"),

    # Пятница
    ("fri", 8, 30, "Пришел на работу"),
    ("fri", 12, 30, "Вышел на обед"),
    ("fri", 13,  0, "Вернулся с обеда"),
    ("fri", 17, 30, "Ушел с работы"),
]

# Для EMPLOYEE_USERS в авто-режиме разрешаем только эти события (обед)
LUNCH_ACTIONS = {"Вышел на обед", "Вернулся с обеда"}


def _auto_mark(action: str):
    """
    Автоматические отметки:
      - AUTO_APPROVED_USERS: все события из расписания
      - EMPLOYEE_USERS: только обед (выход/возврат)
    Работает только если у пользователя включён авто-режим (is_auto_enabled).
    """
    ts = datetime.now(TS_ZONE).strftime("%Y-%m-%d %H:%M:%S")

    # Полный авто-режим (все события из SCHEDULE_ACTIONS)
    for uid in AUTO_APPROVED_USERS.keys():
        if is_auto_enabled(uid):
            save_work_time(uid, action, ts)

    # Сотрудники — только обед
    if action in LUNCH_ACTIONS:
        for uid in EMPLOYEE_USERS.keys():
            if is_auto_enabled(uid):
                save_work_time(uid, action, ts)


def _send_reports(bot):
    month = datetime.now(TS_ZONE).strftime("%Y-%m")
    for admin in ADMIN_IDS:
        bot.send_message(admin, f"📊 Отчёты за {month}:")
        all_trusted = {**AUTO_APPROVED_USERS, **EMPLOYEE_USERS}
        for uid, name in all_trusted.items():
            buf = generate_excel_report_by_months(uid, name)
            if buf:
                bot.send_document(admin, InputFile(buf, f"Report_{name}_{month}.xlsx"))
            else:
                bot.send_message(admin, f"⚠️ Нет данных для {name}.")


def setup_scheduler(scheduler: BackgroundScheduler, bot):
    scheduler.remove_all_jobs()

    # Авто-отметки по расписанию
    for dow, hr, mn, act in SCHEDULE_ACTIONS:
        scheduler.add_job(
            _auto_mark,
            CronTrigger(day_of_week=dow, hour=hr, minute=mn, timezone=TS_ZONE),
            args=[act],
            id=f"auto_{dow}_{hr:02d}{mn:02d}_{act.replace(' ', '_')}",
            replace_existing=True,
            coalesce=True,
            misfire_grace_time=3600,
            max_instances=1,
        )

    # Рассылка отчётов (пример: 29/30 числа в 08:30)
    scheduler.add_job(
        _send_reports,
        CronTrigger(day="29,30", hour=8, minute=30, timezone=TS_ZONE),
        args=[bot],
        id="monthly_reports",
        replace_existing=True,
        coalesce=True,
        misfire_grace_time=3600,
        max_instances=1,
    )
