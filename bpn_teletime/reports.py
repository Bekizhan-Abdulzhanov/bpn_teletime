from openpyxl import Workbook
from openpyxl.styles import Font, Border, Side, Alignment
from datetime import datetime, timedelta
from config import EXCEL_REPORT_DIR, WORKTIME_FILE
import os
import csv
import calendar

# 👉 Настройка графика (начало дня по умолчанию 08:30)
START_HOUR = 8
START_MINUTE = 30
WORK_HOURS_PER_DAY = 8

def generate_excel_report_by_months(user_id, username):
    if not os.path.exists(WORKTIME_FILE):
        print("[ERROR] Файл work_time.csv не найден.")
        return None

    monthly_data = {m: {} for m in range(1, 13)}
    worked_days = set()
    late_days = set()
    missed_days = []

    with open(WORKTIME_FILE, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader, None)
        for row in reader:
            if len(row) != 4:
                continue
            row_user_id, row_username, action, timestamp = row
            if row_user_id != str(user_id):
                continue
            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            date = dt.date()
            month = dt.month
            if date not in monthly_data[month]:
                monthly_data[month][date] = {"start": '', "lunch_out": '', "lunch_in": '', "end": ''}
            if action == "Пришел на работу":
                monthly_data[month][date]["start"] = dt
            elif action == "Вышел на обед":
                monthly_data[month][date]["lunch_out"] = dt
            elif action == "Вернулся с обеда":
                monthly_data[month][date]["lunch_in"] = dt
            elif action == "Ушел с работы":
                monthly_data[month][date]["end"] = dt

    if not os.path.exists(EXCEL_REPORT_DIR):
        os.makedirs(EXCEL_REPORT_DIR)

    wb = Workbook()
    wb.remove(wb.active)

    total_minutes = 0

    for month in range(1, 13):
        if not monthly_data[month]:
            continue

        ws = wb.create_sheet(title=datetime(2025, month, 1).strftime('%B'))
        ws.append(["Дата", "Начало", "Обед-выход", "Обед-возврат", "Конец", "Часы", "Опоздание?"])

        month_calendar = calendar.Calendar()
        for day in month_calendar.itermonthdates(2025, month):
            if day.month != month or day.weekday() >= 5:
                continue  # Пропуск выходных

            times = monthly_data[month].get(day, None)
            if times:
                start = times['start']
                lunch_out = times['lunch_out']
                lunch_in = times['lunch_in']
                end = times['end']
                work_minutes = 0
                if start and end:
                    work_minutes = int((end - start).total_seconds() / 60)
                    if lunch_out and lunch_in:
                        work_minutes -= int((lunch_in - lunch_out).total_seconds() / 60)
                total_minutes += work_minutes
                hours = round(work_minutes / 60, 2)
                is_late = start.time() > datetime(2025, 1, 1, START_HOUR, START_MINUTE).time()
                if is_late:
                    late_days.add(day)
                worked_days.add(day)
                ws.append([
                    day.strftime('%Y-%m-%d'),
                    start.strftime('%H:%M:%S') if start else '',
                    lunch_out.strftime('%H:%M:%S') if lunch_out else '',
                    lunch_in.strftime('%H:%M:%S') if lunch_in else '',
                    end.strftime('%H:%M:%S') if end else '',
                    hours,
                    "✅" if is_late else ""
                ])
            else:
                missed_days.append(day)
                ws.append([
                    day.strftime('%Y-%m-%d'), '', '', '', '', '', "❌ Пропуск"
                ])

        # Стили
        for col in ws.columns:
            for cell in col:
                cell.border = Border(left=Side(style='thin'), right=Side(style='thin'),
                                     top=Side(style='thin'), bottom=Side(style='thin'))
                cell.alignment = Alignment(horizontal='center')
                if cell.row == 1:
                    cell.font = Font(bold=True)

    # ❗Лист "Итоги"
    total_hours = round(total_minutes / 60, 2)
    summary_sheet = wb.create_sheet(title="Итоги")
    summary_sheet.append(["Имя пользователя", "ID", "Всего часов за год", "Дней отработано", "Опозданий", "Пропусков"])
    summary_sheet.append([username, user_id, total_hours, len(worked_days), len(late_days), len(missed_days)])

    # ❗Пустой лист с нормой времени
    norm_sheet = wb.create_sheet(title="Норма времени 2025")
    norm_sheet.append(["Месяц", "Норма часов", "Комментарий"])
    for i in range(1, 13):
        norm_sheet.append([calendar.month_name[i], "", ""])  # пустая норма, можно позже заполнить

    # Сохранение
    report_path = f"{EXCEL_REPORT_DIR}/summary_{username}_{user_id}.xlsx"
    wb.save(report_path)
    print(f"[DEBUG] Отчёт сохранён: {report_path}")
    return report_path


