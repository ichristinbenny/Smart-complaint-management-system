import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'city_care.settings')
django.setup()

from complaints.models import Complaint, Department
from accounts.models import User
from complaints.ml_utils import predict_department

# Ensure we have departments
dept_road, _ = Department.objects.get_or_create(name='Road')
dept_water, _ = Department.objects.get_or_create(name='Water')

desc = "There is a big pothole in the road near the bus stop and water is leaking from an underground pipe through the pothole."

depts = predict_department(desc)
print("Predicted departments:", [d.name for d in depts])

user, _ = User.objects.get_or_create(username='testuser', email='test@test.com')
c = Complaint.objects.create(
    user=user,
    title="Test multi-department complaint",
    description=desc,
    location="Main Street"
)

if depts:
    c.departments.set(depts)

print("Complaint departments:", [d.name for d in c.departments.all()])

# Clean up
c.delete()
