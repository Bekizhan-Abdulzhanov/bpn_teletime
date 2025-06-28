from apscheduler.schedulers.background import BackgroundScheduler
from storage import save_work_time, get_all_users, is_auto_enabled
from reports import generate_excel_report_by_months
from datetime import datetime
from telebot.types import InputFile
from config import ADMIN_IDS

# ✅ Эти пользователи имеют право включать авто-режим
AUTO_USERS = {
    378268765: "ErlanNasiev",
    557174721: "BekizhanAbdulzhanov",
}

def setup_scheduler(scheduler, bot):
    # 🕐 Автоматические отметки
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

    for user_id, username in AUTO_USERS.items():
        if not is_auto_enabled(user_id):
            continue  # режим не включён пользователем

        for day, hour, minute, action in schedule_actions:
            scheduler.add_job(
                save_work_time,
                trigger="cron",
                day_of_week=day,
                hour=hour,
                minute=minute,
                args=[user_id, username, action]
            )

    # 🗓 Отчёты для админов 29/30 числа
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

    # 🗓 Отчёт 27 февраля
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

# 📎 Отправка отчётов админам
def send_monthly_reports_to_admins(bot):
    now = datetime.now()
    month_name = now.strftime('%B')
    all_users = get_all_users()

    for admin_id in ADMIN_IDS:
        bot.send_message(admin_id, f"📦 Ежемесячные отчёты за {month_name}:")

        for user_id, username in all_users.items():
            try:
                file = generate_excel_report_by_months(user_id, username)
                if file:
                    filename = f"Отчет_{username}_{month_name}.xlsx"
                    bot.send_document(admin_id, InputFile(file, filename), caption=f"📎 {username}")
                else:
                    bot.send_message(admin_id, f"⚠️ Нет данных для {username}.")
            except Exception as e:
                bot.send_message(admin_id, f"❌ Ошибка при отправке отчёта {username}: {e}")




from datetime import date
import calendar
from telebot.types import InputFile

# ⏰ Отправка Excel-отчета каждому пользователю с авто-режимом в 18:00 (будние дни)
def send_daily_auto_reports(bot):
    today = date.today()
    if calendar.weekday(today.year, today.month, today.day) >= 5:  # Сб/Вс
        return

    for user_id, username in AUTO_USERS.items():
        if not is_auto_enabled(user_id):
            continue

        file = generate_excel_report_by_months(user_id, username)
        if file:
            filename = f"Отчет_{username}_{today.strftime('%Y-%m-%d')}.xlsx"
            try:
                bot.send_document(user_id, InputFile(file, filename),
                                  caption="📄 Ваш автоматический отчёт за сегодня.")
            except Exception as e:
                print(f"[ERROR] Не удалось отправить отчет пользователю {user_id}: {e}")
