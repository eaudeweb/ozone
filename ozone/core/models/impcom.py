from django.db import models

from .legal import ReportingPeriod


__all__ = ['ImpComBody', 'ImpComTopic', 'ImpComRecommendation', ]


class ImpComBody(models.Model):
    """
    Used to model countries/bodies from IMPCOM recommendations.
    """

    sort_order = models.IntegerField(default=20)

    name = models.CharField(max_length=256, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'impcom_bodies'
        verbose_name = 'IMPCOM Body'
        verbose_name_plural = 'IMPCOM Bodies'
        ordering = ('sort_order', 'name', )


class ImpComTopic(models.Model):
    """
    Used to model topics from IMPCOM recommendations.
    """

    name = models.CharField(max_length=512, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'impcom_topics'
        verbose_name = 'IMPCOM Topic'
        verbose_name_plural = 'IMPCOM Topics'
        ordering = ('name', )


class ImpComRecommendationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'reporting_period'
        ).prefetch_related(
            'bodies', 'topics'
        )


class ImpComRecommendation(models.Model):
    objects = ImpComRecommendationManager()

    reporting_period = models.ForeignKey(
        ReportingPeriod,
        related_name='imp_com_recommendations',
        on_delete=models.PROTECT
    )

    recommendation_number = models.CharField(max_length=256)

    bodies = models.ManyToManyField(ImpComBody)

    topics = models.ManyToManyField(ImpComTopic)

    excerpt = models.CharField(max_length=32768)

    # Tab-separated data extracted from the `excerpt` field when that contains
    # a table.
    table_data = models.CharField(max_length=32768, blank=True, default='')

    # There can be several decisions (or none) resulting from recommendation
    resulting_decisions = models.CharField(max_length=128, blank=True)

    link_to_report = models.URLField(max_length=512)

    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = 'impcom_recommendations'
        verbose_name = 'IMPCOM Recommendation'
        verbose_name_plural = 'IMPCOM Recommendations'
        ordering = ('-reporting_period', 'sort_order')
