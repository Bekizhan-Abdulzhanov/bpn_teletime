import os
import csv

# Каталог текущего скрипта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Пути к CSV-файлам
USERS_FILE = os.path.join(BASE_DIR, os.environ.get('USERS_FILE', 'users.csv'))
WORKTIME_FILE = os.path.join(BASE_DIR, os.environ.get('WORKTIME_FILE', 'work_time.csv'))
AUTO_APPROVED_FILE = os.path.join(BASE_DIR, os.environ.get('AUTO_APPROVED_FILE', 'auto_approved_users.csv'))

def save_work_time(user_id, event, timestamp):
    """Записать метку времени в work_time.csv"""
    with open(WORKTIME_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([user_id, event, timestamp])

def is_user_approved(user_id):
    """Проверить, одобрен ли пользователь (есть ли в users.csv)"""
    if not os.path.exists(USERS_FILE):
        return False
    with open(USERS_FILE, newline='', encoding='utf-8') as f:
        return any(row[0] == str(user_id) for row in csv.reader(f))

def get_all_users():
    """Вернуть {user_id: username} для всех одобренных пользователей"""
    users = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, newline='', encoding='utf-8') as f:
            for row in csv.reader(f):
                # Ожидаем строки вида [id, username, status?]
                users[row[0]] = row[1]
    return users

def approve_user(user_id):
    """Добавить пользователя в авто-одобренные"""
    approved = set()
    if os.path.exists(AUTO_APPROVED_FILE):
        with open(AUTO_APPROVED_FILE, encoding='utf-8') as f:
            approved = set(line.strip() for line in f)
    approved.add(str(user_id))
    with open(AUTO_APPROVED_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(approved))

def deny_user(user_id):
    """Убрать пользователя из авто-одобренных"""
    if not os.path.exists(AUTO_APPROVED_FILE):
        return
    with open(AUTO_APPROVED_FILE, encoding='utf-8') as f:
        approved = set(line.strip() for line in f)
    approved.discard(str(user_id))
    with open(AUTO_APPROVED_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(approved))

def get_pending_users():
    """Вернуть {user_id: username} для пользователей в статусе 'pending'"""
    pending = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, newline='', encoding='utf-8') as f:
            for row in csv.reader(f):
                # Предполагаем, что в третьем столбце хранится статус
                if len(row) >= 3 and row[2] == 'pending':
                    pending[row[0]] = row[1]
    return pending

def enable_auto_mode(user_id):
    """Включить авто-режим для пользователя"""
    approve_user(user_id)

def disable_auto_mode(user_id):
    """Отключить авто-режим для пользователя"""
    deny_user(user_id)

def is_auto_enabled(user_id):
    """Проверить, включён ли авто-режим (наличие в AUTO_APPROVED_FILE)"""
    if not os.path.exists(AUTO_APPROVED_FILE):
        return False
    with open(AUTO_APPROVED_FILE, encoding='utf-8') as f:
        return str(user_id) in (line.strip() for line in f)
