import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'city_care.settings')
django.setup()

from complaints.models import Department
from django.db.models import Count
from django.contrib.auth import get_user_model

User = get_user_model()

departments = Department.objects.annotate(num_complaints=Count('complaint'))

audit_data = []

for d in departments:
    admins = list(User.objects.filter(groups__name=f"{d.name} Admin").values_list('username', flat=True))
    audit_data.append({
        "id": d.id,
        "name": d.name,
        "num_complaints": d.num_complaints,
        "admins": admins
    })

with open('audit_results.json', 'w', encoding='utf-8') as f:
    json.dump(audit_data, f, indent=4)
