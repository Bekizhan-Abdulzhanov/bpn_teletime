from apscheduler.schedulers.background import BackgroundScheduler
from storage import save_work_time
AUTO_USERS = {
    378268765: "ErlanNasiev",
    557174721: "BekizhanAbdulzhanov",
}

def setup_scheduler(scheduler):
    for user_id, name in AUTO_USERS.items():
        scheduler.add_job(save_work_time, 'cron', day_of_week='mon-fri', hour=8, minute=29, args=[user_id, name, 'Пришел на работу'])
        scheduler.add_job(save_work_time, 'cron', day_of_week='mon-fri', hour=12, minute=0, args=[user_id, name, 'Вышел на обед'])
        scheduler.add_job(save_work_time, 'cron', day_of_week='mon-fri', hour=13, minute=0, args=[user_id, name, 'Вернулся с обеда'])
        scheduler.add_job(save_work_time, 'cron', day_of_week='mon-fri', hour=17, minute=30, args=[user_id, name, 'Ушел с работы'])
