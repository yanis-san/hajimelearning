from .models import Notification


def user_notifications(request):
    """
    Injecte dans tous les templates :

    Flux étudiant (cloche principale navbar) :
      - navbar_notifications        : 10 dernières notifs 'student'
      - navbar_unread_count         : nb non lues 'student'

    Flux instructeur (badge espace instructeur) :
      - navbar_instructor_unread_count : nb non lues 'instructor'
                                         (0 si pas instructeur actif)
    """
    if not request.user.is_authenticated:
        return {
            'navbar_notifications': [],
            'navbar_unread_count': 0,
            'navbar_instructor_unread_count': 0,
        }

    base_qs = request.user.notifications

    student_qs = base_qs.filter(notification_type=Notification.TYPE_STUDENT)
    navbar_notifications = student_qs.order_by('-created_at')[:10]
    navbar_unread_count = student_qs.filter(is_read=False).count()

    # Badge instructeur uniquement si l'utilisateur a un profil actif
    navbar_instructor_unread_count = 0
    profile = getattr(request.user, 'instructor_profile', None)
    if profile and profile.is_active:
        navbar_instructor_unread_count = base_qs.filter(
            notification_type=Notification.TYPE_INSTRUCTOR,
            is_read=False,
        ).count()

    return {
        'navbar_notifications': navbar_notifications,
        'navbar_unread_count': navbar_unread_count,
        'navbar_instructor_unread_count': navbar_instructor_unread_count,
    }
