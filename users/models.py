from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(_('email address'), unique=True)
    password = models.CharField(_('password'), max_length=128)  
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    followers_count = models.PositiveIntegerField(default=0)
    following_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

class Follow(models.Model):
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    followed = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'followed')

@receiver(post_save, sender=Follow)
def update_follow_counts_on_save(sender, instance, created, **kwargs):
    if created:
        instance.follower.following_count += 1
        instance.follower.save(update_fields=['following_count'])
        instance.followed.followers_count += 1
        instance.followed.save(update_fields=['followers_count'])

def update_follow_counts_on_delete(sender, instance, **kwargs):
    instance.follower.following_count = max(0, instance.follower.following_count - 1)
    instance.follower.save(update_fields=['following_count'])
    instance.followed.followers_count = max(0, instance.followed.followers_count - 1)
    instance.followed.save(update_fields=['followers_count'])

models.signals.pre_delete.connect(update_follow_counts_on_delete, sender=Follow)
