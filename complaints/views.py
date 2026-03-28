from django.shortcuts import render, redirect, get_object_or_404

from django.contrib.auth.decorators import login_required, user_passes_test

from django.contrib import messages

from django.http import HttpResponseForbidden, JsonResponse

from django.views.decorators.http import require_POST

from .models import Complaint, Department, Notification, DepartmentStaff

from django.forms import modelform_factory

from .forms import ComplaintForm

from .ml_utils import predict_department

from django.utils import timezone

from django.utils.translation import gettext as _



def home(request):

    return render(request, 'home.html')



@login_required

def submit_complaint(request):

    if request.method == 'POST':

        form = ComplaintForm(request.POST, request.FILES)

        if form.is_valid():

            complaint = form.save(commit=False)

            complaint.user = request.user

            complaint.save()  # save first to get PK for M2M



            # ML Classification -> may map to one or more departments (ManyToMany)

            depts = predict_department(complaint.description)

            if depts:

                complaint.departments.set(depts)



            # Emergency logic

            if complaint.priority == 'Emergency':

                # Logic to flag escalation if needed (handled by background task usually, but here we just mark priority)

                pass



            # Notify department admins for all mapped departments

            if depts:

                from accounts.models import User

                admins = User.objects.filter(

                    is_department_admin=True,

                    department__in=depts,

                ).distinct()

                for admin in admins:

                    Notification.objects.create(

                        user=admin,

                        complaint=complaint,

                        message=_("New complaint received: %(title)s") % {'title': complaint.title}

                    )



            return redirect('complaint_success')

    else:

        form = ComplaintForm()

    return render(request, 'complaints/complaint_form.html', {'form': form})



@login_required

def complaint_success(request):

    return render(request, 'complaints/complaint_success.html')



@login_required

def my_complaints(request):

    complaints = Complaint.objects.filter(user=request.user).order_by('-created_at')

    

    # Update status logic centrally

    for c in complaints:

        c.update_escalation_status()



        # Flag if there are any unread notifications for this complaint for the current user

        c.has_unread_notifications = Notification.objects.filter(

            user=request.user, complaint=c, is_read=False

        ).exists()



    return render(request, 'complaints/my_complaints.html', {'complaints': complaints})



@login_required

def complaint_detail(request, pk):

    c = get_object_or_404(Complaint, pk=pk)

    

    c.update_escalation_status()



    context = {'complaint': c}



    # For dept admins: provide available staff for the assignment dropdown

    if request.user.is_department_admin and request.user.department:

        dept = request.user.department

        base_token = (dept.name or "").split()[0]

        related_depts = Department.objects.filter(name__icontains=base_token)

        context['available_staff'] = DepartmentStaff.objects.filter(department__in=related_depts)



    # Check if current user is a department staff member
    context['is_staff_user'] = hasattr(request.user, 'departmentstaff')



    return render(request, 'complaints/complaint_detail.html', context)



@login_required

@require_POST

def update_complaint_status(request, pk):

    complaint = get_object_or_404(Complaint, pk=pk)



    if not request.user.is_department_admin:

        return HttpResponseForbidden(_("You are not authorized to perform this action."))



    new_status = request.POST.get('status')

    if new_status and complaint.status != new_status:

        complaint.status = new_status

        complaint.save()

        Notification.objects.create(

            user=complaint.user,

            complaint=complaint,

            message=_("Status updated to '%(status)s' for your complaint: %(title)s") % {'status': new_status, 'title': complaint.title}

        )



    return redirect('complaint_detail', pk=pk)



def is_dept_admin(user):

    return user.is_authenticated and user.is_department_admin



@login_required

