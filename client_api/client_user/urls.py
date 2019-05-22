from django.conf.urls import include, url
from django.urls import path
from rest_framework import routers
from rest_framework_jwt.views import ObtainJSONWebToken

from client_user import views

router = routers.DefaultRouter()
router.register(r'orders', views.OrdersViewSet, basename='orders')
router.register(r'instruments',
                views.InstrumentsViewSet,
                basename='instruments')

urlpatterns = [
    url(r'api-token-auth/', ObtainJSONWebToken.as_view(), name='login'),
    url(r'create-user/', views.ClientUserAPIView.as_view()),
    url(r'user-info/', views.UserInfoAPIView.as_view()),
    url(r'fiat-balance/(?P<id>\d*)', views.FiatBalanceApiView.as_view()),
    url(r'instrument-balance/(?P<id>\d*)',
        views.InstrumentBalanceApiView.as_view()),
    url(r'orders/delete-all/',
        views.OrdersViewSet.as_view(actions={'delete': 'destroy_all'})),
    url(r'stats/', views.StatisticsAPIView.as_view()),
    url(r'price/', views.PricesApiView.as_view()),
    url(r'^', include(router.urls)),
]

urlpatterns += router.urls
