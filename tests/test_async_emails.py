import pytest
from django.core import mail

from access.models import AccessRequest
from access.tasks import send_access_confirmation_email


@pytest.mark.django_db
class TestAsyncEmailing:

    def test_task_sends_email_directly(self, student, course):
        """ Test Unitaire : La tâche Celery envoie-t-elle un mail ? """
        # 1. On crée une demande (peu importe le statut, on teste la tâche brute)
        req = AccessRequest.objects.create(student=student, course=course, status='PENDING')

        # 2. On appelle la tâche DIRECTEMENT (comme une fonction python normale)
        # Note: On appelle la fonction décorée, pas .delay() ici pour tester la logique interne
        send_access_confirmation_email(req.id)

        # 3. Vérifications
        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        assert "Accès validé" in email.subject
        assert student.email in email.to
        assert course.title in email.body

    def test_signal_triggers_task_on_approval(self, student, course, settings):
        """ Test Intégration : Est-ce que sauvegarder en 'APPROVED' lance la tâche ? """

        # --- MAGIE CELERY ---
        # On dit à Celery : "Exécute les tâches immédiatement en local, pas via Redis"
        settings.CELERY_TASK_ALWAYS_EAGER = True

        # 1. On crée une demande directement approuvée
        AccessRequest.objects.create(student=student, course=course, status='APPROVED')

        # 2. Comme on est en mode EAGER, la tâche a dû s'exécuter tout de suite
        assert len(mail.outbox) == 1
        assert "Accès validé" in mail.outbox[0].subject

    def test_signal_does_not_trigger_on_pending(self, student, course, settings):
        """ Vérifie qu'on n'envoie PAS de mail si c'est juste 'En attente' """
        settings.CELERY_TASK_ALWAYS_EAGER = True

        # 1. Création en PENDING
        AccessRequest.objects.create(student=student, course=course, status='PENDING')

        # 2. Vérification : Boîte vide
        assert len(mail.outbox) == 0

    def test_signal_does_not_trigger_on_rejected(self, student, course, settings):
        """ Vérifie qu'on n'envoie PAS de mail si c'est 'Refusé' """
        settings.CELERY_TASK_ALWAYS_EAGER = True

        AccessRequest.objects.create(student=student, course=course, status='REJECTED')

        assert len(mail.outbox) == 0
