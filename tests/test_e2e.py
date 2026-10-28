"""
Tests de bout en bout dans un vrai navigateur (Playwright) : composants Alpine et HTMX.

Prérequis : `playwright install chromium`. Sans navigateur, ces tests sont ignorés.
Lancer uniquement ceux-ci : `pytest -m e2e` ; les exclure : `pytest -m "not e2e"`.
"""

import os

import pytest

# Playwright (API synchrone) tourne dans une boucle asyncio : l'ORM de la fixture est utilisé en test uniquement.
os.environ.setdefault('DJANGO_ALLOW_ASYNC_UNSAFE', 'true')

pytest.importorskip('playwright')
from playwright.sync_api import expect, sync_playwright  # noqa: E402

from django.urls import reverse  # noqa: E402

from access.models import AccessRequest  # noqa: E402
from courses.models import ContentBlock, QuizResult, StudentNote  # noqa: E402

pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]


@pytest.fixture(scope='module')
def browser():
    with sync_playwright() as playwright:
        try:
            instance = playwright.chromium.launch()
        except Exception as exc:  # navigateur non installé
            pytest.skip(f'Chromium indisponible : {exc}')
        yield instance
        instance.close()


@pytest.fixture
def page(browser, live_server):
    context = browser.new_context()
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.live_server_url = live_server.url
    yield page
    context.close()
    assert not errors, f'Erreurs JavaScript : {errors}'


def login_as(page, user):
    """Ouvre une session pour `user` en posant directement le cookie de session."""
    from django.conf import settings
    from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY
    from django.contrib.sessions.backends.db import SessionStore

    session = SessionStore()
    session[SESSION_KEY] = str(user.pk)
    session[BACKEND_SESSION_KEY] = 'django.contrib.auth.backends.ModelBackend'
    session[HASH_SESSION_KEY] = user.get_session_auth_hash()
    session.save()
    page.context.add_cookies(
        [{'name': settings.SESSION_COOKIE_NAME, 'value': session.session_key, 'url': page.live_server_url}]
    )


@pytest.fixture
def lesson(course):
    module = course.modules.create(title='Module', order=1)
    return module.lessons.create(title='Leçon', slug='lecon', order=1, is_free=True)


def lesson_url(page, course, lesson):
    return page.live_server_url + reverse('lesson_detail', args=[course.slug, lesson.slug])


def test_quiz_flow_saves_the_result(page, student, course, lesson):
    block = ContentBlock.objects.create(lesson=lesson, type='quiz', quiz_title='Mon quiz', order=1)
    block.questions.create(question_text='Q1', choice_a='Bonne', choice_b='Mauvaise', correct_answer='a', duration=30)
    AccessRequest.objects.create(student=student, course=course, status=AccessRequest.Status.APPROVED)
    login_as(page, student)

    page.goto(lesson_url(page, course, lesson))
    page.get_by_role('button', name='Commencer').click()
    page.get_by_text('Bonne', exact=True).click()
    page.get_by_role('button', name='Voir les résultats').click()

    expect(page.get_by_role('button', name='Recommencer')).to_be_visible()
    page.wait_for_function('true')
    for _ in range(20):  # l'enregistrement part en arrière-plan (fetch)
        if QuizResult.objects.filter(student=student, block=block, score=1, total_questions=1).exists():
            break
        page.wait_for_timeout(150)
    assert QuizResult.objects.filter(student=student, block=block, score=1, total_questions=1).exists()


def test_personal_note_is_saved_through_ajax(page, student, course, lesson):
    block = ContentBlock.objects.create(lesson=lesson, type='text', text_content='Contenu', order=1)
    login_as(page, student)

    page.goto(lesson_url(page, course, lesson))
    page.get_by_role('button', name='Ajouter une note').click()
    page.locator('textarea[name="note_content"]').fill('Ma note de test')
    page.get_by_role('button', name='Enregistrer').click()

    expect(page.get_by_role('button', name='Ma note')).to_be_visible()
    assert StudentNote.objects.get(student=student, block=block).content == 'Ma note de test'


def test_builder_autosave_creates_then_updates_the_block(page, admin_user, course, lesson):
    login_as(page, admin_user)
    page.goto(page.live_server_url + reverse('manage_lesson_content', args=[course.slug, lesson.slug]))

    page.get_by_role('button', name='Texte').first.click()
    editor = page.locator('textarea[name="text_content"]')
    editor.fill('Premier jet')
    expect(page.get_by_text('Enregistré automatiquement').first).to_be_visible(timeout=8000)
    block = ContentBlock.objects.get(lesson=lesson)
    assert block.text_content == 'Premier jet'

    editor.fill('Version corrigée')
    expect(page.get_by_text('Enregistré automatiquement').first).to_be_visible(timeout=8000)
    assert ContentBlock.objects.filter(lesson=lesson).count() == 1  # mise à jour, pas de doublon
    block.refresh_from_db()
    assert block.text_content == 'Version corrigée'


def test_course_form_tabs_switch(page, admin_user, course):
    login_as(page, admin_user)
    page.goto(page.live_server_url + reverse('manage_course_edit', args=[course.slug]))

    expect(page.locator('[x-show="tab === \'infos\'"]')).to_be_visible()
    page.get_by_role('button', name='SEO').click()
    expect(page.locator('[x-show="tab === \'seo\'"]')).to_be_visible()
    expect(page.locator('[x-show="tab === \'infos\'"]')).to_be_hidden()
