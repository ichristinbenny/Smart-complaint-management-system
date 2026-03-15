from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    
    # User Management
    path('users/', views.manage_users, name='manage_users'),
    path('admins/', views.manage_admins, name='manage_admins'),
    path('admins/add/', views.add_admin, name='add_admin'),
    path('users/toggle-status/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    
    # Complaint Management
    path('complaints/', views.complaints_admin, name='complaints_admin'),
    path('complaints/update/<int:pk>/', views.admin_update_complaint, name='admin_update_complaint'),
    path('complaints/delete/<int:pk>/', views.delete_complaint, name='delete_complaint'),
    path('complaints/bulk-delete/', views.bulk_delete_complaints, name='bulk_delete_complaints'),
    
    # Department Management
    path('departments/', views.departments_admin, name='departments_admin'),
    path('departments/add/', views.add_department, name='add_department'),
    path('departments/edit/<int:pk>/', views.edit_department, name='edit_department'),
    path('departments/delete/<int:pk>/', views.delete_department, name='delete_department'),
    
    # Authority & Settings
    path('authorities/', views.authorities_admin, name='authorities_admin'),
    path('settings/', views.settings_admin, name='settings_admin'),
]
