"""Préférences d'e-mails : catégories facultatives, désabonnement en un clic (RFC 8058), e-mails essentiels intouchables."""

import html
import re

import pytest
from django.core import signing
from django.urls import reverse

from access.models import AccessRequest
from notifications.models import NotificationPreference
from notifications.preferences import unsubscribe_token, wants_email
from support.models import Question, Response
from users.models import User


@pytest.fixture
def teacher(course):
    user = User.objects.create_user(email='sensei@test.com', password='x', first_name='Sensei')
    course.instructor = user
    course.save()
    return user


@pytest.fixture
def question(student, course, teacher):
    module = course.modules.create(title='M', order=1)
    lesson = module.lessons.create(title='L', slug='l', order=1)
    return Question.objects.create(student=student, course=course, lesson=lesson, title='Aide', content='Je bloque')


def html_of(message):
    return message.alternatives[0][0]


@pytest.mark.django_db
class TestPreferenceLogic:
    def test_defaults(self, student):
        assert wants_email(student, 'support') is True
        assert wants_email(student, 'progress') is True
        assert wants_email(student, 'newsletter') is False  # opt-in
        assert wants_email(student, 'essential') is True

    def test_choice_is_respected_per_category(self, student):
        NotificationPreference.objects.create(user=student, email_support=False, email_newsletter=True)
        assert wants_email(student, 'support') is False
        assert wants_email(student, 'progress') is True
        assert wants_email(student, 'newsletter') is True


@pytest.mark.django_db
class TestOptionalEmails:
    def test_optional_email_carries_unsubscribe_footer_and_headers(self, question, teacher, mailoutbox):
        message = [m for m in mailoutbox if teacher.email in m.to][0]

        assert 'Se désabonner' in html_of(message) and 'Gérer mes préférences' in html_of(message)
        url = re.search(r'<a href="([^"]+/notifications/unsubscribe/[^"]+)"', html_of(message)).group(1)
        assert message.extra_headers['List-Unsubscribe'] == f'<{url}>'
        assert message.extra_headers['List-Unsubscribe-Post'] == 'List-Unsubscribe=One-Click'

    def test_unsubscribed_user_no_longer_receives_the_category(self, question, student, teacher, mailoutbox):
        NotificationPreference.objects.create(user=teacher, email_support=False)
        mailoutbox.clear()
        Response.objects.create(question=question, author=student, content='Un détail de plus')
        assert [m for m in mailoutbox if teacher.email in m.to] == []

        # …mais la notification dans le site reste créée
        from notifications.models import Notification

        assert Notification.objects.filter(recipient=teacher).exists()

    def test_other_categories_are_unaffected(self, student, course, monkeypatch, mailoutbox):
        from courses import tasks
        from courses.models import CourseCompletion

        NotificationPreference.objects.create(user=student, email_support=False)
        monkeypatch.setattr(tasks, 'render_pdf', lambda template, context: b'%PDF-ok')
        completion = CourseCompletion.objects.create(student=student, course=course)
        tasks.generate_certificate_pdf.run(completion.id)
        assert any('certificat est prêt' in m.subject for m in mailoutbox)

    def test_progress_opt_out_blocks_the_certificate_email(self, student, course, monkeypatch, mailoutbox):
        from courses import tasks
        from courses.models import CourseCompletion

        NotificationPreference.objects.create(user=student, email_progress=False)
        monkeypatch.setattr(tasks, 'render_pdf', lambda template, context: b'%PDF-ok')
        tasks.generate_certificate_pdf.run(CourseCompletion.objects.create(student=student, course=course).id)
        assert mailoutbox == []


@pytest.mark.django_db
class TestEssentialEmails:
    def test_essential_emails_ignore_every_opt_out(self, student, course, mailoutbox):
        NotificationPreference.objects.create(
            user=student, email_support=False, email_progress=False, email_newsletter=False
        )
        AccessRequest.objects.create(student=student, course=course, status=AccessRequest.Status.APPROVED)

        message = [m for m in mailoutbox if student.email in m.to][0]
        assert 'Accès validé' in message.subject
        assert 'Se désabonner' not in html_of(message)
        assert 'List-Unsubscribe' not in message.extra_headers


@pytest.mark.django_db
class TestUnsubscribeFlow:
    def test_get_shows_confirmation_without_changing_anything(self, client, teacher):
        url = reverse('unsubscribe', args=[unsubscribe_token(teacher, 'support')])
        response = client.get(url)

        assert response.status_code == 200 and 'Confirmer le désabonnement' in response.content.decode()
        assert wants_email(teacher, 'support') is True  # un simple clic de prévisualisation ne désabonne pas

    def test_post_unsubscribes_without_login_or_csrf_token(self, client, teacher):
        from django.test import Client

        strict_client = Client(enforce_csrf_checks=True)  # comme une messagerie : pas de jeton CSRF
        url = reverse('unsubscribe', args=[unsubscribe_token(teacher, 'support')])
        response = strict_client.post(url, headers={'List-Unsubscribe': 'One-Click'})

        assert response.status_code == 200 and "C'est fait" in html.unescape(response.content.decode())
        assert wants_email(teacher, 'support') is False
        assert wants_email(teacher, 'progress') is True  # seule la catégorie visée est coupée

    def test_forged_or_unknown_tokens_are_rejected(self, client, teacher):
        assert client.get(reverse('unsubscribe', args=['n-importe-quoi'])).status_code == 404
        forged = signing.dumps({'user': teacher.pk, 'category': 'support'}, salt='autre-sel')
        assert client.post(reverse('unsubscribe', args=[forged])).status_code == 404
        unknown_category = signing.dumps(
            {'user': teacher.pk, 'category': 'essential'}, salt='notifications.unsubscribe'
        )
        assert client.get(reverse('unsubscribe', args=[unknown_category])).status_code == 404
        assert wants_email(teacher, 'support') is True


@pytest.mark.django_db
class TestPreferencesPage:
    def test_login_required(self, client):
        assert client.get(reverse('notification_preferences')).status_code == 302

    def test_user_can_change_preferences(self, client, student):
        client.force_login(student)
        page = client.get(reverse('notification_preferences'))
        assert page.status_code == 200 and 'Questions et réponses' in page.content.decode()

        response = client.post(reverse('notification_preferences'), {'email_progress': 'on', 'email_newsletter': 'on'})

        assert response.status_code == 302
        assert wants_email(student, 'support') is False
        assert wants_email(student, 'progress') is True
        assert wants_email(student, 'newsletter') is True

    def test_each_user_only_edits_their_own_preferences(self, client, student, teacher):
        client.force_login(student)
        client.post(reverse('notification_preferences'), {})
        assert wants_email(teacher, 'support') is True
