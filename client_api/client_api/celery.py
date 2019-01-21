from __future__ import absolute_import, unicode_literals
import os
import logging
from celery import Celery
from django.core.mail import send_mail
from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'client_api.settings')

app = Celery('client_api')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


logger = logging.getLogger(__name__)

@app.task(bind=True, name='send_django_emails', max_retries=getattr(settings, 'EMAIL_FAIL_RETRY_COUNT', 5))
def send_django_emails_task(self, emails, subject, body):
    if not isinstance(emails, list):
        emails = [emails]

    number_sent = send_mail(
        subject,
        message=body,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=emails,
    )
    if not number_sent:
        error = 'Can not send emails to users:\n{}.'.format('\n'.join([email for email in emails]))
        logger.error(error)
