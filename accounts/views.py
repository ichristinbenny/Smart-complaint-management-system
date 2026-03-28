from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import CitizenRegistrationForm

def register(request):
    if request.method == 'POST':
        form = CitizenRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home') # We need to create a home view
    else:
        form = CitizenRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

from django.contrib.auth.decorators import login_required

@login_required
def role_based_redirect(request):
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    if request.user.is_department_admin:
        return redirect('home')
    if hasattr(request.user, 'departmentstaff'):
        return redirect('staff_dashboard')
    return redirect('my_complaints')
