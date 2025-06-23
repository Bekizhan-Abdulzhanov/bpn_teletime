from openpyxl import Workbook
from openpyxl.styles import Font, Border, Side, Alignment
from datetime import datetime
from config import EXCEL_REPORT_DIR, WORKTIME_FILE
import os
import csv
import telebot
from apscheduler.schedulers.background import BackgroundScheduler
from storage import get_all_users
from config import TOKEN

bot = telebot.TeleBot(TOKEN)

scheduler = BackgroundScheduler(timezone='Asia/Bishkek')


def generate_excel_report_by_months(user_id):
    if not os.path.exists(WORKTIME_FILE):
        print("[ERROR] Файл work_time.csv не найден.")
        return None

    # Структура: {месяц: {дата: {...}}}
    monthly_data = {m: {} for m in range(1, 13)}
    username = ""

    with open(WORKTIME_FILE, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader, None)  # Пропустить заголовок
        for row in reader:
            if len(row) != 4:
                continue
            row_user_id, name, action, timestamp = row
            if row_user_id != str(user_id):
                continue
            username = name
            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            date = dt.date()
            month = dt.month
            if date not in monthly_data[month]:
                monthly_data[month][date] = {"start": '', "lunch_out": '', "lunch_in": '', "end": ''}
            if action == "Пришел на работу":
                monthly_data[month][date]["start"] = timestamp
            elif action == "Вышел на обед":
                monthly_data[month][date]["lunch_out"] = timestamp
            elif action == "Вернулся с обеда":
                monthly_data[month][date]["lunch_in"] = timestamp
            elif action == "Ушел с работы":
                monthly_data[month][date]["end"] = timestamp

    if not os.path.exists(EXCEL_REPORT_DIR):
        os.makedirs(EXCEL_REPORT_DIR)

    wb = Workbook()
    wb.remove(wb.active)  # Удалить стандартный лист

    for month in range(1, 13):
        if not monthly_data[month]:
            continue
        ws = wb.create_sheet(title=datetime(2025, month, 1).strftime('%B'))  # Название месяца

        ws.append([f"Отчет по сотруднику: {username}"])
        ws.append(["Дата", "Начало", "Обед-выход", "Обед-возврат", "Конец"])

        for date, times in sorted(monthly_data[month].items()):
            ws.append([
                date.strftime('%Y-%m-%d'),
                times['start'].split()[1] if times['start'] else '',
                times['lunch_out'].split()[1] if times['lunch_out'] else '',
                times['lunch_in'].split()[1] if times['lunch_in'] else '',
                times['end'].split()[1] if times['end'] else ''
            ])

        for col in ws.columns:
            for cell in col:
                cell.border = Border(left=Side(style='thin'), right=Side(style='thin'),
                                     top=Side(style='thin'), bottom=Side(style='thin'))
                cell.alignment = Alignment(horizontal='center')
                if cell.row in [1, 2]:
                    cell.font = Font(bold=True)

    report_path = f"{EXCEL_REPORT_DIR}/report_{user_id}_months.xlsx"
    wb.save(report_path)
    print(f"[DEBUG] Отчет по месяцам сохранен в: {report_path}")
    return report_path


# Уведомления по времени

def send_reminder_to_all_users(text):
    users = get_all_users()
    for user_id in users:
        try:
            bot.send_message(user_id, text)
        except Exception as e:
            print(f"[ERROR] Не удалось отправить сообщение {user_id}: {e}")

scheduler.add_job(lambda: send_reminder_to_all_users("Вы уже в пути на работу? Не забудьте меня отметить 😊"), 'cron', hour=8, minute=28)
scheduler.add_job(lambda: send_reminder_to_all_users("Приятного аппетита! Не забудьте меня отметить 😊"), 'cron', hour=11, minute=58)
scheduler.add_job(lambda: send_reminder_to_all_users("Желаю вам продуктивной работы! Не забудьте меня отметить 😊"), 'cron', hour=13, minute=58)
scheduler.add_job(lambda: send_reminder_to_all_users("Вы сегодня хорошо поработали! Не забудьте меня отметить 😊"), 'cron', hour=17, minute=28)

scheduler.start()
