import pytest
from django.urls import reverse

from courses.models import Course, Lesson, Module
from instructors.decorators import is_instructor
from instructors.models import InstructorPlan, InstructorProfile, InstructorRequest

pytestmark = pytest.mark.django_db


# ── Fixtures ────────────────────────────────────────


@pytest.fixture
def starter_plan():
    return InstructorPlan.objects.create(
        name='Starter', slug='starter', price=5000,
        max_courses=1, max_modules_per_course=5,
        max_lessons_per_course=10, revenue_percent=70,
        features="1 formation\n70% des revenus",
        order=1,
    )


@pytest.fixture
def pro_plan():
    return InstructorPlan.objects.create(
        name='Pro', slug='pro', price=12000,
        max_courses=3, max_modules_per_course=15,
        max_lessons_per_course=50, revenue_percent=80,
        is_featured=True, order=2,
    )


@pytest.fixture
def inactive_plan():
    return InstructorPlan.objects.create(
        name='Ancien', slug='ancien', price=999,
        max_courses=1, revenue_percent=50, is_active=False, order=99,
    )


@pytest.fixture
def instructor_user(student, starter_plan):
    """Un utilisateur avec un profil instructeur actif (plan Starter)."""
    InstructorProfile.objects.create(
        user=student,
        plan=starter_plan,
        max_courses=starter_plan.max_courses,
        max_modules_per_course=starter_plan.max_modules_per_course,
        max_lessons_per_course=starter_plan.max_lessons_per_course,
        revenue_percent=starter_plan.revenue_percent,
    )
    return student


# ── Models ──────────────────────────────────────────


class TestInstructorPlanModel:
    def test_str(self, starter_plan):
        assert "Starter" in str(starter_plan)
        assert "5000" in str(starter_plan)

    def test_get_features_list(self, starter_plan):
        features = starter_plan.get_features_list()
        assert len(features) == 2
        assert features[0] == "1 formation"

    def test_get_features_list_empty(self):
        plan = InstructorPlan(name='Vide', features='')
        assert plan.get_features_list() == []

    def test_ordering(self, starter_plan, pro_plan):
        plans = list(InstructorPlan.objects.values_list('slug', flat=True))
        assert plans.index('starter') < plans.index('pro')


class TestInstructorRequestModel:
    def test_str(self, student, starter_plan):
        req = InstructorRequest(user=student, plan=starter_plan, status='PENDING')
        assert student.email in str(req)
        assert "Starter" in str(req)

    def test_default_status_is_pending(self, student, starter_plan):
        req = InstructorRequest.objects.create(
            user=student, plan=starter_plan, payment_proof='test.jpg',
        )
        assert req.status == 'PENDING'


class TestInstructorProfileModel:
    def test_str(self, instructor_user):
        profile = instructor_user.instructor_profile
        assert instructor_user.email in str(profile)

    def test_courses_remaining_with_limit(self, instructor_user):
        profile = instructor_user.instructor_profile
        assert profile.courses_remaining == 1  # max=1, used=0

    def test_courses_remaining_after_creating_course(self, instructor_user):
        Course.objects.create(
            title='Mon Cours', slug='mon-cours',
            short_description='desc', price=1000,
            instructor=instructor_user,
        )
        profile = instructor_user.instructor_profile
        assert profile.courses_remaining == 0

    def test_courses_remaining_unlimited(self, student, pro_plan):
        profile = InstructorProfile.objects.create(
            user=student, plan=pro_plan,
            max_courses=0, revenue_percent=80,
        )
        assert profile.courses_remaining is None

    def test_can_create_course_true(self, instructor_user):
        assert instructor_user.instructor_profile.can_create_course is True

    def test_can_create_course_false_when_limit_reached(self, instructor_user):
        Course.objects.create(
            title='Cours 1', slug='cours-1',
            short_description='desc', price=1000,
            instructor=instructor_user,
        )
        assert instructor_user.instructor_profile.can_create_course is False


# ── Signal ──────────────────────────────────────────


