from .base import *

DEBUG = True

SECRET_KEY = 'django-insecure-dev-secret-key-change-in-production-abc123xyz789'

ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
