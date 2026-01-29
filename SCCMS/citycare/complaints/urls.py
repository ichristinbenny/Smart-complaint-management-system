from django.urls import path
from . import views

urlpatterns = [
    path("add/", views.add_complaint, name="add_complaint"),
    path("success/", views.success, name="success"),
]
