"""E-mails transactionnels : contenu, boutons, destinataires, transitions d'état, robustesse aux pannes SMTP."""

import re
import smtplib

import pytest
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse

from access.models import AccessRequest, Coupon
from config.emailing import EmailContent, html_to_text, render_html, send_email
from contact.models import ContactMessage, ContactReason
from courses.models import CourseCompletion
from instructors.models import InstructorPlan, InstructorRequest
from notifications.models import Notification
from notifications.previews import preview_contents
from support.models import Question, Response
from users.models import User

SITE = 'http://127.0.0.1:8000'


def html_of(message):
    return message.alternatives[0][0]


def button_url(message):
    """URL du premier bouton d'action de l'e-mail HTML."""
    return re.search(r'<a href="([^"]+)" target="_blank"', html_of(message)).group(1)


@pytest.fixture
def teacher(course):
    user = User.objects.create_user(email='sensei@test.com', password='x', first_name='Sensei')
    course.instructor = user
    course.save()
    return user


@pytest.fixture
def pending_request(student, course):
    return AccessRequest.objects.create(student=student, course=course, status=AccessRequest.Status.PENDING)


@pytest.mark.django_db
class TestInfrastructure:
    def test_message_is_multipart_with_branding_and_prefix(self, mailoutbox):
        content = EmailContent(
            to=['a@test.com'],
            subject='Sujet',
            template='certificate_ready',
            context={'first_name': 'A', 'course': type('C', (), {'title': 'Cours'})(), 'cta_url': f'{SITE}/x/'},
            reply_to=['r@test.com'],
        )
        assert send_email(content) is True
        message = mailoutbox[0]
        assert message.subject == '[Hajime Learning] Sujet'
        assert message.reply_to == ['r@test.com']
        assert message.alternatives[0][1] == 'text/html'
        assert 'Hajime Learning' in html_of(message) and 'img/hanko_round' in html_of(message)

    def test_text_version_keeps_links(self):
        text = html_to_text(
            '<p>Bonjour</p><a href="https://x.test/a">Ouvrir</a><a href="mailto:me@x.test?subject=Re">me</a>'
        )
        assert 'Ouvrir : https://x.test/a' in text and 'me : me@x.test' in text

    def test_no_recipient_sends_nothing(self, mailoutbox):
        assert send_email(EmailContent(to=[''], subject='s', template='certificate_ready')) is False
        assert mailoutbox == []

    def test_smtp_failure_is_swallowed(self, monkeypatch, caplog):
        def boom(self, fail_silently=False):
            raise smtplib.SMTPException('serveur indisponible')

        monkeypatch.setattr(EmailMultiAlternatives, 'send', boom)
        content = preview_contents()['certificate_ready']
        content.to = ['a@test.com']
        assert send_email(content) is False
        assert "Échec d'envoi" in caplog.text

    def test_every_catalogue_email_renders_with_an_absolute_button(self):
        contents = preview_contents()
        assert len(contents) == 11
        for name, content in contents.items():
            markup = render_html(content)
            url = re.search(r'<a href="([^"]+)" target="_blank"', markup).group(1)
            assert url.startswith(('http://', 'https://', 'mailto:')), f'{name} : bouton non absolu ({url})'
            assert url in html_to_text(markup), f'{name} : lien absent de la version texte'


