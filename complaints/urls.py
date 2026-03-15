from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('submit/', views.submit_complaint, name='submit_complaint'),
    path('success/', views.complaint_success, name='complaint_success'),
    path('my/', views.my_complaints, name='my_complaints'),
    path('detail/<int:pk>/', views.complaint_detail, name='complaint_detail'),
    path('detail/<int:pk>/update-status/', views.update_complaint_status, name='update_complaint_status'),
    path('department/manage/', views.department_complaints, name='department_complaints'),
    path('notifications/read-all/', views.mark_notifications_read, name='mark_notifications_read'),
    path('ai-chat/', views.ai_chatbot, name='ai_chatbot'),
]