class TestApprovalSignal:
    def test_approval_creates_profile(self, student, starter_plan):
        req = InstructorRequest.objects.create(
            user=student, plan=starter_plan, payment_proof='test.jpg',
        )
        req.status = 'APPROVED'
        req.save()

        profile = InstructorProfile.objects.get(user=student)
        assert profile.plan == starter_plan
        assert profile.max_courses == starter_plan.max_courses
        assert profile.revenue_percent == starter_plan.revenue_percent
        assert profile.is_active is True

    def test_approval_updates_existing_profile(self, instructor_user, pro_plan):
        """Si l'instructeur upgrade, le profil est mis à jour."""
        InstructorRequest.objects.create(
            user=instructor_user, plan=pro_plan, payment_proof='test.jpg',
            status='APPROVED',
        )
        # Le signal a déjà tourné au create. Force re-save pour tester.
        instructor_user.instructor_profile.refresh_from_db()
        assert instructor_user.instructor_profile.plan == pro_plan
        assert instructor_user.instructor_profile.max_courses == 3

    def test_rejection_does_not_create_profile(self, student, starter_plan):
        req = InstructorRequest.objects.create(
            user=student, plan=starter_plan, payment_proof='test.jpg',
        )
        req.status = 'REJECTED'
        req.save()

        assert not InstructorProfile.objects.filter(user=student).exists()

    def test_pending_does_not_create_profile(self, student, starter_plan):
        InstructorRequest.objects.create(
            user=student, plan=starter_plan, payment_proof='test.jpg',
        )
        assert not InstructorProfile.objects.filter(user=student).exists()


# ── Decorators ──────────────────────────────────────


class TestIsInstructor:
    def test_active_instructor(self, instructor_user):
        assert is_instructor(instructor_user) is True

    def test_non_instructor(self, student):
        assert is_instructor(student) is False

    def test_inactive_instructor(self, instructor_user):
        instructor_user.instructor_profile.is_active = False
        instructor_user.instructor_profile.save()
        assert is_instructor(instructor_user) is False


# ── Views ───────────────────────────────────────────


class TestPlansView:
    def test_plans_page_public(self, client, starter_plan, pro_plan):
        resp = client.get(reverse('instructor_plans'))
        assert resp.status_code == 200
        assert 'Starter' in resp.content.decode()
        assert 'Pro' in resp.content.decode()

    def test_inactive_plan_hidden(self, client, starter_plan, inactive_plan):
        resp = client.get(reverse('instructor_plans'))
        content = resp.content.decode()
        assert 'Starter' in content
        assert 'Ancien' not in content

    def test_authenticated_with_profile_shows_flag(self, client, instructor_user):
        client.force_login(instructor_user)
        resp = client.get(reverse('instructor_plans'))
        assert resp.context['has_profile'] is True

    def test_authenticated_with_pending_request(self, client, student, starter_plan):
        InstructorRequest.objects.create(
            user=student, plan=starter_plan, payment_proof='test.jpg',
        )
        client.force_login(student)
        resp = client.get(reverse('instructor_plans'))
        assert resp.context['has_pending'] is True


class TestRequestView:
    def test_requires_login(self, client, starter_plan):
        url = reverse('instructor_request', args=[starter_plan.slug])
        resp = client.get(url)
        assert resp.status_code == 302
        assert '/accounts/login/' in resp.url

    def test_shows_form(self, client, student, starter_plan):
        client.force_login(student)
        resp = client.get(reverse('instructor_request', args=[starter_plan.slug]))
        assert resp.status_code == 200
        assert 'Starter' in resp.content.decode()

    def test_already_instructor_redirects(self, client, instructor_user, starter_plan):
        client.force_login(instructor_user)
        resp = client.get(reverse('instructor_request', args=[starter_plan.slug]))
        assert resp.status_code == 302
        assert reverse('instructor_dashboard') in resp.url

    def test_already_pending_redirects(self, client, student, starter_plan):
        InstructorRequest.objects.create(
            user=student, plan=starter_plan, payment_proof='test.jpg',
        )
        client.force_login(student)
        resp = client.get(reverse('instructor_request', args=[starter_plan.slug]))
        assert resp.status_code == 302

    def test_inactive_plan_404(self, client, student, inactive_plan):
        client.force_login(student)
        resp = client.get(reverse('instructor_request', args=[inactive_plan.slug]))
        assert resp.status_code == 404


