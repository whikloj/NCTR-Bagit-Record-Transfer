
import json
from types import SimpleNamespace

from ms_identity_web.constants import AuthorityType

from .exceptions import AzureAuthConfigurationException
from . import settings

class AzureAuth:

    _tenant_id = None

    _client_id = None

    _client_secret = None

    _is_multi_tenant = False

    _redirect_uri = None

    _scopes = []

    """ List of only required config keys """
    _required_config_keys = [
        'tenant_id',
        'client_id',
        'client_secret',
        'redirect_uri',
    ]

    """ Valid config keys, required plus extras """
    _valid_config_keys = _required_config_keys + [
        'is_multi_tenant',
        'scopes',
    ]

    def __init__(self, config=None):
        if config is None:
            config = {}
        valid_config = self._validate_config(config)
        for k, v in valid_config.items():
            self.__setattr__(k, v)
        if len(self._scopes) == 0:
            self._scopes = ["User.Read"]

    def newinstance(self, **kwargs):
        return SimpleNamespace(**kwargs)

    def _validate_config(self, config) -> dict:
        filtered_config = {k: v for k, v in config.items() if k in self._valid_config_keys}
        missing_required = [x for x in self._required_config_keys if x not in filtered_config.keys()]
        if len(missing_required) > 0:
            raise AzureAuthConfigurationException(f"Configuration is missing required values for {', '.join(missing_required)}")
        return filtered_config

    def get_client_id(self) -> str:
        return self._client_id

    def get_client_secret(self) -> str:
        return self._client_secret

    def get_authority(self) -> str:
        return f"https://login.microsoftonline.com/{'common' if self._is_multi_tenant else self._tenant_id }"

    def get_authority_type(self) -> AuthorityType:
        return AuthorityType.MULTI_TENANT if self._is_multi_tenant else AuthorityType.SINGLE_TENANT

    def get_redirect_uri(self) -> str:
        return self._redirect_uri

    def get_scopes(self) -> list:
        return self._scopes

    def get_scopes_json(self) -> str:
        return json.dumps(self._scopes)

    def generate_config_json(self):
        return "{" + \
                "\"type\": {" +\
                "\"client_type\": \"CONFIDENTIAL\"," + \
                f"\"authority_type\": \"{}\"," + \
                "\"framework\": \"DJANGO\"" + \
                "}," + \
                "\"client\": {" + \
                f"\"client_id\": \"{self._client_id}\"," + \
                f"\"client_credential\": \"{self._client_secret}\"," + \
                f"\"authority\": \"https://login.microsoftonline.com/{'common' if self._is_multi_tenant else self._tenant_id }\"" +\
                "}," + \
                "\"auth_request\": {" +\
                f"\"redirect_uri\": \"{self._redirect_uri}\"," +\
                f"\"scopes\": {json.dumps(self._scopes)}," +\
                "\"response_type\": \"code\"" +\
                "}," + \
                "\"flask\": null," + \
                "\"django\": {" + \
                "\"id_web_configs\": \"MS_ID_WEB_CONFIGS\"," + \
                "\"auth_endpoints\": {" + \
                "\"prefix\": \"azure-signin\"," + \
                "\"sign_in\": \"login\"," + \
                "\"edit_profile\": \"edit_profile\"," + \
                "\"redirect\": \"redirect\"," + \
                "\"sign_out\": \"logout\"," + \
                "\"post_sign_out\": \"post_sign_out\"" + \
                "}" + \
                "}" + \
                "}"

AzureAuthConfigured = AzureAuth(config=settings.AUTH_CONFIGURATION).newinstance()
