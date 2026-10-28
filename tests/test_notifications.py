import pytest
from django.urls import NoReverseMatch, reverse

from notifications.models import Notification
from support.models import Question, Response


@pytest.mark.django_db
class TestNotificationSystem:
    @pytest.fixture
    def question(self, student, course):
        """Crée une question de base pour le test"""
        module = course.modules.create(title="Mod", order=1)
        lesson = module.lessons.create(title="Lec", slug="lec", order=1)
        return Question.objects.create(
            student=student, course=course, lesson=lesson, title="Help", content="Besoin d'aide"
        )

    def test_reply_triggers_notification(self, client, admin_user, question):
        """Vérifie que si le prof répond, l'élève reçoit une notif"""

        # CORRECTION ICI : On vérifie les notifs de l'étudiant SEULEMENT.
        # (Car il y a déjà une notif pour l'admin suite à la création de la question)
        assert Notification.objects.filter(recipient=question.student).count() == 0

        # Action : Le prof répond à la question
        Response.objects.create(question=question, author=admin_user, content="Voici la solution", is_instructor=True)

        # Résultat attendu : 1 notif pour l'étudiant
        # (On filtre encore pour ignorer la notif de l'admin)
        student_notifs = Notification.objects.filter(recipient=question.student)
        assert student_notifs.count() == 1

        notif = student_notifs.first()
        assert notif.is_read is False
        assert "Nouvelle réponse" in notif.title

    def test_mark_as_read(self, client, student):
        """Vérifie qu'on peut marquer une notif comme lue"""
        notif = Notification.objects.create(recipient=student, message="Test", link="/dashboard/")

        client.force_login(student)

        # On appelle l'URL qui marque comme lu (ou l'URL HTMX si tu as changé)
        # Note: Assure-toi que le nom de l'url 'mark_read_and_redirect' ou 'mark_notif_read' est le bon
        try:
            url = reverse('mark_read_and_redirect', args=[notif.id])
        except NoReverseMatch:
            # Fallback si tu utilises le nom HTMX de l'autre fichier de test
            url = reverse('mark_notif_read', args=[notif.id])

        client.get(url) if 'redirect' in url else client.post(url)

        # La notif doit être marquée lue en BDD
        notif.refresh_from_db()
        assert notif.is_read is True
