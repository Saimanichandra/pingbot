from django.contrib import admin
from .models import Website, HealthCheckLog, Alert


@admin.register(Website)
class WebsiteAdmin(admin.ModelAdmin):
    list_display = ['name', 'url', 'current_status', 'last_check_time', 'last_response_time', 'is_active']
    list_filter = ['current_status', 'is_active']
    search_fields = ['name', 'url']
    readonly_fields = ['created_at', 'updated_at', 'last_check_time']


@admin.register(HealthCheckLog)
class HealthCheckLogAdmin(admin.ModelAdmin):
    list_display = ['website', 'checked_at', 'is_up', 'status_code', 'response_time']
    list_filter = ['is_up', 'checked_at']
    search_fields = ['website__name', 'error_message']
    readonly_fields = ['checked_at']


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['website', 'alert_type', 'created_at', 'is_read']
    list_filter = ['alert_type', 'is_read', 'created_at']
    search_fields = ['website__name', 'message']
    readonly_fields = ['created_at']
