import unittest
try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch
from importlib import import_module
module = import_module('conductor.blueprints.datastore.services')

# authentication_token = \
#     'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyaWQiOiIxMjM0NTYifQ.C122A' \
#     '4FmDqVHYhZytHfahRfK3X2-Iu4qMuH7gDhy_Ck'
authorization_token = \
    'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzZXJ2aWNlIjoib3MuZGF0YXN0b3Jl' \
    'IiwicGVybWlzc2lvbnMiOnsiZGF0YXBhY2thZ2UtdXBsb2FkIjp0cnVlfX0.NZLaa54k6' \
    '4R6lBM9dhZGAo9OftEsdfS5wIu0CaeRnRE2SObJ876yKvBe3YGOBIiAwHfiocoSu7QjVj' \
    'hRBxfZvWDbjmQl5addQXtDZBaCyoDid4sOz9Gu78jWAJBRsx7QWncE8fjUlPVcdf_vKyi' \
    'QCkuZahxGKuoLmQio0DkWBpxnXJz6cKkhBcgqFwhCW6lk3ttMSI8AGh4siiikeeKeSgTS' \
    'juiYbMfyJscWmLfKVrjUYwqWGbsBLhOIQfNGIQLTvfXZJkU1ka1MiwkU7o31ofkZH8Suq' \
    'izIOZS_N5kgudqIyRJtcOUvQbE-dcmcQS754h6n7i2N22cjK9unH1Yk7g'
public_key = """
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAzSrV/SxRNKufc6f0GQIu
YMASgBCOiJW5fvCnGtVMIrWvBQoCFAp9QwRHrbQrQJiPg6YqqnTvGhWssL5LMMvR
8jXXOpFUKzYaSgYaQt1LNMCwtqMB0FGSDjBrbmEmnDSo6g0Naxhi+SJX3BMcce1W
TgKRybv3N3F+gJ9d8wPkyx9xhd3H4200lHk4T5XK5+LyAPSnP7FNUYTdJRRxKFWg
ZFuII+Ex6mtUKU9LZsg9xeAC6033dmSYe5yWfdrFehmQvPBUVH4HLtL1fXTNyXuz
ZwtO1v61Qc1u/j7gMsrHXW+4csjS3lDwiiPIg6q1hTA7QJdB1M+rja2MG+owL0U9
owIDAQAB
-----END PUBLIC KEY-----
"""


class VerifyTest(unittest.TestCase):

    # Actions

    def setUp(self):
        self.addCleanup(patch.stopall)
        module.public_key = public_key

    # Tests

    def test_verified(self):
        self.assertTrue(module.verify(authorization_token, 'bla'))
        self.assertTrue(module.verify('testing-token', '__tests'))

    def test_not_verified(self):
        self.assertFalse(module.verify('key3', 'bla'))
        self.assertFalse(module.verify('testing-token', 'bla'))
        self.assertFalse(module.verify('bla', '__tests'))
