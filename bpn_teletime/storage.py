import os
import csv
from datetime import datetime

# Константы
WORKTIME_FILE = "work_time.csv"
USERS_FILE = "users.csv"
AUTO_ENABLED_FILE = "auto_enabled.csv"

# 📌 Работа с отметками времени
def save_work_time(user_id, username, action):
    os.makedirs(os.path.dirname(WORKTIME_FILE) or ".", exist_ok=True)
    with open(WORKTIME_FILE, "a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([user_id, username, action, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

# 📌 Проверка, одобрен ли пользователь
def is_user_approved(user_id):
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


def is_auto_enabled(user_id):
    if not os.path.exists(AUTO_ENABLED_FILE):
        return False
    with open(AUTO_ENABLED_FILE, "r") as f:
        return str(user_id) in f.read().splitlines()

def enable_auto_mode(user_id):
    if not is_auto_enabled(user_id):
        with open(AUTO_ENABLED_FILE, "a") as f:
            f.write(f"{user_id}\n")

def disable_auto_mode(user_id):
    if not os.path.exists(AUTO_ENABLED_FILE):
        return
    with open(AUTO_ENABLED_FILE, "r") as f:
        lines = f.read().splitlines()
    lines = [uid for uid in lines if uid != str(user_id)]
    with open(AUTO_ENABLED_FILE, "w") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))
