import os
import csv
from datetime import datetime

# Каталог текущего скрипта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Пути к CSV-файлам
USERS_FILE = os.path.join(BASE_DIR, os.environ.get('USERS_FILE', 'users.csv'))
WORKTIME_FILE = os.path.join(BASE_DIR, os.environ.get('WORKTIME_FILE', 'work_time.csv'))

# Файл со списком пользователей, у кого ВКЛЮЧЁН авто-режим
AUTO_ENABLED_FILE = os.path.join(BASE_DIR, os.environ.get('AUTO_ENABLED_FILE', 'auto_enabled.csv'))


# ---------- Work time ----------
def save_work_time(user_id: str | int, event: str, timestamp: str) -> None:
    """Добавить новую запись в work_time.csv."""
    with open(WORKTIME_FILE, 'a', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow([str(user_id), event, timestamp])


# ---------- Users approvals ----------
def is_user_approved(user_id: str | int) -> bool:
    """Проверить, что пользователь есть в users.csv и имеет статус 'approved'."""
    if not os.path.exists(USERS_FILE):
        return False
    with open(USERS_FILE, newline='', encoding='utf-8') as f:
        for row in csv.reader(f):
            if row and row[0] == str(user_id) and len(row) >= 3 and row[2] == 'approved':
                return True
    return False


def get_all_users() -> dict[str, str]:
    """Вернуть словарь одобренных пользователей: {user_id: username}."""
    users: dict[str, str] = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, newline='', encoding='utf-8') as f:
            for row in csv.reader(f):
                if len(row) >= 3 and row[2] == 'approved':
                    users[row[0]] = row[1]
    return users


def get_pending_users() -> dict[str, str]:
    """Словарь пользователей в статусе 'pending' из users.csv."""
    pending: dict[str, str] = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, newline='', encoding='utf-8') as f:
            for row in csv.reader(f):
                if len(row) >= 3 and row[2] == 'pending':
                    pending[row[0]] = row[1]
    return pending


def set_user_status(user_id: str | int, status: str) -> None:
    """Обновить статус пользователя (approved/pending/rejected) в users.csv."""
    if not os.path.exists(USERS_FILE):
        return
    rows: list[list[str]] = []
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


# ---------- Auto mode (enabled ids) ----------
def enable_auto_mode(user_id: str | int) -> None:
    """Включить авто-режим (добавить user_id в auto_enabled.csv)."""
    ids = set()
    if os.path.exists(AUTO_ENABLED_FILE):
        with open(AUTO_ENABLED_FILE, 'r', encoding='utf-8') as f:
            ids = set(line.strip() for line in f if line.strip())
    ids.add(str(user_id))
    with open(AUTO_ENABLED_FILE, 'w', encoding='utf-8') as f:
        for uid in sorted(ids):
            f.write(f"{uid}\n")


def disable_auto_mode(user_id: str | int) -> None:
    """Выключить авто-режим (удалить user_id из auto_enabled.csv)."""
    if not os.path.exists(AUTO_ENABLED_FILE):
        return
    with open(AUTO_ENABLED_FILE, 'r', encoding='utf-8') as f:
        ids = set(line.strip() for line in f if line.strip())
    ids.discard(str(user_id))
    with open(AUTO_ENABLED_FILE, 'w', encoding='utf-8') as f:
        for uid in sorted(ids):
            f.write(f"{uid}\n")


def is_auto_enabled(user_id: str | int) -> bool:
    """Проверить, включён ли авто-режим для user_id."""
    if not os.path.exists(AUTO_ENABLED_FILE):
        return False
    with open(AUTO_ENABLED_FILE, 'r', encoding='utf-8') as f:
        return str(user_id) in (line.strip() for line in f if line.strip())


# ---------- Admin edit helpers ----------
def update_work_time_entry(user_id: str | int, date_str: str, action: str, new_time_str: str) -> bool:
    """
    Обновить в work_time.csv запись с user_id, action и датой.
    date_str: 'YYYY-MM-DD', new_time_str: 'HH:MM:SS'.
    Возвращает True, если хотя бы одна строка была изменена.
    """
    updated = False
    temp_rows: list[list[str]] = []

    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return False

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

    if updated:
        with open(WORKTIME_FILE, 'w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerows(temp_rows)

    return updated


def get_user_dates(user_id: str | int) -> list[str]:
    """Отсортированный список уникальных дат ('YYYY-MM-DD') для user_id из work_time.csv."""
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
