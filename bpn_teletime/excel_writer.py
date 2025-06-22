# excel_writer.py
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font, Border, Side, Alignment
from datetime import datetime
import os
from config import EXCEL_REPORT_DIR

def write_event_to_excel(user_id, username, action, timestamp_str):
    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    month_name = timestamp.strftime('%B')
    date_str = timestamp.strftime('%Y-%m-%d')
    time_str = timestamp.strftime('%H:%M:%S')

    file_path = os.path.join(EXCEL_REPORT_DIR, f"report_{user_id}_2025_by_months.xlsx")
    os.makedirs(EXCEL_REPORT_DIR, exist_ok=True)

    if os.path.exists(file_path):
        wb = load_workbook(file_path)
    else:
        wb = Workbook()
        wb.remove(wb.active)

    if month_name not in wb.sheetnames:
        ws = wb.create_sheet(title=month_name)
        ws.append(["Дата", "Начало", "Обед‑выход", "Обед‑возврат", "Конец"])
    else:
        ws = wb[month_name]

    row_found = False
    for row in range(2, ws.max_row + 1):
        if ws.cell(row=row, column=1).value == date_str:
            row_found = True
            col = {"Пришел на работу": 2, "Вышел на обед": 3,
                   "Вернулся с обеда": 4, "Ушел с работы": 5}[action]
            ws.cell(row=row, column=col).value = time_str
            break

    if not row_found:
        new_row = [date_str, "", "", "", ""]
        new_row[{"Пришел на работу": 1, "Вышел на обед": 2,
                 "Вернулся с обеда": 3, "Ушел с работы": 4}[action]] = time_str
        ws.append(new_row)

    for col in ws.columns:
        for cell in col:
            cell.border = Border(left=Side(style='thin'),
                                 right=Side(style='thin'),
                                 top=Side(style='thin'),
                                 bottom=Side(style='thin'))
            cell.alignment = Alignment(horizontal='center')
            if cell.row == 1:
                cell.font = Font(bold=True)

    wb.save(file_path)
    print(f"[DEBUG] Записан {action} {date_str} {time_str} в {month_name}")
