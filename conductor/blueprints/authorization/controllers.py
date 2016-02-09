from __future__ import print_function
import os
import requests

try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse  # silence pyflakes
import jwt

from flask import request, url_for, send_from_directory
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
                    'permissions': permissions
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


class Sample:

    def __call__(self, path):
        return send_from_directory(
                        os.path.join(os.path.dirname(__file__), 'sample'),
                        path)


class SampleService:

    def __call__(self):
        url = 'http://localhost:8000'+url_for('.public-key')
        public_key = requests.get(url).text
        token = request.values.get('jwt')
        token = jwt.decode(token.encode('ascii'),
                           public_key,
                           algorithm='RS256')
        return jsonpify(token['permissions'])
