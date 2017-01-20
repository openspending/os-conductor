import jwt
import sys
import datetime
from hashlib import md5
import zlib
import json
import pprint
import base64
import os

print(help(jwt.encode))

try:
    credentials = b''.join(x.split('"')[1].encode('ascii') for x in open('ppp.env'))
    credentials = base64.decodebytes(credentials)
    credentials = zlib.decompress(credentials).decode('ascii')
    credentials = json.loads(credentials)
except:
    credentials = {}
    raise

private_key = credentials['private.pem']
print(repr(private_key))

email = sys.argv[1]
idhash = md5(email.encode('utf8')).hexdigest()
weeks = int(sys.argv[2])
print('EMAIL=',email,'WEEKS:',weeks)
exp = datetime.datetime.utcnow() + datetime.timedelta(days=7*weeks)
rec = dict((('userid',idhash),('exp',exp)))
print(rec)
token = jwt.encode(rec, private_key)
print('TOKEN')
print(repr(token))

print(jwt.decode(token, private_key))
