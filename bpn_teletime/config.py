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

WORKTIME_FILE = "work_time.csv"