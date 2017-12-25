from importlib import import_module
from importlib.util import find_spec

import logging

from .credentials import allowed_services


def get_token(service, userid):
    if service not in allowed_services:
        return {}

    module_name = allowed_services[service]

    if not find_spec(module_name):
        return {}

    module = import_module(module_name)

    try:
        get_permissions = module.get_permissions
    except AttributeError:
        logging.warning("Can't find 'get_permissions' function in %s", module_name)
        return {}

    return get_permissions(service, userid)

