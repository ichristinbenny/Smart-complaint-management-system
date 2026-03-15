from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from complaints.models import Department

class CitizenRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_citizen = True
        if commit:
            user.save()
        return user

class DepartmentAdminCreationForm(UserCreationForm):
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=True, empty_label="Select Department")

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'department']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_department_admin = True
        # The department is linked directly because of the ModelChoiceField matching the model field
        if commit:
            user.save()
        return user