class TestPendingView:
    def test_requires_login(self, client):
        resp = client.get(reverse('instructor_request_pending'))
        assert resp.status_code == 302

    def test_shows_pending_page(self, client, student, starter_plan):
        InstructorRequest.objects.create(
            user=student, plan=starter_plan, payment_proof='test.jpg',
        )
        client.force_login(student)
        resp = client.get(reverse('instructor_request_pending'))
        assert resp.status_code == 200


class TestDashboardView:
    def test_requires_instructor(self, client, student):
        client.force_login(student)
        resp = client.get(reverse('instructor_dashboard'))
        assert resp.status_code == 302

    def test_anonymous_redirects(self, client):
        resp = client.get(reverse('instructor_dashboard'))
        assert resp.status_code == 302

    def test_instructor_sees_dashboard(self, client, instructor_user):
        client.force_login(instructor_user)
        resp = client.get(reverse('instructor_dashboard'))
        assert resp.status_code == 200

    def test_dashboard_shows_courses(self, client, instructor_user):
        Course.objects.create(
            title='Mon Cours', slug='mon-cours-dash',
            short_description='desc', price=1000,
            instructor=instructor_user,
        )
        client.force_login(instructor_user)
        resp = client.get(reverse('instructor_dashboard'))
        assert 'Mon Cours' in resp.content.decode()

    def test_dashboard_context_has_counters(self, client, instructor_user):
        """Le contexte du dashboard contient les compteurs globaux."""
        course = Course.objects.create(
            title='Compteur Test', slug='compteur-test',
            short_description='desc', price=1000,
            instructor=instructor_user,
        )
        m = Module.objects.create(course=course, title='M1', order=1)
        Lesson.objects.create(module=m, title='L1', slug='l1-ct', order=1)
        Lesson.objects.create(module=m, title='L2', slug='l2-ct', order=2)

        client.force_login(instructor_user)
        resp = client.get(reverse('instructor_dashboard'))
        assert resp.context['total_modules'] == 1
        assert resp.context['total_lessons'] == 2
        assert resp.context['total_students'] == 0

    def test_dashboard_annotates_per_course_counts(self, client, instructor_user):
        """Chaque cours du dashboard a modules_count, lessons_count, students_count."""
        course = Course.objects.create(
            title='Annotated', slug='annotated-c',
            short_description='desc', price=1000,
            instructor=instructor_user,
        )
        m1 = Module.objects.create(course=course, title='M1', order=1)
        m2 = Module.objects.create(course=course, title='M2', order=2)
        Lesson.objects.create(module=m1, title='L1', slug='l1-ann', order=1)
        Lesson.objects.create(module=m2, title='L2', slug='l2-ann', order=1)
        Lesson.objects.create(module=m2, title='L3', slug='l3-ann', order=2)

        from access.models import AccessRequest
        from users.models import User
        s1 = User.objects.create_user(email='s1@t.com', password='pw')
        AccessRequest.objects.create(student=s1, course=course, status='APPROVED')
        s2 = User.objects.create_user(email='s2@t.com', password='pw')
        AccessRequest.objects.create(student=s2, course=course, status='PENDING')

        client.force_login(instructor_user)
        resp = client.get(reverse('instructor_dashboard'))
        c = list(resp.context['my_courses'])[0]
        assert c.modules_count == 2
        assert c.lessons_count == 3
        assert c.students_count == 1  # only APPROVED

    def test_dashboard_students_link_present(self, client, instructor_user):
        """Le dashboard affiche un lien vers la page étudiants de chaque cours."""
        course = Course.objects.create(
            title='Lien Étudiants', slug='lien-etudiants',
            short_description='desc', price=1000,
            instructor=instructor_user,
        )
        client.force_login(instructor_user)
        resp = client.get(reverse('instructor_dashboard'))
        expected_url = reverse('manage_course_students', args=[course.slug])
        assert expected_url in resp.content.decode()

    def test_dashboard_counters_multi_courses(self, client, instructor_user):
        """Les totaux globaux s'additionnent sur plusieurs formations."""
        # Augmenter max_courses
        instructor_user.instructor_profile.max_courses = 5
        instructor_user.instructor_profile.save()

        c1 = Course.objects.create(
            title='C1', slug='c1-multi',
            short_description='d', price=1000,
            instructor=instructor_user,
        )
        c2 = Course.objects.create(
            title='C2', slug='c2-multi',
            short_description='d', price=2000,
            instructor=instructor_user,
        )
        m1 = Module.objects.create(course=c1, title='M1', order=1)
        Lesson.objects.create(module=m1, title='L1', slug='l1-mc', order=1)
        m2 = Module.objects.create(course=c2, title='M2', order=1)
        m3 = Module.objects.create(course=c2, title='M3', order=2)
        Lesson.objects.create(module=m2, title='L2', slug='l2-mc', order=1)
        Lesson.objects.create(module=m3, title='L3', slug='l3-mc', order=1)
        Lesson.objects.create(module=m3, title='L4', slug='l4-mc', order=2)

        from access.models import AccessRequest
        from users.models import User
        s = User.objects.create_user(email='sm@t.com', password='pw')
        AccessRequest.objects.create(student=s, course=c1, status='APPROVED')
        AccessRequest.objects.create(student=s, course=c2, status='APPROVED')

        client.force_login(instructor_user)
        resp = client.get(reverse('instructor_dashboard'))
        assert resp.context['total_modules'] == 3  # 1 + 2
        assert resp.context['total_lessons'] == 4   # 1 + 3
        assert resp.context['total_students'] == 2  # 1 per course

    def test_dashboard_empty_state(self, client, instructor_user):
        """Le dashboard sans cours affiche l'état vide."""
        client.force_login(instructor_user)
        resp = client.get(reverse('instructor_dashboard'))
        assert resp.context['total_modules'] == 0
        assert resp.context['total_lessons'] == 0
        assert resp.context['total_students'] == 0
        assert 'Pas encore de formation' in resp.content.decode()


