import re

with open('e:/Projectx/dashboard/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

# dashboard/views.py forms
text = re.sub(
    r'from django\.forms import modelform_factory as _mff\s*_StaffForm = _mff\(DepartmentStaff, fields=\[\'name\', \'email\', \'phone\', \'department\'\]\)',
    r'''from complaints.forms import DepartmentStaffCreationForm, DepartmentStaffEditForm

class _SuperAdminStaffCreationForm(DepartmentStaffCreationForm):
    class Meta(DepartmentStaffCreationForm.Meta):
        fields = ['phone', 'department']

class _SuperAdminStaffEditForm(DepartmentStaffEditForm):
    class Meta(DepartmentStaffEditForm.Meta):
        fields = ['phone', 'department']''',
    text
)

text = re.sub(r'_StaffForm\(request\.POST\)', r'_SuperAdminStaffCreationForm(request.POST)', text)
text = re.sub(r'_StaffForm\(\)', r'_SuperAdminStaffCreationForm()', text)
text = re.sub(r'_StaffForm\(request\.POST, instance=staff\)', r'_SuperAdminStaffEditForm(request.POST, instance=staff)', text)
text = re.sub(r'_StaffForm\(instance=staff\)', r'_SuperAdminStaffEditForm(instance=staff)', text)

text = re.sub(
    r'name = staff\.name\s*staff\.delete\(\)',
    r'name = staff.user.get_full_name() or staff.user.username\n    user = staff.user\n    staff.delete()\n    if user:\n        user.delete()',
    text
)

with open('e:/Projectx/dashboard/views.py', 'w', encoding='utf-8') as f:
    f.write(text)


with open('e:/Projectx/complaints/views.py', 'r', encoding='utf-8') as f:
    text2 = f.read()

text2 = re.sub(
    r'DepartmentStaffForm = modelform_factory\(DepartmentStaff, fields=\[\'name\', \'email\', \'phone\'\]\)',
    r'from .forms import DepartmentStaffCreationForm, DepartmentStaffEditForm',
    text2
)
text2 = re.sub(r'DepartmentStaffForm\(request\.POST\)', r'DepartmentStaffCreationForm(request.POST)', text2)
text2 = re.sub(r'DepartmentStaffForm\(\)', r'DepartmentStaffCreationForm()', text2)
text2 = re.sub(r'DepartmentStaffForm\(request\.POST, instance=staff\)', r'DepartmentStaffEditForm(request.POST, instance=staff)', text2)
text2 = re.sub(r'DepartmentStaffForm\(instance=staff\)', r'DepartmentStaffEditForm(instance=staff)', text2)

text2 = re.sub(
    r'is_staff_user = DepartmentStaff\.objects\.filter\(email=request\.user\.email\)\.exists\(\)',
    r'is_staff_user = hasattr(request.user, "departmentstaff")',
    text2
)

text2 = re.sub(
    r'staff_records = DepartmentStaff\.objects\.filter\(email=request\.user\.email\)\s*if not staff_records\.exists\(\):',
    r'staff = getattr(request.user, "departmentstaff", None)\n    if not staff:',
    text2
)

text2 = re.sub(r'assigned_staff__in=staff_records', r'assigned_staff=staff', text2)
text2 = re.sub(r'\'staff\': staff_records\.first\(\)', r'"staff": staff', text2)

text2 = re.sub(
    r'name = staff\.name\s*staff\.delete\(\)',
    r'name = staff.user.get_full_name() or staff.user.username\n    user = staff.user\n    staff.delete()\n    if user:\n        user.delete()',
    text2
)

text2 = re.sub(
    r'staff_users = User\.objects\.filter\(email=staff\.email\)\s*for su in staff_users:',
    r'su = staff.user\n    for su in [su]:',
    text2
)

with open('e:/Projectx/complaints/views.py', 'w', encoding='utf-8') as f:
    f.write(text2)

print("Updates completed via regex!")
