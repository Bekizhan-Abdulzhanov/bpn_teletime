import os
import csv

# Каталог текущего скрипта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Пути к CSV-файлам
USERS_FILE = os.path.join(BASE_DIR, os.environ.get('USERS_FILE', 'users.csv'))
WORKTIME_FILE = os.path.join(BASE_DIR, os.environ.get('WORKTIME_FILE', 'work_time.csv'))
AUTO_APPROVED_FILE = os.path.join(BASE_DIR, os.environ.get('AUTO_APPROVED_FILE', 'auto_approved_users.csv'))

def save_work_time(user_id, event, timestamp):
    with open(WORKTIME_FILE, 'a', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow([user_id, event, timestamp])

def is_user_approved(user_id):
    if not os.path.exists(USERS_FILE):
        return False
    with open(USERS_FILE, newline='', encoding='utf-8') as f:
        return any(row[0] == str(user_id) and len(row) >= 3 and row[2] == 'approved' for row in csv.reader(f))

def get_all_users():
    users = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, newline='', encoding='utf-8') as f:
            for row in csv.reader(f):
                if len(row) >= 2 and row[2] == 'approved':
                    users[row[0]] = row[1]
    return users

def approve_user(user_id):
    approved = set()
    if os.path.exists(AUTO_APPROVED_FILE):
        with open(AUTO_APPROVED_FILE, encoding='utf-8') as f:
            approved = set(line.strip() for line in f)
    approved.add(str(user_id))
    with open(AUTO_APPROVED_FILE, 'w', encoding='utf-8') as f:
        for uid in approved:
            f.write(f"{uid}\n")

def deny_user(user_id):
    if not os.path.exists(AUTO_APPROVED_FILE):
        return
    with open(AUTO_APPROVED_FILE, encoding='utf-8') as f:
        approved = set(line.strip() for line in f)
    approved.discard(str(user_id))
    with open(AUTO_APPROVED_FILE, 'w', encoding='utf-8') as f:
        for uid in approved:
            f.write(f"{uid}\n")

def get_pending_users():
    pending = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, newline='', encoding='utf-8') as f:
            for row in csv.reader(f):
                if len(row) >= 3 and row[2] == 'pending':
                    pending[row[0]] = row[1]
    return pending

def enable_auto_mode(user_id):
    approve_user(user_id)

def disable_auto_mode(user_id):
    deny_user(user_id)

def is_auto_enabled(user_id):
    if not os.path.exists(AUTO_APPROVED_FILE):
        return False
    with open(AUTO_APPROVED_FILE, encoding='utf-8') as f:
        return str(user_id) in (line.strip() for line in f)

def set_user_status(user_id: int, status: str):
    """
    Проставляет в users.csv для строки с данным user_id значение status
    в третьей колонке.
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
