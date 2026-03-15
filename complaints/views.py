from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.http import require_POST
from .models import Complaint, Department, Notification
from .forms import ComplaintForm
from .ml_utils import predict_department
from django.utils import timezone

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
                        message=f"New complaint received: {complaint.title}"
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
    return render(request, 'complaints/complaint_detail.html', {'complaint': c})

@login_required
@require_POST
def update_complaint_status(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)

    if not request.user.is_department_admin:
        return HttpResponseForbidden("You are not authorized to perform this action.")

    new_status = request.POST.get('status')
    if new_status and complaint.status != new_status:
        complaint.status = new_status
        complaint.save()
        Notification.objects.create(
            user=complaint.user,
            complaint=complaint,
            message=f"Status updated to '{new_status}' for your complaint: {complaint.title}"
        )

    return redirect('complaint_detail', pk=pk)

def is_dept_admin(user):
    return user.is_authenticated and user.is_department_admin

@login_required
def department_complaints(request):
    if not request.user.is_department_admin:
        return HttpResponseForbidden("You are not authorized to access this page.")

    dept = request.user.department
    if not dept:
        messages.error(
            request,
            "Your account is not assigned to any department yet. Please contact a superadmin to assign a department.",
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
                message=f"Status updated to '{new_status}' for your complaint: {c.title}"
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
            "reply": "Hi! You can ask me things like:\n"
                     "- status 3 (check complaint ID 3)\n"
                     "- Street light is not working\n"
                     "- How do I report a complaint?"
        })

    lower = message.lower()

    # Help / greeting
    if any(word in lower for word in ["hi", "hello", "help", "how to report"]):
        return JsonResponse({
            "reply": (
                "I'm City Care Assistant.\n\n"
                "- To check a complaint status, type: status <complaint_id>\n"
                "- To get help choosing a department, just describe your issue.\n"
                "- Example: 'Garbage not collected for 3 days'."
            )
        })

    # Complaint status: expect format "status <id>"
    if lower.startswith("status"):
        parts = lower.split()
        if len(parts) < 2:
            return JsonResponse({
                "reply": "Please provide a complaint ID. Example: status 5"
            })
        try:
            c_id = int(parts[1])
        except ValueError:
            return JsonResponse({
                "reply": "Complaint ID should be a number. Example: status 5"
            })

        try:
            complaint = Complaint.objects.get(pk=c_id, user=request.user)
        except Complaint.DoesNotExist:
            return JsonResponse({
                "reply": "I couldn't find a complaint with that ID under your account."
            })

        dept_qs = complaint.departments.all()
        dept_names = ", ".join([d.name for d in dept_qs]) if dept_qs.exists() else "Unassigned"
        return JsonResponse({
            "reply": (
                f"Complaint ID {complaint.id} – \"{complaint.title}\"\n"
                f"Department(s): {dept_names}\n"
                f"Status: {complaint.status}\n"
                f"Priority: {complaint.priority}"
            )
        })

    # FAQs: simple keyword-based answers
    if "how" in lower and "complaint" in lower:
        return JsonResponse({
            "reply": (
                "To report a complaint:\n"
                "1) Click 'Submit Complaint' in the top menu.\n"
                "2) Describe the issue clearly.\n"
                "3) Add location and an image if possible.\n"
                "4) Submit – we'll route it to the right department."
            )
        })

    if "which department" in lower or "who handles" in lower:
        return JsonResponse({
            "reply": (
                "Examples:\n"
                "- Electricity: street lights, power cuts.\n"
                "- Water Supply Department: water leakage, no water.\n"
                "- Road & Transport Department: potholes, damaged roads.\n"
                "- Garbage Department: trash not collected."
            )
        })

    # Free-text issue description -> suggest department(s) using existing ML helper
    depts = predict_department(message)
    if depts:
        names = ", ".join([d.name for d in depts])
        return JsonResponse({
            "reply": (
                f"It looks like this issue belongs to the following department(s): {names}.\n"
                "You can click 'Submit Complaint' and describe the issue in detail."
            )
        })

    # Fallback
    return JsonResponse({
        "reply": (
            "I'm not fully sure which department this belongs to.\n"
            "Please go to 'Submit Complaint' and provide more details – "
            "our team will route it to the correct department."
        )
    })
