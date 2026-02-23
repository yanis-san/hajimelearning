from django import forms

from .models import ContactMessage, ContactReason


class ContactForm(forms.ModelForm):
    class Meta:
        model  = ContactMessage
        fields = ['first_name', 'last_name', 'email', 'reason', 'message']
        labels = {
            'first_name': 'Prénom',
            'last_name':  'Nom',
            'email':      'Adresse email',
            'reason':     'Motif de contact',
            'message':    'Votre message',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'Votre prénom'}),
            'last_name':  forms.TextInput(attrs={'placeholder': 'Votre nom'}),
            'email':      forms.EmailInput(attrs={'placeholder': 'vous@example.com'}),
            'message':    forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Décrivez votre demande en détail...',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ne proposer que les motifs actifs
        self.fields['reason'].queryset = ContactReason.objects.filter(is_active=True)
        self.fields['reason'].empty_label = "— Choisissez un motif —"
        self.fields['reason'].required = True
