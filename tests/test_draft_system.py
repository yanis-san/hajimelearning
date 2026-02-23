"""
Tests du système de brouillon (draft) à tous les niveaux :
- Course.is_published
- Module.is_published
- Lesson.is_published

L'instructeur/staff peut voir le contenu en brouillon, pas les étudiants.
"""
import pytest
from django.test import Client
from django.urls import reverse

from courses.models import Course, Module, Lesson
from access.models import AccessRequest
from users.models import User
from instructors.models import InstructorPlan, InstructorProfile


@pytest.fixture
def plan():
    return InstructorPlan.objects.create(
        name='Starter', slug='starter', price=5000,
        max_courses=5, max_modules_per_course=10,
        max_lessons_per_course=50, revenue_percent=70,
    )


@pytest.fixture
def instructor(plan):
    user = User.objects.create_user(
        email='prof@test.com', password='password123',
        first_name='Prof', last_name='Cours',
    )
    InstructorProfile.objects.create(
        user=user, plan=plan,
        max_courses=5, max_modules_per_course=10,
        max_lessons_per_course=50, revenue_percent=70,
    )
    return user


@pytest.fixture
def student():
    return User.objects.create_user(
        email='eleve@test.com', password='password123',
        first_name='Élève', last_name='Test',
    )


@pytest.fixture
def superuser():
    return User.objects.create_superuser(
        email='super@test.com', password='password123',
    )


@pytest.fixture
def published_course(instructor):
    """Cours publié avec 2 modules (1 publié, 1 brouillon)."""
    course = Course.objects.create(
        title='Cours Complet', slug='cours-complet',
        short_description='desc', description='Full desc',
        price=5000, is_published=True, instructor=instructor,
    )
    m1 = Module.objects.create(
        course=course, title='Module 1', order=1, is_published=True,
    )
    m2 = Module.objects.create(
        course=course, title='Module 2 Draft', order=2, is_published=False,
    )
    # Module 1 : 2 leçons (1 publiée, 1 brouillon)
    Lesson.objects.create(
        module=m1, title='Leçon 1.1', slug='lecon-1-1',
        order=1, is_published=True,
    )
    Lesson.objects.create(
        module=m1, title='Leçon 1.2 Draft', slug='lecon-1-2-draft',
        order=2, is_published=False,
    )
    # Module 2 (brouillon) : 1 leçon publiée
    Lesson.objects.create(
        module=m2, title='Leçon 2.1', slug='lecon-2-1',
        order=1, is_published=True,
    )
    return course


@pytest.fixture
def enrolled_student(student, published_course):
    """Étudiant inscrit au cours."""
    AccessRequest.objects.create(
        student=student, course=published_course, status='APPROVED',
    )
    return student


@pytest.fixture
def client():
    return Client()


# ──────────────────────────────────────────────────────────
#  TESTS : filtrage brouillon dans course_detail
# ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestDraftCourseDetail:

    def test_student_sees_only_published_modules(self, client, enrolled_student, published_course):
        """Un étudiant inscrit ne voit que les modules publiés."""
        client.force_login(enrolled_student)
        resp = client.get(reverse('course_detail', args=[published_course.slug]))
        assert resp.status_code == 200
        content = resp.content.decode()
        assert 'Module 1' in content
        assert 'Module 2 Draft' not in content

    def test_student_sees_only_published_lessons(self, client, enrolled_student, published_course):
        """Un étudiant inscrit ne voit que les leçons publiées (dans un module publié)."""
        client.force_login(enrolled_student)
        resp = client.get(reverse('course_detail', args=[published_course.slug]))
        content = resp.content.decode()
        assert 'Leçon 1.1' in content
        assert 'Leçon 1.2 Draft' not in content

    def test_instructor_sees_all_modules(self, client, published_course):
        """L'instructeur propriétaire voit tous les modules, même les brouillons."""
        client.force_login(published_course.instructor)
        resp = client.get(reverse('course_detail', args=[published_course.slug]))
        content = resp.content.decode()
        assert 'Module 1' in content
        assert 'Module 2 Draft' in content

    def test_instructor_sees_draft_lessons(self, client, published_course):
        """L'instructeur propriétaire voit les leçons en brouillon."""
        client.force_login(published_course.instructor)
        resp = client.get(reverse('course_detail', args=[published_course.slug]))
        content = resp.content.decode()
        assert 'Leçon 1.2 Draft' in content

    def test_superuser_sees_all_content(self, client, superuser, published_course):
        """Un superuser voit tout le contenu, y compris les brouillons."""
        client.force_login(superuser)
        resp = client.get(reverse('course_detail', args=[published_course.slug]))
        content = resp.content.decode()
        assert 'Module 2 Draft' in content
        assert 'Leçon 1.2 Draft' in content


