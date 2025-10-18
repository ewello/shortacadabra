from django.contrib import admin
from .models import Url, Click


@admin.register(Url)
class UrlAdmin(admin.ModelAdmin):
    list_display = ("id", "url", "status", "user", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("url", "user__username")


@admin.register(Click)
class ClickAdmin(admin.ModelAdmin):
    list_display = ("id", "url", "user", "ip_address", "created_at")
    list_filter = ("created_at",)
    search_fields = ("url__url", "user__username", "ip_address", "user_agent")