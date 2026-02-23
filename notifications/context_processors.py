from .models import Notification

def user_notifications(request):
    """
    Rend les notifications accessibles dans tous les templates
    via les variables : navbar_notifications et navbar_unread_count
    """
    if request.user.is_authenticated:
        # On récupère les 10 dernières notifications (du plus récent au plus vieux)
        notifs = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:10]
        
        # On compte seulement celles qui ne sont pas lues
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        
        return {
            'navbar_notifications': notifs,
            'navbar_unread_count': unread_count
        }
    
    # Si l'utilisateur n'est pas connecté, on renvoie des listes vides
    return {
        'navbar_notifications': [],
        'navbar_unread_count': 0
    }