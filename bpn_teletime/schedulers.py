from apscheduler.schedulers.background import BackgroundScheduler
from storage import save_work_time, get_all_users
from reports import generate_excel_report_by_months
from datetime import datetime
import os

AUTO_USERS = {
    378268765: "ErlanNasiev",
    557174721: "BekizhanAbdulzhanov",
}

def log_action(user_id, name, action):
    print(f"[AUTO] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} — {name} ({user_id}): {action}")

def scheduled_save(user_id, username, action):
    try:
        save_work_time(user_id, username, action)
        log_action(user_id, username, action)
    except Exception as e:
        print(f"[ERROR] Запись не выполнена для {username}: {e}")

def generate_all_monthly_reports():
    print("[SCHEDULER] Генерация всех отчетов по месяцам...")
    users = get_all_users()
    for user_id, username in users.items():
        try:
            path = generate_excel_report_by_months(user_id)
            if path and os.path.exists(path):
                print(f"[REPORT] Отчёт создан для {username} ({user_id}): {path}")
            else:
                print(f"[WARNING] Данных нет для: {username} ({user_id})")
        except Exception as e:
            print(f"[ERROR] Ошибка при генерации отчета для {username}: {e}")

def setup_scheduler(scheduler: BackgroundScheduler):
    for user_id, name in AUTO_USERS.items():
        
        scheduler.add_job(scheduled_save, 'cron', day_of_week='mon,wed', hour=8, minute=29, args=[user_id, name, 'Пришел на работу'])
        scheduler.add_job(scheduled_save, 'cron', day_of_week='mon,wed', hour=12, minute=0, args=[user_id, name, 'Вышел на обед'])
        scheduler.add_job(scheduled_save, 'cron', day_of_week='mon,wed', hour=13, minute=0, args=[user_id, name, 'Вернулся с обеда'])
        scheduler.add_job(scheduled_save, 'cron', day_of_week='mon,wed', hour=17, minute=30, args=[user_id, name, 'Ушел с работы'])

        
        scheduler.add_job(scheduled_save, 'cron', day_of_week='tue,thu', hour=8, minute=28, args=[user_id, name, 'Пришел на работу'])
        scheduler.add_job(scheduled_save, 'cron', day_of_week='tue,thu', hour=12, minute=1, args=[user_id, name, 'Вышел на обед'])
        scheduler.add_job(scheduled_save, 'cron', day_of_week='tue,thu', hour=13, minute=0, args=[user_id, name, 'Вернулся с обеда'])
        scheduler.add_job(scheduled_save, 'cron', day_of_week='tue,thu', hour=17, minute=30, args=[user_id, name, 'Ушел с работы'])

        
        scheduler.add_job(scheduled_save, 'cron', day_of_week='fri', hour=8, minute=27, args=[user_id, name, 'Пришел на работу'])
        scheduler.add_job(scheduled_save, 'cron', day_of_week='fri', hour=12, minute=0, args=[user_id, name, 'Вышел на обед'])
        scheduler.add_job(scheduled_save, 'cron', day_of_week='fri', hour=13, minute=0, args=[user_id, name, 'Вернулся с обеда'])
        scheduler.add_job(scheduled_save, 'cron', day_of_week='fri', hour=17, minute=30, args=[user_id, name, 'Ушел с работы'])

    # Генерация всех отчетов каждый день в 18:00
    scheduler.add_job(generate_all_monthly_reports, 'cron', hour=18, minute=0)

    print("[SCHEDULER] Все задачи успешно зарегистрированы.")
