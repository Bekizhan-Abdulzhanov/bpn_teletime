from openpyxl import Workbook
from openpyxl.styles import Font, Border, Side, Alignment
from datetime import datetime, timedelta, date
from calendar import monthrange, Calendar
from config import EXCEL_REPORT_DIR, WORKTIME_FILE
import os
import csv

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
            d = dt.date()
            m = dt.month
            if d not in monthly_data[m]:
                monthly_data[m][d] = {"start": '', "lunch_out": '', "lunch_in": '', "end": ''}
            if action == "Пришел на работу":
                monthly_data[m][d]["start"] = dt
            elif action == "Вышел на обед":
                monthly_data[m][d]["lunch_out"] = dt
            elif action == "Вернулся с обеда":
                monthly_data[m][d]["lunch_in"] = dt
            elif action == "Ушел с работы":
                monthly_data[m][d]["end"] = dt

    if not os.path.exists(EXCEL_REPORT_DIR):
        os.makedirs(EXCEL_REPORT_DIR)

    wb = Workbook()
    wb.remove(wb.active)

    total_minutes = 0
    calendar = Calendar()

    for month in range(1, 13):
        if not monthly_data[month]:
            continue

        ws = wb.create_sheet(title=datetime(2025, month, 1).strftime('%B'))
        ws.append(["Дата", "Начало", "Обед-выход", "Обед-возврат", "Конец", "Часы", "Опоздание", "Пропуск"])

        for day in calendar.itermonthdates(2025, month):
            if day.month != month:
                continue
            times = monthly_data[month].get(day, {})

            start = times.get("start")
            lunch_out = times.get("lunch_out")
            lunch_in = times.get("lunch_in")
            end = times.get("end")

            work_minutes = 0
            is_late = False
            is_absent = False

            if isinstance(start, datetime) and isinstance(end, datetime):
                work_minutes = int((end - start).total_seconds() / 60)
                if isinstance(lunch_out, datetime) and isinstance(lunch_in, datetime):
                    work_minutes -= int((lunch_in - lunch_out).total_seconds() / 60)
                if start.time() > datetime(2025, 1, 1, START_HOUR, START_MINUTE).time():
                    is_late = True
            else:
                is_absent = True

            hours = round(work_minutes / 60, 2) if work_minutes > 0 else ''
            total_minutes += work_minutes if work_minutes > 0 else 0

            ws.append([
                day.strftime('%Y-%m-%d'),
                start.strftime('%H:%M:%S') if isinstance(start, datetime) else '',
                lunch_out.strftime('%H:%M:%S') if isinstance(lunch_out, datetime) else '',
                lunch_in.strftime('%H:%M:%S') if isinstance(lunch_in, datetime) else '',
                end.strftime('%H:%M:%S') if isinstance(end, datetime) else '',
                hours,
                'Да' if is_late else '',
                'Да' if is_absent else ''
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
    summary_sheet.append(["Имя пользователя", "ID", "Всего часов за год"])
    summary_sheet.append([username, user_id, total_hours])

    wb.create_sheet(title="Норма 2025")

    report_path = f"{EXCEL_REPORT_DIR}/summary_{username}_{user_id}.xlsx"
    wb.save(report_path)
    print(f"[DEBUG] Отчёт сохранён: {report_path}")
    return report_path



