# pylint: disable=wildcard-import
import re
from decouple import config
from .base import *

# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/
DEBUG = False
SITE_ID = config('SITE_ID', default=2, cast=int)

ALLOWED_HOSTS = re.split(r'\s+', config('HOST_DOMAINS'))

DATABASES = {
    'default': {
        'ENGINE': 'mysql.connector.django',
        'PORT': 3306,
        'HOST': config('MYSQL_HOST'),
        'USER': config('MYSQL_USER'),
        'PASSWORD': config('MYSQL_PASSWORD'),
        'NAME': config('MYSQL_DATABASE'),
    }
}


# Redis task queues
# https://github.com/rq/django-rq#deploying-on-ubuntu

RQ_QUEUES = {
    'default': {
        'HOST': config('RQ_HOST_DEFAULT'),
        'PORT': config('RQ_PORT_DEFAULT'),
        'DB': config('RQ_DB_DEFAULT'),
        'PASSWORD': config('RQ_PASSWORD_DEFAULT'),
        'DEFAULT_TIMEOUT': config('RQ_TIMEOUT_DEFAULT', default=360),
    },
}

RQ_SHOW_ADMIN_LINK = True


# Emailing

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT')
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=False, cast=bool)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)


# Logging
# We can log everything to stdout since systemd will capture output and put it in the journal for us
# automatically

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
            'formatter': 'standard'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO')
        },
        'recordtransfer': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'rq.worker': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        }
    }
}
