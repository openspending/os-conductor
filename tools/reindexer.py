import os
import logging
import urllib3

from elasticsearch import Elasticsearch, NotFoundError
from os_package_registry import PackageRegistry
from sqlalchemy import MetaData, create_engine

urllib3.disable_warnings()
logging.root.setLevel(logging.INFO)


def reindex(src_pr, dst_pr):
    for package in src_pr.list_models():
        try:
            params = src_pr.get_raw(package)
            dst_pr.save_model(*params)
            logging.info('REINDEXING %s', package)
        except KeyError:
            logging.exception('FAILED TO READ DATA FOR %s', package)


if __name__ == "__main__":

    # Reindex ES
    es_host = os.environ['OS_ELASTICSEARCH_ADDRESS']
    es = Elasticsearch(hosts=[es_host], use_ssl='https' in es_host)

    source_index = None
    target_index = None
    backup_index = 'packages-backup'
    existing_alias = None
    for i in range(2):
        idx = 'packages-%d' % i
        if es.indices.exists(idx):
            logging.info('INDEX %s EXISTS', idx)
            if source_index is None:
                source_index = idx
                existing_alias = idx
        else:
            if target_index is None:
                target_index = idx

    if source_index is None:
        source_index = 'packages'
    if target_index is None:
        target_index = 'packages-1'

    assert source_index != target_index

    logging.info('SOURCE INDEX %s', source_index)
    logging.info('TARGET INDEX %s', target_index)
    logging.info('BACKUP INDEX %s', backup_index)

    try:
        logging.info('DELETING TARGET INDEX')
        es.indices.delete(target_index)
    except NotFoundError:
        logging.info('TARGET INDEX NOT FOUND')

    source_pr = PackageRegistry(es_instance=es, index_name=source_index)
    backup_pr = PackageRegistry(es_instance=es, index_name=backup_index)

    reindex(source_pr, backup_pr)

    if es.indices.exists_alias(source_index, 'packages'):
        es.indices.delete_alias(source_index, 'packages')

    target_pr = PackageRegistry(es_instance=es, index_name=target_index)
    reindex(source_pr, target_pr)

    es.indices.delete(source_index)
    es.indices.put_alias(target_index, 'packages')

    # Find orphan DB tables
    used_tables = set()
    for pkg_id in target_pr.list_models():
        rec = target_pr.get_raw(pkg_id)
        fact_table = rec[3].get('fact_table')  # model
        if fact_table is not None:
            used_tables.add(fact_table)

    engine = create_engine(os.environ['OS_CONDUCTOR_ENGINE'])
    meta = MetaData()
    meta.reflect(bind=engine,
                 only=lambda t, _: t.startswith('fdp'))
    for table in reversed(meta.sorted_tables):
        if table in used_tables:
            logging.info('SKIPPING %s', table)
        else:
            logging.info('NOT DELETING %s', table)
