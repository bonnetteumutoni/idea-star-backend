from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django_rest_passwordreset.views import (
    ResetPasswordRequestToken,
    ResetPasswordValidateToken,
    ResetPasswordConfirm,
)
from django_rest_passwordreset.models import ResetPasswordToken
from .serializers import (
    UserSerializer,
    FollowSerializer,
    SignupSerializer,
    LoginSerializer,
    ForgotPasswordSerializer,
    VerifyCodeSerializer,
    ResetPasswordSerializer,
)
from users.models import User, Follow
from django.core.cache import cache
from django.core.mail import send_mail, BadHeaderError
from django.conf import settings
from rest_framework_simplejwt.tokens import AccessToken

import secrets
import string
import smtplib


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        if 'password' in serializer.validated_data:
            password = serializer.validated_data.pop('password')
            instance.set_password(password)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def follow(self, request, pk=None):
        followed = self.get_object()
        if request.user == followed:
            return Response({"detail": "Cannot follow yourself."}, status=status.HTTP_400_BAD_REQUEST)
        follow, created = Follow.objects.get_or_create(follower=request.user, followed=followed)
        if created:
            return Response({"detail": "Followed successfully."}, status=status.HTTP_201_CREATED)
        return Response({"detail": "Already following."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def unfollow(self, request, pk=None):
        followed = self.get_object()
        follow_qs = Follow.objects.filter(follower=request.user, followed=followed)
        if follow_qs.exists():
            follow_qs.delete()
            return Response({"detail": "Unfollowed successfully."}, status=status.HTTP_200_OK)
        return Response({"detail": "Not following."}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"], permission_classes=[permissions.AllowAny])
    def followers(self, request, pk=None):
        user = self.get_object()
        followers = User.objects.filter(following__followed=user)
        serializer = UserSerializer(followers, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], permission_classes=[permissions.AllowAny])
    def following(self, request, pk=None):
        user = self.get_object()
        following = User.objects.filter(followers__follower=user)
        serializer = UserSerializer(following, many=True)
        return Response(serializer.data),



class SignupView(generics.CreateAPIView):
    serializer_class = SignupSerializer
    permission_classes = [AllowAny]

class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        access = AccessToken.for_user(user)
        return Response({
            "access": str(access),
            "user": {
                "id": user.id,
                "email": user.email,
                "password": user.first_name,
            }
        })



class ForgotPasswordView(generics.GenericAPIView):
    serializer_class = ForgotPasswordSerializer
    permission_classes = [AllowAny]   
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        user = User.objects.get(email=email)
        otp = cache.get(f"otp_{user.id}")
        send_mail(
            "Your OTP Code",
            f"Use this OTP to reset your password: {otp}",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return Response({"message": "OTP sent to your email"})

class VerifyCodeView(generics.GenericAPIView):
    serializer_class = VerifyCodeSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get("email")
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "Invalid email."}, status=status.HTTP_400_BAD_REQUEST)
        cache.delete(f"otp_{user.id}")
        cache.set(f"otp_verified_{user.id}", True, timeout=300) 

        return Response({"message": "OTP verified successfully"}, status=status.HTTP_200_OK)



class ResetPasswordView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get("email")
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "Invalid email."}, status=status.HTTP_400_BAD_REQUEST)
        if not cache.get(f"otp_verified_{user.id}"):
            return Response({"detail": "OTP not verified or expired."}, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        cache.delete(f"otp_verified_{user.id}")

        return Response({"message": "Password has been reset successfully"}, status=status.HTTP_200_OK)




