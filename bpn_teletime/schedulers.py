from apscheduler.schedulers.background import BackgroundScheduler
from storage import save_work_time
from admin_utils import send_monthly_reports

AUTO_USERS = {
    378268765: "ErlanNasiev",
    557174721: "BekizhanAbdulzhanov",
}

def setup_scheduler(scheduler, bot):
    for user_id, name in AUTO_USERS.items():
        scheduler.add_job(save_work_time, 'cron', day_of_week='mon,wed', hour=8, minute=29,
                          args=[user_id, name, 'Пришел на работу'])
        scheduler.add_job(save_work_time, 'cron', day_of_week='mon,wed', hour=12, minute=0,
                          args=[user_id, name, 'Вышел на обед'])
        scheduler.add_job(save_work_time, 'cron', day_of_week='mon,wed', hour=13, minute=0,
                          args=[user_id, name, 'Вернулся с обеда'])
        scheduler.add_job(save_work_time, 'cron', day_of_week='mon,wed', hour=17, minute=30,
                          args=[user_id, name, 'Ушел с работы'])

        scheduler.add_job(save_work_time, 'cron', day_of_week='tue,thu', hour=8, minute=28,
                          args=[user_id, name, 'Пришел на работу'])
        scheduler.add_job(save_work_time, 'cron', day_of_week='tue,thu', hour=12, minute=1,
                          args=[user_id, name, 'Вышел на обед'])
        scheduler.add_job(save_work_time, 'cron', day_of_week='tue,thu', hour=13, minute=0,
                          args=[user_id, name, 'Вернулся с обеда'])
        scheduler.add_job(save_work_time, 'cron', day_of_week='tue,thu', hour=17, minute=30,
                          args=[user_id, name, 'Ушел с работы'])

        scheduler.add_job(save_work_time, 'cron', day_of_week='fri', hour=8, minute=27,
                          args=[user_id, name, 'Пришел на работу'])
        scheduler.add_job(save_work_time, 'cron', day_of_week='fri', hour=12, minute=0,
                          args=[user_id, name, 'Вышел на обед'])
        scheduler.add_job(save_work_time, 'cron', day_of_week='fri', hour=13, minute=0,
                          args=[user_id, name, 'Вернулся с обеда'])
        scheduler.add_job(save_work_time, 'cron', day_of_week='fri', hour=17, minute=30,
                          args=[user_id, name, 'Ушел с работы'])

    # 📤 Автоматическая отправка отчётов админу в конце месяца
    scheduler.add_job(send_monthly_reports, 'cron', day='last', hour=8, minute=30, args=[bot])
