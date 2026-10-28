"""Rendu de bout en bout des pages principales : détecte tout template cassé après un refactor."""

import pytest
from django.urls import reverse

from courses.models import ContentBlock


@pytest.fixture
def full_course(course):
    module = course.modules.create(title='Module 1', order=1)
    lesson = module.lessons.create(title='Leçon 1', slug='lecon-1', order=1, is_free=True)
    ContentBlock.objects.create(lesson=lesson, type='text', text_content='# Titre\n\n{漢字|かんじ}', order=1)
    quiz = ContentBlock.objects.create(lesson=lesson, type='quiz', quiz_title='Quiz', order=2)
    quiz.questions.create(question_text='Q ?', choice_a='A', choice_b='B', correct_answer='a')
    course.landing_sections.create(section_type='faq', title='FAQ', body='### Q\nR', order=1)
    course.landing_sections.create(section_type='testimonials', title='Avis', body='### ★★★★★ | Marie\nSuper', order=2)
    return course, lesson


@pytest.mark.django_db
class TestPagesRender:
    @pytest.mark.parametrize('name', ['course_list', 'catalogue', 'contact', 'account_login', 'account_signup'])
    def test_public_pages(self, client, name):
        assert client.get(reverse(name)).status_code == 200

    def test_course_and_lesson_pages(self, client, student, full_course):
        course, lesson = full_course
        client.force_login(student)
        assert client.get(reverse('course_detail', args=[course.slug])).status_code == 200
        response = client.get(reverse('lesson_detail', args=[course.slug, lesson.slug]))
        assert response.status_code == 200
        assert b'quiz-data-' in response.content

    def test_student_pages(self, client, student, full_course):
        client.force_login(student)
        for name in ('user_dashboard', 'user_profile', 'my_notifications', 'my_questions'):
            assert client.get(reverse(name)).status_code == 200, name

    def test_manager_pages(self, client, admin_user, full_course):
        course, lesson = full_course
        client.force_login(admin_user)
        pages = [
            reverse('manage_course_list'),
            reverse('manage_course_create'),
            reverse('manage_course_edit', args=[course.slug]),
            reverse('manage_course_modules', args=[course.slug]),
            reverse('manage_module_lessons', args=[course.slug, course.modules.first().id]),
            reverse('manage_lesson_content', args=[course.slug, lesson.slug]),
            reverse('manage_course_landing', args=[course.slug]),
            reverse('manage_course_students', args=[course.slug]),
            reverse('course_detail', args=[course.slug]) + '?view=landing',
        ]
        for url in pages:
            assert client.get(url).status_code == 200, url

    def test_course_form_renders_all_tabs(self, client, admin_user, course):
        client.force_login(admin_user)
        html = client.get(reverse('manage_course_edit', args=[course.slug])).content.decode()
        for tab in ('infos', 'vente', 'seo'):
            assert f"x-show=\"tab === '{tab}'\"" in html

    def test_enrolled_student_sees_student_view_and_full_lesson(self, client, student, full_course):
        from access.models import AccessRequest

        course, lesson = full_course
        AccessRequest.objects.create(student=student, course=course, status='APPROVED')
        client.force_login(student)

        detail = client.get(reverse('course_detail', args=[course.slug])).content.decode()
        assert 'Progression' in detail

        html = client.get(reverse('lesson_detail', args=[course.slug, lesson.slug])).content.decode()
        for marker in ('Tout replier', 'quiz-data-', reverse('ask_question', args=[lesson.id])):
            assert marker in html, marker


@pytest.mark.django_db
def test_every_template_compiles():
    """Aucun template (composants Cotton compris) ne doit contenir d'erreur de syntaxe."""
    from pathlib import Path

    from django.template.loader import get_template

    broken = []
    for path in sorted(Path('templates').rglob('*.html')):
        name = path.relative_to('templates').as_posix()
        try:
            get_template(name)
        except Exception as exc:
            broken.append(f'{name}: {exc}')
    assert not broken, broken


@pytest.mark.django_db
def test_lesson_renders_every_block_type(client, student, course):
    from django.core.files.base import ContentFile

    module = course.modules.create(title='M', order=1)
    lesson = module.lessons.create(title='L', slug='l', order=1, is_free=True)
    ContentBlock.objects.create(lesson=lesson, type='text', text_content='texte', order=1)
    ContentBlock.objects.create(lesson=lesson, type='video', video_id='dQw4w9WgXcQ', order=2)
    for order, (kind, filename) in enumerate([('audio', 'a.mp3'), ('file', 'f.pdf'), ('anki', 'd.apkg')], start=3):
        block = ContentBlock.objects.create(lesson=lesson, type=kind, order=order)
        block.file_content.save(filename, ContentFile(b'x'))
        if kind == 'audio':
            block.related_file.save('t.pdf', ContentFile(b'%PDF'))
    ContentBlock.objects.create(lesson=lesson, type='quiz', order=6)

    client.force_login(student)
    response = client.get(reverse('lesson_detail', args=[course.slug, lesson.slug]))
    assert response.status_code == 200
    assert b'Voir la correction' in response.content