class TestCourseCreateView:
    def test_requires_instructor(self, client, student):
        client.force_login(student)
        resp = client.get(reverse('instructor_course_create'))
        assert resp.status_code == 302

    def test_shows_form(self, client, instructor_user):
        client.force_login(instructor_user)
        resp = client.get(reverse('instructor_course_create'))
        assert resp.status_code == 200

    def test_create_course(self, client, instructor_user):
        client.force_login(instructor_user)
        resp = client.post(reverse('instructor_course_create'), {
            'title': 'Nouveau Cours',
            'slug': 'nouveau-cours',
            'short_description': 'Un cours test',
            'description': 'Description complète',
            'price': 3000,
        })
        assert resp.status_code == 302
        course = Course.objects.get(slug='nouveau-cours')
        assert course.instructor == instructor_user

    def test_create_course_can_publish(self, client, instructor_user):
        """L'instructeur peut choisir de publier son cours."""
        client.force_login(instructor_user)
        client.post(reverse('instructor_course_create'), {
            'title': 'Tentative Publi',
            'slug': 'tentative-publi',
            'short_description': 'desc',
            'description': 'desc',
            'price': 1000,
            'is_published': 'on',
        })
        course = Course.objects.get(slug='tentative-publi')
        assert course.is_published is True

    def test_create_course_default_unpublished(self, client, instructor_user):
        """Sans cocher 'publier', le cours reste en brouillon."""
        client.force_login(instructor_user)
        client.post(reverse('instructor_course_create'), {
            'title': 'Brouillon',
            'slug': 'brouillon',
            'short_description': 'desc',
            'description': 'desc',
            'price': 1000,
        })
        course = Course.objects.get(slug='brouillon')
        assert course.is_published is False

    def test_create_form_has_publish_field(self, client, instructor_user):
        """Le formulaire instructeur contient is_published mais pas is_featured."""
        client.force_login(instructor_user)
        resp = client.get(reverse('instructor_course_create'))
        form = resp.context['form']
        assert 'is_published' in form.fields
        assert 'is_featured' not in form.fields

    def test_limit_reached_redirects(self, client, instructor_user):
        Course.objects.create(
            title='Cours Existant', slug='cours-existant',
            short_description='desc', price=1000,
            instructor=instructor_user,
        )
        client.force_login(instructor_user)
        resp = client.get(reverse('instructor_course_create'))
        assert resp.status_code == 302
        assert reverse('instructor_dashboard') in resp.url


