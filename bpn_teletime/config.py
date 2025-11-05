import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
PORT = int(os.getenv("PORT", 8443))
TIMEZONE = os.getenv("TIMEZONE", "Asia/Bishkek")


ADMIN_IDS = [
    557174721,  # BekizhanAbdulzhanov
    378268765,  # ErlanNasiev
]
ADMIN_IDS = [int(x) for x in ADMIN_IDS]


AUTO_APPROVED_USERS = {
    378268765: "ErlanNasiev",
    557174721: "BekizhanAbdulzhanov",
}


EMPLOYEE_USERS = {
    459732737: "apkanat",
    883069902: "AmanAkylbekov",
    1033131013: "kristi_bpn",
    5320022391: "KI",
    5785249519: "Peri_Masali",
    7321119959: "Vlad74Orlov",
}


ALLOWED_AUTO_USERS = {**AUTO_APPROVED_USERS, **EMPLOYEE_USERS}


DATA_DIR = os.path.abspath(os.getenv("DATA_DIR", "data"))


USERS_FILE_NAME        = os.getenv("USERS_FILE", "users.csv")
WORKTIME_FILE_NAME     = os.getenv("WORKTIME_FILE", "work_time.csv")
AUTO_ENABLED_FILE_NAME = os.getenv("AUTO_ENABLED_FILE", "auto_enabled.csv")


WORKTIME_FILE = WORKTIME_FILE_NAME
