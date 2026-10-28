"""Utilitaires partagés par les vues de l'app courses."""

from django.contrib import messages
from django.db.models import Max, Prefetch
from django.http import HttpResponse
from django.shortcuts import redirect

from ..models import Lesson, Module


def is_course_manager(user, course):
    """L'utilisateur est-il staff ou propriétaire de la formation ?"""
    if not user.is_authenticated:
        return False
    return user.is_staff or course.instructor_id == user.id


def modules_queryset(is_manager):
    """Modules (et leçons) visibles : tout pour un manager, uniquement le publié sinon."""
    if is_manager:
        return Module.objects.prefetch_related('lessons')
    return Module.objects.filter(is_published=True).prefetch_related(
        Prefetch('lessons', queryset=Lesson.objects.filter(is_published=True))
    )


def plan_limit_reached(user, course, kind):
    """
    Un instructeur (non staff) a-t-il atteint la limite de son plan ?

    `kind` vaut 'modules' ou 'lessons'. Le staff n'est jamais limité.
    """
    if user.is_staff:
        return False
    profile = getattr(user, 'instructor_profile', None)
    if profile is None:
        return False
    check = profile.modules_limit_reached if kind == 'modules' else profile.lessons_limit_reached
    return check(course)


def limit_reached_response(request, redirect_url):
    """Message d'erreur + retour à la page (redirection HTMX côté client si besoin)."""
    messages.error(request, "Vous avez atteint la limite de votre offre pour cet élément.")
    if request.headers.get('HX-Request'):
        response = HttpResponse(status=204)
        response['HX-Redirect'] = redirect_url
        return response
    return redirect(redirect_url)


def is_autosave(request):
    """La requête provient-elle de l'auto-enregistrement du builder ?"""
    return request.headers.get('X-Autosave') == 'true' or request.POST.get('is_autosave') == '1'


def next_order(queryset):
    """Prochain numéro d'ordre (1 si le queryset est vide)."""
    return (queryset.aggregate(last=Max('order'))['last'] or 0) + 1


def apply_order(queryset, ids):
    """
    Réécrit le champ `order` (1..n) selon la liste d'identifiants reçue.

    Seuls les objets présents dans `queryset` sont modifiés : le queryset
    porte la portée de sécurité (cours géré par l'utilisateur).
    """
    pks = [int(pk) for pk in ids if str(pk).isdigit()]
    objects = queryset.in_bulk(pks)
    ordered = []
    for position, pk in enumerate(pks, start=1):
        obj = objects.get(pk)
        if obj is not None:
            obj.order = position
            ordered.append(obj)
    queryset.model.objects.bulk_update(ordered, ['order'])
