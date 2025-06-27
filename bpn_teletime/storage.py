import csv
import os
from datetime import datetime

USERS_FILE = 'users.csv'
ADMINS_FILE = 'admins.csv'
WORKTIME_FILE = 'work_time.csv'


def is_user_approved(user_id):
    if not os.path.exists(USERS_FILE):
        return False
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        for row in csv.reader(f):
            if str(user_id) == row[0] and row[2] == "1":
                return True
    return False

def approve_user_id(user_id, username):
    users = []
    found = False
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            for row in csv.reader(f):
                if row[0] == str(user_id):
                    users.append([row[0], username, "1"])
                    found = True
                else:
                    users.append(row)
    if not found:
        users.append([str(user_id), username, "1"])
    with open(USERS_FILE, 'w', encoding='utf-8', newline='') as f:
        csv.writer(f).writerows(users)

def save_work_time(user_id, username, action):
    from datetime import datetime
    if not os.path.exists(WORKTIME_FILE):
        with open(WORKTIME_FILE, 'w', encoding='utf-8', newline='') as f:
            csv.writer(f).writerow(['user_id', 'username', 'action', 'timestamp'])
    with open(WORKTIME_FILE, 'a', encoding='utf-8', newline='') as f:
        csv.writer(f).writerow([user_id, username, action, datetime.now().isoformat()])

def get_all_users():
    result = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            for row in csv.reader(f):
                result[row[0]] = row[1]
    return result