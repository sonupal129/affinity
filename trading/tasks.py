from celery import Celery
from celery.schedules import crontab



app = Celery('tasks', broker='redis://redis:6379')


# Celery Tasks Schedule

# app.conf.beat_schedule = {
#     "start_trade": {
#         'task': 'start_trade',
#         'schedule': crontab(minute='*/3', day_of_week='mon,tue,wed,thu,fri'),
#     }
# }


