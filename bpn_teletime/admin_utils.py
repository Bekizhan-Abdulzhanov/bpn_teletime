import os
from config import ADMIN_IDS  # теперь список, а не один ID
from storage import get_all_users
from reports import generate_excel_report_by_months

def send_monthly_reports(bot):
    users = get_all_users()
    for user_id, username in users.items():
        path = generate_excel_report_by_months(user_id, username)
        for admin_id in ADMIN_IDS:
            if path and os.path.exists(path):
                with open(path, 'rb') as f:
                    bot.send_document(admin_id, f, caption=f"📄 Отчёт за месяц: {username}")
            else:
                bot.send_message(admin_id, f"⚠️ Нет данных для {username}")
