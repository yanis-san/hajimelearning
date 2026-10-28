import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class SpecialCharacterValidator:
    """
    Valide que le mot de passe contient au moins un caractère spécial.
    """

    def validate(self, password, user=None):
        # Regex qui cherche n'importe quel symbole
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                _("Le mot de passe doit contenir au moins un caractère spécial (!@#$%)."),
                code='password_no_symbol',
            )

    def get_help_text(self):
        return _("Votre mot de passe doit contenir au moins un caractère spécial.")
