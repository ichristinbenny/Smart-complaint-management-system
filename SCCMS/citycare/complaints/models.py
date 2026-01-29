from django.db import models
from django.contrib.auth.models import User


class Department(models.Model):
    name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=15)
    email = models.EmailField()

    def __str__(self):
        return self.name


class Complaint(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True
    )
    status = models.CharField(max_length=50, default="Submitted")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class DepartmentAdmin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username
