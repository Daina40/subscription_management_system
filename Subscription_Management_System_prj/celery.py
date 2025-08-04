import os
from celery import Celery
from celery.schedules import crontab 

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Subscription_Management_System_prj.settings')

app = Celery('Subscription_Management_System_prj')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'fetch-every-hour': {
        'task': 'Subscription_app.tasks.fetch_usd_to_bdt_rate',
        'schedule': crontab(minute=0, hour='*'),  # every hour
    },
}