class TestCourseEditView:
    def test_edit_own_course(self, client, instructor_user):
        course = Course.objects.create(
            title='Mon Cours', slug='mon-cours-edit',
            short_description='desc', price=1000,
            instructor=instructor_user,
        )
        client.force_login(instructor_user)
        resp = client.get(reverse('instructor_course_edit', args=[course.slug]))
        assert resp.status_code == 200

    def test_cannot_edit_others_course(self, client, instructor_user, admin_user, starter_plan):
        # Créer un autre instructeur
        InstructorProfile.objects.create(
            user=admin_user, plan=starter_plan,
            max_courses=5, revenue_percent=70,
        )
        course = Course.objects.create(
            title='Autre Cours', slug='autre-cours',
            short_description='desc', price=1000,
            instructor=admin_user,
        )
        client.force_login(instructor_user)
        resp = client.get(reverse('instructor_course_edit', args=[course.slug]))
        assert resp.status_code == 404

    def test_edit_saves_changes(self, client, instructor_user):
        course = Course.objects.create(
            title='Ancien Titre', slug='ancien-titre',
            short_description='desc', price=1000,
            instructor=instructor_user,
        )
        client.force_login(instructor_user)
        resp = client.post(reverse('instructor_course_edit', args=[course.slug]), {
            'title': 'Nouveau Titre',
            'slug': 'ancien-titre',
            'short_description': 'desc modifiée',
            'description': 'nouvelle description',
            'price': 2000,
        })
        assert resp.status_code == 302
        course.refresh_from_db()
        assert course.title == 'Nouveau Titre'

    def test_edit_can_toggle_publish(self, client, instructor_user):
        """L'instructeur peut publier/dépublier son cours via l'édition."""
        course = Course.objects.create(
            title='Draft Cours', slug='draft-cours',
            short_description='desc', price=1000,
            instructor=instructor_user, is_published=False,
        )
        client.force_login(instructor_user)
        client.post(reverse('instructor_course_edit', args=[course.slug]), {
            'title': 'Draft Cours',
            'slug': 'draft-cours',
            'short_description': 'desc',
            'description': 'new',
            'price': 1000,
            'is_published': 'on',
        })
        course.refresh_from_db()
        assert course.is_published is True


