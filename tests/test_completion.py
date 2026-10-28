import pytest
from django.urls import reverse

from courses.models import CourseCompletion, StudentProgress


@pytest.mark.django_db
class TestCourseCompletion:
    """Tests de la logique de complétion de cours (modèle + vue)."""

    def _setup_course_with_lessons(self, course, n=2):
        """Crée un module avec n leçons publiées et retourne la liste."""
        module = course.modules.create(title="Module A", order=1, is_published=True)
        lessons = []
        for i in range(1, n + 1):
            lesson = module.lessons.create(
                title=f"Leçon {i}", slug=f"lecon-{i}", order=i, is_published=True
            )
            lessons.append(lesson)
        return lessons

    # ── Modèle ────────────────────────────────────────────────────────────────

    def test_course_completion_created_manually(self, student, course):
        """CourseCompletion peut être créé manuellement."""
        completion = CourseCompletion.objects.create(student=student, course=course)
        assert completion.pk is not None
        assert str(completion) == f"{student.email} — {course.title}"

    def test_course_completion_unique_per_student_course(self, student, course):
        """Un seul enregistrement par (student, course)."""
        CourseCompletion.objects.create(student=student, course=course)
        obj, created = CourseCompletion.objects.get_or_create(student=student, course=course)
        assert created is False
        assert CourseCompletion.objects.filter(student=student, course=course).count() == 1

    # ── Vue mark_lesson_complete → complétion automatique ─────────────────────

    def test_completion_created_when_all_lessons_done(self, client, student, course):
        """
        Quand un étudiant termine toutes les leçons publiées, CourseCompletion
        est créé automatiquement.
        """
        from access.models import AccessRequest
        AccessRequest.objects.create(student=student, course=course, status='APPROVED', final_price=0)
        client.force_login(student)

        lessons = self._setup_course_with_lessons(course, n=2)

        # Compléter la première leçon manuellement en base
        StudentProgress.objects.create(student=student, lesson=lessons[0])

        # Marquer la dernière leçon via la vue
        url = reverse('mark_lesson_complete', kwargs={
            'course_slug': course.slug,
            'lesson_slug': lessons[1].slug,
        })
        client.post(url)

        assert CourseCompletion.objects.filter(student=student, course=course).exists()

    def test_no_completion_when_lessons_remain(self, client, student, course):
        """Pas de CourseCompletion si des leçons restent non terminées."""
        from access.models import AccessRequest
        AccessRequest.objects.create(student=student, course=course, status='APPROVED', final_price=0)
        client.force_login(student)

        lessons = self._setup_course_with_lessons(course, n=3)

        # Marquer uniquement la première leçon via la vue (2 restantes)
        url = reverse('mark_lesson_complete', kwargs={
            'course_slug': course.slug,
            'lesson_slug': lessons[0].slug,
        })
        client.post(url)

        assert not CourseCompletion.objects.filter(student=student, course=course).exists()

    def test_completion_not_duplicated_on_re_complete(self, client, student, course):
        """
        Si l'étudiant complète une leçon alors que la complétion existe,
        on ne crée pas de doublon.
        """
        from access.models import AccessRequest
        AccessRequest.objects.create(student=student, course=course, status='APPROVED', final_price=0)
        client.force_login(student)

        lessons = self._setup_course_with_lessons(course, n=1)
        CourseCompletion.objects.create(student=student, course=course)

        url = reverse('mark_lesson_complete', kwargs={
            'course_slug': course.slug,
            'lesson_slug': lessons[0].slug,
        })
        client.post(url)

        assert CourseCompletion.objects.filter(student=student, course=course).count() == 1

    # ── Vue download_certificate ───────────────────────────────────────────────

    def test_download_certificate_requires_login(self, client, course):
        """Vue refusée si non connecté."""
        url = reverse('download_certificate', kwargs={'course_slug': course.slug})
        response = client.get(url)
        assert response.status_code == 302
        assert '/accounts/login' in response['Location'] or '/login' in response['Location']

    def test_download_certificate_404_without_completion(self, client, student, course):
        """404 si aucune complétion pour cet étudiant."""
        client.force_login(student)
        url = reverse('download_certificate', kwargs={'course_slug': course.slug})
        response = client.get(url)
        assert response.status_code == 404

    def test_download_certificate_redirects_if_pdf_not_ready(self, client, student, course):
        """
        Si la complétion existe mais le PDF n'est pas encore généré,
        on redirige vers le dashboard avec un message warning.
        """
        client.force_login(student)
        CourseCompletion.objects.create(student=student, course=course)

        url = reverse('download_certificate', kwargs={'course_slug': course.slug})
        response = client.get(url)

        assert response.status_code == 302
        assert response['Location'].endswith(reverse('user_dashboard'))

    def test_download_certificate_returns_pdf(self, client, student, course, tmp_path):
        """Retourne un PDF si le fichier est présent."""
        from django.core.files.base import ContentFile
        client.force_login(student)

        completion = CourseCompletion.objects.create(student=student, course=course)
        # Simuler un fichier PDF minimal
        pdf_content = b"%PDF-1.4 fake pdf content"
        completion.certificate_pdf.save("test.pdf", ContentFile(pdf_content), save=True)

        url = reverse('download_certificate', kwargs={'course_slug': course.slug})
        response = client.get(url)

        assert response.status_code == 200
        assert response['Content-Type'] == 'application/pdf'
        assert 'attachment' in response['Content-Disposition']

    # ── Dashboard ─────────────────────────────────────────────────────────────

    def test_dashboard_shows_completed_course_ids(self, client, student, course):
        """Le dashboard passe les IDs des cours complétés en contexte."""
        from access.models import AccessRequest
        AccessRequest.objects.create(student=student, course=course, status='APPROVED', final_price=0)
        client.force_login(student)

        CourseCompletion.objects.create(student=student, course=course)

        url = reverse('user_dashboard')
        response = client.get(url)

        assert response.status_code == 200
        assert course.id in response.context['completed_course_ids']

    def test_dashboard_empty_completed_ids_for_student_without_completion(
        self, client, student, course
    ):
        """Pas de cours complétés → set vide."""
        from access.models import AccessRequest
        AccessRequest.objects.create(student=student, course=course, status='APPROVED', final_price=0)
        client.force_login(student)

        url = reverse('user_dashboard')
        response = client.get(url)

        assert response.status_code == 200
        assert len(response.context['completed_course_ids']) == 0
