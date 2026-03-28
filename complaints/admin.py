from django.contrib import admin
from .models import Department, Complaint, DepartmentStaff

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

@admin.register(DepartmentStaff)
class DepartmentStaffAdmin(admin.ModelAdmin):
    list_display = ('get_name', 'get_email', 'department', 'phone', 'created_at')
    list_filter = ('department',)
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'user__username')

    def get_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_name.short_description = 'Name'

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'get_departments', 'status', 'priority', 'is_escalated', 'created_at')
    list_filter = ('status', 'priority', 'departments', 'is_escalated')
    search_fields = ('title', 'description', 'location')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'

    def get_departments(self, obj):
        return ", ".join([d.name for d in obj.departments.all()])
    get_departments.short_description = 'Departments'
