"""Garde-fous ajoutés lors du nettoyage : portée des réordonnancements, validation du quiz, slugs."""
import json

import pytest
from django.urls import reverse

from access.models import AccessRequest
from courses.models import ContentBlock, Course, Lesson, Module, StudentProgress
from courses.progress import get_course_progress, get_courses_progress
from instructors.models import InstructorPlan, InstructorProfile
from users.models import User


def _make_instructor(email):
    user = User.objects.create_user(email=email, password='password123')
    plan, _ = InstructorPlan.objects.get_or_create(slug='test', defaults={'name': 'Test', 'price': 0, 'max_courses': 5, 'max_modules_per_course': 5, 'max_lessons_per_course': 5, 'revenue_percent': 0})
    InstructorProfile.objects.create(
        user=user, plan=plan, is_active=True,
        max_courses=5, max_modules_per_course=5, max_lessons_per_course=5, revenue_percent=0,
    )
    return user


def _make_course(slug, instructor=None):
    return Course.objects.create(
        title=slug, slug=slug, short_description='x', description='x',
        price=0, is_published=True, instructor=instructor,
    )


@pytest.mark.django_db
class TestReorderScope:
    def test_instructor_cannot_reorder_foreign_modules(self, client):
        owner = _make_instructor('owner@test.com')
        attacker = _make_instructor('attacker@test.com')
        own_course = _make_course('own', attacker)
        foreign_course = _make_course('foreign', owner)
        m1 = Module.objects.create(course=foreign_course, title='A', order=1)
        m2 = Module.objects.create(course=foreign_course, title='B', order=2)

        client.force_login(attacker)
        url = reverse('manage_module_reorder', args=[own_course.slug])
        client.post(url, {'module_order': [m2.id, m1.id]})

        m1.refresh_from_db()
        m2.refresh_from_db()
        assert (m1.order, m2.order) == (1, 2)

    def test_instructor_cannot_reorder_foreign_blocks(self, client):
        owner = _make_instructor('owner@test.com')
        attacker = _make_instructor('attacker@test.com')
        course = _make_course('foreign', owner)
        lesson = Lesson.objects.create(module=Module.objects.create(course=course, title='M'), title='L', slug='l')
        b1 = ContentBlock.objects.create(lesson=lesson, type='text', order=1)
        b2 = ContentBlock.objects.create(lesson=lesson, type='text', order=2)

        client.force_login(attacker)
        client.post(reverse('update_block_order'), {'block_order': [b2.id, b1.id]})

        b1.refresh_from_db()
        b2.refresh_from_db()
        assert (b1.order, b2.order) == (1, 2)

    def test_owner_can_reorder_own_modules(self, client):
        owner = _make_instructor('owner@test.com')
        course = _make_course('own', owner)
        m1 = Module.objects.create(course=course, title='A', order=1)
        m2 = Module.objects.create(course=course, title='B', order=2)

        client.force_login(owner)
        client.post(reverse('manage_module_reorder', args=[course.slug]), {'module_order': [m2.id, m1.id, 'junk']})

        m1.refresh_from_db()
        m2.refresh_from_db()
        assert (m2.order, m1.order) == (1, 2)


