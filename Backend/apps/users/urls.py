from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView,
    LoginView,
    ProfileView,
    DriverDetailUpdateView,
    RiderDetailUpdateView,
    ChangePasswordView,
)

app_name = 'users'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='user-register'),
    path('login/', LoginView.as_view(), name='user-login'),
    path('profile/', ProfileView.as_view(), name='user-profile'),
    path('driver-detail/',DriverDetailUpdateView.as_view(),name='driver-detail-update'),
    path('rider-detail/',RiderDetailUpdateView.as_view(),name='rider-detail-update'),
    path('change-password/',ChangePasswordView.as_view(),name='user-change-password'),
    path('token/refresh/',TokenRefreshView.as_view(),name='token-refresh'),
]
