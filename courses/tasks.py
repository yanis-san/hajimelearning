import logging

from celery import shared_task
from django.core.files.base import ContentFile

from config.pdf import render_pdf

logger = logging.getLogger(__name__)


@shared_task
def generate_certificate_pdf(completion_id):
    """
    Génère le PDF du certificat pour un CourseCompletion et le stocke
    sur le modèle (champ `certificate_pdf`).

    Déclenché à la complétion du cours (vue `mark_lesson_complete`) ou à la demande si le fichier manque.
    """
    try:
        from notifications.signals import notify_certificate_ready

        from .models import CourseCompletion

        completion = CourseCompletion.objects.select_related('student', 'course').get(id=completion_id)

        pdf_content = render_pdf(
            'courses/certificate.html',
            {
                'student': completion.student,
                'course': completion.course,
                'completed_at': completion.completed_at,
            },
        )

        if not pdf_content:
            logger.error("Certificat vide (completion_id=%s)", completion_id)
            return

        filename = f"certificat_{completion.student.id}_{completion.course.slug}.pdf"
        first_generation = not completion.certificate_pdf  # une régénération ne re-notifie pas
        completion.certificate_pdf.save(filename, ContentFile(pdf_content), save=True)
        if first_generation:
            notify_certificate_ready(completion)
        logger.info(
            "Certificat généré : complétion #%s (%s - %s)",
            completion_id,
            completion.student.email,
            completion.course.title,
        )
    except Exception:
        logger.exception("Erreur génération certificat (completion_id=%s)", completion_id)
