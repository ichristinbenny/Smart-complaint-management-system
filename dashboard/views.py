from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from complaints.models import Complaint, Department
from django.db.models import Count
from django.contrib import messages
from accounts.models import User
from accounts.forms import DepartmentAdminCreationForm
from .decorators import superadmin_required
import json

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

    context = {
        'total_complaints': total_complaints,
        'pending_complaints': pending_complaints,
        'in_progress_complaints': in_progress_complaints,
        'resolved_complaints': resolved_complaints,
        'total_users': total_users,
        'total_departments': total_departments,
        'recent_complaints': recent_complaints,
        'escalated_complaints': escalated_complaints,
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
        
        messages.success(request, f"Complaint #{pk} updated successfully.")
        return redirect('complaints_admin')
    return redirect('complaint_detail', pk=pk)

@superadmin_required
def departments_admin(request):
    departments = Department.objects.all()
    return render(request, 'dashboard/departments_admin.html', {'departments': departments})

from django.forms import modelform_factory
DepartmentForm = modelform_factory(Department, fields=['name', 'description', 'higher_authority_contact'])

@superadmin_required
def add_department(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Department added successfully.")
            return redirect('departments_admin')
    else:
        form = DepartmentForm()
    return render(request, 'dashboard/add_department.html', {'form': form})

@superadmin_required
def edit_department(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=dept)
        if form.is_valid():
            form.save()
            messages.success(request, "Department updated successfully.")
            return redirect('departments_admin')
    else:
        form = DepartmentForm(instance=dept)
    return render(request, 'dashboard/edit_department.html', {'form': form, 'department': dept})

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
        # The user wants to cleanup, so we delete even if complaints exist (they should be migrated or handled)
        # However, for safety, let's just delete the associations automatically by Django
        dept.delete()
        messages.success(request, f"Department '{name}' deleted successfully.")
    return redirect('departments_admin')
