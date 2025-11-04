from django.contrib.auth.forms import PasswordResetForm
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from rest_framework.validators import UniqueValidator
from users.models import User, Follow
from django_rest_passwordreset.models import ResetPasswordToken
import random
from django.core.cache import cache
from django.contrib.auth import authenticate


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "password",         
            "profile_image",
            "followers_count",
            "following_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "followers_count",
            "following_count",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ["id", "follower", "followed", "created_at"]
        read_only_fields = ["created_at"]


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ["id", "follower", "followed", "created_at"]
        read_only_fields = ["created_at"]


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )
    confirm_password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all(), message="Email already registered.")]
    )

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "confirm_password",
        ]

    def validate(self, attrs):
        pw = attrs.get("password")
        pw2 = attrs.get("confirm_password")
        if pw != pw2:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("confirm_password", None)
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        otp = random.randint(1000, 9999)
        cache.set(f"otp_{user.id}", otp, timeout=600)
        return value


class VerifyCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=4)

    def validate(self, data):
        try:
            user = User.objects.get(email=data["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email")
        cached_otp = cache.get(f"otp_{user.id}")
        if not cached_otp or str(cached_otp) != str(data["otp"]):
            raise serializers.ValidationError("Invalid or expired OTP")
        return data


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    def save(self, **kwargs):
        user = User.objects.get(email=self.validated_data["email"])
        user.set_password(self.validated_data["password"])
        user.save()
        cache.delete(f"otp_{user.id}")
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data["email"], password=data["password"])
        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        if not user.is_active:
            raise serializers.ValidationError("This account is inactive.")
        data["user"] = user
        return data