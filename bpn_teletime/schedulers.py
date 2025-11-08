# schedulers.py
from datetime import datetime
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from telebot.types import InputFile

from storage import save_work_time, is_auto_enabled, get_all_users
from reports import generate_excel_report_by_months
from config import ADMIN_IDS, TIMEZONE, AUTO_APPROVED_USERS, EMPLOYEE_USERS

TS_ZONE = ZoneInfo(TIMEZONE)

# Расписание авто-отметок:
# - Приход/уход поминутно по дням (как у тебя было).
# - ОБЕД каждый будний день: 12:30 (выход) и 13:00 (возврат).
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


def _all_targets() -> dict[int, str]:
    """
    Объединённый список пользователей для месячных отчётов:
      - approved из users.csv
      - AUTO_APPROVED_USERS
      - EMPLOYEE_USERS
    """
    targets: dict[int, str] = {}

    # approved из users.csv
    for uid_str, uname in get_all_users().items():
        try:
            targets[int(uid_str)] = uname or f"user_{uid_str}"
        except ValueError:
            continue

    # full-auto
    for uid, name in AUTO_APPROVED_USERS.items():
        targets[int(uid)] = name

    # сотрудники (обед-авто)
    for uid, name in EMPLOYEE_USERS.items():
        targets[int(uid)] = name

    return targets


def _send_reports(bot):
    """
    Ежемесячные отчёты всем администраторам:
    отправляем Excel по каждому пользователю из _all_targets().
    """
    month = datetime.now(TS_ZONE).strftime("%Y-%m")
    targets = _all_targets()

    for admin in ADMIN_IDS:
        try:
            bot.send_message(admin, f"📦 Ежемесячные отчёты за {month}")
        except Exception as e:
            print(f"[REPORTS][WARN] cannot notify admin {admin}: {e}")

        for uid, name in targets.items():
            try:
                buf = generate_excel_report_by_months(uid, name)
                if buf:
                    bot.send_document(admin, InputFile(buf, f"Report_{name}_{month}.xlsx"))
                else:
                    bot.send_message(admin, f"⚠️ Нет данных для {name}")
            except Exception as e:
                print(f"[REPORTS][ERROR] send to admin={admin}, uid={uid}, name={name}: {e}")


def setup_scheduler(scheduler: BackgroundScheduler, bot):
    # Сносим старые задачи
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

    # Рассылка ежемесячных отчётов (29 и 30 числа в 08:30, по Бишкеку)
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