# ──────────────────────────────────────────────────────────
#  TESTS : filtrage brouillon dans lesson_detail
# ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestDraftLessonAccess:

    def test_student_blocked_from_draft_lesson(self, client, enrolled_student, published_course):
        """Un étudiant ne peut pas accéder à une leçon en brouillon."""
        client.force_login(enrolled_student)
        resp = client.get(
            reverse('lesson_detail', args=[published_course.slug, 'lecon-1-2-draft']),
            follow=True,
        )
        # Redirigé vers course_detail
        assert resp.redirect_chain[-1][0] == reverse('course_detail', args=[published_course.slug])

    def test_student_blocked_from_lesson_in_draft_module(self, client, enrolled_student, published_course):
        """Un étudiant ne peut pas accéder à une leçon dans un module brouillon."""
        client.force_login(enrolled_student)
        resp = client.get(
            reverse('lesson_detail', args=[published_course.slug, 'lecon-2-1']),
            follow=True,
        )
        assert resp.redirect_chain[-1][0] == reverse('course_detail', args=[published_course.slug])

    def test_instructor_can_access_draft_lesson(self, client, published_course):
        """L'instructeur peut accéder à ses propres leçons en brouillon."""
        client.force_login(published_course.instructor)
        resp = client.get(
            reverse('lesson_detail', args=[published_course.slug, 'lecon-1-2-draft']),
        )
        assert resp.status_code == 200
        assert 'Leçon 1.2 Draft' in resp.content.decode()

    def test_instructor_can_access_lesson_in_draft_module(self, client, published_course):
        """L'instructeur peut accéder à une leçon dans un module brouillon."""
        client.force_login(published_course.instructor)
        resp = client.get(
            reverse('lesson_detail', args=[published_course.slug, 'lecon-2-1']),
        )
        assert resp.status_code == 200

    def test_superuser_can_access_draft_lesson(self, client, superuser, published_course):
        """Un superuser peut accéder aux leçons en brouillon."""
        client.force_login(superuser)
        resp = client.get(
            reverse('lesson_detail', args=[published_course.slug, 'lecon-1-2-draft']),
        )
        assert resp.status_code == 200

    def test_student_can_access_published_lesson(self, client, enrolled_student, published_course):
        """Un étudiant inscrit peut accéder normalement aux leçons publiées."""
        client.force_login(enrolled_student)
        resp = client.get(
            reverse('lesson_detail', args=[published_course.slug, 'lecon-1-1']),
        )
        assert resp.status_code == 200


# ──────────────────────────────────────────────────────────
#  TESTS : toggle brouillon dans le builder
# ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestDraftToggleBuilder:

    def test_module_toggle_publish(self, client, published_course):
        """Le builder peut toggler is_published d'un module."""
        client.force_login(published_course.instructor)
        module = published_course.modules.first()
        assert module.is_published is True

        # Dépublier (pas de checkbox = False)
        client.post(
            reverse('manage_module_edit', args=[published_course.slug, module.id]),
            {'title': module.title},
        )
        module.refresh_from_db()
        assert module.is_published is False

        # Republier
        client.post(
            reverse('manage_module_edit', args=[published_course.slug, module.id]),
            {'title': module.title, 'is_published': 'on'},
        )
        module.refresh_from_db()
        assert module.is_published is True

    def test_lesson_toggle_publish(self, client, published_course):
        """Le builder peut toggler is_published d'une leçon."""
        client.force_login(published_course.instructor)
        module = published_course.modules.first()
        lesson = module.lessons.first()
        assert lesson.is_published is True

        # Dépublier
        client.post(
            reverse('manage_lesson_edit', args=[published_course.slug, module.id, lesson.id]),
            {'title': lesson.title, 'slug': lesson.slug},
        )
        lesson.refresh_from_db()
        assert lesson.is_published is False

        # Republier
        client.post(
            reverse('manage_lesson_edit', args=[published_course.slug, module.id, lesson.id]),
            {'title': lesson.title, 'slug': lesson.slug, 'is_published': 'on'},
        )
        lesson.refresh_from_db()
        assert lesson.is_published is True
