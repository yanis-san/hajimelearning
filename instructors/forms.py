from django import forms

from .models import InstructorRequest


class InstructorRequestForm(forms.ModelForm):
    class Meta:
        model = InstructorRequest
        fields = ['payment_proof']
