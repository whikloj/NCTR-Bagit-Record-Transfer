from http import HTTPStatus

import requests
from msal import ConfidentialClientApplication, SerializableTokenCache
from .configuration import AzureAuthConfigured
from .exceptions import AzureAuthInvalidTokenException


class Authenticator:

    """ Microsoft ConfidentialClientApplication instance. """
    _ms_app = None

    """ Microsoft Graph URI. """
    _ms_graph_uri = "https://graph.microsoft.com/v1.0/me"

    """ AzureAuth instance for configuring the client. """
    _config = None

    """ The token cache. """
    _cache = None

    """ Id of the token cache """
    _token_cache_id = "azure-auth-token-cache"

    """ The current request we are handling """
    request = None

    def __init__(self, request=None):
        self._cache = SerializableTokenCache()
        self.request = request

    @property
    def ms_app(self) -> ConfidentialClientApplication:
        if not self._ms_app:
            self._ms_app = ConfidentialClientApplication(
                client_id=AzureAuthConfigured.get_client_id(),
                client_credential=AzureAuthConfigured.get_client_secret(),
                authority=AzureAuthConfigured.get_authority(),
                token_cache=self._token_cache
            )
        return self._ms_app

    @property
    def _token_cache(self):
        c = self.request.session.get(self._token_cache_id, None)
        if c:
            self._cache.deserialize(c)
        return self._cache

    def get_token(self):
        accounts = self.ms_app.get_accounts()
        if accounts:
            chosen = accounts[0]
            result = self.ms_app.acquire_token_silent(AzureAuthConfigured.get_scopes(), account=chosen)
            self._serialize_cache_changes()
            return result

    def _serialize_cache_changes(self):
        if self._cache.has_state_changed:
            self.request.session[self._token_cache_id] = self._cache.serialize()

    def get_user(self, token):
        access_token = token.get("access_token")
        if not access_token:
            return {}

        response = requests.get(
            self._ms_graph_uri,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if response.ok:
            output = response.json()
        elif response.status_code == HTTPStatus.UNAUTHORIZED:
            raise AzureAuthInvalidTokenException(response.json()["error"])
