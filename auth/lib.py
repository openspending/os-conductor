from urllib.parse import urljoin

import jwt
import requests


class Verifyer:

    def __init__(self, *, auth_endpoint=None, public_key=None):
        if public_key is None:
            if auth_endpoint is not None:
                public_key = requests.get(urljoin(auth_endpoint, 'public-key')).text
        assert public_key is not None
        self.public_key = public_key

    def extract_permissions(self, auth_token):
        if not auth_token:
            return False
        try:
            token = jwt.decode(auth_token.encode('ascii'),
                               self.public_key,
                               algorithm='RS256')
            return token
        except jwt.InvalidTokenError:
            return False


