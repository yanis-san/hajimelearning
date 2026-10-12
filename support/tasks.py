from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
import os
import logging

logger = logging.getLogger(__name__)

SITE_URL = os.environ.get('SITE_URL', 'http://127.0.0.1:8000').rstrip('/')


@shared_task
def send_question_notification_email(question_id):
    """
    Notifie l'instructeur du cours (ou les admins si cours plateforme)
    qu'un étudiant a posé une nouvelle question.
    """
    from .models import Question
    try:
        question = Question.objects.select_related(
            'student', 'course', 'course__instructor', 'lesson'
        ).get(id=question_id)
    except Question.DoesNotExist:
        return "Question introuvable"

    course = question.course
    student = question.student
    student_name = student.get_full_name() or student.first_name or student.email

    recipients = []
    if course.instructor and course.instructor != student and course.instructor.email:
        recipients.append(course.instructor.email)
    else:
        # Cours sans instructeur spécifique : notifier les superusers
        User = get_user_model()
        admins = User.objects.filter(is_superuser=True).exclude(pk=student.pk)
        recipients.extend([a.email for a in admins if a.email])

    if not recipients:
        return "Aucun destinataire"

    question_url = f"{SITE_URL}{reverse('question_detail', args=[question.id])}"
    lesson_info = f" (Leçon : {question.lesson.title})" if question.lesson else ""

    subject = f"[Hajime Learning] 🙋 Nouvelle question : {question.title}"
    body = f"""Bonjour,

L'étudiant {student_name} a posé une question dans la formation « {course.title} »{lesson_info}.

Sujet : {question.title}

Message :
{question.content}

Répondre à l'étudiant :
{question_url}

--
L'équipe Hajime Learning
"""

    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=list(set(recipients)),
        fail_silently=False,
    )
    return f"Email envoyé à {recipients}"


@shared_task
def send_response_notification_email(response_id):
    """
    Notifie les parties prenantes lors d'une nouvelle réponse :
    - L'auteur de la question (s'il n'est pas l'auteur de cette réponse)
    - L'instructeur du cours (s'il n'est pas l'auteur de cette réponse et pas déjà notifié)
    """
    from .models import Response
    try:
        response = Response.objects.select_related(
            'question', 'question__student', 'question__course', 'question__course__instructor', 'author'
        ).get(id=response_id)
    except Response.DoesNotExist:
        return "Réponse introuvable"

    question = response.question
    course = question.course
    author = response.author
    author_name = "Votre Sensei" if response.is_instructor else (author.get_full_name() or author.first_name or author.email)

    question_url = f"{SITE_URL}{reverse('question_detail', args=[question.id])}"

    # 1. Notifier l'étudiant qui a posé la question (s'il ne s'est pas répondu à lui-même)
    if question.student != author and question.student.email:
        student_subject = f"[Hajime Learning] 💬 Nouvelle réponse à votre question : {question.title}"
        student_body = f"""Bonjour {question.student.first_name or question.student.email},

{author_name} a répondu à votre question « {question.title} » dans le cours « {course.title} ».

Réponse :
{response.content}

Voir la discussion et répondre :
{question_url}

--
L'équipe Hajime Learning
"""
        send_mail(
            subject=student_subject,
            message=student_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[question.student.email],
            fail_silently=False,
        )

    # 2. Notifier l'instructeur du cours (s'il existe, n'est pas l'auteur de la réponse, et n'est pas déjà notifié comme auteur)
    instructor = course.instructor
    if instructor and instructor != author and instructor != question.student and instructor.email:
        inst_subject = f"[Hajime Learning] 💬 Nouveau message sur « {question.title} »"
        inst_body = f"""Bonjour {instructor.first_name or instructor.email},

Un nouveau message a été posté par {author_name} sur la question « {question.title} » dans votre formation « {course.title} ».

Message :
{response.content}

Accéder à la discussion :
{question_url}

--
L'équipe Hajime Learning
"""
        send_mail(
            subject=inst_subject,
            message=inst_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instructor.email],
            fail_silently=False,
        )

    return "Notifications email envoyées"
