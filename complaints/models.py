from django.db import models
from django.conf import settings
from django.utils import timezone

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    authority_name = models.CharField(max_length=150, blank=True, null=True)
    authority_phone = models.CharField(max_length=15, blank=True, null=True)
    authority_email = models.EmailField(blank=True, null=True)
    authority_designation = models.CharField(max_length=150, blank=True, null=True)
    higher_authority_name = models.CharField(max_length=150, blank=True, null=True)
    higher_authority_phone = models.CharField(max_length=15, blank=True, null=True)
    higher_authority_email = models.EmailField(blank=True, null=True)
    higher_authority_designation = models.CharField(max_length=150, blank=True, null=True)
    higher_authority_contact = models.TextField(help_text="Contact info for higher authority if complaint is overdue", blank=True, null=True)

    def __str__(self):
        return self.name

class Complaint(models.Model):
    PRIORITY_CHOICES = [
        ('Normal', 'Normal'),
        ('Emergency', 'Emergency (High Priority)'),
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Escalated', 'Escalated'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
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
        - Emergency: Escalates after 24 hours.
        - Normal: Escalates after 3 days.
        """
        now = timezone.now()
        time_passed = (now - self.created_at).total_seconds()
        should_escalate = False
        
        if self.status != 'Resolved':
            if self.priority == 'Emergency':
                if time_passed > 86400: # 24 hours
                    should_escalate = True
            else: # Normal
                if time_passed > 259200: # 3 days (3 * 86400)
                    should_escalate = True
        
        if should_escalate:
            updates = []
            if not self.is_escalated:
                self.is_escalated = True
                updates.append('is_escalated')
            if self.status != 'Escalated':
                self.status = 'Escalated'
                updates.append('status')
            
            if updates:
                self.save(update_fields=updates)

    @property
    def is_overdue(self):
        """Returns True if the complaint is considered escalated/overdue."""
        return self.status == 'Escalated' or self.is_escalated

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
