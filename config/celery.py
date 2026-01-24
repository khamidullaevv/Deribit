"""
Celery configuration for Deribit project.
"""

import os
from celery import Celery
from celery.schedules import schedule

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('deribit')

# Load configuration from Django settings with CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery connection."""
    print(f'Request: {self.request!r}')
