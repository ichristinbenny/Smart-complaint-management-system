from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'is_citizen', 'is_department_admin', 'department', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('is_citizen', 'is_department_admin', 'department')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('is_citizen', 'is_department_admin', 'department')}),
    )

admin.site.register(User, CustomUserAdmin)
