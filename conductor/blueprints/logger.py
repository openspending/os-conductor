import sys
import logging

logger = logging.getLogger('os-conductor')
handlr = logging.StreamHandler(sys.stderr)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handlr.setFormatter(formatter)
logger.addHandler(handlr)
logger.setLevel(logging.INFO)

es_logger = logging.getLogger('elasticsearch')
es_logger.setLevel(logging.INFO)


