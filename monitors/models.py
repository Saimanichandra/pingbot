from django.db import models

class Website(models.Model):
    name = models.CharField(max_length=200)
    url = models.URLField()
    ping_interval = models.PositiveIntegerField(default=30)
    is_up = models.BooleanField(default=True)
    last_checked = models.DateTimeField(null=True, blank=True)
    last_status_change = models.DateTimeField(null=True, blank=True)
    sms_enabled = models.BooleanField(default=False)
    alert_phone_number = models.CharField(max_length=20, blank=True, null=True)
    alert_email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.name
