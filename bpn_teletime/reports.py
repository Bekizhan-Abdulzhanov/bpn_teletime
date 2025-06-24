from openpyxl import Workbook
from openpyxl.styles import Font, Border, Side, Alignment
from openpyxl.chart import LineChart, Reference
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
        ws.append(["Дата", "Начало", "Обед-выход", "Обед-возврат", "Конец", "Часы"])

        daily_hours = []

        for date, times in sorted(monthly_data[month].items()):
            start = times['start']
            lunch_out = times['lunch_out']
            lunch_in = times['lunch_in']
            end = times['end']

            work_minutes = 0
            if start and end:
                work_minutes = int((end - start).total_seconds() / 60)
                if lunch_out and lunch_in:
                    lunch_break = int((lunch_in - lunch_out).total_seconds() / 60)
                    work_minutes -= lunch_break

            total_minutes += work_minutes
            hours = round(work_minutes / 60, 2) if work_minutes > 0 else ''

            ws.append([
                date.strftime('%Y-%m-%d'),
                start.strftime('%H:%M:%S') if start else '',
                lunch_out.strftime('%H:%M:%S') if lunch_out else '',
                lunch_in.strftime('%H:%M:%S') if lunch_in else '',
                end.strftime('%H:%M:%S') if end else '',
                hours
            ])

            daily_hours.append(hours if hours != '' else 0)

        # Стилизация
        for col in ws.columns:
            for cell in col:
                cell.border = Border(left=Side(style='thin'), right=Side(style='thin'),
                                     top=Side(style='thin'), bottom=Side(style='thin'))
                cell.alignment = Alignment(horizontal='center')
                if cell.row == 1:
                    cell.font = Font(bold=True)

        # Диаграмма
        if len(daily_hours) > 1:
            chart = LineChart()
            chart.title = "Часы по дням"
            chart.y_axis.title = 'Часы'
            chart.x_axis.title = 'Дни'
            data_ref = Reference(ws, min_col=6, min_row=1, max_row=len(daily_hours) + 1)
            chart.add_data(data_ref, titles_from_data=True)
            ws.add_chart(chart, "H2")

    total_hours = round(total_minutes / 60, 2)
    summary_sheet = wb.create_sheet(title="Итоги")
    summary_sheet.append(["Имя пользователя", "ID", "Всего часов за год"])
    summary_sheet.append([username, user_id, total_hours])

    report_path = f"{EXCEL_REPORT_DIR}/summary_{username}_{user_id}.xlsx"
    wb.save(report_path)
    print(f"[DEBUG] Отчёт сохранён: {report_path}")
    return report_path


