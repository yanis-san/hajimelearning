import pytest
from django.urls import reverse

from access.models import AccessRequest, ActivationCode
from courses.models import StudentProgress


@pytest.mark.django_db
class TestInstructorDashboard:
    @pytest.fixture
    def course_with_content(self, course):
        """Un cours avec 2 leçons pour faciliter les calculs (1 leçon = 50%)"""
        module = course.modules.create(title="Module 1", order=1)
        l1 = module.lessons.create(title="Leçon 1", slug="l1", order=1)
        l2 = module.lessons.create(title="Leçon 2", slug="l2", order=2)
        return course, l1, l2

    def test_dashboard_access_denied_for_student(self, client, student, course):
        """Un étudiant ne doit PAS pouvoir voir le tableau de bord prof"""
        client.force_login(student)
        url = reverse('manage_course_students', args=[course.slug])

        # Doit rediriger (vers home ou login selon ta config @staff_member_required)
        response = client.get(url)
        assert response.status_code == 302

    def test_dashboard_stats_calculation(self, client, admin_user, student, course_with_content):
        """Vérifie que le calcul de progression (50%) est correct"""
        course, l1, l2 = course_with_content

        # 1. On inscrit l'étudiant (Via CCP validé)
        AccessRequest.objects.create(student=student, course=course, status='APPROVED')

        # 2. L'étudiant termine la leçon 1 (donc 1 sur 2 = 50%)
        StudentProgress.objects.create(student=student, lesson=l1)

        # 3. Le prof regarde le dashboard
        client.force_login(admin_user)
        url = reverse('manage_course_students', args=[course.slug])
        response = client.get(url)

        assert response.status_code == 200

        # 4. Vérifications des données
        stats = response.context['student_stats']
        assert len(stats) == 1
        assert stats[0]['user'] == student
        assert stats[0]['percent'] == 50  # 1 leçon sur 2
        assert stats[0]['completed'] == 1

    def test_dashboard_includes_code_users(self, client, admin_user, course_with_content):
        """Vérifie qu'un étudiant inscrit via CODE apparaît aussi"""
        course, l1, l2 = course_with_content

        # On crée un 2ème étudiant à la volée
        from users.models import User

        student2 = User.objects.create_user(email="code@test.com", password="pw")

        # Il utilise un code
        ActivationCode.objects.create(course=course, is_used=True, used_by=student2, code="CODE123")

        # Il finit TOUT (100%)
        StudentProgress.objects.create(student=student2, lesson=l1)
        StudentProgress.objects.create(student=student2, lesson=l2)

        # Le prof regarde
        client.force_login(admin_user)
        url = reverse('manage_course_students', args=[course.slug])
        response = client.get(url)

        stats = response.context['student_stats']

        # On doit trouver student2 à 100%
        user_stat = next((s for s in stats if s['user'] == student2), None)
        assert user_stat is not None
        assert user_stat['percent'] == 100
