import logging
import os
import json

import jwt
import requests
from six import StringIO

from conductor.blueprints.user.controllers import PUBLIC_KEY
from .models import package_registry

os_api = os.environ.get('OS_API')


def upload(datapackage, callback, token, cache_set):
    """Initiate a package load to the database
    :param datapackage: URL for datapackage to load
    :param callback: URL for callback to send to loader
    :param token: authentication token for user performing the upload
    """
    try:
        token = jwt.decode(token.encode('ascii'),
                           PUBLIC_KEY,
                           algorithm='RS256')
    except jwt.InvalidTokenError:
        token = None

    key = None
    if token is None:
        ret = {
            "status": "fail",
            "error": 'unauthorized'
        }
    else:
        params = {
            'package': datapackage,
            'callback': callback
        }
        load_url = 'http://'+os_api+'/api/3/loader/'
        response = requests.get(load_url, params=params)
        if response.status_code == 200:
            key = 'os-conductor:package:'+datapackage
            ret = {
                "progress": 0,
                "status": "queued"
            }
        else:
            ret = {
                "status": "fail",
                "error": 'HTTP %s' % response.status_code
            }
    if key is not None:
        cache_set(key, ret, 3600)
    return ret


def upload_status(datapackage, cache_get):
    key = 'os-conductor:package:'+datapackage
    ret = cache_get(key)
    return ret


def upload_status_update(datapackage, status, error,
                         progress, cache_get, cache_set):
    logging.error('upload_status_update: %s sts:%s, err:%s, prog:%s',
                  datapackage, status, error, progress)
    if datapackage is not None and status is not None:
        key = 'os-conductor:package:'+datapackage
        ret = cache_get(key)
        if ret is None:
            ret = {
                'status': status,
                'progress': 0
            }
        if progress is not None:
            ret['progress'] = int(progress)
        if status == 'fail' and error is not None:
            ret['error'] = error
        ret['status'] = status
        cache_set(key, ret, 3600)


def toggle_publish(name, token, toggle=False, publish=False):
    try:
        jwt.decode(token.encode('ascii'),
                   PUBLIC_KEY,
                   algorithm='RS256')
    except jwt.InvalidTokenError:
        return None

    name, datapackage_url, datapackage, \
        model, dataset_name, author,\
        status, loaded = package_registry.get_raw(name)
    private = datapackage.get('private', False)
    if toggle:
        private = not private
    else:
        private = not publish
    datapackage['private'] = private
    package_registry.save_model(name, datapackage_url, datapackage,
                                model, dataset_name, author,
                                status, loaded)
    return {'success': True, 'published': not private}


obeu_url = 'http://eis-openbudgets.iais.fraunhofer.de/' \
           'linkedpipes/execute/fdp2rdf'
webhook_obeu_url = os.environ.get('WEBHOOK_OBEU_URL', obeu_url)


def run_hooks(name, token):
    try:
        jwt.decode(token.encode('ascii'),
                   PUBLIC_KEY,
                   algorithm='RS256')
    except jwt.InvalidTokenError:
        return None

    _, datapackage_url, _, _, _, _, _, _ = package_registry.get_raw(name)
    json_ld_payload = {
        "@context": {
            "@vocab": "http://schema.org/",
            "url": {"@type": "@id"}
        },
        "url": datapackage_url
    }
    filename = 'package-url.jsonld'
    files = [
        ('input',
         (filename, StringIO(json.dumps(json_ld_payload)), 'application/json')
         )
    ]
    response = requests.post(webhook_obeu_url, files=files)
    return {'success': True,
            'response': response.text,
            'payload': json_ld_payload}
