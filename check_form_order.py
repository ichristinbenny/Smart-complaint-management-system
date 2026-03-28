import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'city_care.settings')
django.setup()

from dashboard.views import _SuperAdminStaffCreationForm
from complaints.forms import DepartmentStaffCreationForm

print("Dept Admin Form:", list(DepartmentStaffCreationForm().fields.keys()))
print("Super Admin Form:", list(_SuperAdminStaffCreationForm().fields.keys()))
