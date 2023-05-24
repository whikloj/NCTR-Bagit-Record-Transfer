
class AzureAuthConfigurationException(BaseException):
    """ Exception caused by errors in the configuration. """
    def __init__(self, message):
        BaseException.__init__(self, message)


class AzureAuthInvalidTokenException(BaseException):
    """ Exception if the token is invalid. """
    def __init__(self, message):
        BaseException.__init__(self, message)
