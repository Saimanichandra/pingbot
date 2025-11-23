import time
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Avg
from datetime import timedelta
from .models import Website, HealthCheckLog, Alert
from django.core.mail import send_mail
from django.conf import settings
from website_monitor.utils.twilio_client import send_sms

from django.shortcuts import get_object_or_404


def check_website_health(website):
    """
    Perform an accurate health check on a website
    Returns: dict with status information
    """
    start_time = time.time()
    result = {
        'is_up': False,
        'status_code': None,
        'response_time': None,
        'error_message': None,
        'status': 'down'
    }
    
    try:
        response = requests.get(
            website.url,
            timeout=website.timeout,
            allow_redirects=True,
            headers={'User-Agent': 'Website-Monitor/1.0'}
        )
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        result['status_code'] = response.status_code
        result['response_time'] = round(response_time, 2)
        
        # Check if status code matches expected
        if response.status_code == website.expected_status_code:
            result['is_up'] = True
            result['status'] = 'up'
        elif 200 <= response.status_code < 300:
            result['is_up'] = True
            result['status'] = 'up'
        elif 300 <= response.status_code < 400:
            result['is_up'] = True
            result['status'] = 'up'
        else:
            result['error_message'] = f"Unexpected status code: {response.status_code}"
            result['status'] = 'degraded'
    except requests.exceptions.Timeout:
     result['error_message'] = f"Request timeout after {website.timeout} seconds"
     result['response_time'] = None

    except requests.exceptions.ConnectionError as e:
     result['error_message'] = f"Connection error: {str(e)}"
     result['response_time'] = None

    except requests.exceptions.RequestException as e:
     result['error_message'] = f"Request error: {str(e)}"
     result['response_time'] = None

    
    return result


def create_alert_if_needed(website, new_status, old_status):
    """Create alerts when website status changes"""
    if old_status != new_status:
        if new_status == 'down' and old_status != 'down':
            Alert.objects.create(
                website=website,
                alert_type='down',
                message=f"{website.name} is DOWN! URL: {website.url}"
            )
        elif new_status == 'up' and old_status in ['down', 'degraded', 'unknown']:
            Alert.objects.create(
                website=website,
                alert_type='up',
                message=f"{website.name} is back UP! URL: {website.url}"
            )
        elif new_status == 'degraded' and old_status == 'up':
            Alert.objects.create(
                website=website,
                alert_type='degraded',
                message=f"{website.name} is DEGRADED! URL: {website.url}"
            )


def dashboard(request):
    """Main dashboard view"""
    websites = Website.objects.filter(is_active=True)
    recent_alerts = Alert.objects.filter(is_read=False)[:10]
    
    # Calculate overall statistics
    total_websites = websites.count()
    up_count = websites.filter(current_status='up').count()
    down_count = websites.filter(current_status='down').count()
    
    context = {
        'websites': websites,
        'recent_alerts': recent_alerts,
        'total_websites': total_websites,
        'up_count': up_count,
        'down_count': down_count,
        'unread_alerts_count': recent_alerts.count(),
    }
    
    return render(request, 'monitor/dashboard.html', context)


def check_website_ajax(request, website_id):
    """AJAX endpoint to check a single website"""
    website = get_object_or_404(Website, id=website_id)
    
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
    
    return JsonResponse({
        'id': website.id,
        'name': website.name,
        'url': website.url,
        'status': result['status'],
        'is_up': result['is_up'],
        'status_code': result['status_code'],
        'response_time': result['response_time'],
        'error_message': result['error_message'],
        'last_check_time': website.last_check_time.isoformat() if website.last_check_time else None,
    })


