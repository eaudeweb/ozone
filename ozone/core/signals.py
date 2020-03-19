import django.dispatch
import logging

from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete

from .utils.cache import (
    invalidate_aggregation_cache,
    invalidate_party_cache,
    invalidate_teap_reports_cache,
    invalidate_teap_report_types_cache,
    invalidate_teap_indicative_reports_cache,
    invalidate_status_of_ratification_cache,
    invalidate_impcom_recommendations_cache,
    invalidate_impcom_bodies_cache,
    invalidate_impcom_topics_cache,
    invalidate_licensing_system_cache,
    invalidate_focal_points_cache,
)

from ozone.core.models import (
    PartyDeclaration,
    PartyHistory,
    PartyRatification,

    FocalPoint,
    IllegalTrade,
    LicensingSystem,
    MultilateralFund,
    ORMReport,
    OtherCountryProfileData,
    ReclamationFacility,
    Website,

    TEAPReport,
    TEAPReportType,
    TEAPIndicativeNumberOfReports,

    ImpComBody,
    ImpComTopic,
    ImpComRecommendation,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

# Signals to be received
clear_aggregation_cache_signal = django.dispatch.Signal()
clear_country_profile_cache_signal = django.dispatch.Signal()

clear_teap_reports_cache_signal = django.dispatch.Signal()
clear_teap_report_types_cache_signal = django.dispatch.Signal()
clear_teap_indicative_reports_cache_signal = django.dispatch.Signal()
clear_status_of_ratification_cache_signal = django.dispatch.Signal()

clear_impcom_recommendations_cache_signal = django.dispatch.Signal()
clear_impcom_bodies_cache_signal = django.dispatch.Signal()
clear_impcom_topics_cache_signal = django.dispatch.Signal()


@receiver(clear_aggregation_cache_signal)
def clear_aggregation_cache(sender, instance, **kwargs):
    """
    Handler for the custom clear_aggregation_cache signal.
    A custom signal was needed to allow it to be sent only in certain specific
    scenarios.
    """
    invalidate_aggregation_cache(instance)


def clear_country_profile_cache(sender, instance, **kwargs):
    """
    Clear the cache of the main website
    """
    try:
        invalidate_party_cache(instance.party_id)
    except Exception:
        logger.exception('Error while invalidating country profile cache.')


def clear_teap_reports_cache(sender, instance, **kwargs):
    return invalidate_teap_reports_cache()


def clear_teap_report_types_cache(sender, instance, **kwargs):
    return invalidate_teap_report_types_cache()


def clear_teap_indicative_reports_cache(sender, instance, **kwargs):
    return invalidate_teap_indicative_reports_cache()


def clear_status_of_ratification_cache(sender, instance, **kwargs):
    return invalidate_status_of_ratification_cache()


def clear_impcom_recommendations_cache(sender, instance, **kwargs):
    return invalidate_impcom_recommendations_cache()


def clear_impcom_bodies_cache(sender, instance, **kwargs):
    return invalidate_impcom_bodies_cache()


def clear_impcom_topics_cache(sender, instance, **kwargs):
    return invalidate_impcom_topics_cache()


def clear_licensing_system_cache(sender, instance, **kwargs):
    return invalidate_licensing_system_cache()


def clear_focal_points_cache(sender, instance, **kwargs):
    return invalidate_focal_points_cache()


models_handlers_mapping = [
    # Country profile models/signal handlers
    (FocalPoint, (clear_country_profile_cache, clear_focal_points_cache, )),
    (IllegalTrade, (clear_country_profile_cache, )),
    (
        LicensingSystem,
        (clear_country_profile_cache, clear_licensing_system_cache, )
    ),
    (MultilateralFund, (clear_country_profile_cache, )),
    (ORMReport, (clear_country_profile_cache, )),
    (OtherCountryProfileData, (clear_country_profile_cache, )),
    (PartyDeclaration, (clear_country_profile_cache, )),
    (PartyHistory, (clear_country_profile_cache, )),
    (PartyRatification, (clear_country_profile_cache, )),
    (ReclamationFacility, (clear_country_profile_cache, )),
    (Website, (clear_country_profile_cache, )),
    # TEAP models/signal handlers
    (TEAPReport, (clear_teap_reports_cache, )),
    (TEAPReportType, (clear_teap_report_types_cache, )),
    (TEAPIndicativeNumberOfReports, (clear_teap_indicative_reports_cache, )),
    (
        PartyRatification,
        (clear_status_of_ratification_cache, clear_licensing_system_cache, )
    ),
    # ImpCom models/signal handlers
    (ImpComRecommendation, (clear_impcom_recommendations_cache, )),
    (
        ImpComBody,
        (clear_impcom_bodies_cache, clear_impcom_recommendations_cache, )
    ),
    (
        ImpComTopic,
        (clear_impcom_topics_cache, clear_impcom_recommendations_cache, )
    ),
]
for model, signal_handlers in models_handlers_mapping:
    for handler in signal_handlers:
        post_save.connect(handler, model)
        post_delete.connect(handler, model)