@pytest.mark.django_db
class TestAccessEmails:
    def test_submitting_proof_notifies_student_and_team(self, student, course, admin_user, mailoutbox):
        AccessRequest.objects.create(
            student=student, course=course, status=AccessRequest.Status.PENDING, final_price=4000
        )

        to_student = [m for m in mailoutbox if student.email in m.to]
        assert len(to_student) == 1 and 'Preuve de paiement bien reçue' in to_student[0].subject
        assert button_url(to_student[0]) == f'{SITE}{reverse("course_detail", args=[course.slug])}'
        assert '4000 DA' in html_of(to_student[0])

        to_team = [m for m in mailoutbox if admin_user.email in m.to]
        assert len(to_team) == 1 and 'Paiement à valider' in to_team[0].subject
        assert '/admin/access/accessrequest/' in button_url(to_team[0])
        assert Notification.objects.filter(recipient=admin_user, title__startswith='Paiement à valider').exists()

    def test_approval_sends_receipt_and_notification(self, pending_request, student, course, mailoutbox):
        mailoutbox.clear()
        pending_request.status = AccessRequest.Status.APPROVED
        pending_request.save()

        message = mailoutbox[0]
        assert 'Accès validé' in message.subject and button_url(message).endswith(course.get_absolute_url())
        assert message.attachments and message.attachments[0][0] == f'Recu_{pending_request.pk}.pdf'
        assert Notification.objects.filter(recipient=student, title__startswith='Accès accordé').exists()

    def test_resaving_an_approved_request_does_not_resend(self, pending_request, mailoutbox):
        pending_request.status = AccessRequest.Status.APPROVED
        pending_request.save()
        mailoutbox.clear()
        pending_request.admin_note = 'Note interne'
        pending_request.save()
        assert mailoutbox == []

    def test_rejection_explains_why_and_offers_to_retry(self, pending_request, student, course, mailoutbox):
        mailoutbox.clear()
        pending_request.status = AccessRequest.Status.REJECTED
        pending_request.admin_note = 'Reçu illisible'
        pending_request.save()

        message = mailoutbox[0]
        assert 'Paiement non validé' in message.subject and 'Reçu illisible' in html_of(message)
        assert button_url(message) == f'{SITE}{reverse("request_access", args=[course.pk])}'
        assert Notification.objects.filter(recipient=student, title='Paiement non validé').exists()

    def test_resubmission_after_rejection_is_acknowledged_again(self, pending_request, student, mailoutbox):
        pending_request.status = AccessRequest.Status.REJECTED
        pending_request.save()
        mailoutbox.clear()
        pending_request.status = AccessRequest.Status.PENDING
        pending_request.save()
        assert any('Preuve de paiement bien reçue' in m.subject for m in mailoutbox if student.email in m.to)

    def test_coupon_is_shown_in_the_summary(self, student, course, mailoutbox):
        coupon = Coupon.objects.create(code='PROMO20', discount_percent=20)
        AccessRequest.objects.create(student=student, course=course, applied_coupon=coupon, final_price=4000)
        assert 'PROMO20' in html_of(mailoutbox[0])


@pytest.mark.django_db
class TestInstructorEmails:
    @pytest.fixture
    def plan(self):
        return InstructorPlan.objects.create(
            name='Starter',
            slug='starter',
            price=0,
            max_courses=3,
            max_modules_per_course=5,
            max_lessons_per_course=10,
            revenue_percent=70,
        )

    def test_approval_welcomes_the_instructor(self, student, plan, mailoutbox):
        request = InstructorRequest.objects.create(user=student, plan=plan, payment_proof='x.png')
        mailoutbox.clear()
        request.status = InstructorRequest.Status.APPROVED
        request.save()

        assert 'espace instructeur est activé' in mailoutbox[0].subject
        assert button_url(mailoutbox[0]) == f'{SITE}{reverse("instructor_dashboard")}'
        assert Notification.objects.filter(recipient=student, title__startswith='Espace instructeur activé').exists()

    def test_rejection_gives_the_reason(self, student, plan, mailoutbox):
        request = InstructorRequest.objects.create(user=student, plan=plan, payment_proof='x.png')
        mailoutbox.clear()
        request.status = InstructorRequest.Status.REJECTED
        request.admin_note = 'Justificatif manquant'
        request.save()

        assert 'Justificatif manquant' in html_of(mailoutbox[0])
        assert Notification.objects.filter(recipient=student, title='Demande instructeur refusée').exists()


@pytest.mark.django_db
class TestCertificateEmail:
    def test_first_generation_notifies_once(self, student, course, monkeypatch, mailoutbox):
        from courses import tasks

        monkeypatch.setattr(tasks, 'render_pdf', lambda template, context: b'%PDF-ok')
        completion = CourseCompletion.objects.create(student=student, course=course)

        tasks.generate_certificate_pdf.run(completion.id)
        assert len(mailoutbox) == 1 and 'certificat est prêt' in mailoutbox[0].subject
        assert button_url(mailoutbox[0]) == f'{SITE}{reverse("download_certificate", args=[course.slug])}'
        assert Notification.objects.filter(recipient=student, title__startswith='Certificat prêt').count() == 1

        tasks.generate_certificate_pdf.run(completion.id)  # régénération : pas de nouvelle notification
        assert len(mailoutbox) == 1


@pytest.mark.django_db
class TestSupportEmails:
    @pytest.fixture
    def question(self, student, course, teacher):
        module = course.modules.create(title='M', order=1)
        lesson = module.lessons.create(title='Leçon', slug='l', order=1)
        return Question.objects.create(
            student=student, course=course, lesson=lesson, title='Aide', content='Je bloque\nici'
        )

    def test_new_question_email_has_a_reply_button(self, question, teacher, mailoutbox):
        message = [m for m in mailoutbox if teacher.email in m.to][0]
        assert 'Nouvelle question : Aide' in message.subject
        assert button_url(message) == f'{SITE}{reverse("question_detail", args=[question.pk])}'
        assert 'Je bloque' in html_of(message) and 'Répondre à la question' in html_of(message)

    def test_instructor_reply_emails_the_student_only(self, question, student, teacher, mailoutbox):
        mailoutbox.clear()
        Response.objects.create(question=question, author=teacher, content='Voici la solution', is_instructor=True)

        assert [m.to for m in mailoutbox] == [[student.email]]
        assert 'Votre Sensei' in html_of(mailoutbox[0]) and 'Voici la solution' in html_of(mailoutbox[0])

    def test_user_content_is_escaped(self, student, course, teacher, mailoutbox):
        Question.objects.create(student=student, course=course, title='XSS', content='<script>alert(1)</script>')
        assert '<script>' not in html_of(mailoutbox[0])