def check_all_websites_ajax(request):
    """AJAX endpoint to check all websites"""
    websites = Website.objects.filter(is_active=True)
    results = []
    
    for website in websites:
        old_status = website.current_status
        result = check_website_health(website)
        
        # Save health check log
        HealthCheckLog.objects.create(
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
        
        results.append({
            'id': website.id,
            'name': website.name,
            'url': website.url,
            'status': result['status'],
            'is_up': result['is_up'],
            'status_code': result['status_code'],
            'response_time': result['response_time'],
            'error_message': result['error_message'],
            'last_check_time': website.last_check_time.isoformat() if website.last_check_time else None,
        })
    
    return JsonResponse({'websites': results})


def website_detail(request, website_id):
    """Detailed view for a single website with real-time graphs"""
    website = get_object_or_404(Website, id=website_id)
    
    # Get last 30 minutes of health check data (real-time)
    thirty_minutes_ago = timezone.now() - timedelta(minutes=30)
    health_checks = website.health_checks.filter(
        checked_at__gte=thirty_minutes_ago
    ).order_by('checked_at')
    
    # Prepare data for charts
    chart_data = {
        'labels': [check.checked_at.strftime('%H:%M:%S') for check in health_checks],
        'response_times': [check.response_time if check.response_time else 0 for check in health_checks],
        'status': [1 if check.is_up else 0 for check in health_checks],
    }
    
    # Calculate statistics
    avg_response_time = health_checks.aggregate(Avg('response_time'))['response_time__avg']
    uptime_percentage = (health_checks.filter(is_up=True).count() / health_checks.count() * 100) if health_checks.count() > 0 else 0
    
    context = {
        'website': website,
        'chart_data': chart_data,
        'avg_response_time': round(avg_response_time, 2) if avg_response_time else 0,
        'uptime_percentage': round(uptime_percentage, 2),
        'recent_checks': health_checks[:20],
        'time_range': 'Last 30 minutes (Real-time)',
    }
    
    return render(request, 'monitor/website_detail.html', context)


def add_website(request):
    """Add a new website to monitor"""
    if request.method == 'POST':
        name = request.POST.get('name')
        url = request.POST.get('url')
        check_interval = request.POST.get('check_interval', 300)
        timeout = request.POST.get('timeout', 10)
        expected_status_code = request.POST.get('expected_status_code', 200)
        
        try:
            website = Website.objects.create(
                name=name,
                url=url,
                check_interval=int(check_interval),
                timeout=int(timeout),
                expected_status_code=int(expected_status_code),
            )
            messages.success(request, f'Website "{name}" added successfully!')
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, f'Error adding website: {str(e)}')
    
    return render(request, 'monitor/add_website.html')


def edit_website(request, website_id):
    """Edit an existing website"""
    website = get_object_or_404(Website, id=website_id)
    
    if request.method == 'POST':
        website.name = request.POST.get('name')
        website.url = request.POST.get('url')
        website.check_interval = int(request.POST.get('check_interval', 300))
        website.timeout = int(request.POST.get('timeout', 10))
        website.expected_status_code = int(request.POST.get('expected_status_code', 200))
        website.is_active = request.POST.get('is_active') == 'on'
        
        try:
            website.save()
            messages.success(request, f'Website "{website.name}" updated successfully!')
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, f'Error updating website: {str(e)}')
    
    return render(request, 'monitor/edit_website.html', {'website': website})


def delete_website(request, website_id):
    """Delete a website"""
    website = get_object_or_404(Website, id=website_id)
    
    if request.method == 'POST':
        name = website.name
        website.delete()
        messages.success(request, f'Website "{name}" deleted successfully!')
        return redirect('dashboard')
    
    return render(request, 'monitor/delete_website.html', {'website': website})