class TestPlanUpgrade:
    """Tests du flow d'upgrade d'offre instructeur."""

    def test_instructor_can_view_plans_with_upgrade(self, client, instructor_user, pro_plan):
        """Un instructeur voit les offres avec possibilité d'upgrade."""
        client.force_login(instructor_user)
        resp = client.get(reverse('instructor_plans'))
        assert resp.status_code == 200
        assert resp.context['current_plan'] is not None
        content = resp.content.decode()
        assert 'Passer à' in content  # btn upgrade vers plan supérieur

    def test_instructor_same_plan_redirects(self, client, instructor_user, starter_plan):
        """Demander le même plan redirige avec message."""
        client.force_login(instructor_user)
        resp = client.get(reverse('instructor_request', args=[starter_plan.slug]))
        assert resp.status_code == 302
        assert reverse('instructor_dashboard') in resp.url

    def test_instructor_can_request_upgrade(self, client, instructor_user, pro_plan):
        """Un instructeur peut envoyer une demande d'upgrade."""
        import io

        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image
        # Créer une vraie image
        buf = io.BytesIO()
        Image.new('RGB', (10, 10), color='red').save(buf, format='JPEG')
        buf.seek(0)
        img = SimpleUploadedFile('proof.jpg', buf.read(), content_type='image/jpeg')
        client.force_login(instructor_user)
        resp = client.post(
            reverse('instructor_request', args=[pro_plan.slug]),
            {'payment_proof': img},
        )
        assert resp.status_code == 302
        req = InstructorRequest.objects.filter(user=instructor_user, plan=pro_plan).first()
        assert req is not None
        assert req.status == 'PENDING'

    def test_upgrade_request_form_shows_context(self, client, instructor_user, pro_plan):
        """Le formulaire d'upgrade affiche le contexte is_upgrade."""
        client.force_login(instructor_user)
        resp = client.get(reverse('instructor_request', args=[pro_plan.slug]))
        assert resp.status_code == 200
        assert resp.context['is_upgrade'] is True
        assert resp.context['current_plan'] is not None

    def test_upgrade_approval_updates_profile(self, instructor_user, pro_plan):
        """L'approbation d'un upgrade met à jour le profil avec les nouvelles limites."""
        req = InstructorRequest.objects.create(
            user=instructor_user, plan=pro_plan,
            payment_proof='fake.jpg', status='PENDING',
        )
        req.status = 'APPROVED'
        req.save()

        instructor_user.instructor_profile.refresh_from_db()
        profile = instructor_user.instructor_profile
        assert profile.plan == pro_plan
        assert profile.max_courses == pro_plan.max_courses
        assert profile.max_modules_per_course == pro_plan.max_modules_per_course
        assert profile.revenue_percent == pro_plan.revenue_percent

    def test_pending_request_blocks_second_request(self, client, instructor_user, pro_plan):
        """Impossible de soumettre un 2e upgrade si un est déjà en attente."""
        InstructorRequest.objects.create(
            user=instructor_user, plan=pro_plan,
            payment_proof='fake.jpg', status='PENDING',
        )
        client.force_login(instructor_user)
        resp = client.get(reverse('instructor_request', args=[pro_plan.slug]))
        assert resp.status_code == 302
        assert reverse('instructor_request_pending') in resp.url

    def test_dashboard_shows_upgrade_link(self, client, instructor_user):
        """Le dashboard affiche un lien vers les offres pour changer."""
        client.force_login(instructor_user)
        resp = client.get(reverse('instructor_dashboard'))
        content = resp.content.decode()
        assert reverse('instructor_plans') in content
        assert "Changer d" in content


# ── Management Command ──────────────────────────────


class TestSeedCommand:
    def test_seed_creates_plans(self):
        from django.core.management import call_command
        call_command('seed_instructor_plans')
        assert InstructorPlan.objects.count() == 3
        assert InstructorPlan.objects.get(slug='starter').price == 5000
        assert InstructorPlan.objects.get(slug='pro').is_featured is True
        assert InstructorPlan.objects.get(slug='expert').revenue_percent == 90

    def test_seed_is_idempotent(self):
        from django.core.management import call_command
        call_command('seed_instructor_plans')
        call_command('seed_instructor_plans')
        assert InstructorPlan.objects.count() == 3


# ── Builder Access (Instructor uses admin builder) ──


@pytest.fixture
def instructor_course(instructor_user):
    """Un cours appartenant à l'instructeur."""
    return Course.objects.create(
        title='Mon Cours Instructeur', slug='mon-cours-inst',
        short_description='desc', price=1000,
        instructor=instructor_user, is_published=True,
    )


@pytest.fixture
def instructor_module(instructor_course):
    return Module.objects.create(
        course=instructor_course, title='Module 1', order=1,
    )


@pytest.fixture
def instructor_lesson(instructor_module):
    return Lesson.objects.create(
        module=instructor_module, title='Leçon 1', slug='lecon-1', order=1,
    )


@pytest.fixture
def other_course(admin_user):
    """Un cours appartenant à un autre utilisateur (admin)."""
    return Course.objects.create(
        title='Cours Admin', slug='cours-admin',
        short_description='desc', price=1000,
        instructor=admin_user, is_published=True,
    )


