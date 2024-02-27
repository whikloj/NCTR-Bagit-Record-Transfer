''' Application-specific settings for the recordtransfer app '''
from decouple import config

# Enable or disable the sign-up ability

SIGN_UP_ENABLED = config('SIGN_UP_ENABLED', default=True, cast=bool)

# The location where bags will be stored

BAG_STORAGE_FOLDER = config('BAG_STORAGE_FOLDER')

# The location where uploaded files are stored temporarily

UPLOAD_STORAGE_FOLDER = config('UPLOAD_STORAGE_FOLDER')

# Whether to allow updating BagIt bags

ALLOW_BAG_CHANGES = config('ALLOW_BAG_CHANGES', default=True, cast=bool)

# Email Usernames

DO_NOT_REPLY_USERNAME = config('DO_NOT_REPLY_USERNAME', default='do-not-reply')
ARCHIVIST_EMAIL = config('ARCHIVIST_EMAIL')

# Checksum types

BAG_CHECKSUMS = [
    algorithm.strip() for algorithm in config('BAG_CHECKSUMS', default='sha512').split(',')
]

# Maximum upload thresholds (in MB)

MAX_TOTAL_UPLOAD_SIZE = config('MAX_TOTAL_UPLOAD_SIZE', default=256, cast=int)
MAX_SINGLE_UPLOAD_SIZE = config('MAX_SINGLE_UPLOAD_SIZE', default=64, cast=int)
MAX_TOTAL_UPLOAD_COUNT = config('MAX_TOTAL_UPLOAD_COUNT', default=40, cast=int)
MAX_TOTAL_STORAGE_SIZE = config('MAX_TOTAL_STORAGE_SIZE', default=1024, cast=int)

MAX_TOTAL_STORAGE_WARNING_PERCENT = config('MAX_TOTAL_WARNING_PERCENT', default=80, cast=int)
MAX_TOTAL_STORAGE_WARNING_SIZE = MAX_TOTAL_STORAGE_SIZE * (MAX_TOTAL_STORAGE_WARNING_PERCENT / 100)
MAX_TOTAL_STORAGE_CRITICAL_PERCENT = config('MAX_TOTAL_CRITICAL_PERCENT', default=90, cast=int)
MAX_TOTAL_STORAGE_CRITICAL_SIZE = MAX_TOTAL_STORAGE_SIZE * (MAX_TOTAL_STORAGE_CRITICAL_PERCENT / 100)

# CLAMAV configuration.

CLAMAV_ENABLED = config('CLAMAV_ENABLED', default=False, cast=bool)
CLAMAV_HOST = config('CLAMAV_HOST', default=None)
CLAMAV_PORT = config('CLAMAV_PORT', default=3310, cast=int)

# Filepicker config
FP_TENANT_ID = config('MS_FILE_PICKER_TENANT_ID', '')
FP_CLIENT_ID = config('MS_FILE_PICKER_CLIENT_ID', '')

SITE_NAME_SHORT = config('SITE_NAME_SHORT', 'NCTR Record Transfer')
SITE_NAME = config('SITE_NAME', 'National Centre for Truth and Reconciliation Record Transfer')

# File types allowed to be uploaded to the backend. Do not use periods before the extension, and
# ensure that all file extensions are lowercase.

ACCEPTED_FILE_FORMATS = {
    'Archive': [
        'zip',
    ],
    'Audio': [
        'acc',
        'flac',
        'm4a',
        'mp3',
        'ogg',
        'wav',
        'wma',
    ],
    'Document': [
        'doc',
        'docx',
        'odt',
        'pdf',
        'rtf',
        'txt',
        'html',
    ],
    'Image': [
        'jpg',
        'jpeg',
        'gif',
        'png',
    ],
    'Presentation': [
        'ppt',
        'pptx',
        'pps',
        'ppsx',
    ],
    'Spreadsheet': [
        'xls',
        'xlsx',
        'csv',
    ],
    'Video': [
        'avi',
        'mkv',
        'mov',
        'mp4',
        'mpeg4',
        'mpg',
        'wmv',
    ],
}
