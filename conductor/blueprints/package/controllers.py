import logging
import os
import json
from six import StringIO

import jwt
import requests
from slugify import slugify
from dpp_runner.lib import DppRunner

from datapackage import Package

from conductor.blueprints.user.controllers import PUBLIC_KEY
from .models import package_registry

os_api_url = os.environ.get('OS_API_URL')
runner = DppRunner()


os.environ['DPP_DB_ENGINE'] = os.environ['OS_CONDUCTOR_ENGINE']
os.environ['ELASTICSEARCH_ADDRESS'] = os.environ['OS_ELASTICSEARCH_ADDRESS']
os.environ['AWS_ACCESS_KEY_ID'] = os.environ['OS_ACCESS_KEY_ID']
os.environ['AWS_SECRET_ACCESS_KEY'] = os.environ['OS_SECRET_ACCESS_KEY']
os.environ['S3_BUCKET_NAME'] = os.environ['OS_STORAGE_BUCKET_NAME']


def copy_except(obj, fields):
    return dict(
        (k, v)
        for k, v in obj.items()
        if k not in fields
    )


def prepare_field(field, slugs):
    slug_base = slugify(field['name'], separator='_', to_lower=True)
    slug = slug_base
    if slug in slugs:
        suffix = 0
        while slug in slugs:
            suffix += 1
            slug = '{}_{}'.format(slug_base, suffix)
    if slug != field['name']:
        aliases = [field['name']]
    else:
        aliases = []
    ret = {
        'header': slug,
        'aliases': aliases,
        'osType': field['osType'],
    }
    if 'title' in field:
        ret['title'] = field['title']
    ret['options'] = copy_except(field,
                                 ('name', 'title', 'osType', 'type', 'slug', 'conceptType', 'format'))
    return ret


def upload(datapackage, token, cache_get, cache_set):
    """Initiate a package load to the database
    :param datapackage: URL for datapackage to load
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
        key = 'os-conductor:package:'+datapackage
        ret = {
            "progress": 0,
            "status": "queued"
        }
        cache_set(key, ret, 3600)
        package = Package(datapackage)
        desc = package.descriptor

        slugs = set()
        fiscal_spec = {
            'dataset-name:': desc['name'],
            'resource-name': package.resources[0].name,
            'title': desc.get('title', desc['name']),
            'datapackage-url': datapackage,
            'owner-id': token['userid'],
            'sources': [
                {
                    'url': package.resources[0].source
                }
            ],
            'fields': [
                prepare_field(f, slugs)
                for f in package.resources[0].descriptor['schema']['fields']
                if 'osType' in f
            ]
        }
        status_cb = StatusCallback(datapackage, cache_get, cache_set)
        runner.start('fiscal', json.dumps(fiscal_spec).encode('utf8'),
                     verbosity=2, status_cb=status_cb)
    return ret


def upload_status(datapackage, cache_get):
    key = 'os-conductor:package:'+datapackage
    ret = cache_get(key)
    return ret


class StatusCallback:

    def __init__(self, datapackage_url, cache_get, cache_set):
        self.datapackage_url = datapackage_url
        self.cache_get = cache_get
        self.cache_set = cache_set
        self.statuses = {}
        self.error = None

    def status(self):
        statuses = self.statuses.values()
        if 'FAILED' in statuses:
            return 'fail'
        if 'INPROGRESS' in statuses:
            return 'loading-data'
        if all(self.statuses.get(pi) == 'SUCCESS' 
               for pi in ('./finalize_datapackage_flow', './dumper_flow_update_status')):
            return 'done'
        return 'loading-data'


    def __call__(self, pipeline_id, status, errors=None, stats=None):
        logging.error('upload_status_update: %s pipeline:%s, ' +
                      'status:%s, err:%s, stats:%s',
                      self.datapackage_url, pipeline_id, status, errors, stats)
        key = 'os-conductor:package:'+self.datapackage_url
        ret = self.cache_get(key)
        if ret is None:
            ret = {
                'status': status,
                'progress': 0
            }
        if status == 'FAILED' and errors is not None and self.error is None:
            self.error = '\n'.join(errors)
            ret['error'] = self.error
        self.statuses[pipeline_id] = status
        ret['status'] = self.status()
        if ret['status'] == 'done':
            if stats is not None:
                progress = stats.get('count_of_rows')
                if progress:
                    ret['progress'] = int(progress)
        self.cache_set(key, ret, 3600)


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


def delete_package(name, token):
    try:
        token = jwt.decode(token.encode('ascii'),
                           PUBLIC_KEY,
                           algorithm='RS256')
        userid = token['userid']
        if name.split(':')[0] != userid:
            logging.error('USERID=%r, name=%r', userid, name)
            return None

    except jwt.InvalidTokenError:
        return None

    success = package_registry.delete_model(name)
    return {'success': success}


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


def stats():
    return package_registry.get_stats()
