# notifier.py
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, time
from zoneinfo import ZoneInfo
from telebot.types import InputFile
import csv
import os

from config import (
    ADMIN_IDS,
    TIMEZONE,
    AUTO_APPROVED_USERS,
    EMPLOYEE_USERS,
)
from storage import get_all_users
from reports import generate_excel_report_by_months
from storage import WORKTIME_FILE  # абсолютный путь к CSV из storage

TS_ZONE = ZoneInfo(TIMEZONE)

# Время начала рабочего дня (после него считаем опоздание)
START_TIME = time(8, 30)

# Напоминания по дням
REMINDERS = [
    ("Вы уже в пути на работу? Не забудьте отметить!", 8, 28),
    ("✅ Вы сегодня отлично поработали! Не забудьте отметить!", 16, 45),
]

def _iter_all_targets() -> dict[int, str]:
    """
    Кого уведомлять/кому слать отчёты:
      - все 'approved' из users.csv (id -> username)
      - все из AUTO_APPROVED_USERS
      - все из EMPLOYEE_USERS
    Возвращаем единый словарь {user_id: name}
    """
    combined: dict[int, str] = {}

    # approved из users.csv
    for uid_str, uname in get_all_users().items():
        try:
            combined[int(uid_str)] = uname or f"user_{uid_str}"
        except ValueError:
            # пропустим странные id
            continue

    # full-auto
    for uid, name in AUTO_APPROVED_USERS.items():
        combined[int(uid)] = name

    # сотрудники (обед-авто)
    for uid, name in EMPLOYEE_USERS.items():
        combined[int(uid)] = name

    return combined

def _get_today_start_dt(user_id: int) -> datetime | None:
    """Самая ранняя отметка 'Пришел на работу' за сегодня или None."""
    if not os.path.exists(WORKTIME_FILE):
        return None

    today = datetime.now(TS_ZONE).date()
    first_dt: datetime | None = None

    with open(WORKTIME_FILE, newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) < 3:
                continue
            uid, action, ts = row[0], row[1], row[2]
            if uid != str(user_id) or action != "Пришел на работу":
                continue
            try:
                dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
            if dt.date() != today:
                continue
            if first_dt is None or dt < first_dt:
                first_dt = dt
    return first_dt

def _check_lateness_and_notify(bot):
    """
    В 09:00:
      - нет прихода → напоминание
      - приход позже START_TIME → сообщение о количестве минут опоздания
    """
    now_local = datetime.now(TS_ZONE)
    print(f"[LATE_CHECK] {now_local:%Y-%m-%d %H:%M} старт проверки (START_TIME={START_TIME})")

    for uid in _iter_all_targets().keys():
        try:
            start_dt = _get_today_start_dt(uid)
            if start_dt is None:
                bot.send_message(
                    uid,
                    "⚠️ Вы ещё не отметили *приход на работу*. Пожалуйста, отметьтесь командой /start или кнопкой.",
                    parse_mode="Markdown",
                )
                continue

            planned = datetime.combine(start_dt.date(), START_TIME, tzinfo=TS_ZONE)
            if start_dt > planned:
                late_minutes = int((start_dt - planned).total_seconds() // 60)
                bot.send_message(
                    uid,
                    f"⏰ Вы опоздали на *{late_minutes} мин.* (приход в {start_dt:%H:%M}, норма {START_TIME.strftime('%H:%M')}).",
                    parse_mode="Markdown",
                )
        except Exception as e:
            print(f"[LATE_CHECK][ERROR] uid={uid}: {e}")

def setup_notifications(scheduler, bot):
    # Регулярные напоминания по будням
    def notify_all(text):
        for uid in _iter_all_targets().keys():
            try:
                bot.send_message(uid, text)
            except Exception as e:
                print(f"[ERROR] Не удалось уведомить {uid}: {e}")

    for text, h, m in REMINDERS:
        scheduler.add_job(
            notify_all,
            CronTrigger(day_of_week="mon-fri", hour=h, minute=m, timezone=TS_ZONE),
            args=[text],
            id=f"reminder_{h:02d}{m:02d}",
            replace_existing=True,
            coalesce=True,
            misfire_grace_time=3600,
            max_instances=1,
        )

    # Проверка опозданий/неотмеченных — будни в 09:00
    scheduler.add_job(
        _check_lateness_and_notify,
        CronTrigger(day_of_week="mon-fri", hour=9, minute=0, timezone=TS_ZONE),
        args=[bot],
        id="late_check_0900",
        replace_existing=True,
        coalesce=True,
        misfire_grace_time=3600,
        max_instances=1,
    )

    # Ежедневный отчёт в 17:40 — теперь всем (approved + AUTO_APPROVED_USERS + EMPLOYEE_USERS)
    def daily_report():
        targets = _iter_all_targets()
        for uid, name in targets.items():
            try:
                rep = generate_excel_report_by_months(uid, name)
                if rep:
                    fn = f"Отчёт_{name}_{datetime.now(TS_ZONE):%d.%m.%Y}.xlsx"
                    bot.send_document(uid, InputFile(rep, fn))
                else:
                    bot.send_message(uid, "⚠️ Сегодняшний отчёт не найден.")
            except Exception as e:
                print(f"[ERROR] Не удалось отправить отчёт {uid}: {e}")

    scheduler.add_job(
        daily_report,
        CronTrigger(day_of_week="mon-fri", hour=17, minute=40, timezone=TS_ZONE),
        id="daily_report_1740",
        replace_existing=True,
        coalesce=True,
        misfire_grace_time=3600,
        max_instances=1,
    )

    print("[SCHEDULER] Напоминания, проверка опозданий и ежедневные отчёты настроены.")
