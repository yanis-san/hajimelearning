"""Préférences d'e-mails : catégories, lecture du choix de l'utilisateur, jetons de désabonnement signés."""

from django.core import signing
from django.urls import reverse

from config.emailing import absolute_url

from .models import NotificationPreference

ESSENTIAL = 'essential'

# Catégorie facultative → (champ du modèle, libellé affiché)
CATEGORIES = {
    'support': ('email_support', 'questions et réponses'),
    'progress': ('email_progress', 'progression et certificats'),
    'newsletter': ('email_newsletter', 'actualités'),
}

_SALT = 'notifications.unsubscribe'


def wants_email(user, category):
    """L'utilisateur accepte-t-il cette catégorie d'e-mails ? Les e-mails essentiels sont toujours envoyés."""
    if category == ESSENTIAL:
        return True
    field = CATEGORIES[category][0]
    default = NotificationPreference._meta.get_field(field).default
    preference = NotificationPreference.objects.filter(user=user).values_list(field, flat=True).first()
    return default if preference is None else preference


def set_preference(user, category, value):
    field = CATEGORIES[category][0]
    NotificationPreference.objects.update_or_create(user=user, defaults={field: value})


def unsubscribe_token(user, category):
    """Jeton signé (sans expiration : un lien de désabonnement doit toujours fonctionner)."""
    return signing.dumps({'user': user.pk, 'category': category}, salt=_SALT)


def read_unsubscribe_token(token):
    """(user_id, category) si le jeton est authentique, sinon None."""
    try:
        data = signing.loads(token, salt=_SALT)
    except signing.BadSignature:
        return None
    return (data['user'], data['category']) if data.get('category') in CATEGORIES else None


def unsubscribe_url(user, category):
    return absolute_url(reverse('unsubscribe', args=[unsubscribe_token(user, category)]))


def preferences_url():
    return absolute_url(reverse('notification_preferences'))
