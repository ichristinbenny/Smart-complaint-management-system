from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    is_citizen = models.BooleanField(default=False)
    is_department_admin = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    department = models.ForeignKey('complaints.Department', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.username
