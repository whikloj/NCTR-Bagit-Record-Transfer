
from decouple import config

IS_MULTITENANT = config("AZURE_AUTH_IS_MULTITENANT", False, cast=bool)
TENANT_ID = config("AZURE_AUTH_TENANT_ID")
CLIENT_ID = config("AZURE_AUTH_CLIENT_ID")
CLIENT_SECRET = config("AZURE_AUTH_CLIENT_SECRET")
REDIRECT_URI = config("AZURE_AUTH_REDIRECT_URI")
SCOPES = config("AZURE_AUTH_SCOPES", [])

AUTH_CONFIGURATION = {
    'tenant_id': TENANT_ID,
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'redirect_uri': REDIRECT_URI,
    'scopes': SCOPES,
    'is_multi_tenant': IS_MULTITENANT
}