@pytest.mark.django_db
class TestQuizValidation:
    @pytest.fixture
    def quiz_block(self, course):
        module = course.modules.create(title='M', order=1)
        lesson = module.lessons.create(title='L', slug='l', order=1)
        return ContentBlock.objects.create(lesson=lesson, type='quiz', order=1)

    @pytest.mark.parametrize('payload', [
        {'score': 11, 'total': 10},
        {'score': -1, 'total': 10},
        {'score': 1, 'total': 0},
        {'score': 'abc', 'total': 10},
        {'total': 10},
    ])
    def test_invalid_scores_are_rejected(self, client, student, quiz_block, payload):
        AccessRequest.objects.create(student=student, course=quiz_block.lesson.module.course, status='APPROVED')
        client.force_login(student)
        response = client.post(
            reverse('save_quiz_result', args=[quiz_block.id]),
            data=json.dumps(payload), content_type='application/json',
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestLessonSlugs:
    def test_duplicate_slug_in_course_is_suffixed(self, client, admin_user):
        course = _make_course('c')
        m1 = Module.objects.create(course=course, title='M1', order=1)
        m2 = Module.objects.create(course=course, title='M2', order=2)
        client.force_login(admin_user)

        client.post(reverse('manage_module_lessons', args=[course.slug, m1.id]), {'title': 'Intro', 'slug': 'intro'})
        client.post(reverse('manage_module_lessons', args=[course.slug, m2.id]), {'title': 'Intro', 'slug': 'intro'})

        slugs = sorted(Lesson.objects.filter(module__course=course).values_list('slug', flat=True))
        assert slugs == ['intro', 'intro-2']


@pytest.mark.django_db
class TestBatchProgress:
    def test_batch_matches_single_course_progress(self, student, course, free_course):
        for c in (course, free_course):
            module = c.modules.create(title='M', order=1)
            first = module.lessons.create(title='1', slug='un', order=1)
            module.lessons.create(title='2', slug='deux', order=2)
            StudentProgress.objects.create(student=student, lesson=first)

        batch = get_courses_progress(student, [course, free_course])
        for c in (course, free_course):
            single = get_course_progress(student, c)
            assert batch[c.id].percent == single.percent == 50
            assert batch[c.id].resume_lesson.slug == single.resume_lesson.slug == 'deux'


@pytest.mark.django_db
class TestPlanLimits:
    def test_module_limit_is_enforced_for_instructors(self, client):
        instructor = _make_instructor('limited@test.com')
        profile = instructor.instructor_profile
        profile.max_modules_per_course = 1
        profile.save()
        course = _make_course('limited', instructor)

        client.force_login(instructor)
        url = reverse('manage_course_modules', args=[course.slug])
        client.post(url, {'title': 'Premier'})
        client.post(url, {'title': 'Second'})

        assert course.modules.count() == 1

    def test_staff_is_never_limited(self, client, admin_user):
        course = _make_course('free')
        client.force_login(admin_user)
        url = reverse('manage_course_modules', args=[course.slug])
        client.post(url, {'title': 'A'})
        client.post(url, {'title': 'B'})
        assert course.modules.count() == 2


@pytest.mark.django_db
class TestTemplateComponents:
    def test_quiz_block_exposes_json_payload_not_inline_js(self, client, admin_user, course):
        module = course.modules.create(title='M', order=1)
        lesson = module.lessons.create(title='L', slug='l', order=1)
        block = ContentBlock.objects.create(lesson=lesson, type='quiz', quiz_title='Quiz', order=1)
        block.questions.create(
            question_text='<b>Q</b>', choice_a='A', choice_b='B', correct_answer='a', duration=10,
        )

        client.force_login(admin_user)
        html = client.get(reverse('lesson_detail', args=[course.slug, lesson.slug])).content.decode()

        assert f'id="quiz-data-{block.id}"' in html
        assert f"x-data=\"quiz('quiz-data-{block.id}'" in html
        assert '<b>Q</b>' not in html  # texte échappé, pas de HTML brut
        assert 'startQuiz()' in html and 'const getCookie' not in html

    def test_furigana_filter_escapes_html(self):
        from courses.templatetags.md import furigana_filter

        rendered = furigana_filter('<script>alert(1)</script>{漢字|かんじ}')
        assert '<script>' not in rendered
        assert '<ruby>漢字<rt>かんじ</rt></ruby>' in rendered

    def test_no_inline_style_or_script_in_templates(self):
        from pathlib import Path

        offenders = []
        for path in Path('templates').rglob('*.html'):
            text = path.read_text(encoding='utf-8')
            if '<style' in text or ' style="' in text or ' onclick="' in text:
                offenders.append(str(path))
            # Les seuls <script> admis chargent un fichier (src) ou portent des données JSON
            for line in text.splitlines():
                if '<script' in line and ' src=' not in line and 'application/json' not in line:
                    offenders.append(f'{path}: {line.strip()}')
        assert not offenders, offenders
