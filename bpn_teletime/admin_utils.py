import os
from config import ADMIN_ID
from storage import get_all_users
from reports import generate_excel_report_by_months

def send_monthly_reports(bot):
    for user_id, username in get_all_users().items():
        path = generate_excel_report_by_months(user_id, username)
        if path and os.path.exists(path):
            with open(path, 'rb') as f:
                bot.send_document(ADMIN_ID, f, caption=f"📄 Отчёт за месяц: {username}")
        else:
            bot.send_message(ADMIN_ID, f"⚠️ Нет данных для {username}")
