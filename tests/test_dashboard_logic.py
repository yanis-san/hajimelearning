import pytest
from django.urls import reverse

from access.models import AccessRequest, Enrollment
from courses.models import Course


@pytest.mark.django_db
class TestDashboardLogic:
    def test_dashboard_shows_only_purchased_courses(self, client, student):
        """Le dashboard ne doit montrer que les cours payés et validés"""
        # 1. Cours Payé NON acheté
        Course.objects.create(title="Payant 1", slug="p1", price=1000, is_published=True)

        # 2. Cours Payé ACHETÉ (Validé)
        c2 = Course.objects.create(title="Payant 2", slug="p2", price=1000, is_published=True)
        AccessRequest.objects.create(student=student, course=c2, status='APPROVED')

        # 3. Cours Payé EN ATTENTE
        c3 = Course.objects.create(title="Payant 3", slug="p3", price=1000, is_published=True)
        AccessRequest.objects.create(student=student, course=c3, status='PENDING')

        # 4. Cours GRATUIT (inscrit)
        c4 = Course.objects.create(title="Gratuit", slug="free", price=0, is_published=True)
        Enrollment.objects.create(student=student, course=c4)

        # --- ACTION ---
        client.force_login(student)
        response = client.get(reverse('user_dashboard'))

        # --- VÉRIFICATION ---
        assert response.status_code == 200
        content = response.content.decode()

        # DOIT être là
        assert "Payant 2" in content
        assert "Gratuit" in content

        # NE DOIT PAS être là
        assert "Payant 1" not in content
        assert "Payant 3" not in content
