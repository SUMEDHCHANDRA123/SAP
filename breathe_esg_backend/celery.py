import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "breathe_esg_backend.settings")

app = Celery("breathe_esg_backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
