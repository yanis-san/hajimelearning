"""Filtres de template pour la progression et le sommaire des cours."""
from django import template

register = template.Library()


def _as_id_set(ids):
    if not ids:
        return set()
    if isinstance(ids, str):
        return set()
    try:
        return set(ids)
    except TypeError:
        return set()


@register.filter
def done_count(lessons, completed_ids):
    """Nombre de leçons terminées dans une liste/queryset de leçons."""
    done = _as_id_set(completed_ids)
    return sum(1 for l in lessons if l.id in done)


@register.filter
def total_minutes(lessons):
    """Somme des durées estimées d'une liste de leçons."""
    return sum((l.duration_minutes or 0) for l in lessons)


@register.filter
def duration(minutes):
    """45 → « 45 min », 90 → « 1 h 30 »."""
    try:
        minutes = int(minutes or 0)
    except (TypeError, ValueError):
        return ''
    if minutes <= 0:
        return ''
    if minutes < 60:
        return f"{minutes} min"
    h, m = divmod(minutes, 60)
    return f"{h} h {m:02d}" if m else f"{h} h"


@register.filter
def in_ids(value, ids):
    """`lesson.id|in_ids:completed_ids` — robuste aux chaînes vides."""
    return value in _as_id_set(ids)
