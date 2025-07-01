import os
import csv
from datetime import datetime, time
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Font, Border, Side, Alignment

# Импортируем WORKTIME_FILE из storage.py, чтобы путь совпадал с тем, куда пишутся метки
from storage import WORKTIME_FILE

# Время начала рабочего дня для подсчёта опозданий
START_TIME = time(8, 30)

def generate_excel_report_by_months(user_id, username, today_only=False):
    """
    Формирует Excel-отчёт по записям work_time.csv.
    Если today_only=True, включает только записи за текущую дату.
    """
    # Проверяем, существует ли файл с записями
    if not os.path.exists(WORKTIME_FILE):
        print(f"[ERROR] Файл {WORKTIME_FILE} не найден.")
        return None

    # Структура: для каждого месяца словарь дат
    data_by_month = {m: {} for m in range(1, 13)}

    # Читаем CSV. Ожидаемый формат строк: [user_id, action, timestamp]
    with open(WORKTIME_FILE, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            # Пропускаем некорректные строки
            if len(row) < 3:
                continue
            uid = row[0]
            action = row[1]
            ts = row[-1]
            if uid != str(user_id):
                continue

            # Парсим метку времени
            try:
                dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                # Если формат отличается, пропускаем
                continue
            d = dt.date()
            m = d.month

            rec = data_by_month[m].setdefault(d, {
                "start": None,
                "lunch_out": None,
                "lunch_in": None,
                "end": None
            })

            # Заполняем соответствующее поле
            if action == "Пришел на работу":
                rec["start"] = dt
            elif action == "Вышел на обед":
                rec["lunch_out"] = dt
            elif action == "Вернулся с обеда":
                rec["lunch_in"] = dt
            elif action == "Ушел с работы":
                rec["end"] = dt

    # Если нужен отчёт за текущий день
    if today_only:
        today = datetime.now().date()
        m = today.month
        rec = data_by_month.get(m, {}).get(today, {
            "start": None,
            "lunch_out": None,
            "lunch_in": None,
            "end": None
        })
        data_by_month = {m: {today: rec}}

    # Создаём Excel книгу и удаляем дефолтный лист
    wb = Workbook()
    wb.remove(wb.active)

    total_minutes = 0
    total_late = 0
    total_days = 0
    total_absent = 0

    # Заполняем листы по месяцам
    for month, records in data_by_month.items():
        if not records:
            continue
        ws = wb.create_sheet(title=datetime(2025, month, 1).strftime('%B'))
        ws.append(["Дата", "Начало", "Обед-выход", "Обед-возврат", "Конец", "Часы", "Опоздание"])

        for date, times in sorted(records.items()):
            st = times["start"]
            lo = times["lunch_out"]
            li = times["lunch_in"]
            en = times["end"]

            minutes = 0
            late_flag = ""

            if st and en:
                total_days += 1
                minutes = int((en - st).total_seconds() // 60)
                if lo and li:
                    minutes -= int((li - lo).total_seconds() // 60)
                if st.time() > START_TIME:
                    late_flag = "✅"
                    total_late += 1
            else:
                total_absent += 1

            total_minutes += max(minutes, 0)
            hours = round(minutes / 60, 2) if minutes > 0 else ''

            ws.append([
                date.strftime('%Y-%m-%d'),
                st.strftime('%H:%M:%S') if st else '',
                lo.strftime('%H:%M:%S') if lo else '',
                li.strftime('%H:%M:%S') if li else '',
                en.strftime('%H:%M:%S') if en else '',
                hours,
                late_flag
            ])

        # Стилизация таблицы
        for col in ws.columns:
            for cell in col:
                cell.border = Border(
                    left=Side(style='thin'), right=Side(style='thin'),
                    top=Side(style='thin'), bottom=Side(style='thin')
                )
                cell.alignment = Alignment(horizontal='center')
                if cell.row == 1:
                    cell.font = Font(bold=True)

    # Итоговый лист
    total_hours = round(total_minutes / 60, 2)
    summary = wb.create_sheet(title="Итоги")
    summary.append(["Имя пользователя", "ID", "Всего часов", "Рабочих дней", "Опозданий", "Пропусков"])
    summary.append([username, user_id, total_hours, total_days, total_late, total_absent])

    # Лист с нормами
    norm = wb.create_sheet(title="Норма 2025")
    norm.append(["Месяц", "Норма часов"])
    for m in range(1, 13):
        norm.append([datetime(2025, m, 1).strftime('%B'), ""])

    # Сохраняем в буфер и возвращаем
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    print(f"[DEBUG] Отчёт сформирован: {username} ({user_id})")
    return buf
