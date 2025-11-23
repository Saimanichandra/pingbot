from django.core.management.base import BaseCommand
from monitors.models import Website

class Command(BaseCommand):
    help = "Adds example test websites."

    def handle(self, *args, **options):
        sites = [
            {"name": "Google", "url": "https://www.google.com", "sms_enabled": False},
            {"name": "Example", "url": "https://www.example.com", "sms_enabled": False},
            {"name": "InvalidSite", "url": "https://invalid-site-123456789.com", "sms_enabled": False},
        ]
        for s in sites:
            obj, created = Website.objects.get_or_create(name=s["name"], defaults={
                "url": s["url"],
                "sms_enabled": s.get("sms_enabled", False)
            })
            if created:
                self.stdout.write(self.style.SUCCESS(f"Added {s['name']}"))
            else:
                self.stdout.write(f"{s['name']} already exists")
