from django.contrib import admin
from .models import Department, Complaint

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

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
