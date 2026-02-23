from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.template.loader import render_to_string
from .models import Notification

@login_required
def my_notifications(request):
    """ Affiche la liste complète des notifications (Page dédiée) """
    # C'est mieux de trier par date décroissante (plus récent en haut)
    notifs = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    return render(request, 'notifications/list.html', {'notifications': notifs})

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
    
    # On inverse le statut (Lu <-> Non lu) pour permettre de re-marquer comme non lu
    notif.is_read = not notif.is_read
    notif.save()

    # Recalcul du compteur pour le badge
    unread_count = request.user.notifications.filter(is_read=False).count()

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
    context = {'notif': notif}
    notification_html = render_to_string('notifications/partials/single_notification.html', context)
    
    return HttpResponse(notification_html + badge_html)

@login_required
@require_POST
def mark_all_read(request):
    """ Marque tout comme lu d'un coup """
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)

    # Badge OOB (vider le compteur dans la navbar)
    badge_html = '<div id="notification-badge" hx-swap-oob="true"></div>'

    if getattr(request, 'htmx', False):
        notifs = Notification.objects.filter(recipient=request.user).order_by('-created_at')

        # Depuis le dropdown navbar
        if request.headers.get('X-Source') == 'dropdown':
            html = render_to_string(
                'notifications/partials/dropdown_inner.html',
                {'notifications': notifs[:10]},
                request=request,
            )
        else:
            # Depuis la page /notifications/
            html = render_to_string(
                'notifications/partials/notification_list.html',
                {'notifications': notifs},
                request=request,
            )
        return HttpResponse(html + badge_html)

    return redirect('my_notifications')