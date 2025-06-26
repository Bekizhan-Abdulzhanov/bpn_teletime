from openpyxl import Workbook
from openpyxl.styles import Font, Border, Side, Alignment
from datetime import datetime, time
from io import BytesIO
import csv
import os

from config import WORKTIME_FILE

# Настройки
START_HOUR = 8
START_MINUTE = 30

def generate_excel_report_by_months(user_id, username):
    if not os.path.exists(WORKTIME_FILE):
        print("[ERROR] Файл work_time.csv не найден.")
        return None

    monthly_data = {m: {} for m in range(1, 13)}

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
                monthly_data[month][date] = {"start": None, "lunch_out": None, "lunch_in": None, "end": None}
            if action == "Пришел на работу":
                monthly_data[month][date]["start"] = dt
            elif action == "Вышел на обед":
                monthly_data[month][date]["lunch_out"] = dt
            elif action == "Вернулся с обеда":
                monthly_data[month][date]["lunch_in"] = dt
            elif action == "Ушел с работы":
                monthly_data[month][date]["end"] = dt

    wb = Workbook()
    wb.remove(wb.active)

    total_minutes = 0
    total_working_days = 0
    total_late = 0
    total_absent = 0

    for month in range(1, 13):
        if not monthly_data[month]:
            continue

        ws = wb.create_sheet(title=datetime(2025, month, 1).strftime('%B'))
        ws.append(["Дата", "Начало", "Обед-выход", "Обед-возврат", "Конец", "Часы", "Опоздание"])

        for date, times in sorted(monthly_data[month].items()):
            start = times['start']
            lunch_out = times['lunch_out']
            lunch_in = times['lunch_in']
            end = times['end']

            work_minutes = 0
            is_late = ''

            if start and end:
                total_working_days += 1
                start_dt = start
                end_dt = end
                work_minutes = int((end_dt - start_dt).total_seconds() / 60)
                if lunch_out and lunch_in:
                    lunch_break = int((lunch_in - lunch_out).total_seconds() / 60)
                    work_minutes -= lunch_break
                is_late = "✅" if start_dt.time() > time(START_HOUR, START_MINUTE) else ""
                if is_late:
                    total_late += 1
            else:
                total_absent += 1

            hours = round(work_minutes / 60, 2) if work_minutes > 0 else ''
            total_minutes += work_minutes

            ws.append([
                date.strftime('%Y-%m-%d'),
                start.strftime('%H:%M:%S') if start else '',
                lunch_out.strftime('%H:%M:%S') if lunch_out else '',
                lunch_in.strftime('%H:%M:%S') if lunch_in else '',
                end.strftime('%H:%M:%S') if end else '',
                hours,
                is_late
            ])

        for col in ws.columns:
            for cell in col:
                cell.border = Border(left=Side(style='thin'), right=Side(style='thin'),
                                     top=Side(style='thin'), bottom=Side(style='thin'))
                cell.alignment = Alignment(horizontal='center')
                if cell.row == 1:
                    cell.font = Font(bold=True)

    total_hours = round(total_minutes / 60, 2)
    summary_sheet = wb.create_sheet(title="Итоги")
    summary_sheet.append(["Имя пользователя", "ID", "Всего часов", "Рабочих дней", "Опозданий", "Пропусков"])
    summary_sheet.append([username, user_id, total_hours, total_working_days, total_late, total_absent])

    # Пустой лист "Норма 2025"
    norm_sheet = wb.create_sheet(title="Норма 2025")
    norm_sheet.append(["Месяц", "Норма часов"])
    for m in range(1, 13):
        norm_sheet.append([datetime(2025, m, 1).strftime('%B'), ''])

    # Сохраняем в память, а не на диск
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    print(f"[DEBUG] Отчет сформирован для {username}")
    return output
