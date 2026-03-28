from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import user_passes_test
from complaints.models import Complaint, Department
from django.db.models import Count
from django.contrib import messages
from django.utils.translation import gettext as _
from accounts.models import User
from accounts.forms import DepartmentAdminCreationForm
from .decorators import superadmin_required
import json
import io
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.utils import timezone
from datetime import datetime

@superadmin_required
def admin_dashboard(request):
    total_complaints = Complaint.objects.count()
    pending_complaints = Complaint.objects.filter(status='Pending').count()
    in_progress_complaints = Complaint.objects.filter(status='In Progress').count()
    resolved_complaints = Complaint.objects.filter(status='Resolved').count()
    
    total_users = User.objects.count()
    total_departments = Department.objects.count()
    
    recent_complaints = Complaint.objects.order_by('-created_at')[:5]
    
    escalated_complaints = Complaint.objects.filter(is_escalated=True).count()
    
    # Chart Data: Status Distribution
    status_counts = Complaint.objects.values('status').annotate(total=Count('status'))
    status_data = {item['status']: item['total'] for item in status_counts}
    
    # Chart Data: Department Distribution
    dept_counts = Department.objects.annotate(total=Count('complaint')).values('name', 'total')
    dept_labels = [item['name'] for item in dept_counts]
    dept_values = [item['total'] for item in dept_counts]
    
    # Chart Data: Priority Distribution
    priority_counts = Complaint.objects.values('priority').annotate(total=Count('priority'))
    priority_data = {item['priority']: item['total'] for item in priority_counts}

    context = {
        'total_complaints': total_complaints,
        'pending_complaints': pending_complaints,
        'in_progress_complaints': in_progress_complaints,
        'resolved_complaints': resolved_complaints,
        'total_users': total_users,
        'total_departments': total_departments,
        'recent_complaints': recent_complaints,
        'escalated_complaints': escalated_complaints,
        'chart_status_data': json.dumps(status_data),
        'chart_dept_labels': json.dumps(dept_labels),
        'chart_dept_values': json.dumps(dept_values),
        'chart_priority_data': json.dumps(priority_data),
    }
    return render(request, 'dashboard/dashboard.html', context)

@superadmin_required
def manage_users(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'dashboard/users_admin.html', {'users': users})

