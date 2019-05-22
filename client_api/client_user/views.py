import logging

import django_filters
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status, views, viewsets
from rest_framework.mixins import ListModelMixin, UpdateModelMixin
from rest_framework.response import Response
from rest_framework_jwt.serializers import JSONWebTokenSerializer
from rest_framework_jwt.views import ObtainJSONWebToken

from client_user import models, serializers

from .filters import FiatBalanceFilter, InstrumentBalanceFilter

logger = logging.getLogger('django.views')


class ObtainJWTWithTotop(ObtainJSONWebToken):
    serializer_class = JSONWebTokenSerializer


class ClientUserAPIView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.ClientUserSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(request)
        return Response(status=status.HTTP_201_CREATED)


class UserInfoAPIView(generics.RetrieveAPIView):
    pagination_class = None
    serializer_class = serializers.ClientUserSerializer

    def get_object(self):
        return self.request.user


class InstrumentsViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.InstrumentSerializer
    permission_classes = (permissions.IsAuthenticated, )
    queryset = models.Instrument.objects.all()
    lookup_field = 'id'


class OrdersViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.OrderSerializer
    permission_classes = (permissions.IsAuthenticated, )
    lookup_field = 'id'

    def get_queryset(self):
        return models.Order.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        if 'instrument' in request.data and 'instrument_id' not in request.data:
            request.data['instrument_id'] = request.data['instrument']
        return super().create(request, *args, **kwargs)

    def destroy_all(self, request, *args, **kwargs):
        orders = models.Order.objects.all()
        orders.delete()
        return Response({'result': 'ok'}, status=200)


class FiatBalanceApiView(UpdateModelMixin, generics.GenericAPIView):
    serializer_class = serializers.FiatBalanceSerializer
    permission_classes = (permissions.IsAuthenticated, )
    lookup_field = 'id'

    def get_object(self):
        return models.FiatBalance.objects.get(user=self.request.user)

    def get(self, request, *args, **kwargs):
        return Response(self.get_serializer(self.get_object()).data)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class InstrumentBalanceApiView(UpdateModelMixin, generics.GenericAPIView):
    serializer_class = serializers.InstrumentBalanceSerializer
    permission_classes = (permissions.IsAuthenticated, )
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, )
    filter_class = InstrumentBalanceFilter
    lookup_field = 'id'

    def get_queryset(self):
        return models.InstrumentBalance.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        return Response(
            self.get_serializer(self.filter_queryset(self.get_queryset()),
                                many=True).data)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class PricesApiView(views.APIView):
    permission_classes = (permissions.AllowAny, )

    def get(self, request, *args, **kwargs):
        instrument_id = self.request.query_params.get('instrument_id')
        if not instrument_id:
            return Response(
                {
                    'status': 'error',
                    'result': 'instrument id was not provided'
                },
                status=404)

        instrument = get_object_or_404(models.Instrument, id=instrument_id)
        avg_price = models.Order.get_avg_price(instrument=instrument)
        return Response({'result': avg_price}, status=200)


class StatisticsAPIView(views.APIView):
    permission_classes = (permissions.AllowAny, )

    def post(self, request, *args, **kwargs) -> Response:
        """
        Tell API to write statistics about current emulation round
        """
        instrument_id = self.request.data.get('instrument_id')
        emulation_uuid = self.request.data.get('emulation_uuid')
        if not emulation_uuid:
            return Response({'result': 'emulation_uuid was not provided'},
                            status=400)
        if not instrument_id:
            instrument = models.Instrument.objects.order_by(
                'created_at_dt').last()
        else:
            instrument = models.Instrument.objects.get(id=instrument_id)

        avg_price = models.Order.get_avg_price(instrument)
        if avg_price != 0:
            models.OrderPriceHistory.objects.create(price=avg_price,
                                                    instrument=instrument,
                                                    uuid=emulation_uuid)
        else:
            # In case current price is 0 because of empty orderbook
            last_price = models.OrderPriceHistory.objects.filter(
                uuid=emulation_uuid,
                instrument=instrument).latest('created_at_dt')
            last_price.pk = None
            last_price.save()

        liquidity_rate = models.Order.get_liquidity_rate(instrument)
        placed_assets_rate = models.Order.get_placed_assets_rate(instrument)

        models.LiquidityHistory.objects.create(value=liquidity_rate,
                                               instrument=instrument,
                                               uuid=emulation_uuid)
        models.PlacedAssetsHistory.objects.create(value=placed_assets_rate,
                                                  instrument=instrument,
                                                  uuid=emulation_uuid)

        return Response({'result': 'ok'}, status=200)

    def get(self, request, *args, **kwargs) -> Response:
        """
        Retrieve stats about current emulation round
        """
        uuid = self.request.query_params.get('uuid')
        if not uuid:
            return Response({'result': 'uuid was not provided'}, status=400)
        price_stats = serializers.OrderPriceHistorySerializer(
            models.OrderPriceHistory.objects.filter(uuid=uuid), many=True)
        liquidity_stats = serializers.LiquidityRateSerializer(
            models.LiquidityHistory.objects.filter(uuid=uuid), many=True)
        placement_stats = serializers.PlacementRateSerializer(
            models.PlacedAssetsHistory.objects.filter(uuid=uuid), many=True)
        return Response(
            {
                'result': {
                    'price_stats':
                    [v.get('price', 0) for v in price_stats.data],
                    'liquidity_stats':
                    [v.get('value', 0) for v in liquidity_stats.data],
                    'placement_stats':
                    [v.get('value', 0) for v in placement_stats.data],
                }
            },
            status=200)
