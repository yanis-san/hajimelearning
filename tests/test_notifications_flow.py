import pytest
from django.urls import reverse
from notifications.models import Notification


@pytest.mark.django_db
class TestNotificationFlow:

    def test_htmx_mark_read_updates_db_and_returns_html(self, client, student):
        """
        Test Robuste du Flux HTMX :
        1. On clique sur le bouton (POST).
        2. La DB passe de Non lu -> Lu.
        3. Le HTML renvoyé contient la notif sans fond bleu.
        4. Le HTML renvoyé contient la mise à jour du Badge (OOB).
        """
        # 1. Setup : Une notification NON lue
        notif = Notification.objects.create(
            recipient=student,
            title="Bienvenue",
            message="Test message",
            is_read=False,
        )

        client.force_login(student)
        url = reverse("mark_notif_read", args=[notif.id])

        # 2. Action : Simulation du clic HTMX
        # On ajoute l'header HTMX pour faire propre
        response = client.post(url, HTTP_HX_REQUEST="true")

        # 3. Vérification BDD
        notif.refresh_from_db()
        assert (
            notif.is_read is True
        ), "La notification doit être marquée comme lue en base."

        # 4. Analyse du HTML reçu
        html = response.content.decode()

        # A. Vérification de la notification elle-même (Swap principal)
        assert f'id="notif-{notif.id}"' in html or f'id="notif-item-{notif.id}"' in html

        # B. Vérification du Badge (Swap Out of Band)
        assert 'id="notification-badge"' in html
        assert 'hx-swap-oob="true"' in html

        # Comme il n'y a plus de notif non lue, le badge doit être vide
        assert "bg-red-600" not in html

    def test_htmx_badge_counter_logic(self, client, student):
        """
        Vérifie que le compteur du badge est correct
        quand il reste d'autres notifications non lues.
        """
        # On crée 3 notifs : 2 non lues, 1 lue
        n1 = Notification.objects.create(
            recipient=student, title="N1", is_read=False
        )
        n2 = Notification.objects.create(
            recipient=student, title="N2", is_read=False
        )
        n3 = Notification.objects.create(
            recipient=student, title="N3", is_read=True
        )

        client.force_login(student)

        # On marque N1 comme lue (il restera donc N2 en non lue)
        url = reverse("mark_notif_read", args=[n1.id])
        response = client.post(url)
        html = response.content.decode()

        # Vérification du Badge OOB
        # Il doit contenir le chiffre "1" (car il reste N2)
        assert 'id="notification-badge"' in html
        assert 'hx-swap-oob="true"' in html
        assert "bg-red-500" in html  # Le point rouge doit être là
        assert "1" in html  # Le compteur doit afficher 1

    def test_mark_read_idempotent(self, client, student):
        """Vérifie que marquer comme lu est idempotent"""
        notif = Notification.objects.create(recipient=student, is_read=False)

        client.force_login(student)
        url = reverse("mark_notif_read", args=[notif.id])

        # Premier clic : Elle doit devenir LUE
        client.post(url)
        notif.refresh_from_db()
        assert notif.is_read is True

        # Deuxième clic : Elle reste LUE (pas d'inversion)
        client.post(url)
        notif.refresh_from_db()
        assert notif.is_read is True

    def test_security_cannot_read_others_notif(
        self, client, student, django_user_model
    ):
        """Un étudiant ne peut pas marquer lue la notif d'un autre"""
        # Un autre utilisateur (Hacker)
        hacker = django_user_model.objects.create_user(
            email="hacker@test.com", password="password"
        )

        # Une notif qui appartient à 'student'
        notif = Notification.objects.create(recipient=student, is_read=False)

        # Le hacker se connecte
        client.force_login(hacker)

        # Il essaie de lire la notif de l'étudiant
        url = reverse("mark_notif_read", args=[notif.id])
        response = client.post(url)

        # Doit retourner 404
        assert response.status_code == 404

        # La notif ne doit pas avoir bougé
        notif.refresh_from_db()
        assert notif.is_read is False
