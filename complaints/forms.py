from django import forms
from .models import Complaint

class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['title', 'description', 'location', 'image', 'priority']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'priority': forms.RadioSelect(choices=[('Normal', 'Normal'), ('Emergency', 'Emergency')])
        }
