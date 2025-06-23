from openpyxl import Workbook
from openpyxl.styles import Font, Border, Side, Alignment
from datetime import datetime
from config import EXCEL_REPORT_DIR, WORKTIME_FILE
import os
import csv

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
    wb.remove(wb.active)

    for month in range(1, 13):
        if not monthly_data[month]:
            continue
        ws = wb.create_sheet(title=datetime(2025, month, 1).strftime('%B'))
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
                if cell.row == 1:
                    cell.font = Font(bold=True)

    safe_name = username.replace(" ", "_").replace("@", "")
    report_path = f"{EXCEL_REPORT_DIR}/report_{safe_name}_{user_id}.xlsx"
    wb.save(report_path)
    print(f"[DEBUG] Отчет по месяцам сохранен в: {report_path}")
    return report_path



