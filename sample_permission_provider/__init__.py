def get_permissions(service, userid):
    return {
        'provider-token': '{}-{}'.format(service, userid)
    }