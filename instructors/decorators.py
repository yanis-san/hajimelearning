from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .models import InstructorProfile


def instructor_required(view_func):
    """Décorateur : l'utilisateur doit être un instructeur actif."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        try:
            profile = request.user.instructor_profile
            if not profile.is_active:
                messages.error(request, "Votre compte instructeur est désactivé.")
                return redirect('instructor_plans')
        except InstructorProfile.DoesNotExist:
            messages.error(request, "Vous devez être instructeur pour accéder à cette page.")
            return redirect('instructor_plans')
        return view_func(request, *args, **kwargs)
    return _wrapped


def is_instructor(user):
    """Utilitaire : vérifie si l'user est un instructeur actif."""
    if not user.is_authenticated:
        return False
    try:
        return user.instructor_profile.is_active
    except InstructorProfile.DoesNotExist:
        return False
