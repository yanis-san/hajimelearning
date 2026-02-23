from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import Notification
from courses.models import StudentProgress, Lesson
from support.models import Response, Question

User = get_user_model()

S = Notification.TYPE_STUDENT
I = Notification.TYPE_INSTRUCTOR
P = Notification.CATEGORY_PROGRESS
SUP = Notification.CATEGORY_SUPPORT
INS = Notification.CATEGORY_INSTRUCTOR


# ── 1. PROGRESSION ÉTUDIANT ──────────────────────────────────────────────────

@receiver(post_save, sender=StudentProgress)
def handle_progress_notifications(sender, instance, created, **kwargs):
    """Leçon validée → notif étudiant. Cours 100% → notif étudiant."""
    if not created:
        return

    student = instance.student
    lesson  = instance.lesson
    course  = lesson.module.course

    # A. Leçon terminée
    Notification.objects.create(
        recipient=student,
        notification_type=S,
        category=P,
        title="Leçon validée ✅",
        message=f"Bravo ! Vous avez terminé « {lesson.title} ».",
        link=reverse('lesson_detail', kwargs={
            'course_slug': course.slug,
            'lesson_slug': lesson.slug,
        }),
    )

    # B. Cours entier terminé ?
    total     = Lesson.objects.filter(module__course=course).count()
    completed = StudentProgress.objects.filter(
        student=student, lesson__module__course=course
    ).count()

    if total > 0 and completed == total:
        Notification.objects.create(
            recipient=student,
            notification_type=S,
            category=P,
            title="Cours COMPLÉTÉ ! 🏆",
            message=f"Félicitations, vous avez terminé 100 % de « {course.title} » !",
            link=reverse('course_detail', kwargs={'course_slug': course.slug}),
        )


# ── 2. RÉPONSE SUPPORT → ÉTUDIANT ────────────────────────────────────────────

@receiver(post_save, sender=Response)
def notify_student_on_reply(sender, instance, created, **kwargs):
    """Quand l'instructeur/admin répond → notifie l'étudiant auteur de la question."""
    if not created:
        return

    question = instance.question

    # Ne pas notifier l'étudiant s'il se répond lui-même
    if instance.author == question.student:
        return

    Notification.objects.create(
        recipient=question.student,
        notification_type=S,
        category=SUP,
        title="Nouvelle réponse 💬",
        message=f"Réponse à votre question : « {question.title} »",
        link=reverse('question_detail', args=[question.id]),
    )


# ── 2b. QUESTION RÉSOLUE → ÉTUDIANT ─────────────────────────────────────────

@receiver(pre_save, sender=Question)
def notify_student_on_resolved(sender, instance, **kwargs):
    """Quand le statut d'une question passe à RESOLVED → notifie l'étudiant."""
    if not instance.pk:
        return  # création, pas mise à jour

    try:
        previous = Question.objects.get(pk=instance.pk)
    except Question.DoesNotExist:
        return

    # Ne déclenche que si le statut change vers RESOLVED
    if previous.status != 'RESOLVED' and instance.status == 'RESOLVED':
        Notification.objects.create(
            recipient=instance.student,
            notification_type=S,
            category=SUP,
            title="Question résolue ✅",
            message=f"Votre question « {instance.title} » a été marquée comme résolue.",
            link=reverse('question_detail', args=[instance.pk]),
        )


# ── 3. NOUVELLE QUESTION → INSTRUCTEUR + ADMINS ───────────────────────────────

@receiver(post_save, sender=Question)
def notify_instructors_on_new_question(sender, instance, created, **kwargs):
    """
    Quand un étudiant pose une question dans un cours :
    - Notifie l'instructeur du cours (s'il existe), type='instructor'
    - Notifie tous les superusers en tant qu'admins, type='instructor'
    Les deux reçoivent une notif dans leur espace instructeur, pas dans le flux étudiant.
    """
    if not created:
        return

    nom_etudiant = instance.student.get_full_name() or instance.student.email
    lien = reverse('question_detail', args=[instance.id])

    # Destinataires uniques (évite doublon si l'instructeur est aussi superuser)
    recipients_seen = set()

    # A. Instructeur propriétaire du cours
    course = instance.course
    if course.instructor and course.instructor != instance.student:
        recipients_seen.add(course.instructor.pk)
        Notification.objects.create(
            recipient=course.instructor,
            notification_type=I,
            category=INS,
            title="Nouvelle question 🙋",
            message=f"{nom_etudiant} a posé une question dans « {course.title} ».",
            link=lien,
        )

    # B. Superusers (admins plateforme)
    for admin in User.objects.filter(is_superuser=True):
        if admin == instance.student:
            continue
        if admin.pk in recipients_seen:
            continue
        recipients_seen.add(admin.pk)
        Notification.objects.create(
            recipient=admin,
            notification_type=I,
            category=INS,
            title="Nouvelle question élève 🙋",
            message=f"{nom_etudiant} a posé une question dans « {course.title} ».",
            link=lien,
        )
