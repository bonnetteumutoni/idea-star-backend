from django.db import models
from django.conf import settings
from django_countries.fields import CountryField
from django.core.exceptions import ValidationError

class Project(models.Model):
    PROJECT_FIELD_CHOICES = [
        ('TECH', 'Technology'),
        ('AGRI', 'Agriculture'),
        ('FASH', 'Fashion'),
        ('HEALTH', 'Health'),
        ('EDU', 'Education'),
        ('FIN', 'Finance'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project_name = models.CharField(max_length=255)
    project_description = models.TextField()
    cover_image = models.ImageField(upload_to='cover_images/')
    project_location = CountryField(blank_label="(Select country)")
    project_field = models.CharField(max_length=50, choices=PROJECT_FIELD_CHOICES)
    project_products = models.ImageField(upload_to='project_products/',blank=True, null=True)
    project_document = models.FileField(
        upload_to='project_documents/',
        blank=True,
        null=True
    )

    def __str__(self):
        return self.project_name
