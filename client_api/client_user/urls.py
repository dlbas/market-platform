from django.conf.urls import include, url
from django.urls import path
from rest_framework import routers

from client_user import views
from rest_framework_jwt.views import ObtainJSONWebToken

router = routers.DefaultRouter()
router.register(r'orders', views.OrdersViewSet, basename='orders')

urlpatterns = [
    url(r'api-token-auth/', ObtainJSONWebToken.as_view(), name='login'),
    url(r'create-user/', views.ClientUserAPIView.as_view()),
    url(r'verify-email/', views.EmailVerificationAPIView.as_view(), name='verify-email'),
    # url('change-password/', views.ChangePasswordAPIView.as_view()),
    # url('restore-password/', views.RestorePasswordAPIView.as_view()),
    # url('request-restore-password/', views.RequestRestorePasswordAPIView.as_view()),
    # url('check-restore-password/', views.CheckRestorePasswordAPIView.as_view()),
    url(r'user-info/', views.UserInfoAPIView.as_view()),
    url(r'instruments/', views.InstrumentsApiView.as_view()),
    url(r'^', include(router.urls)),
]

urlpatterns += router.urls
