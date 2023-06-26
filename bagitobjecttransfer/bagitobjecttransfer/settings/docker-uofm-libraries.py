# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
import re
from pathlib import Path
from decouple import config
from .base import *

DEBUG = False
SITE_ID = config('SITE_ID', default=1, cast=int)

ALLOWED_HOSTS = re.split(r'\s+', config('HOST_DOMAINS'))
CSRF_TRUSTED_ORIGINS = re.split(r'\s+', config('TRUSTED_ORIGINS'))

# MySQL Database

DATABASES = {
    'default': {
        'ENGINE': 'mysql.connector.django',
        'HOST': config('MYSQL_HOST', 'db'),
        'PORT': config('MYSQL_PORT', 3306),
        'USER': config('MYSQL_USER'),
        'PASSWORD': config('MYSQL_PASSWORD'),
        'NAME': config('MYSQL_DATABASE'),
    }
}


# Asynchronous Redis Task Queue Manager
# https://github.com/rq/django-rq

RQ_QUEUES = {
    'default': {
        'HOST': config('RQ_HOST_DEFAULT', 'redis'),
        'PORT': config('RQ_PORT_DEFAULT', 6379),
        'DB': config('RQ_DB_DEFAULT', 0),
        'PASSWORD': config('RQ_PASSWORD_DEFAULT', ''),
        'DEFAULT_TIMEOUT': config('RQ_TIMEOUT_DEFAULT', default=360),
    },
}

RQ_SHOW_ADMIN_LINK = True

# Emailing - Uses MailHog to intercept emails
# MailHog web UI runs at localhost:8025
# More information: https://github.com/mailhog/MailHog

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT')
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=False, cast=bool)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)

# Captcha

SILENCED_SYSTEM_CHECKS = ['captcha.recaptcha_test_key_error']

# Logging

log_folder = Path(BASE_DIR) / 'logs'
REDIS_LOG_FILE = log_folder / 'redis-server.log'
RQ_WORKER_LOG_FILE = log_folder / 'rqworker.log'
MY_SQL_ERROR_LOG_FILE = log_folder / 'mysql_error.log'
MY_SQL_GENERAL_LOG_FILE = log_folder / 'mysql.log'
MY_SQL_SLOW_QUERY_LOG_FILE = log_folder / 'mysql_slow_queries.log'

#for log_file in (
#    REDIS_LOG_FILE,
#    RQ_WORKER_LOG_FILE,
#    MY_SQL_ERROR_LOG_FILE,
#    MY_SQL_GENERAL_LOG_FILE,
#    MY_SQL_SLOW_QUERY_LOG_FILE):
#    if not log_file.exists():
#        log_file.touch()

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '{levelname} {asctime} {module}: {message}',
            'style': '{'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
        'rqworker_file': {
            'class': 'logging.FileHandler',
            'filename': '/var/log/django-rq/rqworker.log',
            'formatter': 'standard',
        },
        'recordtransfer_file': {
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/recordtransfer.log',
            'formatter': 'standard',
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO')
        },
        'recordtransfer': {
            'handlers': ['recordtransfer_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'rq.worker': {
            'handlers': ['rqworker_file'],
            'level': 'INFO',
            'propagate': True,
        }
    }
}