class TestInstructorBuilderAccess:
    """Tests : l'instructeur accède au builder pour SES cours uniquement."""

    def test_instructor_can_access_modules(self, client, instructor_user, instructor_course):
        client.force_login(instructor_user)
        resp = client.get(reverse('manage_course_modules', args=[instructor_course.slug]))
        assert resp.status_code == 200

    def test_instructor_cannot_access_others_modules(self, client, instructor_user, other_course):
        client.force_login(instructor_user)
        resp = client.get(reverse('manage_course_modules', args=[other_course.slug]))
        assert resp.status_code == 404

    def test_instructor_can_access_lessons(self, client, instructor_user, instructor_course, instructor_module):
        client.force_login(instructor_user)
        resp = client.get(reverse('manage_module_lessons', args=[instructor_course.slug, instructor_module.id]))
        assert resp.status_code == 200

    def test_instructor_cannot_access_others_lessons(self, client, instructor_user, other_course, admin_user):
        module = Module.objects.create(course=other_course, title='M', order=1)
        client.force_login(instructor_user)
        resp = client.get(reverse('manage_module_lessons', args=[other_course.slug, module.id]))
        assert resp.status_code == 404

    def test_instructor_can_access_builder(self, client, instructor_user, instructor_course, instructor_lesson):
        client.force_login(instructor_user)
        resp = client.get(reverse('manage_lesson_content', args=[instructor_course.slug, instructor_lesson.slug]))
        assert resp.status_code == 200

    def test_instructor_can_access_landing(self, client, instructor_user, instructor_course):
        client.force_login(instructor_user)
        resp = client.get(reverse('manage_course_landing', args=[instructor_course.slug]))
        assert resp.status_code == 200

    def test_instructor_cannot_access_others_landing(self, client, instructor_user, other_course):
        client.force_login(instructor_user)
        resp = client.get(reverse('manage_course_landing', args=[other_course.slug]))
        assert resp.status_code == 404

    def test_instructor_can_edit_course(self, client, instructor_user, instructor_course):
        client.force_login(instructor_user)
        resp = client.get(reverse('manage_course_edit', args=[instructor_course.slug]))
        assert resp.status_code == 200

    def test_instructor_cannot_edit_others_course(self, client, instructor_user, other_course):
        client.force_login(instructor_user)
        resp = client.get(reverse('manage_course_edit', args=[other_course.slug]))
        assert resp.status_code == 404

    def test_student_cannot_access_builder(self, client, student, instructor_course):
        """Un étudiant sans profil instructeur ne peut pas accéder au builder."""
        # Need a fresh student (not the instructor_user fixture)
        from users.models import User
        normal_user = User.objects.create_user(email='normal@test.com', password='pass123')
        client.force_login(normal_user)
        resp = client.get(reverse('manage_course_modules', args=[instructor_course.slug]))
        assert resp.status_code == 302  # redirect to login

    def test_admin_can_access_any_course(self, client, admin_user, instructor_course):
        client.force_login(admin_user)
        resp = client.get(reverse('manage_course_modules', args=[instructor_course.slug]))
        assert resp.status_code == 200

    def test_instructor_can_add_module(self, client, instructor_user, instructor_course):
        client.force_login(instructor_user)
        resp = client.post(
            reverse('manage_course_modules', args=[instructor_course.slug]),
            {'title': 'Nouveau Module'},
            HTTP_HX_REQUEST='true',
        )
        assert resp.status_code == 200
        assert Module.objects.filter(course=instructor_course, title='Nouveau Module').exists()

    def test_instructor_can_delete_course(self, client, instructor_user, instructor_course):
        client.force_login(instructor_user)
        resp = client.post(reverse('manage_course_delete', args=[instructor_course.slug]))
        assert resp.status_code == 200
        assert not Course.objects.filter(slug='mon-cours-inst').exists()

    def test_instructor_cannot_delete_others_course(self, client, instructor_user, other_course):
        client.force_login(instructor_user)
        resp = client.post(reverse('manage_course_delete', args=[other_course.slug]))
        assert resp.status_code == 404

    def test_instructor_can_access_students_stats(self, client, instructor_user, instructor_course):
        client.force_login(instructor_user)
        resp = client.get(reverse('manage_course_students', args=[instructor_course.slug]))
        assert resp.status_code == 200

    def test_instructor_cannot_access_admin_course_list(self, client, instructor_user):
        """L'instructeur ne peut PAS accéder à la liste admin des cours."""
        client.force_login(instructor_user)
        resp = client.get(reverse('manage_course_list'))
        assert resp.status_code == 302  # redirect (staff_member_required)

    def test_instructor_cannot_create_via_admin(self, client, instructor_user):
        """L'instructeur ne peut PAS créer via la route admin."""
        client.force_login(instructor_user)
        resp = client.get(reverse('manage_course_create'))
        assert resp.status_code == 302  # redirect (staff_member_required)