@pytest.mark.django_db
class TestContactEmails:
    @pytest.fixture
    def payload(self):
        reason = ContactReason.objects.create(label='Cours particulier')
        return {
            'first_name': 'Yanis',
            'last_name': 'B',
            'email': 'yanis@test.com',
            'reason': reason.pk,
            'message': 'Bonjour !',
        }

    def test_team_message_is_replyable_and_sender_gets_a_receipt(self, client, payload, mailoutbox, settings):
        client.post(reverse('contact'), payload)

        team = [m for m in mailoutbox if settings.CONTACT_EMAIL in m.to][0]
        assert team.reply_to == ['yanis@test.com']
        assert button_url(team).startswith('mailto:yanis@test.com')

        receipt = [m for m in mailoutbox if 'yanis@test.com' in m.to][0]
        assert 'bien reçu' in receipt.subject and 'Bonjour !' in html_of(receipt)

    def test_form_still_works_when_smtp_is_down(self, client, payload, monkeypatch):
        def boom(self, fail_silently=False):
            raise smtplib.SMTPException('hors service')

        monkeypatch.setattr(EmailMultiAlternatives, 'send', boom)
        response = client.post(reverse('contact'), payload)

        assert response.status_code == 302
        assert ContactMessage.objects.count() == 1


@pytest.mark.django_db
class TestResilience:
    def test_posting_a_question_survives_an_smtp_outage(self, client, student, course, teacher, monkeypatch):
        from access.models import AccessRequest

        def boom(self, fail_silently=False):
            raise smtplib.SMTPException('hors service')

        monkeypatch.setattr(EmailMultiAlternatives, 'send', boom)
        module = course.modules.create(title='M', order=1)
        lesson = module.lessons.create(title='L', slug='l', order=1)
        AccessRequest.objects.create(student=student, course=course, status=AccessRequest.Status.APPROVED)
        client.force_login(student)

        response = client.post(reverse('ask_question', args=[lesson.id]), {'title': 'Panne', 'content': 'test'})

        assert response.status_code == 302
        assert Question.objects.filter(title='Panne').exists()


@pytest.mark.django_db
class TestAuthEmails:
    def test_signup_confirmation_is_branded_with_a_button(self, client, mailoutbox):
        client.post(
            reverse('account_signup'),
            {
                'email': 'nouveau@test.com',
                'password1': 'Str0ng!Passw0rd#',
                'first_name': 'Nou',
                'last_name': 'Veau',
                'gender': 'M',
                'birth_date': '2000-01-01',
                'phone_number': '+213555000000',
                'country': 'DZ',
            },
        )
        message = [m for m in mailoutbox if 'nouveau@test.com' in m.to][0]
        assert message.alternatives and 'Confirmer mon adresse e-mail' in html_of(message)
        assert '/accounts/confirm-email/' in button_url(message)
        assert '/accounts/confirm-email/' in message.body

    def test_password_reset_email_has_a_button(self, client, student, mailoutbox):
        client.post(reverse('account_reset_password'), {'email': student.email})
        message = mailoutbox[0]
        assert 'Réinitialisation de votre mot de passe' in message.subject
        assert '/accounts/password/reset/key/' in button_url(message)
        assert 'Choisir un nouveau mot de passe' in html_of(message)


class TestProductionSettings:
    def _import_prod(self, **env):
        import os
        import subprocess
        import sys

        base = {**os.environ, 'DJANGO_SETTINGS_MODULE': 'config.settings.prod', 'DJANGO_SECRET_KEY': 'k' * 60}
        base.pop('SITE_URL', None)
        return subprocess.run(
            [sys.executable, '-c', 'import config.settings.prod'], env={**base, **env}, capture_output=True, text=True
        )

    def test_site_url_is_mandatory_and_https(self):
        assert 'SITE_URL' in self._import_prod().stderr
        assert 'SITE_URL' in self._import_prod(SITE_URL='http://exemple.com').stderr

    def test_production_settings_load_with_a_valid_site_url(self):
        assert self._import_prod(SITE_URL='https://exemple.com').returncode == 0
