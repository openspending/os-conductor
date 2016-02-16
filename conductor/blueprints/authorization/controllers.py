import os

try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse  # silence pyflakes
import jwt

from flask import request, make_response
from flask.ext.jsonpify import jsonpify

from .models import get_permission


def readfile_or_default(filename, default):
    try:
        return open(filename).read().strip()
    except IOError:
        return default
os_conductor = os.environ.get('OS_EXTERNAL_ADDRESS')

PUBLIC_KEY = readfile_or_default('/secrets/public.pem', 'public key stub')
PRIVATE_KEY = readfile_or_default('/secrets/private.pem', 'private key stub')
LIBJS = readfile_or_default(os.path.join(os.path.dirname(__file__),
                                         'lib',
                                         'lib.js'),
                            'alert("error");')


class Check:
    """Return user authentication for a service
    """

    # Public

    def __call__(self):
        token = request.values.get('jwt')
        service = request.values.get('service')
        if token is not None and service is not None:
            try:
                token = jwt.decode(token, PRIVATE_KEY)
            except jwt.InvalidTokenError:
                token = None

            if token is not None:
                userid = token['userid']
                service_permissions = get_permission('*', service)
                user_permissions = get_permission(userid, service)
                permissions = {}
                if service_permissions is not None:
                    permissions.update(service_permissions)
                if user_permissions is not None:
                    permissions.update(user_permissions)
                ret = {
                    'permissions': permissions,
                    'service': service
                }
                token = jwt.encode(ret, PRIVATE_KEY, algorithm='RS256')\
                           .decode('ascii')
                ret['token'] = token
                return jsonpify(ret)

        ret = {
            'permissions': {}
        }
        return jsonpify(ret)


class PublicKey:

    def __call__(self):
        return PUBLIC_KEY


class Lib:

    def __call__(self):
        resp = make_response(LIBJS)
        resp.headers['Content-Type'] = 'text/javascript'
        return resp
