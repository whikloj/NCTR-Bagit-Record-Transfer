from decouple import config
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SECRET_KEY = config('SECRET_KEY', default='q9n%k!e3k8vuoo9vnromslji*hsczyj84krzz1$g=i$wp2r!s-')

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

INSTALLED_APPS = [
    'recordtransfer.apps.RecordTransferConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_countries',
    'django.forms',
    'formtools',
    'django_rq',
    'captcha',
    'dbtemplates',
    'azure_auth',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

ROOT_URLCONF = 'bagitobjecttransfer.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates')
        ],
        'APP_DIRS': False,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'recordtransfer.context_processors.signup_status',
                'recordtransfer.context_processors.file_uploads',
            ],
            'loaders': [
                'dbtemplates.loader.Loader',
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ]
        },
    },
]

USE_AZURE_AD_LOGIN = config("USE_AZURE_AD_LOGIN", False)
if USE_AZURE_AD_LOGIN:
    AUTHENTICATION_BACKENDS += [
        'azure_auth.backends.AzureBackend',
    ]
    AAD_TENANT_ID = config("MS_TENANT_ID", "")

    AZURE_AUTH = {
        "CLIENT_ID": config("MS_CLIENT_ID", ""),  # Mandatory
        "CLIENT_SECRET": config("MS_CLIENT_SECRET", ""),  # Mandatory
        "REDIRECT_URI": config("MS_REDIRECT_URL", ""),  # Mandatory, and must match Azure app registration.
        "SCOPES": ["User.Read"],
        "AUTHORITY": config("MS_AUTHORITY", "https://login.microsoftonline.com/common"),   # Or https://login.microsoftonline.com/common if multi-tenant
        "LOGOUT_URI": "http://localhost:8000/accounts/logout",    # Optional
        "PUBLIC_URLS": ["recordtransfer:index",]  # Optional, public views accessible by non-authenticated users
        # "PUBLIC_PATHS": ['/go/',],  # Optional, public paths accessible by non-authenticated users
    }
    LOGIN_URL = "azure-signin/login"

# Database primary key fields

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# WSGI

WSGI_APPLICATION = 'bagitobjecttransfer.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LOGIN_REDIRECT_URL = '/'

AUTH_USER_MODEL = 'recordtransfer.User'

FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Winnipeg'

USE_I18N = True

USE_TZ = True

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale')
]

# django-countries configuration
# https://github.com/SmileyChris/django-countries

COUNTRIES_FIRST = [
    'CA',
    'US',
]

COUNTRIES_FLAG_URL = 'flags/{code}.gif'

# django-dbtemplates configuration
# https://github.com/NationalCentreTruthReconciliation/django-dbtemplates

DBTEMPLATES_USE_CODEMIRROR = True

# Media and Static files (CSS, JavaScript, Images)

MEDIA_URL = '/media/'
STATIC_URL = '/static/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
FILE_UPLOAD_PERMISSIONS = 0o644

SITE_NAME = config("SITE_NAME", "National Centre for Truth and Reconciliation Record Transfer)")
SITE_NAME_SHORT = config("SITE_NAME_SHORT", "NCTR Record Transfer")
