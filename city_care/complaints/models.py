from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    higher_authority_contact = models.TextField(help_text="Contact info for higher authority if complaint is overdue")

    def __str__(self):
        return self.name
