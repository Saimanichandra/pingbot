import requests, logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from monitors.models import Website
from django.conf import settings

logger = logging.getLogger(__name__)
ALERT_THRESHOLD_SECONDS = 120  # 2 minutes

class Command(BaseCommand):
    help = "Checks websites and sends email + SMS if down > 2 min."

    def handle(self, *args, **options):
        now = timezone.now()
        for site in Website.objects.all():
            try:
                r = requests.get(site.url, timeout=10)
                is_up = r.status_code < 400
            except requests.RequestException:
                is_up = False

            was_up = getattr(site, 'is_up', True)
            if is_up != was_up:
                site.last_status_change = now
            site.is_up = is_up
            site.last_checked = now
            site.save()

            # --- Alert Logic ---
            if not is_up:
                down_since = site.last_status_change or now
                down_time = (now - down_since).total_seconds()

                if down_time >= ALERT_THRESHOLD_SECONDS:
                    msg = f"{site.name} ({site.url}) is DOWN for {int(down_time)} seconds (checked at {now:%H:%M:%S})."
                    subject = f"[ALERT] {site.name} DOWN"
                    # Send Email
                    if getattr(site, 'alert_email', None):
                        try:
                            send_mail(subject, msg, settings.DEFAULT_FROM_EMAIL, [site.alert_email])
                            logger.info("Email alert sent to %s", site.alert_email)
                        except Exception as e:
                            logger.error("Email send failed: %s", e)
            elif was_up is False and is_up:
                msg = f"{site.name} ({site.url}) is UP again at {now:%H:%M:%S}."
                subject = f"[RECOVERY] {site.name} UP"
                if getattr(site, 'alert_email', None):
                    try:
                        send_mail(subject, msg, settings.DEFAULT_FROM_EMAIL, [site.alert_email])
                    except Exception:
                        logger.exception("Failed to send recovery email to %s", site.alert_email)
