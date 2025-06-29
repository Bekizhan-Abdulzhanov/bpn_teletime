import os
import csv
from datetime import datetime
from config import AUTO_APPROVED_USERS

# Константы
DATA_DIR = "data"
WORKTIME_FILE = os.path.join(DATA_DIR, "work_time.csv")
USERS_FILE = os.path.join(DATA_DIR, "users.csv")
AUTO_ENABLED_FILE = os.path.join(DATA_DIR, "auto_enabled.csv")

# Убедимся, что папка для данных существует
os.makedirs(DATA_DIR, exist_ok=True)

# 📌 Работа с отметками времени
def save_work_time(user_id, username, action):
    with open(WORKTIME_FILE, "a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([user_id, username, action, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

# 📌 Проверка, одобрен ли пользователь
def is_user_approved(user_id):
    if user_id in AUTO_APPROVED_USERS:
        return True
    if not os.path.exists(USERS_FILE):
        return False
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        for row in csv.reader(f):
            if row and row[0] == str(user_id) and row[2] == "1":
                return True
    return False

# 📌 Получение всех одобренных пользователей
def get_all_users():
    users = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            for row in csv.reader(f):
                if row and row[2] == "1":
                    users[int(row[0])] = row[1]
    return users

# 📌 Получение списка ожидающих одобрения
def get_pending_users():
    pending = []
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            for row in csv.reader(f):
                if row and row[2] == "0":
                    pending.append((int(row[0]), row[1]))
    return pending

# 📌 Одобрить пользователя по ID
def approve_user_by_id(user_id):
    if not os.path.exists(USERS_FILE):
        return
    rows = []
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        for row in csv.reader(f):
            if row and row[0] == str(user_id):
                row[2] = "1"
            rows.append(row)
    with open(USERS_FILE, "w", encoding="utf-8", newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

# 📌 Отклонить пользователя по ID
def reject_user_by_id(user_id):
    if not os.path.exists(USERS_FILE):
        return
    rows = []
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        for row in csv.reader(f):
            if row and row[0] != str(user_id):
                rows.append(row)
    with open(USERS_FILE, "w", encoding="utf-8", newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

# 📌 Проверка авто-режима
def is_auto_enabled(user_id):
    if not os.path.exists(AUTO_ENABLED_FILE):
        return False
    with open(AUTO_ENABLED_FILE, "r") as f:
        return str(user_id) in f.read().splitlines()

# 📌 Включить авто-режим
def enable_auto_mode(user_id):
    if is_auto_enabled(user_id):
        return
    with open(AUTO_ENABLED_FILE, "a") as f:
        f.write(f"{user_id}\n")

# 📌 Выключить авто-режим
def disable_auto_mode(user_id):
    if not os.path.exists(AUTO_ENABLED_FILE):
        return
    with open(AUTO_ENABLED_FILE, "r") as f:
        lines = f.read().splitlines()
    lines = [uid for uid in lines if uid != str(user_id)]
    with open(AUTO_ENABLED_FILE, "w") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))
