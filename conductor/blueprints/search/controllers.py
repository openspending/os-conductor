# from werkzeug.contrib.cache import MemcachedCache, SimpleCache
import elasticsearch

from .models import query

# TODO: Add caching to reults (not so simple since we want
#      to immediately show new datasets)
# if 'OS_CONDUCTOR_CACHE' in os.environ:
#     cache = MemcachedCache([os.environ['OS_CONDUCTOR_CACHE']])
# else:
#     cache = SimpleCache()

import logging
log = logging.getLogger(__name__)


def search(kind, userid, args={}):
    """Initiate an elasticsearch query
    """
    try:
        hits = query(kind, userid, **args)
        return hits
    except elasticsearch.exceptions.ElasticsearchException as e:
        log.error(e)
        return []
