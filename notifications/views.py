from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Notification

# Valeurs autorisées pour le filtre ?type=
_VALID_TYPES = {Notification.TYPE_STUDENT, Notification.TYPE_INSTRUCTOR}


def _notifications_for(user, type_filter=None):
    """Notifications de l'utilisateur (récentes d'abord), éventuellement filtrées par espace."""
    qs = Notification.objects.filter(recipient=user)
    if type_filter:
        qs = qs.filter(notification_type=type_filter)
    return qs.order_by('-created_at')


def _clean_type(value):
    return value if value in _VALID_TYPES else None


def _unread_student_count(user):
    """Notifications étudiant non lues (badge de la cloche)."""
    return Notification.objects.filter(
        recipient=user, is_read=False, notification_type=Notification.TYPE_STUDENT
    ).count()


@login_required
def my_notifications(request):
    """Liste complète des notifications ; filtre ?type=student|instructor."""
    type_filter = _clean_type(request.GET.get('type'))
    profile = getattr(request.user, 'instructor_profile', None)

    return render(
        request,
        'notifications/list.html',
        {
            'notifications': _notifications_for(request.user, type_filter),
            'current_type': type_filter,
            'is_instructor': bool(profile and profile.is_active),
        },
    )


@login_required
@require_POST
def mark_read_and_redirect(request, notification_id):
    """Marque une notification lue puis redirige vers sa cible."""
    notif = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    if not notif.is_read:
        notif.is_read = True
        notif.save(update_fields=['is_read'])
    return redirect(notif.link)


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """Marque une notification lue (HTMX) et met à jour le badge."""
    notif = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    if not notif.is_read:
        notif.is_read = True
        notif.save(update_fields=['is_read'])

    return render(
        request,
        'notifications/partials/read_response.html',
        {
            'notif': notif,
            'is_dropdown': request.headers.get('X-Source') == 'dropdown',
            'unread_count': _unread_student_count(request.user),
        },
    )


@login_required
@require_POST
def mark_all_read(request):
    """
    Marque tout comme lu d'un coup.

    Un champ POST `type` (student|instructor) restreint l'opération à un espace.
    """
    type_filter = _clean_type(request.POST.get('type'))

    unread = Notification.objects.filter(recipient=request.user, is_read=False)
    if type_filter:
        unread = unread.filter(notification_type=type_filter)
    unread.update(is_read=True)

    if not getattr(request, 'htmx', False):
        return redirect('my_notifications')

    notifs = _notifications_for(request.user, type_filter)
    is_dropdown = request.headers.get('X-Source') == 'dropdown'
    return render(
        request,
        'notifications/partials/read_response.html',
        {
            'notifications': notifs[:10] if is_dropdown else notifs,
            'is_dropdown': is_dropdown,
            'unread_count': _unread_student_count(request.user),
        },
    )
