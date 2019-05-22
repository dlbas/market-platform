from rest_framework import generics, permissions, response, viewsets

from client_user import models as client_models
from client_user import serializers as client_serializers

from . import models, serializers


class AdminUserView(generics.RetrieveAPIView):
    permission_classes = (permissions.IsAdminUser, )
    queryset = models.AdminUser.objects.all()
    serializer_class = serializers.AdminUserSerializer

    def get(self, request, *args, **kwargs):
        user = self.get_queryset().get(id=request.user.id)
        s = self.get_serializer(user)
        return response.Response(s.data)


class InstrumentViewSet(viewsets.ModelViewSet):
    queryset = client_models.Instrument.objects.all()
    serializer_class = client_serializers.InstrumentSerializer
    permission_classes = (permissions.IsAdminUser, )


class OrdersViewSet(viewsets.ModelViewSet):
    queryset = client_models.Order.objects.all()
    serializer_class = client_serializers.OrderSerializer
    permission_classes = (permissions.IsAdminUser, )