def mark_alerts_read(request):
    """Mark all alerts as read"""
    Alert.objects.filter(is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success'})


def get_alerts(request):
    """Get unread alerts"""
    alerts = Alert.objects.filter(is_read=False).order_by('-created_at')[:10]
    
    alerts_data = [{
        'id': alert.id,
        'type': alert.alert_type,
        'message': alert.message,
        'created_at': alert.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'website_name': alert.website.name,
    } for alert in alerts]
    
    return JsonResponse({'alerts': alerts_data, 'count': len(alerts_data)})

def check_websites(request=None):
    """
    Periodically checks all monitored websites and sends email
    ONLY when a site is confirmed down for > 2 minutes.
    """
    websites = Website.objects.all()
    for website in websites:
        try:
            response = requests.get(website.url, timeout=website.timeout)
            if 200 <= response.status_code < 400:
                # Website is UP
                if website.status != 'Up':
                    website.status = 'Up'
                    website.down_since = None
                    website.alert_sent = False
            else:
                # Website returned error status
                handle_downtime(website)
        except Exception:
            # Any connection or timeout error
            handle_downtime(website)
        website.save()

    if request:
        return render(request, 'monitor/dashboard.html', {'websites': websites})
def website_data(request, website_id):
    website = get_object_or_404(Website, id=website_id)

    last_24h = timezone.now() - timedelta(hours=24)
    checks = website.health_checks.filter(
        checked_at__gte=last_24h
    ).order_by("checked_at")

    labels = [c.checked_at.strftime("%H:%M") for c in checks]
    response_times = [
        c.response_time if c.response_time is not None else None
        for c in checks
    ]
    statuses = [1 if c.is_up else 0 for c in checks]

    return JsonResponse({
        "labels": labels,
        "response_times": response_times,
        "statuses": statuses
    })


def handle_downtime(website):
    """
    Tracks how long a site has been down and triggers email alert after 2 mins.
    """


    if not website.down_since:
        # First time going down
        website.down_since = timezone.now()
        print(f"⚠️ First DOWN detection for {website.name}")
    else:
        # How long it's down?
        downtime = timezone.now() - website.down_since

        if downtime > timedelta(minutes=2) and not website.alert_sent:

            # EMAIL ALERT
            send_email_alert(website)

            # SMS ALERT
            sms_msg = (
                f"🚨 ALERT: {website.name} is DOWN!\n"
                f"URL: {website.url}\n"
                f"Down since: {website.down_since.strftime('%H:%M:%S')}"
            )

            send_sms(settings.ADMIN_PHONE_NUMBER, sms_msg)

            website.alert_sent = True
            print(f"📱 SMS + Email alert sent for {website.name}")

    website.status = 'Down'
    website.save()
    #if not website.down_since:
        # First detection of downtime
     #   website.down_since = timezone.now()
      #  print(f"⚠️ {website.name} first detected DOWN at {website.down_since}")
    #else:
     #   downtime = timezone.now() - website.down_since
      #  if downtime > timedelta(minutes=2) and not website.alert_sent:
       #     send_email_alert(website)
        #    website.alert_sent = True
         #   print(f"🚨 Alert triggered for {website.name}, email sent.")
   # website.status = 'Down'
   #website.save()


def send_email_alert(website):
    """
    Sends an email alert using SMTP (only once per downtime period)
    """
    subject = f"🚨 Website Down: {website.name}"
    message = (
        f"The website '{website.name}' ({website.url}) has been DOWN since "
        f"{website.down_since.strftime('%Y-%m-%d %H:%M:%S')}.\n\n"
        f"Please check the issue immediately."
    )
    recipient_list = ['saimanichandra2580@gmail.com']  # change if needed

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            fail_silently=False
        )
        print(f"✅ Email sent successfully for {website.url}")
    except Exception as e:
        print(f"❌ Failed to send email for {website.url}: {e}")

    
from django.http import JsonResponse
from datetime import timedelta

def get_website_health_data(request, website_id):
    """
    Returns live response time data for the last 2 hours.
    Used by Chart.js to render accurate graphs.
    """
    website = get_object_or_404(Website, id=website_id)
    since = timezone.now() - timedelta(hours=2)
    
    logs = HealthCheckLog.objects.filter(
        website=website,
        checked_at__gte=since
    ).order_by('checked_at')

    data = {
        "labels": [log.checked_at.strftime("%H:%M:%S") for log in logs],
        "response_times": [log.response_time or 0 for log in logs],
        "status": [1 if log.is_up else 0 for log in logs],
    }
    return JsonResponse(data)

