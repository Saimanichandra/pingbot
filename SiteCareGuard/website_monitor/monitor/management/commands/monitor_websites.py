
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

import time
from django.core.management.base import BaseCommand
from django.utils import timezone
from website_monitor.monitor.models import Website, HealthCheckLog, Alert
from website_monitor.monitor.views import check_website_health, create_alert_if_needed


class Command(BaseCommand):
    help = 'Monitor all active websites and log their health status'

    def add_arguments(self, parser):
        parser.add_argument(
            '--once',
            action='store_true',
            help='Run monitoring once instead of continuously',
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Check interval in seconds (default: 60)',
        )

    def handle(self, *args, **options):
        run_once = options['once']
        interval = options['interval']

        self.stdout.write(self.style.SUCCESS('Starting website monitoring...'))

        while True:
            websites = Website.objects.filter(is_active=True)
            
            if not websites.exists():
                self.stdout.write(self.style.WARNING('No active websites to monitor'))
            else:
                for website in websites:
                    self.check_and_log(website)

            if run_once:
                self.stdout.write(self.style.SUCCESS('Monitoring completed (single run)'))
                break

            self.stdout.write(self.style.SUCCESS(f'Sleeping for {interval} seconds...'))
            time.sleep(interval)

    def check_and_log(self, website):
        """Check a website and log the result"""
        self.stdout.write(f'Checking {website.name} ({website.url})...')
        
        old_status = website.current_status
        result = check_website_health(website)
        
        # Save health check log
        log = HealthCheckLog.objects.create(
            website=website,
            status_code=result['status_code'],
            response_time=result['response_time'],
            is_up=result['is_up'],
            error_message=result['error_message']
        )
        
        # Update website status
        website.current_status = result['status']
        website.last_check_time = timezone.now()
        website.last_response_time = result['response_time']
        website.save()
        
        # Create alert if needed
        create_alert_if_needed(website, result['status'], old_status)
        
        status_text = self.style.SUCCESS('UP') if result['is_up'] else self.style.ERROR('DOWN')
        self.stdout.write(f'  Status: {status_text}, Response Time: {result["response_time"]} ms')
        
        if result['error_message']:
            self.stdout.write(self.style.ERROR(f'  Error: {result["error_message"]}'))


    # -------------------------------
    # Email Alert Logic
    # -------------------------------
    from monitor.models import Website, PingLog

    for site in Website.objects.all():
        last_log = PingLog.objects.filter(website=site, status="Down").order_by('-timestamp').first()
        if last_log:
            downtime = timezone.now() - last_log.timestamp
            if downtime.total_seconds() > 120 and not site.alert_sent:
                subject = f"⚠️ Website Down: {site.name}"
                message = f"The website {site.url} has been down for more than 2 minutes."
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, settings.ALERT_RECIPIENTS)
                site.alert_sent = True
                site.save()
        else:
            if site.alert_sent:
                site.alert_sent = False
                site.save()
