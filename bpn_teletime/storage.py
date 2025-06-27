import csv
import os
from datetime import datetime

USERS_FILE = 'users.csv'
ADMINS_FILE = 'admins.csv'
WORKTIME_FILE = 'work_time.csv'


def is_user_approved(user_id: int) -> bool:
    if not os.path.exists(USERS_FILE):
        return False
    with open(USERS_FILE, 'r', encoding='utf-8') as file:
        for line in file:
            parts = line.strip().split(',')
            if str(user_id) == parts[0] and parts[2] == '1':
                return True
    return False


def is_admin(user_id: int) -> bool:
    if not os.path.exists(ADMINS_FILE):
        return False
    with open(ADMINS_FILE, 'r', encoding='utf-8') as file:
        return str(user_id) in [line.strip() for line in file]


def add_admin(user_id: int):
    if not is_admin(user_id):
        with open(ADMINS_FILE, 'a', encoding='utf-8') as file:
            file.write(f"{user_id}\n")


def get_all_users() -> dict:
    users = {}
    if not os.path.exists(USERS_FILE):
        return users
    with open(USERS_FILE, 'r', encoding='utf-8') as file:
        for line in file:
            parts = line.strip().split(',')
            if len(parts) >= 2:
                users[parts[0]] = parts[1]
    return users


def approve_user_by_id(user_id: int):
    updated = False
    rows = []
    user_id = str(user_id)

    if not os.path.exists(USERS_FILE):
        return False

    with open(USERS_FILE, 'r', encoding='utf-8') as file:
        for row in file:
            parts = row.strip().split(',')
            if parts[0] == user_id:
                parts[2] = '1'
                updated = True
            rows.append(','.join(parts))

    if updated:
        with open(USERS_FILE, 'w', encoding='utf-8') as file:
            file.write('\n'.join(rows) + '\n')
    return updated


def save_work_time(user_id: int, username: str, action: str):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(WORKTIME_FILE, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([user_id, username, action, now])

