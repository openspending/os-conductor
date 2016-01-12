import json
import boto
from boto.s3.connection import OrdinaryCallingFormat
from urllib.parse import urlparse, parse_qs
from flask import request, Response
from ... import config
from . import services


class Authorize:
    """Autorize a client for the file uploading.
    """

    # Public

    def __init__(self):
        self.__connection = boto.connect_s3(
                config.OPENSPENDING_ACCESS_KEY_ID,
                config.OPENSPENDING_SECRET_ACCESS_KEY,
                host='s3.amazonaws.com',
                calling_format=OrdinaryCallingFormat())
        self.__bucket = self.__connection.get_bucket(
                config.OPENSPENDING_STORAGE_BUCKET_NAME)

    def __call__(self):

        # Verify client, deny access if not verified
        is_verified = False
        api_key = request.headers.get('API-Key')
        if api_key:
            is_verified = services.verify(api_key)
        if not is_verified:
            return Response(status=401)

        try:

            # Get request payload
            req_payload = json.loads(request.data.decode())

            # Make response payload
            res_payload = {'filedata': {}}
            for path, file in req_payload['filedata'].items():
                s3path = '{0}/{1}/{2}'.format(
                        req_payload['metadata']['owner'],
                        req_payload['metadata']['name'],
                        path)
                s3headers = {
                    'Content-Length': file['length'],
                    'Content-MD5': file['md5'],
                }
                if 'type' in file:
                    s3headers['Content-Type'] = file['type']
                s3key = self.__bucket.new_key(s3path)
                s3url = s3key.generate_url(
                        config.ACCESS_KEY_EXPIRES_IN, 'PUT',
                        headers=s3headers, force_http=True)
                parsed = urlparse(s3url)
                upload_url = '{0}://{1}{2}'.format(
                        parsed.scheme, parsed.netloc, parsed.path)
                upload_query = parse_qs(parsed.query)
                filedata = {
                    'md5': file['md5'],
                    'name': file['name'],
                    'length': file['length'],
                    'upload_url': upload_url,
                    'upload_query': upload_query,
                }
                if 'type' in file:
                    filedata['type'] = file['type']                
                res_payload['filedata'][path] = filedata

            # Return response payload
            return json.dumps(res_payload)

        except Exception as exception:

            # TODO: use logger
            # Log bad request exception
            print('Bad request: {0}'.format(exception))

            # Return request is bad
            return Response(status=400)