def department_complaints(request):

    if not request.user.is_department_admin:

        return HttpResponseForbidden(_("You are not authorized to access this page."))



    dept = request.user.department

    if not dept:

        messages.error(

            request,

            _("Your account is not assigned to any department yet. Please contact a superadmin to assign a department."),

        )

        return render(

            request,

            'complaints/department_complaints.html',

            {'complaints': [], 'department': None},

        )



    # Some databases have multiple department rows like 'Garbage' and

    # 'Garbage Department'. Treat all variants that share the main keyword

    # with the admin's department as equivalent for routing complaints.

    base_token = (dept.name or "").split()[0]  # e.g. 'Garbage', 'Water'

    related_depts = Department.objects.filter(name__icontains=base_token)



    complaints = (

        Complaint.objects

        .filter(departments__in=related_depts)

        .order_by('-created_at')

        .distinct()

    )



    # Ensure escalations are checked whenever Dept Admin pulls the list

    for c in complaints:

        c.update_escalation_status()



    # Handle status update

    if request.method == 'POST':

        c_id = request.POST.get('complaint_id')

        new_status = request.POST.get('status')

        new_priority = request.POST.get('priority')



        c = get_object_or_404(Complaint, pk=c_id, departments__in=related_depts)

        status_changed = False

        if new_status and c.status != new_status:

            c.status = new_status

            status_changed = True

        if new_priority:

            c.priority = new_priority

        c.save()



        if status_changed:

            Notification.objects.create(

                user=c.user,

                complaint=c,

                message=_("Status updated to '%(status)s' for your complaint: %(title)s") % {'status': new_status, 'title': c.title}

            )



        return redirect('department_complaints')



    return render(request, 'complaints/department_complaints.html', {'complaints': complaints, 'department': dept})





@login_required

def mark_notifications_read(request):

    """

    Mark all notifications for the current user as read, then redirect back.

    """

    if request.user.is_authenticated:

        request.user.notifications.filter(is_read=False).update(is_read=True)



    redirect_to = request.META.get('HTTP_REFERER') or 'home'

    return redirect(redirect_to)





@login_required

@require_POST

def ai_chatbot(request):

    """

    Simple AI-like helper endpoint for the floating chatbot.

    Supports:

    - help / hello

    - status <id>  (complaint status)

    - free-text issue description -> suggest department

    """

    message = (request.POST.get('message') or '').strip()

    if not message:

        return JsonResponse({

            "reply": _("Hi! You can ask me things like:\n"

                     "- status 3 (check complaint ID 3)\n"

                     "- Street light is not working\n"

                     "- How do I report a complaint?")

        })



    lower = message.lower()



    # Help / greeting

    if any(word in lower for word in ["hi", "hello", "help", "how to report"]):

        return JsonResponse({

            "reply": (

                _("I'm City Care Assistant.\n\n"

                "- To check a complaint status, type: status <complaint_id>\n"

                "- To get help choosing a department, just describe your issue.\n"

                "- Example: 'Garbage not collected for 3 days'.")

            )

        })



    # Complaint status: expect format "status <id>"

    if lower.startswith("status"):

        parts = lower.split()

        if len(parts) < 2:

            return JsonResponse({

                "reply": _("Please provide a complaint ID. Example: status 5")

            })

        try:

            c_id = int(parts[1])

        except ValueError:

            return JsonResponse({

                "reply": _("Complaint ID should be a number. Example: status 5")

            })



        try:

            complaint = Complaint.objects.get(pk=c_id, user=request.user)

        except Complaint.DoesNotExist:

            return JsonResponse({

                "reply": _("I couldn't find a complaint with that ID under your account.")

            })



        dept_qs = complaint.departments.all()

        dept_names = ", ".join([d.name for d in dept_qs]) if dept_qs.exists() else "Unassigned"

        return JsonResponse({

            "reply": (

                _("Complaint ID %(id)s – \"%(title)s\"\n"

                "Department(s): %(dept_names)s\n"

                "Status: %(status)s\n"

                "Priority: %(priority)s") % {

                    'id': complaint.id,

                    'title': complaint.title,

                    'dept_names': dept_names,

                    'status': complaint.status,

                    'priority': complaint.priority

                }

            )

        })



    # FAQs: simple keyword-based answers

    if "how" in lower and "complaint" in lower:

        return JsonResponse({

            "reply": (

                _("To report a complaint:\n"

                "1) Click 'Submit Complaint' in the top menu.\n"

                "2) Describe the issue clearly.\n"

                "3) Add location and an image if possible.\n"

                "4) Submit – we'll route it to the right department.")

            )

        })



    if "which department" in lower or "who handles" in lower:

        return JsonResponse({

            "reply": (

                _("Examples:\n"

                "- Electricity: street lights, power cuts.\n"

                "- Water Supply Department: water leakage, no water.\n"

                "- Road & Transport Department: potholes, damaged roads.\n"

                "- Garbage Department: trash not collected.")

            )

        })



    # Free-text issue description -> suggest department(s) using existing ML helper

    depts = predict_department(message)

    if depts:

        names = ", ".join([d.name for d in depts])

        return JsonResponse({

            "reply": (

                _("It looks like this issue belongs to the following department(s): %(names)s.\n"

                "You can click 'Submit Complaint' and describe the issue in detail.") % {'names': names}

            )

        })



    # Fallback

    return JsonResponse({

        "reply": (

            _("I'm not fully sure which department this belongs to.\n"

            "Please go to 'Submit Complaint' and provide more details – "

            "our team will route it to the correct department.")

        )

    })







