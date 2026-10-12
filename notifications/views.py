from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.template.loader import render_to_string
from .models import Notification

# Valeurs autorisées pour le filtre ?type=
_VALID_TYPES = {Notification.TYPE_STUDENT, Notification.TYPE_INSTRUCTOR}


@login_required
def my_notifications(request):
    """Affiche la liste complète des notifications (page dédiée).

    Supporte le filtre ?type=student|instructor pour n'afficher
    que les notifications d'un espace donné.
    """
    type_filter = request.GET.get('type')
    if type_filter not in _VALID_TYPES:
        type_filter = None  # "Tout"

    base_qs = Notification.objects.filter(recipient=request.user)
    if type_filter:
        notifs = base_qs.filter(notification_type=type_filter).order_by('-created_at')
    else:
        notifs = base_qs.order_by('-created_at')

    is_instructor = False
    try:
        is_instructor = request.user.instructor_profile.is_active
    except Exception:
        pass

    return render(request, 'notifications/list.html', {
        'notifications': notifs,
        'current_type': type_filter,
        'is_instructor': is_instructor,
    })

@login_required
def mark_read_and_redirect(request, notification_id):
    """ 
    ANCIENNE MÉTHODE (Fallback) :
    Clic sur la cloche -> Marque lu -> Redirige (Rechargement de page complet)
    Utile si le JS est désactivé ou pour les liens dans les emails.
    """
    notif = get_object_or_404(Notification, id=notification_id)
    
    if notif.recipient == request.user:
        if not notif.is_read:
            notif.is_read = True
            notif.save()
        return redirect(notif.link)
    
    return redirect('user_dashboard')

# --- NOUVELLE VUE POUR HTMX + ALPINE ---

@login_required
@require_POST
def mark_notification_read(request, notification_id):
    notif = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    
    # On marque uniquement comme lu (pas de toggle)
    if not notif.is_read:
        notif.is_read = True
        notif.save()

    # Recalcul du compteur pour le badge (uniquement notifs étudiant → cloche)
    unread_count = request.user.notifications.filter(
        is_read=False,
        notification_type=Notification.TYPE_STUDENT,
    ).count()

    # Mise à jour du Badge (OOB) — le compteur sur la cloche
    if unread_count > 0:
        badge_html = f"""
        <div id="notification-badge" hx-swap-oob="true">
            <span class="absolute top-1 right-1 inline-flex items-center justify-center w-4 h-4 text-xs font-bold leading-none text-white bg-red-500 rounded-full border-2 border-white">
                {unread_count}
            </span>
        </div>
        """
    else:
        badge_html = '<div id="notification-badge" hx-swap-oob="true"></div>'

    # Rendu de la notification mise à jour
    is_dropdown = request.headers.get('X-Source') == 'dropdown'
    context = {'notif': notif, 'is_dropdown': is_dropdown}
    notification_html = render_to_string('notifications/partials/hx_item.html', context, request=request)
    
    return HttpResponse(notification_html + badge_html)

@login_required
@require_POST
def mark_all_read(request):
    """Marque tout comme lu d'un coup.

    Accepte un champ POST `type` (student|instructor) pour ne marquer
    que les notifications d'un espace.  Sans ce champ, marque tout.
    """
    type_filter = request.POST.get('type')
    if type_filter not in _VALID_TYPES:
        type_filter = None

    qs = Notification.objects.filter(recipient=request.user, is_read=False)
    if type_filter:
        qs = qs.filter(notification_type=type_filter)
    qs.update(is_read=True)

    # Badge OOB (vider/recalculer le compteur dans la navbar)
    student_unread = Notification.objects.filter(
        recipient=request.user,
        is_read=False,
        notification_type=Notification.TYPE_STUDENT,
    ).count()
    if student_unread > 0:
        badge_html = (
            f'<div id="notification-badge" hx-swap-oob="true">'
            f'<span class="absolute top-1 right-1 inline-flex items-center justify-center '
            f'w-4 h-4 text-xs font-bold leading-none text-white bg-red-500 rounded-full '
            f'border-2 border-white">{student_unread}</span>'
            f'</div>'
        )
    else:
        badge_html = '<div id="notification-badge" hx-swap-oob="true"></div>'

    if getattr(request, 'htmx', False):
        # Re-rendre la liste filtrée dans le même contexte
        all_qs = Notification.objects.filter(recipient=request.user)
        if type_filter:
            notifs = all_qs.filter(notification_type=type_filter).order_by('-created_at')
        else:
            notifs = all_qs.order_by('-created_at')

        if request.headers.get('X-Source') == 'dropdown':
            html = render_to_string(
                'notifications/partials/dropdown_inner.html',
                {'notifications': notifs[:10]},
                request=request,
            )
        else:
            html = render_to_string(
                'notifications/partials/notification_list.html',
                {'notifications': notifs},
                request=request,
            )
        return HttpResponse(html + badge_html)

    return redirect('my_notifications')