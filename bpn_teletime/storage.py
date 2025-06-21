import csv
import os
from config import USERS_FILE, WORKTIME_FILE
from utils import format_now

def save_work_time(user_id, user_name, action):
    file_exists = os.path.isfile(WORKTIME_FILE)
    try:
        with open(WORKTIME_FILE, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(["User ID", "User Name", "Action", "Timestamp"])
            writer.writerow([user_id, user_name, action, format_now()])
    except Exception as e:
        print(f"Ошибка при записи: {e}")

def update_user_status(user_id, status):
    users = []
    with open(USERS_FILE, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == str(user_id):
                row[2] = status
            users.append(row)
    with open(USERS_FILE, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(users)


def is_user_approved(user_id):
    try:
        with open('users.csv', 'r', encoding='utf-8') as f:
            for row in csv.reader(f):
                if row[0] == str(user_id) and row[2] == 'approved':
                    return True
    except FileNotFoundError:
        return False
    return False

def get_all_users():
    users = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                users[row[0]] = row[1]
    return users
