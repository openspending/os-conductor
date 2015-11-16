import json
import boto
from urllib.parse import urlparse, parse_qs
from flask import request, Response
from ... import config
from . import services


class Authorize:
    """Autorize a client for the file uploading.
    """

    # Public

    def __init__(self, bucket=None):

        # S3 bucket
        if not bucket:
            connection = boto.connect_s3(
                    config.OPENSPENDING_ACCESS_KEY_ID,
                    config.OPENSPENDING_SECRET_ACCESS_KEY,
                    host='s3.amazonaws.com')
            bucket = connection.get_bucket(
                    config.OPENSPENDING_STORAGE_BUCKET_NAME)
        self.bucket = bucket

    def __call__(self):

        # Verify client, deny access if not verified
        is_verified = False
        api_key = request.headers.get('API-Key')
        if api_key:
            is_verified = services.verify(api_key)
        if not is_verified:
            return Response(status=401)

        try:

            # Get response data
            req_data = json.loads(request.data.decode())

            # Make request data
            res_data = {'filedata': {}}
            for path, file in req_data['filedata'].items():
                s3path = '{0}/{1}/{2}'.format(
                        req_data['metadata']['owner'],
                        req_data['metadata']['name'],
                        file['name'])
                s3headers = {
                    'Content-Length': file['length'],
                    'Content-MD5': file['md5'],
                }
                s3key = self.bucket.new_key(s3path)
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
                res_data['filedata'][path] = filedata

            # Return response data
            return json.dumps(res_data)

        except Exception as exception:

            # TODO: use logger
            # Log bad request exception
            print('Bad request: {0}'.format(exception))

            # Return request is bad
            return Response(status=400)
