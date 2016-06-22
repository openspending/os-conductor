import os
import requests

from flask import request, abort, url_for
from flask.ext.jsonpify import jsonpify
from werkzeug.contrib.cache import MemcachedCache, SimpleCache

if 'OS_CONDUCTOR_CACHE' in os.environ:
    cache = MemcachedCache([os.environ['OS_CONDUCTOR_CACHE']])
else:
    cache = SimpleCache()

os_api = os.environ.get('OS_API')
os_conductor = os.environ.get('OS_CONDUCTOR')


def upload():
    """Initiate a package load to the database
    """
    datapackage = request.values.get('datapackage')
    if datapackage is None:
        abort(400)
    params = {
        'package': datapackage,
        'callback': 'http://'+os_conductor+url_for('apiload.callback')
    }
    load_url = 'http://'+os_api+'/api/3/loader/'
    response = requests.get(load_url, params=params)
    if response.status_code == 200:
        key = 'os-conductor:apiload:'+datapackage
        ret = {
            "progress": 0,
            "status": "queued"
        }
        cache.set(key, ret, 3600)
    else:
        ret = {
            "status": "fail",
            "error": 'HTTP %s' % response.status_code
        }
    return jsonpify(ret)


def upload_status():
    """Return the current status of a package load.
    """
    datapackage = request.values.get('datapackage')
    if datapackage is None:
        abort(400)
    key = 'os-conductor:apiload:'+datapackage
    ret = cache.get(key)
    if ret is None:
        abort(404)
    return jsonpify(ret)


def upload_status_update():
    """Get notified for changes in the package upload status.
    """
    datapackage = request.values.get('package')
    status = request.values.get('status')
    error = request.values.get('error')
    progress = request.values.get('progress', 0)
    if datapackage is not None and status is not None:
        key = 'os-conductor:apiload:'+datapackage
        ret = cache.get(key)
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
        cache.set(key, ret, 3600)
    return ""
