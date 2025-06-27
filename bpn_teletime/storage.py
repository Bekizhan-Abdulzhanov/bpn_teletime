import os
import csv
from datetime import datetime
from config import WORKTIME_FILE, USERS_FILE


def save_work_time(user_id, username, action):
    os.makedirs(os.path.dirname(WORKTIME_FILE), exist_ok=True)
    with open(WORKTIME_FILE, "a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([user_id, username, action, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])


def is_user_approved(user_id):
    if not os.path.exists(USERS_FILE):
        return False
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        for row in csv.reader(f):
            if row and row[0] == str(user_id) and row[2] == "1":
                return True
    return False


def get_all_users():
    users = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            for row in csv.reader(f):
                if row and row[2] == "1":
                    users[row[0]] = row[1]
    return users


def approve_user_by_id(user_id):
    if not os.path.exists(USERS_FILE):
        return
    rows = []
    updated = False
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        for row in csv.reader(f):
            if row and row[0] == str(user_id):
                row[2] = "1"
                updated = True
            rows.append(row)
    if updated:
        with open(USERS_FILE, "w", encoding="utf-8", newline='') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
