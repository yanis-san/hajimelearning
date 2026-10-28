from django import forms

from .models import NotificationPreference


class NotificationPreferenceForm(forms.ModelForm):
    class Meta:
        model = NotificationPreference
        fields = ['email_support', 'email_progress', 'email_newsletter']
