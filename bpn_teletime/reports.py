from openpyxl import Workbook
from openpyxl.styles import Font, Border, Side, Alignment
from utils import now
from config import EXCEL_REPORT_DIR, WORKTIME_FILE
import csv, os
from datetime import datetime

def generate_excel_report(user_id):
    if not os.path.exists(WORKTIME_FILE):
        return None
    
    data = {}
    with open(WORKTIME_FILE, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader, None)
        for row in reader:
            if len(row) != 4 or row[0] != str(user_id):
                continue
            _, username, action, timestamp = row
            date = timestamp.split()[0]
            if date not in data:
                data[date] = {"start": '', "lunch_out": '', "lunch_in": '', "end": ''}
            if action == "Пришел на работу":
                data[date]["start"] = timestamp
            elif action == "Вышел на обед":
                data[date]["lunch_out"] = timestamp
            elif action == "Вернулся с обеда":
                data[date]["lunch_in"] = timestamp
            elif action == "Ушел с работы":
                data[date]["end"] = timestamp

    if not os.path.exists(EXCEL_REPORT_DIR):
        os.makedirs(EXCEL_REPORT_DIR)

    wb = Workbook()
    ws = wb.active
    ws.title = "Отчёт"
    ws.append(["Дата", "Начало", "Обед-выход", "Обед-возврат", "Конец"])

    for date, times in sorted(data.items()):
        ws.append([
            date,
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

    filename = f"{EXCEL_REPORT_DIR}/report_{user_id}.xlsx"
    wb.save(filename)
    return filename
