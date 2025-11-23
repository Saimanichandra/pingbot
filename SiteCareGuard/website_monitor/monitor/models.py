from django.db import models
from django.utils import timezone


class Website(models.Model):
    STATUS_CHOICES = [
        ('up', 'Up'),
        ('down', 'Down'),
        ('degraded', 'Degraded'),
        ('unknown', 'Unknown'),
    ]

    name = models.CharField(max_length=200, help_text="Friendly name for the website")
    url = models.URLField(max_length=500, unique=True, help_text="Full URL to monitor")
    check_interval = models.IntegerField(default=300, help_text="Check interval in seconds")
    timeout = models.IntegerField(default=10, help_text="Request timeout in seconds")
    expected_status_code = models.IntegerField(default=200, help_text="Expected HTTP status code")
    current_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unknown')
    last_check_time = models.DateTimeField(null=True, blank=True)
    last_response_time = models.FloatField(null=True, blank=True, help_text="Response time in milliseconds")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 👇 Added for email-only alert logic
    status = models.CharField(max_length=20, default='Up')  # Up / Down
    down_since = models.DateTimeField(null=True, blank=True)
    alert_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.url})"


class HealthCheckLog(models.Model):
    website = models.ForeignKey(Website, on_delete=models.CASCADE, related_name='health_checks')
    checked_at = models.DateTimeField(default=timezone.now)
    status_code = models.IntegerField(null=True, blank=True)
    response_time = models.FloatField(null=True, blank=True, help_text="Response time in milliseconds")
    is_up = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-checked_at']
        indexes = [
            models.Index(fields=['website', '-checked_at']),
        ]

    def __str__(self):
        return f"{self.website.name} - {self.checked_at} - {'UP' if self.is_up else 'DOWN'}"


class Alert(models.Model):
    ALERT_TYPES = [
        ('down', 'Website Down'),
        ('up', 'Website Up'),
        ('degraded', 'Degraded Performance'),
    ]

    website = models.ForeignKey(Website, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.alert_type} - {self.website.name} at {self.created_at}"

