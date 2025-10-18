from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

# Create your models here.


class CustomDomain(models.Model):
    """Custom domains that users can set for their shortened URLs"""
    domain = models.CharField(
        max_length=255,
        unique=True,
        validators=[RegexValidator(
            regex=r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$',
            message='Enter a valid domain name'
        )]
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="custom_domains")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.domain


class Url(models.Model):
    url = models.URLField(blank=False)
    status = models.BooleanField(default=True)
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE, related_name="urls")
    custom_domain = models.ForeignKey(CustomDomain, null=True, blank=True, on_delete=models.SET_NULL, related_name="urls")
    created_at = models.DateTimeField(auto_now_add=True)


class Click(models.Model):
    url = models.ForeignKey(Url, on_delete=models.CASCADE, related_name="clicks")
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="clicks")
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    # Geolocation data
    country = models.CharField(max_length=100, null=True, blank=True)
    region = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    # Additional analytics
    referer = models.URLField(null=True, blank=True)
    browser = models.CharField(max_length=50, null=True, blank=True)
    os = models.CharField(max_length=50, null=True, blank=True)
    device_type = models.CharField(max_length=20, null=True, blank=True)  # mobile, desktop, tablet

    class Meta:
        ordering = ["-created_at"]