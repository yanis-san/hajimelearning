import pytest
from django.urls import reverse

from courses.models import Course, Lesson, Module


@pytest.mark.django_db
class TestManageCourseList:
    def test_staff_can_access_course_list(self, client, admin_user, course):
        client.force_login(admin_user)
        resp = client.get(reverse('manage_course_list'))
        assert resp.status_code == 200
        assert course.title in resp.content.decode()

    def test_anonymous_redirected(self, client):
        resp = client.get(reverse('manage_course_list'))
        assert resp.status_code == 302

    def test_student_redirected(self, client, student):
        client.force_login(student)
        resp = client.get(reverse('manage_course_list'))
        assert resp.status_code == 302


@pytest.mark.django_db
class TestManageCourseCreate:
    def test_get_form(self, client, admin_user):
        client.force_login(admin_user)
        resp = client.get(reverse('manage_course_create'))
        assert resp.status_code == 200
        assert b'Nouveau cours' in resp.content

    def test_create_course(self, client, admin_user):
        client.force_login(admin_user)
        data = {
            'title': 'Cours Django',
            'slug': 'cours-django',
            'short_description': 'Apprenez Django',
            'description': '# Django\nContenu',
            'price': 3000,
            'is_published': True,
        }
        resp = client.post(reverse('manage_course_create'), data)
        assert resp.status_code == 302  # redirect to modules
        assert Course.objects.filter(slug='cours-django').exists()

    def test_create_with_auto_slug(self, client, admin_user):
        client.force_login(admin_user)
        data = {
            'title': 'Mon Super Cours',
            'slug': '',
            'short_description': 'Accroche',
            'description': 'Contenu',
            'price': 0,
        }
        resp = client.post(reverse('manage_course_create'), data)
        assert resp.status_code == 302
        assert Course.objects.filter(slug='mon-super-cours').exists()


@pytest.mark.django_db
class TestManageCourseEdit:
    def test_edit_form_prefilled(self, client, admin_user, course):
        client.force_login(admin_user)
        resp = client.get(reverse('manage_course_edit', args=[course.slug]))
        assert resp.status_code == 200
        assert course.title in resp.content.decode()

    def test_edit_saves(self, client, admin_user, course):
        client.force_login(admin_user)
        data = {
            'title': 'Nouveau Titre',
            'slug': course.slug,
            'short_description': 'Nouveau résumé',
            'description': 'Nouveau contenu',
            'price': 9000,
        }
        resp = client.post(reverse('manage_course_edit', args=[course.slug]), data)
        assert resp.status_code == 302
        course.refresh_from_db()
        assert course.title == 'Nouveau Titre'
        assert course.price == 9000

    def test_edit_saves_htmx_autosave(self, client, admin_user, course):
        client.force_login(admin_user)
        data = {
            'title': 'Titre Autosave',
            'slug': course.slug,
            'short_description': 'Sauvegarde auto',
            'description': 'Contenu',
            'price': 4000,
        }
        resp = client.post(reverse('manage_course_edit', args=[course.slug]), data, HTTP_HX_REQUEST='true')
        assert resp.status_code == 200
        assert 'Sauvegardé' in resp.content.decode()
        course.refresh_from_db()
        assert course.title == 'Titre Autosave'
        assert course.price == 4000

    def test_edit_htmx_error(self, client, admin_user, course):
        client.force_login(admin_user)
        data = {
            'title': '',  # Title is required, should trigger error
            'slug': course.slug,
        }
        resp = client.post(reverse('manage_course_edit', args=[course.slug]), data, HTTP_HX_REQUEST='true')
        assert resp.status_code == 400
        assert 'Erreur' in resp.content.decode()


@pytest.mark.django_db
class TestManageCourseDelete:
    def test_delete_course(self, client, admin_user, course):
        client.force_login(admin_user)
        resp = client.post(reverse('manage_course_delete', args=[course.slug]))
        assert resp.status_code == 200
        assert not Course.objects.filter(slug=course.slug).exists()


