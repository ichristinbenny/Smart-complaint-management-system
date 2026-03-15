from django.core.management.base import BaseCommand
from complaints.models import Department

class Command(BaseCommand):
    help = 'Seeds initial departments'

    def handle(self, *args, **kwargs):
        departments = [
            {'name': 'Water', 'description': 'Water Supply Department', 'contact': '1800-WATER-HELP'},
            {'name': 'Electricity', 'description': 'Electricity Board', 'contact': '1800-POWER-HELP'},
            {'name': 'Public Safety', 'description': 'Police / Fire / Safety', 'contact': '100 / 101'},
            {'name': 'Road', 'description': 'Road and Infrastructure', 'contact': '1800-ROAD-HELP'},
            {'name': 'Garbage', 'description': 'Waste Management Department', 'contact': '1800-CLEAN-CITY'},
        ]
        for dept in departments:
            obj, created = Department.objects.get_or_create(
                name=dept['name'],
                defaults={
                    'description': dept['description'],
                    'higher_authority_contact': dept['contact']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created department {dept["name"]}'))
            else:
                self.stdout.write(self.style.WARNING(f'Department {dept["name"]} already exists'))
