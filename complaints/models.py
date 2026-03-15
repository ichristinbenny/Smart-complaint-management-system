from django.db import models
from django.conf import settings
from django.utils import timezone

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    higher_authority_contact = models.TextField(help_text="Contact info for higher authority if complaint is overdue")

    def __str__(self):
        return self.name

class Complaint(models.Model):
    PRIORITY_CHOICES = [
        ('Normal', 'Normal'),
        ('Emergency', 'Emergency (High Priority)'),
        ('Escalated', 'Escalated'),
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=255)
    image = models.ImageField(upload_to='complaints/', blank=True, null=True)
    departments = models.ManyToManyField(Department, blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Normal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    is_escalated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def update_escalation_status(self):
        """
        Evaluates and updates the complaint's escalation/overdue status based on time passed.
        This provides a single source of truth for all views (citizen, department admin, superadmin).
        """
        now = timezone.now()
        was_escalated = self.is_escalated
        
        if self.status != 'Resolved':
            if self.priority == 'Emergency':
                # Escalate emergency after 24 hours
                if (now - self.created_at).total_seconds() > 86400:
                    self.is_escalated = True
        
        if self.is_escalated != was_escalated:
            self.save(update_fields=['is_escalated'])

    @property
    def is_overdue(self):
        """Returns True if the complaint is older than 7 days and not resolved."""
        if self.status != 'Resolved' and self.priority != 'Emergency':
            return (timezone.now() - self.created_at).days > 7
        return False

    def __str__(self):
        return f"{self.title} - {self.status}"

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, null=True, blank=True)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"To {self.user.username}: {self.message}"
