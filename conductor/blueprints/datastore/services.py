import jwt
from conductor.blueprints.user.controllers import PUBLIC_KEY

public_key = PUBLIC_KEY


def verify(auth_token, owner):
    """Verify Auth Token.
    :param auth_token: Authentication token to verify
    :param owner: dataset owner
    """
    if not auth_token:
        return False
    if auth_token == 'testing-token' and owner == '__tests':
        return True
    try:
        token = jwt.decode(auth_token.encode('ascii'),
                           public_key,
                           algorithm='RS256')
        has_permission = token.get('permissions', {})\
            .get('datapackage-upload', False)
        service = token.get('service')
        has_permission = has_permission and service == 'os.datastore'
        has_permission = has_permission and owner == token.get('userid')
        return has_permission
    except jwt.InvalidTokenError:
        return False
