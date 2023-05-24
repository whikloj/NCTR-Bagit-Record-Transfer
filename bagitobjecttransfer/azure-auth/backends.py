from django.contrib.auth.backends import ModelBackend, UserModel
from django.db.models import Q

try:
    from django.contrib.auth import get_user_model
except ImportError:
    from django.contrib.auth.models import User

    def get_user_model(*args, **kwargs):
        return User
import jwt
import logging

from .authentication import Authenticator

logger = logging.getLogger(__name__)


class AzureAuth(ModelBackend):

    def __init__(self):
        self.User = get_user_model()

    def authenticate(self, request, token: dict = None, nonce=None, **kwargs):
        if token is None:
            return None

        payload = Authenticator(request).get_user(token)

        if not payload:
            return None

        try:
            user = self.User.objects.filter(email=payload.get("upn", "NoEmail"))
            logger.debug(user)
        except self.User.DoesNotExist as e:
            """ User doesn't exist, do we want to auto generate one? """
            raise e

        return user