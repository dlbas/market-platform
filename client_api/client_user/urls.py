from django.conf.urls import include
from django.urls import path
from rest_framework import routers

from client_user import views
from rest_framework_jwt.views import ObtainJSONWebToken

router = routers.DefaultRouter()


urlpatterns = [
    path('', include(router.urls)),
    path('api-token-auth/', ObtainJSONWebToken.as_view(), name='login'),
    path('create-user/', views.ClientUserAPIView.as_view()),
    # path('change-password/', views.ChangePasswordAPIView.as_view()),
    # path('restore-password/', views.RestorePasswordAPIView.as_view()),
    # path('request-restore-password/', views.RequestRestorePasswordAPIView.as_view()),
    # path('check-restore-password/', views.CheckRestorePasswordAPIView.as_view()),
    path('user-info/', views.UserInfoAPIView.as_view()),
]
