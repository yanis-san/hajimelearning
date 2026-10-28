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
    plan, _ = InstructorPlan.objects.get_or_create(
        slug='test',
        defaults={
            'name': 'Test',
            'price': 0,
            'max_courses': 5,
            'max_modules_per_course': 5,
            'max_lessons_per_course': 5,
            'revenue_percent': 0,
        },
    )
    InstructorProfile.objects.create(
        user=user,
        plan=plan,
        is_active=True,
        max_courses=5,
        max_modules_per_course=5,
        max_lessons_per_course=5,
        revenue_percent=0,
    )
    return user


def _make_course(slug, instructor=None):
    return Course.objects.create(
        title=slug,
        slug=slug,
        short_description='x',
        description='x',
        price=0,
        is_published=True,
        instructor=instructor,
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

    @pytest.mark.parametrize(
        'payload',
        [
            {'score': 11, 'total': 10},
            {'score': -1, 'total': 10},
            {'score': 1, 'total': 0},
            {'score': 'abc', 'total': 10},
            {'total': 10},
        ],
    )
    def test_invalid_scores_are_rejected(self, client, student, quiz_block, payload):
        AccessRequest.objects.create(student=student, course=quiz_block.lesson.module.course, status='APPROVED')
        client.force_login(student)
        response = client.post(
            reverse('save_quiz_result', args=[quiz_block.id]),
            data=json.dumps(payload),
            content_type='application/json',
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
            question_text='<b>Q</b>',
            choice_a='A',
            choice_b='B',
            correct_answer='a',
            duration=10,
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


@pytest.mark.django_db
class TestMarkdownSanitization:
    def test_md_filter_strips_dangerous_html(self):
        from courses.templatetags.md import render_markdown

        html = render_markdown(
            '<script>alert(1)</script>\n\n<img src=x onerror=alert(1)>\n\n[clic](javascript:alert(1))\n\n**gras**'
        )
        assert '<script' not in html and 'onerror' not in html and 'javascript:' not in html
        assert '<strong>gras</strong>' in html

    def test_md_filter_keeps_furigana_tables_and_links(self):
        from courses.templatetags.md import render_markdown

        html = render_markdown('{漢字|かんじ}\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n[site](https://example.com)')
        assert '<ruby>漢字<rt>かんじ</rt></ruby>' in html
        assert '<table>' in html
        assert 'href="https://example.com"' in html and 'noopener' in html

    def test_builder_preview_is_sanitized(self, client, admin_user):
        client.force_login(admin_user)
        response = client.post(reverse('preview_markdown'), {'text': '<script>x</script>**ok**'})
        content = response.content.decode()
        assert '<script>' not in content and '<strong>ok</strong>' in content

    def test_faq_and_testimonial_names_are_escaped(self):
        from courses.templatetags.md import faq_items, testimonial_items

        assert '<img' not in str(faq_items('### <img src=x onerror=1>\nreponse')[0][0])
        assert '<img' not in str(testimonial_items('### ★★★★★ | <img src=x onerror=1>\ntexte')[0]['name'])


class TestDesignConvention:
    def test_no_leftover_orange_palette(self):
        from pathlib import Path

        offenders = [str(p) for p in Path('templates').rglob('*.html') if '-orange-' in p.read_text(encoding='utf-8')]
        assert not offenders, f"Couleur d'interaction = primary, plus d'orange : {offenders}"

    def test_buttons_use_the_shared_component(self):
        from pathlib import Path

        offenders = []
        for path in Path('templates').rglob('*.html'):
            if path.name == 'btn.html':
                continue
            for line in path.read_text(encoding='utf-8').splitlines():
                if 'shadow-[' in line and 'hover:-translate-y' in line and ('<a ' in line or '<button' in line):
                    offenders.append(f'{path}: {line.strip()[:80]}')
        assert not offenders, offenders


@pytest.mark.django_db
class TestThrottling:
    def test_coupon_validation_is_rate_limited(self, client, course):
        url = reverse('validate_coupon', args=[course.id])
        for _ in range(10):
            assert 'Trop de tentatives' not in client.post(url, {'promo_code': 'NOPE'}).content.decode()
        assert 'Trop de tentatives' in client.post(url, {'promo_code': 'NOPE'}).content.decode()

    def test_activation_code_attempts_are_rate_limited(self, client, student, course):
        client.force_login(student)
        url = reverse('request_access', args=[course.id])
        for _ in range(5):
            client.post(url, {'submit_code': '1', 'code': 'bad-code'})
        response = client.post(url, {'submit_code': '1', 'code': 'bad-code'})
        assert any('Trop de tentatives' in str(m) for m in response.context['messages'])


@pytest.mark.django_db
class TestAccessServices:
    def test_discounted_price_and_coupon_errors(self, course):
        from access.models import Coupon
        from access.services import AccessError, find_valid_coupon

        Coupon.objects.create(code='PROMO20', discount_percent=20)
        coupon = find_valid_coupon(' promo20 ')
        assert coupon.discounted_price(course.price) == 4000
        with pytest.raises(AccessError):
            find_valid_coupon('INCONNU')

    def test_redeem_activation_code_is_single_use(self, student, course):
        from access.models import ActivationCode
        from access.services import AccessError, redeem_activation_code

        code = ActivationCode.objects.create(course=course)
        redeem_activation_code(student, course, str(code.code))
        with pytest.raises(AccessError):
            redeem_activation_code(student, course, str(code.code))


@pytest.mark.django_db
class TestCourseServices:
    @pytest.fixture
    def two_lessons(self, course):
        module = course.modules.create(title='M', order=1)
        first = module.lessons.create(title='1', slug='un', order=1)
        second = module.lessons.create(title='2', slug='deux', order=2)
        return first, second

    def test_completing_every_lesson_completes_course_and_queues_certificate(
        self, student, two_lessons, monkeypatch, django_capture_on_commit_callbacks
    ):
        from courses import services
        from courses.models import CourseCompletion

        queued = []
        monkeypatch.setattr(
            services.generate_certificate_pdf, 'delay', lambda completion_id: queued.append(completion_id)
        )
        first, second = two_lessons

        services.complete_lesson(student, first)
        assert not CourseCompletion.objects.exists()

        with django_capture_on_commit_callbacks(execute=True):
            progress = services.complete_lesson(student, second)

        assert progress.is_complete
        completion = CourseCompletion.objects.get()
        assert queued == [completion.id]

    def test_uncompleting_a_lesson_removes_the_completion(self, student, two_lessons, monkeypatch):
        from courses import services
        from courses.models import CourseCompletion

        monkeypatch.setattr(services.generate_certificate_pdf, 'delay', lambda completion_id: None)
        first, second = two_lessons
        services.complete_lesson(student, first)
        services.complete_lesson(student, second)
        assert CourseCompletion.objects.exists()

        services.uncomplete_lesson(student, second)
        assert not CourseCompletion.objects.exists()

    def test_record_quiz_result_rejects_inconsistent_scores(self, student, two_lessons):
        from courses.models import ContentBlock
        from courses.services import InvalidScore, record_quiz_result

        block = ContentBlock.objects.create(lesson=two_lessons[0], type='quiz', order=1)
        with pytest.raises(InvalidScore):
            record_quiz_result(student, block, 5, 3)
        record_quiz_result(student, block, 3, 5)
        assert block.attempts.count() == 1


@pytest.mark.django_db
class TestContactThrottle:
    def test_contact_form_is_rate_limited(self, client):
        from contact.models import ContactMessage, ContactReason

        reason = ContactReason.objects.create(label='Question')
        data = {
            'first_name': 'A',
            'last_name': 'B',
            'email': 'a@b.co',
            'reason': reason.pk,
            'message': 'Bonjour !',
        }
        for _ in range(5):
            client.post(reverse('contact'), data)
        response = client.post(reverse('contact'), data)

        assert ContactMessage.objects.count() == 5
        assert response.status_code == 200 and 'Trop de messages' in response.content.decode()


@pytest.mark.django_db
class TestBuilderAutosaveContract:
    @pytest.fixture
    def lesson(self, course):
        module = course.modules.create(title='M', order=1)
        return module.lessons.create(title='L', slug='l', order=1)

    def test_autosave_returns_block_list_and_trigger_header(self, client, admin_user, lesson):
        client.force_login(admin_user)
        url = reverse('add_block', args=[lesson.id, 'text'])
        response = client.post(url, {'text_content': 'Bonjour'}, headers={'X-Autosave': 'true', 'HX-Request': 'true'})

        assert response.status_code == 200
        block = ContentBlock.objects.get(lesson=lesson)
        detail = json.loads(response['HX-Trigger'])['builder-saved']
        assert detail['blockId'] == block.id
        assert detail['editUrl'] == reverse('edit_block', args=[block.id])
        assert 'hx-swap-oob' not in response.content.decode()  # le formulaire reste ouvert

    def test_explicit_save_closes_the_form(self, client, admin_user, lesson):
        client.force_login(admin_user)
        response = client.post(reverse('add_block', args=[lesson.id, 'text']), {'text_content': 'Bonjour'})

        assert 'HX-Trigger' not in response
        assert 'id="block-form-container" hx-swap-oob="innerHTML"' in response.content.decode()

    def test_invalid_autosave_is_rejected_without_swapping(self, client, admin_user, lesson):
        client.force_login(admin_user)
        response = client.post(
            reverse('add_block', args=[lesson.id, 'text']), {'video_id': 'x' * 500}, headers={'X-Autosave': 'true'}
        )
        assert response.status_code == 422 and ContentBlock.objects.count() == 0
