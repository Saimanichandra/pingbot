from django.core.management.base import BaseCommand
from website_monitor.monitor.models import Website


class Command(BaseCommand):
    help = 'Seeds the database with test websites'

    def handle(self, *args, **options):
        test_sites = [
            ('Google', 'https://www.google.com'),
            ('Example', 'https://www.example.com'),
            ('InvalidSite', 'https://thissitedoesnotexist1234.com'),
        ]

        for name, url in test_sites:
            obj, created = Website.objects.get_or_create(name=name, url=url)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Added {name}'))
            else:
                self.stdout.write(self.style.WARNING(f'{name} already exists'))

        self.stdout.write(self.style.SUCCESS('✅ Test websites added successfully!'))
