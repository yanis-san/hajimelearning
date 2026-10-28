import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage
from django.urls import reverse

from .models import AccessRequest
from .utils import generate_receipt_pdf

logger = logging.getLogger(__name__)


@shared_task
def send_access_confirmation_email(request_id):
    """Confirme l'accès à un cours et joint le reçu de paiement en PDF."""
    try:
        req = AccessRequest.objects.select_related('student', 'course').get(id=request_id)
    except AccessRequest.DoesNotExist:
        return "Erreur ID"

    user, course = req.student, req.course
    course_url = f"{settings.SITE_URL}{reverse('course_detail', args=[course.slug])}"
    body = (
        f"Bonjour {user.first_name or user.email},\n\n"
        f"Félicitations ! Votre inscription au cours « {course.title} » est maintenant confirmée.\n\n"
        f"Votre paiement de {req.final_price} DA a bien été validé.\n"
        "Vous trouverez votre reçu de paiement en pièce jointe.\n\n"
        f"Accéder au cours : {course_url}\n\n"
        "Cordialement,\n"
        "L'équipe Hajime Learning.\n"
    )

    email = EmailMessage(f"✅ Accès validé + Reçu : {course.title}", body, settings.DEFAULT_FROM_EMAIL, [user.email])
    pdf_content = generate_receipt_pdf(req)
    if pdf_content:
        email.attach(f"Recu_{req.id}.pdf", pdf_content, 'application/pdf')
    else:
        logger.error("Reçu PDF vide pour la demande #%s : email envoyé sans pièce jointe", req.id)
    email.send()
    return f"Email + Reçu envoyé à {user.email}"
