# Quiet down third-party logging in test output.

import logging

es_logger = logging.getLogger('elasticsearch')
es_logger.setLevel(logging.WARNING)

urllib3_logger = logging.getLogger('urllib3')
urllib3_logger.setLevel(logging.WARNING)
