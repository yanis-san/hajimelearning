from django import forms

from .models import AccessRequest

TAILWIND_INPUT = 'w-full px-4 py-2.5 border border-gray-300 rounded-xl bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-orange-400 focus:border-transparent transition text-sm'
TAILWIND_FILE = 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-orange-50 file:text-orange-700 hover:file:bg-orange-100'


class AccessRequestForm(forms.ModelForm):
    class Meta:
        model = AccessRequest
        fields = ['payment_proof']
        widgets = {
            'payment_proof': forms.FileInput(
                attrs={
                    'accept': 'image/*',
                    'class': TAILWIND_FILE,
                }
            )
        }
        labels = {'payment_proof': 'Reçu de paiement (Photo/Capture d\'écran)'}


class CodeActivationForm(forms.Form):
    code = forms.CharField(
        max_length=50,
        label="Code d'activation",
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Ex: CODE-PROMO-2025',
                'class': TAILWIND_INPUT,
            }
        ),
    )
