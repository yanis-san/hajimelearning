from celery import shared_task
from django.core.mail import EmailMessage
from django.conf import settings
from .models import AccessRequest
from .utils import generate_receipt_pdf

import os

# URL du site — variable d'env en prod, fallback en dev
SITE_URL = os.environ.get('SITE_URL', 'http://127.0.0.1:8000').rstrip('/')


@shared_task
def send_access_confirmation_email(request_id):
    try:
        req = AccessRequest.objects.get(id=request_id)
        user = req.student
        course = req.course
        
        subject = f"✅ Accès validé + Reçu : {course.title}"
        
        body = f"""
        Bonjour {user.first_name or user.email},

        Félicitations ! Votre inscription au cours "{course.title}" est maintenant confirmée.

        Votre paiement de {req.final_price} DA a bien été validé.
        Vous trouverez votre reçu de paiement en pièce jointe.

        Accéder au cours : {SITE_URL}/course/{course.slug}/

        Cordialement,
        L'équipe.
        """

        # Création de l'email complexe (avec pièce jointe)
        email = EmailMessage(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )

        # Génération et attachement du PDF
        pdf_content = generate_receipt_pdf(req)
        filename = f"Recu_{req.id}.pdf"
        email.attach(filename, pdf_content, 'application/pdf')

        # Envoi
        email.send()
        return f"Email + Reçu envoyé à {user.email}"

    except AccessRequest.DoesNotExist:
        return "Erreur ID"