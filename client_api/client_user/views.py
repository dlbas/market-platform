from rest_framework import generics, permissions, status, views, viewsets
from rest_framework.response import Response
from rest_framework_jwt.views import ObtainJSONWebToken
from rest_framework_jwt.serializers import JSONWebTokenSerializer
from rest_framework.decorators import action

from client_user import serializers, models

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


class InstrumentsApiView(generics.ListAPIView):
    serializer_class = serializers.InstrumentSerializer
    permission_classes = (permissions.AllowAny,)
    # TODO limit queryset to user
    queryset = models.Instrument.objects.all()
    lookup_field = 'id'


class OrdersViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.OrderSerializer
    permission_classes = (permissions.AllowAny,)
    lookup_field = 'id'

    def get_queryset(self):
        # TODO Add user authorization in queryset
        # return models.Order.objects.filter(user=self.request.user)
        return models.Order.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.data)
        # serializer.is_valid(raise_exception=True)
        if serializer.data.type == models.OrderType.BUY.value:
            balance = models.FiatBalance.objects.get(user=request.user, instrument=serializer.data.instrument)
            if balance < serializer.data.remaining_amount * serializer.data.price:
                return Response('Not enough fiat balance', status=400)
        elif serializer.data.type == models.OrderType.SELL.value:
            balance = models.InstrumentBalance.objects.get(user=request.user, instrument=serializer.data.instrument)
            if balance < serializer.data.remaining_amount:
                return Response('Not enough instrument balance', status=400)
        # models.Order.place_order(serializer.data)
        return super().create(request, *args, **kwargs)
