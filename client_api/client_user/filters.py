import django_filters

from client_user import models


class InstrumentBalanceFilter(django_filters.FilterSet):
    id = django_filters.NumberFilter()
    instrument_id = django_filters.NumberFilter()

    class Meta:
        model = models.InstrumentBalance
        fields = ['id', 'instrument_id']


class FiatBalanceFilter(django_filters.FilterSet):
    id = django_filters.NumberFilter()
    currency_id = django_filters.NumberFilter()

    class Meta:
        model = models.InstrumentBalance
        fields = ['id', 'currency_id']
