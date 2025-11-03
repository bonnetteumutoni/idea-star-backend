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

from .serializers import (
    UserSerializer,
    FollowSerializer,
    RegisterSerializer,
    CustomPasswordResetSerializer,
)
from users.models import User, Follow


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save()

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
        return Response(serializer.data)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["user_id"] = user.id
        return token


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class CustomResetPasswordRequestTokenView(ResetPasswordRequestToken):
    serializer_class = CustomPasswordResetSerializer


class CustomResetPasswordValidateTokenView(ResetPasswordValidateToken):
    pass


class CustomResetPasswordConfirmView(ResetPasswordConfirm):
    pass