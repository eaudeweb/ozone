import concurrent.futures
import logging
import requests
from requests.auth import HTTPBasicAuth

from django.conf import settings


pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)


logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


def make_cache_invalidation_request(params):
    url = settings.CACHE_INVALIDATION_URL
    if url is None:
        return
    try:
        timeout = float(settings.CACHE_INVALIDATION_TIMEOUT)
    except ValueError:
        logger.error(
            'Error while invalidating cache. '
            'CACHE_INVALIDATION_TIMEOUT needs to be a numeric value.'
        )
        timeout = 0

    # requests.get() will timeout after `timeout` even if it receives data
    auth = HTTPBasicAuth(
        settings.CACHE_INVALIDATION_USER, settings.CACHE_INVALIDATION_PASS
    )
    url = f'{url}?{params}'
    pool.submit(requests.get, url, timeout=timeout, auth=auth)


def invalidate_party_cache(party_id):
    """
    For now, due to limitations on the Drupal side, invalidation works by
    invalidating all data for a specific party.
    """
    logger.info(f'Invalidating cache for party {party_id}')
    make_cache_invalidation_request(f'party={party_id}')
    logger.info(f'Queued cache invalidation request for party {party_id}')


def invalidate_global_cache(data_type):
    """
    Invalidates data specified by `data_type` param for all parties
    """
    logger.info(f'Invalidating cache for {data_type} for all parties.')
    make_cache_invalidation_request(f'{data_type}')
    logger.info(
        f'Queued cache invalidation request for {data_type} for all parties'
    )


def invalidate_aggregation_cache(instance):
    """
    Used to invalidate entries in the aggregation cache based on the ProdCons
    instance that was added/modified/deleted.
    """
    invalidate_party_cache(instance.party.id)


def invalidate_aggregations_cache(aggregation_dict_list):
    """
    Used to invalidate entries in the aggregation cache based on a list of
    group/party/period dicts corresponding to a number of ProdCons instances
    that were modified.
    """
    party_id_set = set([item['party'] for item in aggregation_dict_list])
    for party_id in party_id_set:
        invalidate_party_cache(party_id)


def invalidate_teap_reports_cache():
    return invalidate_global_cache('teap_reports')


def invalidate_teap_report_types_cache():
    return invalidate_global_cache('teap_report_types')


def invalidate_teap_indicative_reports_cache():
    return invalidate_global_cache('teap_indicative_reports')


def invalidate_status_of_ratification_cache():
    return invalidate_global_cache('status_of_ratification')


def invalidate_impcom_recommendations_cache():
    return invalidate_global_cache('impcom_recommendations')


def invalidate_impcom_bodies_cache():
    return invalidate_global_cache('impcom_bodies')


def invalidate_impcom_topics_cache():
    return invalidate_global_cache('impcom_topics')


def invalidate_licensing_system_cache():
    return invalidate_global_cache('licensing_system')


def invalidate_focal_points_cache():
    return invalidate_global_cache('focal_points')


def invalidate_substances_cache():
    return invalidate_global_cache('group_substances')


def invalidate_blends_cache():
    return invalidate_global_cache('blends')
