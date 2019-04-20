DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'market_platform_backend',
        'USER': 'postgres',
        'HOST': 'postgres',
        'PORT': '5432',
        'PASSWORD': ''
    }
}

CELERY_BROKER_URL = 'redis://redis:6379'
CELERY_RESULT_BACKEND = 'redis://redis:6379'
API_URL = 'http://0.0.0.0:8000'

