from ... import config


def verify(api_key):
    """Verify API key.
    """
    whitelist = config.API_KEY_WHITELIST.split(',')
    if api_key in whitelist:
        return True
    return False
