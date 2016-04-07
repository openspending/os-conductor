import os

# from werkzeug.contrib.cache import MemcachedCache, SimpleCache

from .models import query

# TODO: Add caching to reults (not so simple since we want
#      to immediately show new datasets)
# if 'OS_CONDUCTOR_CACHE' in os.environ:
#     cache = MemcachedCache([os.environ['OS_CONDUCTOR_CACHE']])
# else:
#     cache = SimpleCache()


class Search(object):
    """Initiate an elasticsearch query
    """

    # Public
    def __call__(self, kind, args={}):
        hits = query(kind, **args)
        return hits
