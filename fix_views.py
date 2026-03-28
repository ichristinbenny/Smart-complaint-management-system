import sys

with open('e:/Projectx/dashboard/views.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    "from complaints.models import DepartmentStaff\nfrom django.forms import modelform_factory as _mff\n_StaffForm = _mff(DepartmentStaff, fields=['name', 'email', 'phone', 'department'])",
    "from complaints.models import DepartmentStaff\nfrom complaints.forms import DepartmentStaffCreationForm, DepartmentStaffEditForm\n\nclass _SuperAdminStaffCreationForm(DepartmentStaffCreationForm):\n    class Meta(DepartmentStaffCreationForm.Meta):\n        fields = ['phone', 'department']\n\nclass _SuperAdminStaffEditForm(DepartmentStaffEditForm):\n    class Meta(DepartmentStaffEditForm.Meta):\n        fields = ['phone', 'department']"
)
text = text.replace(
    "from complaints.models import DepartmentStaff\r\nfrom django.forms import modelform_factory as _mff\r\n_StaffForm = _mff(DepartmentStaff, fields=['name', 'email', 'phone', 'department'])",
    "from complaints.models import DepartmentStaff\r\nfrom complaints.forms import DepartmentStaffCreationForm, DepartmentStaffEditForm\r\n\r\nclass _SuperAdminStaffCreationForm(DepartmentStaffCreationForm):\r\n    class Meta(DepartmentStaffCreationForm.Meta):\r\n        fields = ['phone', 'department']\r\n\r\nclass _SuperAdminStaffEditForm(DepartmentStaffEditForm):\r\n    class Meta(DepartmentStaffEditForm.Meta):\r\n        fields = ['phone', 'department']"
)
text = text.replace("form = _StaffForm(request.POST)", "form = _SuperAdminStaffCreationForm(request.POST)")
text = text.replace("form = _StaffForm()", "form = _SuperAdminStaffCreationForm()")
text = text.replace("form = _StaffForm(request.POST, instance=staff)", "form = _SuperAdminStaffEditForm(request.POST, instance=staff)")
text = text.replace("form = _StaffForm(instance=staff)", "form = _SuperAdminStaffEditForm(instance=staff)")

text = text.replace("    name = staff.name\n    staff.delete()", "    name = staff.user.get_full_name() or staff.user.username\n    user = staff.user\n    staff.delete()\n    if user:\n        user.delete()")
text = text.replace("    name = staff.name\r\n    staff.delete()", "    name = staff.user.get_full_name() or staff.user.username\r\n    user = staff.user\r\n    staff.delete()\r\n    if user:\r\n        user.delete()")

with open('e:/Projectx/dashboard/views.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Dashboard views fixed!")


with open('e:/Projectx/complaints/views.py', 'r', encoding='utf-8') as f:
    text2 = f.read()

text2 = text2.replace(
    "DepartmentStaffForm = modelform_factory(DepartmentStaff, fields=['name', 'email', 'phone'])",
    "from .forms import DepartmentStaffCreationForm, DepartmentStaffEditForm"
)
text2 = text2.replace("form = DepartmentStaffForm(request.POST)", "form = DepartmentStaffCreationForm(request.POST)")
text2 = text2.replace("form = DepartmentStaffForm()", "form = DepartmentStaffCreationForm()")
text2 = text2.replace("form = DepartmentStaffForm(request.POST, instance=staff)", "form = DepartmentStaffEditForm(request.POST, instance=staff)")
text2 = text2.replace("form = DepartmentStaffForm(instance=staff)", "form = DepartmentStaffEditForm(instance=staff)")
text2 = text2.replace("is_staff_user = DepartmentStaff.objects.filter(email=request.user.email).exists()", "is_staff_user = hasattr(request.user, 'departmentstaff')")
text2 = text2.replace("staff_records = DepartmentStaff.objects.filter(email=request.user.email)\n\n    if not staff_records.exists():", "if not hasattr(request.user, 'departmentstaff'):")
text2 = text2.replace("staff_records = DepartmentStaff.objects.filter(email=request.user.email)\r\n\r\n    if not staff_records.exists():", "if not hasattr(request.user, 'departmentstaff'):")
text2 = text2.replace("assigned_staff__in=staff_records", "assigned_staff=request.user.departmentstaff")
text2 = text2.replace("'staff': staff_records.first()", "'staff': request.user.departmentstaff")

text2 = text2.replace("    name = staff.name\n\n    staff.delete()", "    name = staff.user.get_full_name() or staff.user.username\n    user = staff.user\n    staff.delete()\n    if user:\n        user.delete()")
text2 = text2.replace("    name = staff.name\r\n\r\n    staff.delete()", "    name = staff.user.get_full_name() or staff.user.username\r\n    user = staff.user\r\n    staff.delete()\r\n    if user:\r\n        user.delete()")


text2 = text2.replace("    staff_users = User.objects.filter(email=staff.email)\n\n    for su in staff_users:", "    su = staff.user\n    for su in [su]:")
text2 = text2.replace("    staff_users = User.objects.filter(email=staff.email)\r\n\r\n    for su in staff_users:", "    su = staff.user\r\n    for su in [su]:")


with open('e:/Projectx/complaints/views.py', 'w', encoding='utf-8') as f:
    f.write(text2)
print("Complaints views fixed!")

