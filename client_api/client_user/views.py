from rest_framework import generics, permissions, status, views, viewsets
from rest_framework.response import Response
from rest_framework_jwt.views import ObtainJSONWebToken
from rest_framework_jwt.serializers import JSONWebTokenSerializer
from rest_framework.mixins import ListModelMixin, UpdateModelMixin
import django_filters

from client_user import serializers, models
from .filters import InstrumentBalanceFilter, FiatBalanceFilter

import logging

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


class EmailVerificationAPIView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.EmailVerificationSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.activate_user()
        return Response(status=status.HTTP_200_OK)

    def get(self, request):
        code = request.query_params.get('code')
        if code:
            models.ClientUser.activate(code)
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_403_FORBIDDEN)


# class ChangePasswordAPIView(generics.GenericAPIView):
#     serializer_class = serializers.ChangePasswordSerializer
#     authentication_classes = [JWTWithTotpAuthentication]

#     @staticmethod
#     def generate_new_token(user):
#         jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
#         jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
#         payload = jwt_payload_handler(user)
#         return jwt_encode_handler(payload)

#     def post(self, request, *args, **kwargs):
#         user = request.user
#         serializer = self.get_serializer(data=request.data)
#         if serializer.is_valid():
#             old_password = serializer.data.get('old_password')
#             if not user.check_password(old_password):
#                 raise exceptions.ChangePasswordWrongPassword
#             new_password = serializer.data.get('new_password')
#             user.set_password(new_password)
#             user.password_changed_at_dt = timezone.now()
#             user.save(update_fields=['password_changed_at_dt', 'password'])
#             new_token = self.generate_new_token(user)
#             return Response({
#                 'status': 'ok',
#                 'new_token': new_token,
#             }, status=status.HTTP_200_OK)
#         raise exceptions.InvalidRequest


# class RestorePasswordAPIView(generics.GenericAPIView):
#     permission_classes = [permissions.AllowAny]
#     serializer_class = serializers.RestorePasswordSerializer

#     def post(self, request):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         user = serializer.restore_password(request)
#         return Response({'email': user.email}, status=status.HTTP_200_OK)


# class RequestRestorePasswordAPIView(generics.GenericAPIView):
#     permission_classes = [permissions.AllowAny]
#     serializer_class = serializers.RequestRestorePasswordSerializer

#     def post(self, request):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save(request)
#         return Response(status=status.HTTP_200_OK)


# class CheckRestorePasswordAPIView(generics.GenericAPIView):
#     permission_classes = [permissions.AllowAny]
#     serializer_class = serializers.CheckRestorePasswordSerializer

#     def post(self, request):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.check(request)
#         return Response(status=status.HTTP_200_OK)


# class InviteUserAPIView(generics.GenericAPIView):
#     permission_classes = [permissions.IsAuthenticated]
#     serializer_class = serializers.InviteUserSerializer

#     def post(self, request):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save(request)
#         return Response(status=status.HTTP_200_OK)


class UserInfoAPIView(generics.RetrieveAPIView):
    pagination_class = None
    serializer_class = serializers.ClientUserSerializer

    def get_object(self):
        return self.request.user


class InstrumentsViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.InstrumentSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = models.Instrument.objects.all()
    lookup_field = 'id'


class OrdersViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.OrderSerializer
    permission_classes = (permissions.IsAuthenticated,)
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
    permission_classes = (permissions.IsAuthenticated,)
    lookup_field = 'id'

    def get_object(self):
        return models.FiatBalance.objects.get(user=self.request.user)

    def get(self, request, *args, **kwargs):
        return Response(self.get_serializer(self.get_object()).data)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class InstrumentBalanceApiView(UpdateModelMixin, generics.GenericAPIView):
    serializer_class = serializers.InstrumentBalanceSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filter_class = InstrumentBalanceFilter
    lookup_field = 'id'

    def get_queryset(self):
        return models.InstrumentBalance.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        return Response(self.get_serializer(self.filter_queryset(self.get_queryset()), many=True).data)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class StatisticsAPIView(views.APIView):
    permission_classes = (permissions.AllowAny, )

    def post(self, request, *args, **kwargs):
        """
        Tell API to write statistics about current emulation round
        :return:
        """
        instrument_id = self.request.data.get('instrument_id')
        emulation_uuid = self.request.data.get('uuid')
        if not emulation_uuid:
            return Response({'result': 'emulation_uuid was not provided'}, status=400)
        if not instrument_id:
            instrument = models.Instrument.objects.order_by('created_at_dt').last()
        else:
            instrument = models.Instrument.objects.get(id=instrument_id)

        avg_price = models.Order.get_avg_price(instrument)
        liquidity_rate = models.Order.get_liquidity_rate(instrument)
        placed_assets_rate = models.Order.get_placed_assets_rate(instrument)

        models.OrderPriceHistory.objects.create(price=avg_price, instrument=instrument)
        models.LiquidityHistory.objects.create(value=liquidity_rate, instrument=instrument)
        models.PlacedAssetsHistory.objects.create(value=placed_assets_rate, instrument=instrument)

        return Response({'result': 'ok'}, status=200)

    def get(self, request, *args, **kwargs):
        """
        Retrieve stats about current emulation round
        """
        uuid = self.request.query_params.get('uuid')
        if not uuid:
            return Response({'result': 'uuid was not provided'}, status=400)
        price_stats = serializers.OrderPriceHistorySerializer(models.OrderPriceHistory.objects.filter(uuid=uuid),
                                                              many=True)
        liquidity_stats = serializers.LiquidityRateSerializer(models.LiquidityHistory.objects.filter(uuid=uuid),
                                                              many=True)
        placement_stats = serializers.PlacementRateSerializer(models.PlacedAssetsHistory.objects.filter(uuid=uuid),
                                                              many=True)
        return Response({
            'result': {
                'price_stats': price_stats.data,
                'liquidity_stats': liquidity_stats.data,
                'placement_stats': placement_stats.data,
            }
        }, status=200)
