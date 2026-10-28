from allauth.account.forms import LoginForm, ResetPasswordForm, ResetPasswordKeyForm, SignupForm
from django import forms

from .models import User

# Style Tailwind « soft-brutalist » commun aux champs d'authentification
INPUT_CLASSES = (
    'w-full px-4 py-3 border-2 border-gray-200 rounded-xl bg-gray-50 focus:bg-white '
    'focus:border-gray-900 focus:ring-0 transition-colors font-medium text-gray-900'
)


# --- 1. Formulaire d'Inscription (Signup) ---
class CustomSignupForm(SignupForm):
    first_name = forms.CharField(label="Prénom", max_length=30, widget=forms.TextInput(attrs={'placeholder': 'Yanis'}))
    last_name = forms.CharField(label="Nom", max_length=30, widget=forms.TextInput(attrs={'placeholder': 'Ben...'}))
    gender = forms.ChoiceField(label="Sexe", choices=User.Gender.choices)
    birth_date = forms.DateField(label="Date de naissance", widget=forms.DateInput(attrs={'type': 'date'}))
    phone_number = forms.CharField(
        label="Téléphone", max_length=20, widget=forms.TextInput(attrs={'placeholder': '+213...'})
    )
    country = forms.ChoiceField(label="Pays", choices=User.Country.choices, initial=User.Country.ALGERIA)
    city = forms.CharField(label="Ville", max_length=100, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 1. Traduction Email
        if 'email' in self.fields:
            self.fields['email'].label = "Adresse e-mail"
            self.fields['email'].widget.attrs['placeholder'] = 'mon.email@exemple.com'

        # 2. NETTOYAGE RADICAL (La boucle magique)
        # On parcourt TOUS les champs du formulaire
        for field_name, field in self.fields.items():
            # Application du style Tailwind Soft-Brutalist
            field.widget.attrs.update({'class': f'{INPUT_CLASSES} mb-2'})

            # Si c'est un champ mot de passe (ou confirmation), on vide le texte d'aide
            if field_name in ['password', 'password_confirm', 'pass1', 'pass2']:
                field.help_text = ""  # Chaîne vide forcée
                field.widget.attrs.update({'placeholder': 'Votre mot de passe', 'autocomplete': 'new-password'})
                # On traduit les labels au passage
                if 'confirm' in field_name:
                    field.label = "Confirmer le mot de passe"
                else:
                    field.label = "Mot de passe"


# --- 2. Formulaire de Connexion (Login) ---
class CustomLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'login' in self.fields:
            self.fields['login'].label = "Adresse e-mail"
            self.fields['login'].widget.attrs.update(
                {
                    'placeholder': 'ex: yanis@gmail.com',
                    'class': f'{INPUT_CLASSES} mb-4',
                    'autofocus': 'autofocus',
                }
            )

        if 'password' in self.fields:
            self.fields['password'].label = "Mot de passe"
            self.fields['password'].help_text = None  # On enlève le texte d'aide au login aussi au cas où
            self.fields['password'].widget = forms.PasswordInput(
                attrs={
                    'placeholder': 'Votre mot de passe',
                    'class': f'{INPUT_CLASSES} mb-4',
                }
            )

        if 'remember' in self.fields:
            self.fields['remember'].label = "Se souvenir de moi"


# --- 3. Formulaire de Profil ---
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'avatar',
            'first_name',
            'last_name',
            'phone_number',
            'birth_date',
            'gender',
            'country',
            'city',
            'address',
        ]

        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'avatar': forms.FileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs.update(
                {
                    'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-xl bg-gray-50 focus:bg-white focus:border-gray-900 focus:ring-0 transition-colors font-medium text-gray-900'
                }
            )

        self.fields['avatar'].widget.attrs.update(
            {
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-bold file:bg-gray-100 file:text-gray-900 hover:file:bg-gray-200 cursor-pointer'
            }
        )


# --- 4. Formulaire "J'ai oublié mon mot de passe" (Email seul) ---
class CustomResetPasswordForm(ResetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # On applique le style Tailwind au champ Email
        if 'email' in self.fields:
            self.fields['email'].widget.attrs.update(
                {
                    'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-xl bg-gray-50 focus:bg-white focus:border-gray-900 focus:ring-0 transition-colors font-medium text-gray-900',
                    'placeholder': 'Entrez votre adresse e-mail',
                }
            )


# --- 5. Formulaire "Nouveau mot de passe" (Après clic sur le lien email) ---
class CustomResetPasswordKeyForm(ResetPasswordKeyForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # On nettoie tout (Texte d'aide + Style)
        for field_name, field in self.fields.items():
            # 1. Enlever le texte d'aide (Les règles 8 caractères, etc.)
            field.help_text = None

            # 2. Style Tailwind Soft-Brutalist
            field.widget.attrs.update({'class': f'{INPUT_CLASSES} mb-2'})

            # 3. Placeholder sympa
            if 'password' in field_name:
                field.widget.attrs['placeholder'] = 'Nouveau mot de passe'
                field.label = "Nouveau mot de passe"
