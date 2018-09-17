import os
import click

from elasticsearch import Elasticsearch
from os_package_registry import PackageRegistry


@click.command()
@click.argument('id', type=str, nargs=-1)
@click.option('--index', type=str, default='packages',
              help='Name of index, defaults to "packages"')
@click.option('--es-host', type=str,
              default=os.environ.get('OS_ELASTICSEARCH_ADDRESS'),
              help='ElasticSearch address. '
                   'Default to OS_ELASTICSEARCH_ADDRESS in env.')
def remove_package(id, index, es_host):
    """Remove package(s) with id."""
    if es_host is None:
        raise click.UsageError('No es-host provided. See help for details.')

    es = Elasticsearch(hosts=[es_host], use_ssl='https' in es_host)
    pr = PackageRegistry(es_instance=es, index_name=index)
    for i in id:
        ret = pr.delete_model(i)
        if ret is False:
            click.echo('Package "{}" not found in index.'.format(i))


if __name__ == '__main__':
    remove_package()
