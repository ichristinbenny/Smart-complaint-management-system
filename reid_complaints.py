import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'city_care.settings')
django.setup()

from complaints.models import Complaint

def renumber_complaints():
    # Order by creation date to keep chronological sequence
    complaints = list(Complaint.objects.all().order_by('created_at'))
    print(f"Total complaints found: {len(complaints)}")
    
    for i, c in enumerate(complaints, 1):
        old_id = c.id
        depts = list(c.departments.all())
        
        # We need to be careful with PK clashes.
        # Since currently they are 32, 33, 35, moving to 1, 2, 3 won't clash.
        
        c.pk = i
        c.id = i
        c.save() # Saves as new record with ID i
        c.departments.set(depts)
        
        # Only delete old if it's different from the new one
        if old_id != i:
            Complaint.objects.filter(id=old_id).delete()
            print(f"Renumbered #{old_id} to #{i}")
        else:
            print(f"Complaint #{i} already correct.")

    # Reset SQLite sequence if applicable (fixed syntax)
    from django.db import connection
    with connection.cursor() as cursor:
        try:
            cursor.execute("UPDATE sqlite_sequence SET seq = ? WHERE name = 'complaints_complaint';", [len(complaints)])
        except Exception as e:
            print(f"Sequence reset failed (non-critical): {e}")
    print("Renumbering complete.")

if __name__ == "__main__":
    renumber_complaints()
