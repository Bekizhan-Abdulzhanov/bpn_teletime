import csv
import os
from config import WORKTIME_FILE, AUTO_APPROVED_USERS

APPROVED_USERS = set(AUTO_APPROVED_USERS.keys())

PENDING_USERS = {}  # user_id -> username

def is_user_approved(user_id):
    return user_id in APPROVED_USERS

def add_pending_user(user_id, username):
    PENDING_USERS[user_id] = username

def get_pending_users():
    return PENDING_USERS.copy()

def approve_user(user_id):
    APPROVED_USERS.add(user_id)
    if user_id in PENDING_USERS:
        del PENDING_USERS[user_id]

def deny_user(user_id):
    if user_id in PENDING_USERS:
        del PENDING_USERS[user_id]

def save_work_time(user_id, username, action):
    with open(WORKTIME_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([user_id, username, action])

def get_all_users():
    return list(APPROVED_USERS)

# 📌 Проверка авто-режима
def is_auto_enabled(user_id):
    if not os.path.exists(AUTO_APPROVED_USERS):
        return False
    with open(AUTO_APPROVED_USERS, "r") as f:
        return str(user_id) in f.read().splitlines()

# 📌 Включить авто-режим
def enable_auto_mode(user_id):
    if is_auto_enabled(user_id):
        return
    with open(AUTO_APPROVED_USERS, "a") as f:
        f.write(f"{user_id}\n")

# 📌 Выключить авто-режим
def disable_auto_mode(user_id):
    if not os.path.exists(AUTO_APPROVED_USERS):
        return
    with open(AUTO_APPROVED_USERS, "r") as f:
        lines = f.read().splitlines()
    lines = [uid for uid in lines if uid != str(user_id)]
    with open(AUTO_APPROVED_USERS, "w") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))
