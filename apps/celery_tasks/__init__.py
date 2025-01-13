from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

app = Celery('project')

app.config_from_object('django.conf:settings', namespace='CELERY')
import django
django.setup()

app.autodiscover_tasks()


# Autodiscover tasks in all Django apps that have a 'tasks.py' module
from .tasks import *

