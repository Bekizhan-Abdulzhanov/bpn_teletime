import os
import csv
from datetime import datetime
from typing import Iterable


from config import DATA_DIR, USERS_FILE_NAME, WORKTIME_FILE_NAME, AUTO_ENABLED_FILE_NAME


os.makedirs(DATA_DIR, exist_ok=True)


USERS_FILE        = os.path.join(DATA_DIR, USERS_FILE_NAME)
WORKTIME_FILE     = os.path.join(DATA_DIR, WORKTIME_FILE_NAME)
AUTO_ENABLED_FILE = os.path.join(DATA_DIR, AUTO_ENABLED_FILE_NAME)



def _maybe_migrate_legacy_file(legacy_name: str, new_abs_path: str) -> None:
    """
    Если рядом с кодом есть старый файл (legacy_name), а в DATA_DIR файла нет,
    переносим его в DATA_DIR.
    """
    legacy_path = os.path.abspath(os.path.join(os.path.dirname(__file__), legacy_name))
    if os.path.exists(legacy_path) and not os.path.exists(new_abs_path):
        try:
            os.rename(legacy_path, new_abs_path)
            print(f"[MIGRATE] Перенесён {legacy_path} -> {new_abs_path}")
        except Exception as e:
            print(f"[MIGRATE] Не удалось перенести {legacy_path}: {e}")



_maybe_migrate_legacy_file("users.csv", USERS_FILE)
_maybe_migrate_legacy_file("work_time.csv", WORKTIME_FILE)
_maybe_migrate_legacy_file("auto_enabled.csv", AUTO_ENABLED_FILE)
_maybe_migrate_legacy_file("auto_approved_users.csv", AUTO_ENABLED_FILE)  # старое имя



def save_work_time(user_id: str | int, event: str, timestamp: str) -> None:
    with open(WORKTIME_FILE, 'a', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow([str(user_id), event, timestamp])


def is_user_approved(user_id: str | int) -> bool:
    if not os.path.exists(USERS_FILE):
        return False
    with open(USERS_FILE, newline='', encoding='utf-8') as f:
        for row in csv.reader(f):
            if row and row[0] == str(user_id) and len(row) >= 3 and row[2] == 'approved':
                return True
    return False


def get_all_users() -> dict[str, str]:
    users: dict[str, str] = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, newline='', encoding='utf-8') as f:
            for row in csv.reader(f):
                if len(row) >= 3 and row[2] == 'approved':
                    users[row[0]] = row[1]
    return users


def get_pending_users() -> dict[str, str]:
    pending: dict[str, str] = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, newline='', encoding='utf-8') as f:
            for row in csv.reader(f):
                if len(row) >= 3 and row[2] == 'pending':
                    pending[row[0]] = row[1]
    return pending


def set_user_status(user_id: str | int, status: str) -> None:
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



def _read_ids(path: str) -> set[str]:
    if not os.path.exists(path):
        return set()
    with open(path, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())


def _write_ids(path: str, ids: Iterable[str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        for uid in sorted(set(ids)):
            f.write(f"{uid}\n")


def enable_auto_mode(user_id: str | int) -> None:
    ids = _read_ids(AUTO_ENABLED_FILE)
    ids.add(str(user_id))
    _write_ids(AUTO_ENABLED_FILE, ids)


def disable_auto_mode(user_id: str | int) -> None:
    ids = _read_ids(AUTO_ENABLED_FILE)
    ids.discard(str(user_id))
    _write_ids(AUTO_ENABLED_FILE, ids)


def is_auto_enabled(user_id: str | int) -> bool:
    ids = _read_ids(AUTO_ENABLED_FILE)
    return str(user_id) in ids


# ---------- Admin edit helpers ----------
def update_work_time_entry(user_id: str | int, date_str: str, action: str, new_time_str: str) -> bool:
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