# --- Staff Assignment (by Dept Admin) ----------------------------------------







@login_required



@require_POST



def assign_staff(request, pk):



    if not request.user.is_department_admin:



        return HttpResponseForbidden(_("You are not authorized to perform this action."))







    complaint = get_object_or_404(Complaint, pk=pk)



    staff_id = request.POST.get('staff_id')



    if not staff_id:



        messages.error(request, _("Please select a staff member."))



        return redirect('complaint_detail', pk=pk)







    staff = get_object_or_404(DepartmentStaff, pk=staff_id)







    # Ensure staff belongs to admin's department



    dept = request.user.department



    if dept:



        base_token = (dept.name or "").split()[0]



        if base_token.lower() not in staff.department.name.lower():



            messages.error(request, _("You can only assign staff from your own department."))



            return redirect('complaint_detail', pk=pk)







    old_staff = complaint.assigned_staff



    complaint.assigned_staff = staff



    complaint.save(update_fields=['assigned_staff'])







    # Notify assigned staff (find the User with matching email)



    from accounts.models import User



    su = staff.user
    for su in [su]:



        Notification.objects.create(



            user=su,



            complaint=complaint,



            message=_("You have been assigned to complaint #%(pk)s: %(title)s") % {'pk': complaint.pk, 'title': complaint.title}



        )







    action = _("reassigned") if old_staff else _("assigned")



    messages.success(request, _("Staff %(action)s successfully.") % {'action': action})



    return redirect('complaint_detail', pk=pk)











# --- Staff Dashboard ---------------------------------------------------------







@login_required



def staff_dashboard(request):



    staff = getattr(request.user, "departmentstaff", None)
    if not staff:



        return HttpResponseForbidden(_("You are not registered as department staff."))







    complaints = (



        Complaint.objects



        .filter(assigned_staff=request.user.departmentstaff)



        .order_by('-created_at')



    )







    for c in complaints:



        c.update_escalation_status()







    return render(request, 'complaints/staff_dashboard.html', {



        'complaints': complaints,



        'staff': request.user.departmentstaff,



    })











# --- Staff Update Complaint --------------------------------------------------







@login_required



@require_POST



def staff_update_complaint(request, pk):



    staff = getattr(request.user, "departmentstaff", None)
    if not staff:



        return HttpResponseForbidden(_("You are not registered as department staff."))







    complaint = get_object_or_404(Complaint, pk=pk, assigned_staff=request.user.departmentstaff)







    new_status = request.POST.get('status')



    remarks = request.POST.get('remarks', '').strip()







    ALLOWED_STATUSES = ['In Progress', 'Resolved']



    update_fields = []







    if new_status and new_status in ALLOWED_STATUSES and complaint.status != new_status:



        complaint.status = new_status



        update_fields.append('status')







    if remarks:



        complaint.staff_remarks = remarks



        update_fields.append('staff_remarks')







    if update_fields:



        complaint.save(update_fields=update_fields)







        # Notify the department admin



        from accounts.models import User



        dept = complaint.assigned_staff.department



        base_token = (dept.name or "").split()[0]



        dept_admins = User.objects.filter(



            is_department_admin=True,



        ).filter(



            department__name__icontains=base_token



        ).distinct()







        for admin_user in dept_admins:



            parts = []



            if 'status' in update_fields:



                parts.append(_("status updated to %(status)s") % {'status': new_status})



            if 'staff_remarks' in update_fields:



                parts.append(_("new remarks added"))



            Notification.objects.create(



                user=admin_user,



                complaint=complaint,



                message=_("Staff updated complaint #%(pk)s: %(updates)s") % {'pk': complaint.pk, 'updates': ', '.join(parts)}



            )







        messages.success(request, _("Complaint updated successfully."))



    else:



        messages.info(request, _("No changes were made."))







    return redirect('staff_dashboard')











