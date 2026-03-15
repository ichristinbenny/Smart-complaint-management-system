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
