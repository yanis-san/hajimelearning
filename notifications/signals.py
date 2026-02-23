from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db.models import Count

from .models import Notification
from courses.models import StudentProgress, Lesson
from support.models import Response, Question

User = get_user_model()

# --- 1. GESTION PROGRESSION (LEÇON + COURS ENTIER) ---
@receiver(post_save, sender=StudentProgress)
def handle_progress_notifications(sender, instance, created, **kwargs):
    """
    Se déclenche à chaque fois qu'une leçon est validée.
    1. Notifie pour la leçon.
    2. Vérifie si le cours entier est fini pour notifier aussi.
    """
    if created:
        student = instance.student
        lesson = instance.lesson
        course = lesson.module.course
        
        # A. Notification : Leçon Terminée
        url_lecon = reverse('lesson_detail', kwargs={'course_slug': course.slug, 'lesson_slug': lesson.slug})
        Notification.objects.create(
            recipient=student,
            title="Leçon validée ✅",
            message=f"Bravo ! Vous avez terminé '{lesson.title}'.",
            link=url_lecon
        )

        # B. Notification : Cours Entier Terminé ?
        # On compte le total des leçons du cours
        total_lessons = Lesson.objects.filter(module__course=course).count()
        # On compte combien l'élève en a fini dans ce cours
        completed_lessons = StudentProgress.objects.filter(
            student=student, 
            lesson__module__course=course
        ).count()

        if completed_lessons == total_lessons:
            Notification.objects.create(
                recipient=student,
                title="Cours COMPLÉTÉ ! 🏆",
                message=f"Félicitations ! Vous avez terminé 100% du cours : {course.title}. Vous êtes un chef !",
                link=reverse('course_detail', kwargs={'course_slug': course.slug})
            )


# --- 2. GESTION SUPPORT (RÉPONSE PROF -> ÉLÈVE) ---
@receiver(post_save, sender=Response)
def notify_student_on_reply(sender, instance, created, **kwargs):
    if created:
        question = instance.question
        # Si ce n'est pas l'élève qui se répond à lui-même
        if instance.author != question.student:
            try:
                lien = reverse('question_detail', args=[question.id])
            except:
                lien = f"/support/question/{question.id}/"

            Notification.objects.create(
                recipient=question.student,
                title="Nouvelle réponse Support 💬",
                message=f"Réponse sur : {question.title}",
                link=lien
            )


# --- 3. GESTION ADMIN (NOUVELLE QUESTION -> ADMINS) ---
@receiver(post_save, sender=Question)
def notify_admin_on_new_question(sender, instance, created, **kwargs):
    """
    Prévient tous les superusers (Admins) qu'une nouvelle question est posée.
    """
    if created:
        # On récupère tous les admins
        admins = User.objects.filter(is_superuser=True)
        
        for admin in admins:
            # On ne notifie pas l'admin si c'est lui-même qui pose une question de test
            if instance.student != admin:
                try:
                    lien = reverse('question_detail', args=[instance.id])
                except:
                    lien = f"/support/question/{instance.id}/"
                
                # CORRECTION ICI : Utilisation de .email (car .username n'existe pas sur ton User custom)
                # On utilise getattr par sécurité, sinon on convertit l'objet en string
                nom_eleve = getattr(instance.student, 'email', str(instance.student))

                Notification.objects.create(
                    recipient=admin,
                    title="Nouvelle Question Élève 🙋‍♂️",
                    message=f"{nom_eleve} a posé une question dans {instance.course.title}.",
                    link=lien
                )