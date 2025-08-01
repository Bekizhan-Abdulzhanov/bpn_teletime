import os
import csv
from datetime import datetime

# Каталог текущего скрипта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Пути к CSV-файлам
USERS_FILE = os.path.join(BASE_DIR, os.environ.get('USERS_FILE', 'users.csv'))
WORKTIME_FILE = os.path.join(BASE_DIR, os.environ.get('WORKTIME_FILE', 'work_time.csv'))
AUTO_APPROVED_FILE = os.path.join(BASE_DIR, os.environ.get('AUTO_APPROVED_FILE', 'auto_approved_users.csv'))

def save_work_time(user_id: str, event: str, timestamp: str) -> None:
    """Добавить новую запись в work_time.csv."""
    with open(WORKTIME_FILE, 'a', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow([user_id, event, timestamp])

def is_user_approved(user_id: str) -> bool:
    """Проверить, что пользователь есть в users.csv и имеет статус 'approved'."""
    if not os.path.exists(USERS_FILE):
        return False
    with open(USERS_FILE, newline='', encoding='utf-8') as f:
        for row in csv.reader(f):
            if row and row[0] == str(user_id) and len(row) >= 3 and row[2] == 'approved':
                return True
    return False

def get_all_users() -> dict[str, str]:
    """
    Вернуть словарь одобренных пользователей: {user_id: username}.
    Читает users.csv, ищет статус 'approved'.
    """
    users: dict[str, str] = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, newline='', encoding='utf-8') as f:
            for row in csv.reader(f):
                if len(row) >= 3 and row[2] == 'approved':
                    users[row[0]] = row[1]
    return users

def get_pending_users() -> dict[str, str]:
    """Вернуть словарь пользователей в статусе 'pending' из users.csv."""
    pending: dict[str, str] = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, newline='', encoding='utf-8') as f:
            for row in csv.reader(f):
                if len(row) >= 3 and row[2] == 'pending':
                    pending[row[0]] = row[1]
    return pending

def set_user_status(user_id: str, status: str) -> None:
    """
    Обновить статус пользователя (approved/pending) в третьей колонке users.csv.
    Если записи нет — ничего не делает.
    """
    if not os.path.exists(USERS_FILE):
        return
    rows = []
    with open(USERS_FILE, newline='', encoding='utf-8') as rf:
        rows = [row for row in csv.reader(rf)]
    with open(USERS_FILE, 'w', newline='', encoding='utf-8') as wf:
        writer = csv.writer(wf)
        for row in rows:
            if row and row[0] == str(user_id):
                while len(row) < 3:
                    row.append('')
                row[2] = status
            writer.writerow(row)

def approve_user(user_id: str) -> None:
    """Добавить user_id в auto_approved_users.csv."""
    approved = set()
    if os.path.exists(AUTO_APPROVED_FILE):
        with open(AUTO_APPROVED_FILE, 'r', encoding='utf-8') as f:
            approved = set(line.strip() for line in f)
    approved.add(str(user_id))
    with open(AUTO_APPROVED_FILE, 'w', encoding='utf-8') as f:
        for uid in sorted(approved):
            f.write(f"{uid}\n")

def deny_user(user_id: str) -> None:
    """Удалить user_id из auto_approved_users.csv."""
    if not os.path.exists(AUTO_APPROVED_FILE):
        return
    with open(AUTO_APPROVED_FILE, 'r', encoding='utf-8') as f:
        approved = set(line.strip() for line in f)
    approved.discard(str(user_id))
    with open(AUTO_APPROVED_FILE, 'w', encoding='utf-8') as f:
        for uid in sorted(approved):
            f.write(f"{uid}\n")

def is_auto_enabled(user_id: str) -> bool:
    """Проверить, что user_id есть в auto_approved_users.csv."""
    if not os.path.exists(AUTO_APPROVED_FILE):
        return False
    with open(AUTO_APPROVED_FILE, 'r', encoding='utf-8') as f:
        return str(user_id) in (line.strip() for line in f)

# Синонимы
enable_auto_mode  = approve_user
disable_auto_mode = deny_user

def update_work_time_entry(user_id: str, date_str: str, action: str, new_time_str: str) -> bool:
    """
    Обновить в work_time.csv запись с user_id, action и датой.
    date_str: 'YYYY-MM-DD', new_time_str: 'HH:MM:SS'.
    Возвращает True, если хотя бы одна строка была изменена.
    """
    updated = False
    temp_rows: list[list[str]] = []

    # Парсим целевую дату
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return False

    # Читаем и модифицируем
    if os.path.exists(WORKTIME_FILE):
        with open(WORKTIME_FILE, 'r', newline='', encoding='utf-8') as f:
            for row in csv.reader(f):
                if len(row) >= 3 and row[0] == str(user_id) and row[1] == action:
                    try:
                        ts = datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S")
                        if ts.date() == target_date:
                            row[2] = f"{date_str} {new_time_str}"
                            updated = True
                    except ValueError:
                        pass
                temp_rows.append(row)

    # Перезаписать, если были изменения
    if updated:
        with open(WORKTIME_FILE, 'w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerows(temp_rows)

    return updated

def get_user_dates(user_id: str) -> list[str]:
    """
    Вернуть отсортированный список уникальных дат ('YYYY-MM-DD'),
    по которым есть записи в work_time.csv для данного user_id.
    """
    dates = set()
    if os.path.exists(WORKTIME_FILE):
        with open(WORKTIME_FILE, newline='', encoding='utf-8') as f:
            for row in csv.reader(f):
                if row and row[0] == str(user_id) and len(row) >= 3:
                    try:
                        dt = datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S")
                        dates.add(dt.date().isoformat())
                    except ValueError:
                        pass
    return sorted(dates)

