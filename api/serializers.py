from django.contrib.auth.forms import PasswordResetForm
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from users.models import User, Follow


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
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
        password = validated_data.pop("password", None)
        user = User.objects.create_user(
            email=validated_data.get("email"), password=password
        )
        profile_image = validated_data.get("profile_image")
        if profile_image:
            user.profile_image = profile_image
            user.save(update_fields=["profile_image"])
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        if password:
            instance.set_password(password)
            instance.save(update_fields=["password"])
        return super().update(instance, validated_data)


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ["id", "follower", "followed", "created_at"]
        read_only_fields = ["created_at"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ("email", "password", "profile_image")

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(email=validated_data.get("email"), password=password)
        profile_image = validated_data.get("profile_image")
        if profile_image:
            user.profile_image = profile_image
            user.save(update_fields=["profile_image"])
        return user


class CustomPasswordResetSerializer(serializers.Serializer):
    """
    Simple password reset serializer that uses Django's PasswordResetForm.
    It accepts an 'email' field and, when validated and saved, triggers
    Django's password reset email flow (subject to your EMAIL_BACKEND).
    """
    email = serializers.EmailField()

    default_error_messages = {
        "invalid_email": _("No user is associated with this email address.")
    }

    def validate_email(self, value):
        form = PasswordResetForm(data={"email": value})
        if not form.is_valid():
            if not User.objects.filter(email__iexact=value).exists():
                raise serializers.ValidationError(self.error_messages["invalid_email"])
        return value

    def save(self, request=None, use_https=False, token_generator=None, from_email=None, email_template_name=None, subject_template_name=None, extra_email_context=None):
        """
        Use Django's PasswordResetForm to send the reset email.
        Parameters mirror Django's PasswordResetForm.save signature.
        """
        form = PasswordResetForm(data={"email": self.validated_data["email"]})
        if form.is_valid():
            form.save(
                request=request,
                use_https=use_https,
                token_generator=token_generator,
                from_email=from_email,
                email_template_name=email_template_name,
                subject_template_name=subject_template_name,
                extra_email_context=extra_email_context,
            )