# --- Dept Admin: Staff Management (scoped to own department) ------------------







from .forms import DepartmentStaffCreationForm, DepartmentStaffEditForm











@login_required



def dept_manage_staff(request):



    if not request.user.is_department_admin:



        return HttpResponseForbidden(_("You are not authorized to access this page."))



    dept = request.user.department



    if not dept:



        messages.error(request, _("Your account is not assigned to any department."))



        return render(request, 'complaints/dept_manage_staff.html', {'staff_list': [], 'department': None})







    base_token = (dept.name or "").split()[0]



    related_depts = Department.objects.filter(name__icontains=base_token)



    staff_list = DepartmentStaff.objects.filter(department__in=related_depts)



    return render(request, 'complaints/dept_manage_staff.html', {'staff_list': staff_list, 'department': dept})











@login_required



def dept_add_staff(request):



    if not request.user.is_department_admin:



        return HttpResponseForbidden(_("You are not authorized to access this page."))



    dept = request.user.department



    if not dept:



        return redirect('dept_manage_staff')







    if request.method == 'POST':



        form = DepartmentStaffCreationForm(request.POST)



        if form.is_valid():
            from django.db import transaction
            with transaction.atomic():
                staff = form.save(commit=False)
                staff.department = dept
                staff.save()



            messages.success(request, _("Staff member added successfully."))



            return redirect('dept_manage_staff')



    else:



        form = DepartmentStaffCreationForm()



    return render(request, 'complaints/dept_add_staff.html', {'form': form, 'department': dept})











@login_required



def dept_edit_staff(request, pk):



    if not request.user.is_department_admin:



        return HttpResponseForbidden(_("You are not authorized to access this page."))



    dept = request.user.department



    base_token = (dept.name or "").split()[0] if dept else ''



    related_depts = Department.objects.filter(name__icontains=base_token) if base_token else Department.objects.none()



    staff = get_object_or_404(DepartmentStaff, pk=pk, department__in=related_depts)







    if request.method == 'POST':



        form = DepartmentStaffEditForm(request.POST, instance=staff)



        if form.is_valid():



            form.save()



            messages.success(request, _("Staff member updated successfully."))



            return redirect('dept_manage_staff')



    else:



        form = DepartmentStaffEditForm(instance=staff)



    return render(request, 'complaints/dept_edit_staff.html', {'form': form, 'staff': staff, 'department': dept})











@login_required



@require_POST



def dept_delete_staff(request, pk):



    if not request.user.is_department_admin:



        return HttpResponseForbidden(_("You are not authorized to access this page."))



    dept = request.user.department



    base_token = (dept.name or "").split()[0] if dept else ''



    related_depts = Department.objects.filter(name__icontains=base_token) if base_token else Department.objects.none()



    staff = get_object_or_404(DepartmentStaff, pk=pk, department__in=related_depts)



    name = staff.user.get_full_name() or staff.user.username
    user = staff.user
    staff.delete()
    if user:
        user.delete()



    messages.success(request, _("Staff member '%(name)s' deleted.") % {'name': name})



    return redirect('dept_manage_staff')









@login_required
def department_dashboard(request):
    if not request.user.is_department_admin:
        return HttpResponseForbidden(_("You are not authorized to access this page."))
    
    dept = request.user.department
    if not dept:
        # Fallback if no department assigned
        return render(request, 'complaints/department_dashboard.html', {'error': _('No department assigned.')})
    
    base_token = (dept.name or "").split()[0]
    related_depts = Department.objects.filter(name__icontains=base_token)
    
    complaints = Complaint.objects.filter(departments__in=related_depts).distinct()
    staff_count = DepartmentStaff.objects.filter(department__in=related_depts).count()
    
    context = {
        'department': dept,
        'total_complaints': complaints.count(),
        'pending': complaints.filter(status='pending').count(),
        'in_progress': complaints.filter(status='in_progress').count(),
        'resolved': complaints.filter(status='resolved').count(),
        'staff_count': staff_count,
        'recent_complaints': complaints.order_by('-created_at')[:5],
    }
    return render(request, 'complaints/department_dashboard.html', context)

