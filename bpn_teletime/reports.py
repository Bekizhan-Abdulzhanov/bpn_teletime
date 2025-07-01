import os
import csv
from datetime import datetime, time
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Font, Border, Side, Alignment

from config import WORKTIME_FILE

# Стандартное время начала работы
START_TIME = time(8, 30)

def generate_excel_report_by_months(user_id, username, today_only=False):
    # Проверяем, что есть файл с метками
    if not os.path.exists(WORKTIME_FILE):
        print("[ERROR] Файл work_time.csv не найден.")
        return None

    # Подготовка структуры: 12 месяцев → дни
    data_by_month = {m: {} for m in range(1, 13)}

    # Читаем все метки из CSV
    with open(WORKTIME_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if len(row) != 4:
                continue
            uid, _, action, timestamp = row
            if uid != str(user_id):
                continue

            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            date = dt.date()
            month = date.month

            data_by_month[month].setdefault(date, {
                "start": None,
                "lunch_out": None,
                "lunch_in": None,
                "end": None
            })

            if action == "Пришел на работу":
                data_by_month[month][date]["start"] = dt
            elif action == "Вышел на обед":
                data_by_month[month][date]["lunch_out"] = dt
            elif action == "Вернулся с обеда":
                data_by_month[month][date]["lunch_in"] = dt
            elif action == "Ушел с работы":
                data_by_month[month][date]["end"] = dt

    # Если нужен отчёт только за сегодня — отфильтровываем данные
    if today_only:
        today = datetime.now().date()
        month = today.month
        recs = data_by_month.get(month, {})
        today_rec = recs.get(today, {
            "start": None,
            "lunch_out": None,
            "lunch_in": None,
            "end": None
        })
        data_by_month = {month: {today: today_rec}}

    # Создаём книгу Excel
    wb = Workbook()
    wb.remove(wb.active)

    total_minutes = total_late = total_days = total_absent = 0

    # Заполняем листы по месяцам (или только одним — сегодня)
    for month, records in data_by_month.items():
        if not records:
            continue

        ws = wb.create_sheet(title=datetime(2025, month, 1).strftime('%B'))
        ws.append(["Дата", "Начало", "Обед-выход", "Обед-возврат", "Конец", "Часы", "Опоздание"])

        for date, times in sorted(records.items()):
            start   = times["start"]
            lunch_o = times["lunch_out"]
            lunch_i = times["lunch_in"]
            end     = times["end"]

            work_minutes = 0
            late_flag = ""

            if start and end:
                total_days += 1
                work_minutes = int((end - start).total_seconds() // 60)
                if lunch_o and lunch_i:
                    work_minutes -= int((lunch_i - lunch_o).total_seconds() // 60)
                if start.time() > START_TIME:
                    late_flag = "✅"
                    total_late += 1
            else:
                total_absent += 1

            total_minutes += max(work_minutes, 0)
            hours = round(work_minutes / 60, 2) if work_minutes > 0 else ''

            ws.append([
                date.strftime('%Y-%m-%d'),
                start.strftime('%H:%M:%S') if start else '',
                lunch_o.strftime('%H:%M:%S') if lunch_o else '',
                lunch_i.strftime('%H:%M:%S') if lunch_i else '',
                end.strftime('%H:%M:%S') if end else '',
                hours,
                late_flag
            ])

        # Стилизация таблицы
        for col in ws.columns:
            for cell in col:
                cell.border = Border(
                    left=Side(style='thin'),
                    right=Side(style='thin'),
                    top=Side(style='thin'),
                    bottom=Side(style='thin')
                )
                cell.alignment = Alignment(horizontal='center')
                if cell.row == 1:
                    cell.font = Font(bold=True)

    # Лист с итогами
    total_hours = round(total_minutes / 60, 2)
    summary = wb.create_sheet(title="Итоги")
    summary.append(["Имя пользователя", "ID", "Всего часов", "Рабочих дней", "Опозданий", "Пропусков"])
    summary.append([username, user_id, total_hours, total_days, total_late, total_absent])

    # Пустой лист для нормы 2025
    norm = wb.create_sheet(title="Норма 2025")
    norm.append(["Месяц", "Норма часов"])
    for m in range(1, 13):
        norm.append([datetime(2025, m, 1).strftime('%B'), ""])

    # Сохраняем в байтовый буфер и возвращаем
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    print(f"[DEBUG] Отчёт сформирован: {username}")
    return output

