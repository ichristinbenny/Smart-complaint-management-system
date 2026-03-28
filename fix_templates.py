import re

files_to_fix = [
    'e:/Projectx/templates/complaints/dept_manage_staff.html',
    'e:/Projectx/templates/dashboard/manage_staff.html',
    'e:/Projectx/templates/complaints/complaint_detail.html',
    'e:/Projectx/templates/complaints/staff_dashboard.html',
]

for filepath in files_to_fix:
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    # Generic replacements
    text = re.sub(r'\{\{\s*staff\.name\s*\}\}', '{{ staff.user.first_name }} {{ staff.user.last_name }}', text)
    text = re.sub(r'\{\{\s*staff\.email\s*\}\}', '{{ staff.user.email }}', text)
    text = re.sub(r'\{\{\s*s\.name\s*\}\}', '{{ s.user.first_name }} {{ s.user.last_name }}', text)
    text = re.sub(r'\{\{\s*complaint\.assigned_staff\.name\s*\}\}', '{{ complaint.assigned_staff.user.first_name }} {{ complaint.assigned_staff.user.last_name }}', text)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)

print("Templates fixed via python script!")
