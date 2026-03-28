from django import forms
from django.contrib.auth import get_user_model
from .models import Complaint, DepartmentStaff

User = get_user_model()

class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['title', 'description', 'location', 'image', 'priority', 'latitude', 'longitude']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'priority': forms.RadioSelect(),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }

from django.db import transaction

class DepartmentStaffCreationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True, label="First Name")
    last_name = forms.CharField(max_length=30, required=True, label="Last Name")
    email = forms.EmailField(required=True, label="Email Address")
    phone = forms.CharField(max_length=15, required=False, label="Phone")
    username = forms.CharField(max_length=150, required=True, label="Username")
    password = forms.CharField(widget=forms.PasswordInput, required=True, label="Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=True, label="Confirm Password")

    field_order = ['first_name', 'last_name', 'email', 'phone', 'username', 'password', 'confirm_password']

    class Meta:
        model = DepartmentStaff
        fields = ['phone']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("A user with this username already exists.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")

        return cleaned_data

    def save(self, commit=True):
        with transaction.atomic():
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                email=self.cleaned_data['email'],
                password=self.cleaned_data['password'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name']
            )
            staff = super().save(commit=False)
            staff.user = user
            if commit:
                staff.save()
            return staff

class DepartmentStaffEditForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True, label="Username", widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    first_name = forms.CharField(max_length=30, required=True, label="First Name")
    last_name = forms.CharField(max_length=30, required=True, label="Last Name")
    email = forms.EmailField(required=True, label="Email Address", widget=forms.TextInput(attrs={'readonly': 'readonly'}))

    field_order = ['username', 'first_name', 'last_name', 'email', 'phone']

    class Meta:
        model = DepartmentStaff
        fields = ['phone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.user:
            self.initial['username'] = self.instance.user.username
            self.initial['first_name'] = self.instance.user.first_name
            self.initial['last_name'] = self.instance.user.last_name
            self.initial['email'] = self.instance.user.email

    def save(self, commit=True):
        staff = super().save(commit=False)
        if hasattr(self, 'cleaned_data'):
            staff.user.first_name = self.cleaned_data['first_name']
            staff.user.last_name = self.cleaned_data['last_name']
            staff.user.save()
        if commit:
            staff.save()
        return staff
