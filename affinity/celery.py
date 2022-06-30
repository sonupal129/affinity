from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings


# setting the Django settings module.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'affinity.settings')
app = Celery('affinity')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Looks up for task modules in Django applications and loads them
app.autodiscover_tasks()

@app.task
def debug_task():
    print("Debug Successful!")


app.conf.enable_utc = True
app.conf.task_ignore_result = True