@superadmin_required
def toggle_user_status(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user.is_superuser:
        messages.error(request, "Cannot suspend a superuser.")
    else:
        user.is_active = not user.is_active
        user.save()
        status = "activated" if user.is_active else "suspended"
        messages.success(request, f"User {user.username} has been {status}.")
    return redirect('manage_users')

@superadmin_required
@require_POST
def delete_user(request, user_id):
    user_to_delete = get_object_or_404(User, id=user_id)
    if user_to_delete == request.user:
        messages.error(request, "You cannot delete your own account.")
    elif user_to_delete.is_superuser:
        messages.error(request, "Cannot delete a superuser account.")
    else:
        username = user_to_delete.username
        is_admin = user_to_delete.is_department_admin
        user_to_delete.delete()
        messages.success(request, f"User {username} has been permanently deleted.")
        if is_admin:
            return redirect('manage_admins')
    return redirect('manage_users')

@superadmin_required
def manage_admins(request):
    admins = User.objects.filter(is_department_admin=True)
    return render(request, 'dashboard/manage_admins.html', {'admins': admins})

@superadmin_required
def add_admin(request):
    if request.method == 'POST':
        form = DepartmentAdminCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department Admin created successfully!')
            return redirect('manage_admins')
    else:
        form = DepartmentAdminCreationForm()
    return render(request, 'dashboard/add_admin.html', {'form': form})

@superadmin_required
def complaints_admin(request):
    status_filter = request.GET.get('status')
    dept_filter = request.GET.get('department')
    search_query = request.GET.get('q')
    
    complaints = Complaint.objects.all().order_by('-created_at')
    
    if status_filter:
        complaints = complaints.filter(status=status_filter)
    if dept_filter:
        complaints = complaints.filter(departments__id=dept_filter)
    if search_query:
        complaints = complaints.filter(title__icontains=search_query) | complaints.filter(description__icontains=search_query)

    departments = Department.objects.all()
    
    return render(request, 'dashboard/complaints_admin.html', {
        'complaints': complaints,
        'departments': departments,
        'current_status': status_filter,
        'current_dept': dept_filter,
    })

@superadmin_required
def admin_update_complaint(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        new_dept_ids = request.POST.getlist('departments')
        is_escalated = request.POST.get('is_escalated') == 'on'
        
        if new_status:
            complaint.status = new_status
        if new_dept_ids:
            complaint.departments.set(new_dept_ids)
        complaint.is_escalated = is_escalated
        complaint.save()
        
        messages.success(request, _("Complaint #%(pk)s updated successfully.") % {'pk': pk})
        return redirect('complaints_admin')
    return redirect('complaint_detail', pk=pk)

@superadmin_required
def departments_admin(request):
    departments = Department.objects.all()
    return render(request, 'dashboard/departments_admin.html', {'departments': departments})

from django.forms import modelform_factory
DepartmentForm = modelform_factory(Department, fields=[
    'name', 'description', 
    'authority_name', 'authority_phone', 'authority_email', 'authority_designation',
    'higher_authority_name', 'higher_authority_phone', 'higher_authority_email', 'higher_authority_designation',
    'higher_authority_contact'
])

@superadmin_required
def add_department(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Department/Authority added successfully."))
            if 'next' in request.POST:
                return redirect(request.POST.get('next'))
            return redirect('departments_admin')
    else:
        form = DepartmentForm()
    return render(request, 'dashboard/add_department.html', {'form': form, 'next': request.GET.get('next')})

@superadmin_required
def edit_department(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=dept)
        if form.is_valid():
            form.save()
            messages.success(request, _("Department/Authority updated successfully."))
            if 'next' in request.POST:
                return redirect(request.POST.get('next'))
            return redirect('departments_admin')
    else:
        form = DepartmentForm(instance=dept)
    return render(request, 'dashboard/edit_department.html', {'form': form, 'department': dept, 'next': request.GET.get('next')})

@superadmin_required
def authorities_admin(request):
    departments = Department.objects.all()
    return render(request, 'dashboard/authorities_admin.html', {'departments': departments})

@superadmin_required
def settings_admin(request):
    # This would typically involve a Settings model or just showing config
    return render(request, 'dashboard/settings_admin.html')

@superadmin_required
def delete_department(request, pk):
    if request.method == 'POST':
        dept = get_object_or_404(Department, pk=pk)
        name = dept.name
        dept.delete()
        messages.success(request, f"Department/Authority '{name}' deleted successfully.")
        if request.POST.get('next'):
            return redirect(request.POST.get('next'))
    return redirect('departments_admin')

@superadmin_required
@require_POST
def delete_complaint(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)
    complaint.delete()
    messages.success(request, f"Complaint #{pk} has been deleted successfully.")
    return redirect('complaints_admin')

@superadmin_required
@require_POST
def bulk_delete_complaints(request):
    complaint_ids = request.POST.getlist('selected_complaints')
    if complaint_ids:
        count = Complaint.objects.filter(id__in=complaint_ids).count()
        Complaint.objects.filter(id__in=complaint_ids).delete()
        messages.success(request, f"Successfully deleted {count} complaints.")
    else:
        messages.warning(request, "No complaints were selected.")
    return redirect('complaints_admin')

@superadmin_required
def download_complaint_report(request):
    from_date_str = request.GET.get('from_date')
    to_date_str = request.GET.get('to_date')
    
    complaints = Complaint.objects.all().order_by('-created_at')
    
    if from_date_str and to_date_str:
        try:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d')
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d')
            # Make dates aware if using timezone support
            from_date = timezone.make_aware(datetime.combine(from_date, datetime.min.time()))
            to_date = timezone.make_aware(datetime.combine(to_date, datetime.max.time()))
            
            complaints = complaints.filter(created_at__range=(from_date, to_date))
        except ValueError:
            messages.error(request, _("Invalid date format. Please use YYYY-MM-DD."))
            return redirect('complaints_admin')
    
    template_path = 'dashboard/report_pdf.html'
    context = {
        'complaints': complaints,
        'from_date': from_date_str,
        'to_date': to_date_str,
        'generated_at': timezone.now(),
    }
    
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="complaint_report_{from_date_str}_to_{to_date_str}.pdf"'
    
    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(
       html, dest=response)
    
    # if error then show some funny view
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response



# --- Super Admin: Staff Management -------------------------------------------



from complaints.models import DepartmentStaff

from complaints.forms import DepartmentStaffCreationForm, DepartmentStaffEditForm

class _SuperAdminStaffCreationForm(DepartmentStaffCreationForm):
    field_order = ['username', 'first_name', 'last_name', 'email', 'password', 'phone', 'department']
    class Meta(DepartmentStaffCreationForm.Meta):
        fields = ['phone', 'department']

class _SuperAdminStaffEditForm(DepartmentStaffEditForm):
    field_order = ['username', 'first_name', 'last_name', 'email', 'phone', 'department']
    class Meta(DepartmentStaffEditForm.Meta):
        fields = ['phone', 'department']





@superadmin_required

def manage_staff(request):

    staff_list = DepartmentStaff.objects.select_related('department').all()

    return render(request, 'dashboard/manage_staff.html', {'staff_list': staff_list})





@superadmin_required

def add_staff(request):

    if request.method == 'POST':

        form = _SuperAdminStaffCreationForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(request, _('Staff member added successfully.'))

            return redirect('manage_staff_admin')

    else:

        form = _SuperAdminStaffCreationForm()

    return render(request, 'dashboard/add_staff.html', {'form': form})





@superadmin_required

def edit_staff(request, pk):

    staff = get_object_or_404(DepartmentStaff, pk=pk)

    if request.method == 'POST':

        form = _SuperAdminStaffEditForm(request.POST, instance=staff)

        if form.is_valid():

            form.save()

            messages.success(request, _('Staff member updated successfully.'))

            return redirect('manage_staff_admin')

    else:

        form = _SuperAdminStaffEditForm(instance=staff)

    return render(request, 'dashboard/edit_staff.html', {'form': form, 'staff': staff})





@superadmin_required

@require_POST

def delete_staff(request, pk):

    staff = get_object_or_404(DepartmentStaff, pk=pk)

    name = staff.user.get_full_name() or staff.user.username
    user = staff.user
    staff.delete()
    if user:
        user.delete()

    messages.success(request, _("Staff member '%(name)s' deleted.") % {'name': name})

    return redirect('manage_staff_admin')



