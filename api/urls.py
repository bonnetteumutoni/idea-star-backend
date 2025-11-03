from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken.views import obtain_auth_token

from .views import (
    RegisterView,
    CustomTokenObtainPairView,
    UserViewSet,
    CustomResetPasswordRequestTokenView,
    CustomResetPasswordValidateTokenView,
    CustomResetPasswordConfirmView,
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')  
auth_urls = [
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('password/reset/', CustomResetPasswordRequestTokenView.as_view(), name='password_reset'),
    path('password/reset/validate/', CustomResetPasswordValidateTokenView.as_view(), name='password_reset_validate'),
    path('password/reset/confirm/', CustomResetPasswordConfirmView.as_view(), name='password_reset_confirm'),
]

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include((auth_urls, 'auth'))),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)