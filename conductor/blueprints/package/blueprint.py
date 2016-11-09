import logging
import os
import json

from flask import Blueprint, Response, request, abort, url_for
from flask.ext.jsonpify import jsonpify
from werkzeug.contrib.cache import MemcachedCache, SimpleCache

from . import controllers

if 'OS_CONDUCTOR_CACHE' in os.environ:
    cache = MemcachedCache([os.environ['OS_CONDUCTOR_CACHE']])
else:
    cache = SimpleCache()

os_conductor = os.environ.get('OS_CONDUCTOR')


logging.info('CACHE=%r', cache)


def cache_get(key):
    return cache.get(key)


def cache_set(key, value, timeout):
    logging.info('CACHE[%s] <- %r', key, value)
    return cache.set(key, value, timeout)


# Controller Proxies
def upload():
    jwt = request.values.get('jwt')
    datapackage = request.values.get('datapackage')
    if datapackage is None:
        abort(400)
    if jwt is None:
        abort(403)
    callback = 'http://'+os_conductor+url_for('.callback')
    ret = controllers.upload(datapackage, callback, jwt, cache_set)
    return jsonpify(ret)


def upload_status():
    datapackage = request.values.get('datapackage')
    if datapackage is None:
        abort(400)
    ret = controllers.upload_status(datapackage, cache_get)
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

    controllers.upload_status_update(datapackage, status, error,
                                     progress, cache_get, cache_set)
    return jsonpify(True)


def toggle_publish():
    id = request.values.get('id')
    jwt = request.values.get('jwt')
    if jwt is None:
        abort(403)
    value = request.values.get('publish', '')
    value = value.lower()
    toggle = None
    publish = None
    if value == 'toggle':
        toggle = True
    else:
        if value in ['true', 'false']:
            publish = json.loads(value)
    if publish is None and toggle is None:
        return Response(status=400)
    return jsonpify(controllers.toggle_publish(id, jwt, toggle, publish))


def run_hooks():
    id = request.values.get('id')
    jwt = request.values.get('jwt')
    if jwt is None:
        abort(403)
    if id is None:
        abort(400)
    return jsonpify(controllers.run_hooks(id, jwt))


def create():
    """Create blueprint.
    """

    # Create instance
    blueprint = Blueprint('package', 'package')

    # Register routes
    blueprint.add_url_rule(
        'upload', 'load', upload, methods=['POST'])
    blueprint.add_url_rule(
        'status', 'poll', upload_status, methods=['GET'])
    blueprint.add_url_rule(
        'callback', 'callback',
        upload_status_update, methods=['GET', 'POST'])
    blueprint.add_url_rule(
        'publish', 'publish', toggle_publish, methods=['POST'])
    blueprint.add_url_rule(
        'run-hooks', 'run-hooks', run_hooks, methods=['POST'])

    # Return blueprint
    return blueprint