@pytest.mark.django_db
class TestManageModules:
    @pytest.fixture
    def module(self, course):
        return course.modules.create(title='Module 1', order=1)

    def test_modules_page(self, client, admin_user, course):
        client.force_login(admin_user)
        resp = client.get(reverse('manage_course_modules', args=[course.slug]))
        assert resp.status_code == 200

    def test_add_module(self, client, admin_user, course):
        client.force_login(admin_user)
        resp = client.post(
            reverse('manage_course_modules', args=[course.slug]),
            {'title': 'Nouveau Module'},
        )
        assert resp.status_code == 200 or resp.status_code == 302
        assert course.modules.filter(title='Nouveau Module').exists()

    def test_rename_module(self, client, admin_user, course, module):
        client.force_login(admin_user)
        resp = client.post(
            reverse('manage_module_edit', args=[course.slug, module.id]),
            {'title': 'Module Renommé'},
        )
        assert resp.status_code == 200
        module.refresh_from_db()
        assert module.title == 'Module Renommé'

    def test_delete_module(self, client, admin_user, course, module):
        client.force_login(admin_user)
        resp = client.post(reverse('manage_module_delete', args=[course.slug, module.id]))
        assert resp.status_code == 200
        assert not Module.objects.filter(id=module.id).exists()

    def test_reorder_modules(self, client, admin_user, course):
        client.force_login(admin_user)
        m1 = course.modules.create(title='A', order=1)
        m2 = course.modules.create(title='B', order=2)
        resp = client.post(
            reverse('manage_module_reorder', args=[course.slug]),
            {'module_order': [m2.id, m1.id]},
        )
        assert resp.status_code == 200
        m1.refresh_from_db()
        m2.refresh_from_db()
        assert m2.order < m1.order


@pytest.mark.django_db
class TestManageLessons:
    @pytest.fixture
    def module(self, course):
        return course.modules.create(title='Module Test', order=1)

    @pytest.fixture
    def lesson(self, module):
        return module.lessons.create(title='Leçon 1', slug='lecon-1', order=1)

    def test_lessons_page(self, client, admin_user, course, module):
        client.force_login(admin_user)
        resp = client.get(reverse('manage_module_lessons', args=[course.slug, module.id]))
        assert resp.status_code == 200

    def test_add_lesson(self, client, admin_user, course, module):
        client.force_login(admin_user)
        resp = client.post(
            reverse('manage_module_lessons', args=[course.slug, module.id]),
            {'title': 'Nouvelle Leçon', 'slug': 'nouvelle-lecon'},
        )
        assert resp.status_code == 200 or resp.status_code == 302
        assert module.lessons.filter(slug='nouvelle-lecon').exists()

    def test_add_lesson_auto_slug(self, client, admin_user, course, module):
        client.force_login(admin_user)
        resp = client.post(
            reverse('manage_module_lessons', args=[course.slug, module.id]),
            {'title': 'Ma Grande Leçon', 'slug': ''},
        )
        assert resp.status_code == 200 or resp.status_code == 302
        assert module.lessons.filter(slug='ma-grande-lecon').exists()

    def test_edit_lesson(self, client, admin_user, course, module, lesson):
        client.force_login(admin_user)
        resp = client.post(
            reverse('manage_lesson_edit', args=[course.slug, module.id, lesson.id]),
            {'title': 'Nouveau Titre', 'slug': 'nouveau-slug', 'is_free': 'on'},
        )
        assert resp.status_code == 200
        lesson.refresh_from_db()
        assert lesson.title == 'Nouveau Titre'
        assert lesson.slug == 'nouveau-slug'
        assert lesson.is_free is True

    def test_delete_lesson(self, client, admin_user, course, module, lesson):
        client.force_login(admin_user)
        resp = client.post(
            reverse('manage_lesson_delete', args=[course.slug, module.id, lesson.id]),
        )
        assert resp.status_code == 200
        assert not Lesson.objects.filter(id=lesson.id).exists()

    def test_reorder_lessons(self, client, admin_user, course, module):
        client.force_login(admin_user)
        l1 = module.lessons.create(title='A', slug='a', order=1)
        l2 = module.lessons.create(title='B', slug='b', order=2)
        resp = client.post(
            reverse('manage_lesson_reorder', args=[course.slug, module.id]),
            {'lesson_order': [l2.id, l1.id]},
        )
        assert resp.status_code == 200
        l1.refresh_from_db()
        l2.refresh_from_db()
        assert l2.order < l1.order
