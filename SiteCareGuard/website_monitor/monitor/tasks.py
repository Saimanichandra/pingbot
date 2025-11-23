from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

from .models import Website, HealthCheckLog
from .views import check_website_health, send_email_alert
from website_monitor.utils.twilio_client import send_sms


@shared_task
def check_all_websites_task():
    print(f"🔄 Running check_all_websites_task at {timezone.now()}")

    websites = Website.objects.filter(is_active=True)

    for website in websites:

        # Run the accurate health check
        result = check_website_health(website)

        # Save the log entry
        HealthCheckLog.objects.create(
            website=website,
            status_code=result["status_code"],
            response_time=result["response_time"],
            is_up=result["is_up"],
            error_message=result["error_message"],
        )

        # Update website status fields
        website.current_status = result["status"]
        website.last_check_time = timezone.now()
        website.last_response_time = result["response_time"]

        # ------------------------------
        # 🚨 ALERT LOGIC (Email + SMS)
        # ------------------------------
        if not result["is_up"]:
            # Website is DOWN
            if not website.down_since:
                website.down_since = timezone.now()
                website.alert_sent = False
                print(f"⚠️ {website.name} just went DOWN!")

            else:
                downtime = timezone.now() - website.down_since

                # Send alerts every 120 seconds (2 minutes) of downtime
                if downtime.total_seconds() >= 120:
                    if not website.alert_sent:
                        # First alert after 2 minutes
                        print(f"🚨 {website.name} down >2 mins — sending first alerts")
                        
                        # Email alert
                        send_email_alert(website)

                        # SMS alert
                        msg = (
                            f"🚨 ALERT: {website.name} is DOWN!\n"
                            f"URL: {website.url}\n"
                            f"Down since: {website.down_since.strftime('%H:%M:%S')}"
                        )
                        send_sms(settings.ADMIN_PHONE_NUMBER, msg)
                        website.alert_sent = True
                    
                    # Recurring alerts: Reset flag every 120 seconds to allow next alert
                    elif (downtime.total_seconds() % 120) < 30:
                        # Send recurring alerts every 2 minutes
                        print(f"🔔 {website.name} recurring alert (downtime: {int(downtime.total_seconds())}s)")
                        
                        # Email alert
                        send_email_alert(website)

                        # SMS alert
                        msg = (
                            f"🚨 RECURRING ALERT: {website.name} is DOWN!\n"
                            f"URL: {website.url}\n"
                            f"Down since: {website.down_since.strftime('%H:%M:%S')}\n"
                           
                        )
                        send_sms(settings.ADMIN_PHONE_NUMBER, msg)
                        website.alert_sent = True

        else:
            # Website recovered
            website.down_since = None
            website.alert_sent = False

        website.save()

    print("✅ Website checks complete.")
