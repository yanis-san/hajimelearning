import logging
from io import BytesIO

from celery import shared_task
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


@shared_task
def generate_certificate_pdf(completion_id):
    """
    Génère le PDF du certificat pour un CourseCompletion et le stocke
    sur le modèle (champ `certificate_pdf`).

    Déclenché par le signal post_save de CourseCompletion.
    """
    try:
        from xhtml2pdf import pisa
        from .models import CourseCompletion

        completion = CourseCompletion.objects.select_related('student', 'course').get(id=completion_id)

        html_string = render_to_string('courses/certificate.html', {
            'student': completion.student,
            'course': completion.course,
            'completed_at': completion.completed_at,
        })

        pdf_bytes = BytesIO()
        pisa_status = pisa.CreatePDF(html_string, dest=pdf_bytes)
        
        if not pisa_status.err:
            pdf_bytes.seek(0)
            filename = f"certificat_{completion.student.id}_{completion.course.slug}.pdf"
            completion.certificate_pdf.save(filename, pdf_bytes, save=True)

        logger.info(
            "Certificat généré : complétion #%s (%s - %s)",
            completion_id, completion.student.email, completion.course.title,
        )
    except Exception:
        logger.exception("Erreur génération certificat (completion_id=%s)", completion_id)
