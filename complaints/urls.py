from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('submit/', views.submit_complaint, name='submit_complaint'),
    path('success/', views.complaint_success, name='complaint_success'),
    path('my/', views.my_complaints, name='my_complaints'),
    path('detail/<int:pk>/', views.complaint_detail, name='complaint_detail'),
    path('detail/<int:pk>/update-status/', views.update_complaint_status, name='update_complaint_status'),
    path('detail/<int:pk>/assign-staff/', views.assign_staff, name='assign_staff'),
    path('detail/<int:pk>/staff-update/', views.staff_update_complaint, name='staff_update_complaint'),
    path('department/dashboard/', views.department_dashboard, name='department_dashboard'),
    path('department/manage/', views.department_complaints, name='department_complaints'),
    path('department/staff/', views.dept_manage_staff, name='dept_manage_staff'),
    path('department/staff/add/', views.dept_add_staff, name='dept_add_staff'),
    path('department/staff/<int:pk>/edit/', views.dept_edit_staff, name='dept_edit_staff'),
    path('department/staff/<int:pk>/delete/', views.dept_delete_staff, name='dept_delete_staff'),
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('notifications/read-all/', views.mark_notifications_read, name='mark_notifications_read'),
    path('ai-chat/', views.ai_chatbot, name='ai_chatbot'),
]
