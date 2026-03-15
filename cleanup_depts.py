import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'city_care.settings')
django.setup()

from complaints.models import Department, Complaint
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

# Mapping of short-named (to be deleted) to long-named (to be kept)
migration_map = {
    'Water': 'Water Supply Department',
    'Road': 'Road & Transport Department',
    'Garbage': 'Garbage Department',
    'Public Safety': 'Public Safety Department',
}

# The 5 departments we want to keep
KEEP_NAMES = [
    'Electricity',
    'Water Supply Department',
    'Road & Transport Department',
    'Garbage Department',
    'Public Safety Department'
]

print("Starting cleanup...")

# 1. Migrate Complaints
for old_name, new_name in migration_map.items():
    try:
        old_dept = Department.objects.get(name=old_name)
        new_dept = Department.objects.get(name=new_name)
        
        complaints = Complaint.objects.filter(departments=old_dept)
        count = complaints.count()
        if count > 0:
            for c in complaints:
                c.departments.add(new_dept)
                c.departments.remove(old_dept)
            print(f"Migrated {count} complaints from '{old_name}' to '{new_name}'")
        else:
            print(f"No complaints found for '{old_name}'")
    except Department.DoesNotExist:
        print(f"Department '{old_name}' or '{new_name}' does not exist, skipping migration.")

# 2. Delete Redundant Departments
for d in Department.objects.all():
    if d.name not in KEEP_NAMES:
        name = d.name
        d.delete()
        print(f"Deleted redundant department: '{name}'")

# 3. Cleanup Admins and Groups
# Any user who is a department admin but not associated with a 'KEEP' department
# Or more simply, any group starting with [Name] Admin for deleted departments
all_groups = Group.objects.all()
for group in all_groups:
    if group.name.endswith(" Admin"):
        dept_name = group.name.replace(" Admin", "")
        if dept_name not in KEEP_NAMES:
            # Find users in this group and potentially deactivate if they have no other roles
            # For now, let's just delete the group and keep accounts if they are superusers, 
            # but user said "remove rest department admins"
            users = group.user_set.all()
            for u in users:
                if not u.is_superuser:
                    print(f"Removing redundant admin: '{u.username}'")
                    u.delete()
            group.delete()
            print(f"Deleted redundant group: '{group.name}'")

print("Cleanup complete.")
