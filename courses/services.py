"""Règles métier de la progression : leçons terminées, certificats, résultats de quiz."""

from django.db import transaction

from .models import CourseCompletion, QuizAttempt, QuizResult, StudentProgress
from .progress import get_course_progress
from .tasks import generate_certificate_pdf


class InvalidScore(ValueError):
    """Score de quiz incohérent."""


@transaction.atomic
def complete_lesson(user, lesson):
    """
    Marque une leçon comme terminée et déclenche le certificat si le cours est fini.

    Retourne la progression à jour de l'étudiant dans le cours.
    """
    course = lesson.module.course
    StudentProgress.objects.get_or_create(student=user, lesson=lesson)

    progress = get_course_progress(user, course)
    if progress.is_complete:
        completion, created = CourseCompletion.objects.get_or_create(student=user, course=course)
        if created:
            transaction.on_commit(lambda: generate_certificate_pdf.delay(completion.id))
    return progress


@transaction.atomic
def uncomplete_lesson(user, lesson):
    """Annule la complétion d'une leçon ; le cours n'étant plus terminé, son certificat disparaît."""
    course = lesson.module.course
    StudentProgress.objects.filter(student=user, lesson=lesson).delete()

    progress = get_course_progress(user, course)
    if not progress.is_complete:
        CourseCompletion.objects.filter(student=user, course=course).delete()
    return progress


def record_quiz_result(user, block, score, total):
    """Enregistre le dernier résultat (et l'historique) d'un quiz après validation du score."""
    if total <= 0 or not 0 <= score <= total:
        raise InvalidScore(f'score {score}/{total}')

    QuizResult.objects.update_or_create(student=user, block=block, defaults={'score': score, 'total_questions': total})
    QuizAttempt.objects.create(student=user, block=block, score=score, total_questions=total)
