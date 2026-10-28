"""Limitation de débit minimale basée sur le cache Django (compteur à fenêtre fixe)."""

from django.core.cache import cache


def client_identifier(request):
    """Identifiant stable du client : l'utilisateur connecté, sinon son adresse IP."""
    user = getattr(request, 'user', None)
    if user is not None and user.is_authenticated:
        return f'user:{user.pk}'
    return f'ip:{request.META.get("REMOTE_ADDR", "unknown")}'


def allow(request, scope, limit, window):
    """
    Enregistre une tentative et indique si elle est autorisée.

    `scope` nomme l'action limitée, `limit` le nombre de tentatives tolérées
    par fenêtre de `window` secondes pour un même client.
    """
    key = f'throttle:{scope}:{client_identifier(request)}'
    cache.add(key, 0, timeout=window)
    try:
        attempts = cache.incr(key)
    except ValueError:  # clé expirée entre add() et incr()
        cache.set(key, 1, timeout=window)
        attempts = 1
    return attempts <= limit
