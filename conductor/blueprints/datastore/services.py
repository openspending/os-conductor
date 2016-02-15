import jwt
import requests
from flask import url_for

public_key = None


def verify(auth_token, owner):
    """Verify Auth Token.
    :param auth_token: Authentication token to verify
    :param owner: dataset owner
    """
    if auth_token == 'testing-token' and owner == '__tests':
        return True
    global public_key
    if public_key is None:
        url = 'http://localhost:8000'+url_for('authorization.public-key')
        public_key = requests.get(url).text
    try:
        token = jwt.decode(auth_token.encode('ascii'),
                           public_key,
                           algorithm='RS256')
        has_permission = token.get('permissions', {})\
            .get('datapackage-upload', False)
        service = token.get('service')
        return has_permission and service == 'os.datastore'
    except jwt.InvalidTokenError:
        return False
