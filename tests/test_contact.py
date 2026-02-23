import pytest
from django.urls import reverse

from contact.models import ContactReason, ContactMessage


@pytest.fixture
def reason(db):
    return ContactReason.objects.create(label="Support technique", order=1)


@pytest.mark.django_db
class TestContactPage:

    def test_page_loads(self, client):
        url = reverse('contact')
        resp = client.get(url)
        assert resp.status_code == 200

    def test_form_prefilled_when_authenticated(self, client, student):
        client.force_login(student)
        resp = client.get(reverse('contact'))
        assert resp.status_code == 200
        assert resp.context['is_prefilled'] is True

    def test_form_not_prefilled_anonymous(self, client):
        resp = client.get(reverse('contact'))
        assert resp.context['is_prefilled'] is False


@pytest.mark.django_db
class TestContactSubmit:

    def test_valid_submission_creates_message(self, client, reason):
        url = reverse('contact')
        resp = client.post(url, {
            'first_name': 'Alice',
            'last_name':  'Dupont',
            'email':      'alice@test.com',
            'reason':     reason.pk,
            'message':    "Bonjour, j'ai un problème.",
        })
        assert resp.status_code == 302
        assert resp['Location'] == reverse('contact_success')
        assert ContactMessage.objects.filter(email='alice@test.com').exists()

    def test_submission_links_user_when_authenticated(self, client, student, reason):
        client.force_login(student)
        client.post(reverse('contact'), {
            'first_name': student.first_name,
            'last_name':  student.last_name,
            'email':      student.email,
            'reason':     reason.pk,
            'message':    "Question de la part d'un étudiant connecté.",
        })
        msg = ContactMessage.objects.get(email=student.email)
        assert msg.user == student

    def test_anonymous_submission_no_user_link(self, client, reason):
        client.post(reverse('contact'), {
            'first_name': 'Bob',
            'last_name':  'Martin',
            'email':      'bob@test.com',
            'reason':     reason.pk,
            'message':    'Message anonyme.',
        })
        msg = ContactMessage.objects.get(email='bob@test.com')
        assert msg.user is None

    def test_default_status_is_new(self, client, reason):
        client.post(reverse('contact'), {
            'first_name': 'Carl',
            'last_name':  'Durand',
            'email':      'carl@test.com',
            'reason':     reason.pk,
            'message':    'Test statut.',
        })
        msg = ContactMessage.objects.get(email='carl@test.com')
        assert msg.status == ContactMessage.STATUS_NEW

    def test_invalid_form_no_reason(self, client):
        resp = client.post(reverse('contact'), {
            'first_name': 'Alice',
            'last_name':  'D',
            'email':      'alice@test.com',
            'reason':     '',   # motif obligatoire
            'message':    'Test.',
        })
        # Reste sur la page (form invalide)
        assert resp.status_code == 200
        assert not ContactMessage.objects.filter(email='alice@test.com').exists()

    def test_success_page_loads(self, client):
        resp = client.get(reverse('contact_success'))
        assert resp.status_code == 200


@pytest.mark.django_db
class TestContactAdmin:

    def test_mark_as_read_action(self, admin_client, reason):
        msg = ContactMessage.objects.create(
            first_name='Test', last_name='User',
            email='t@t.com', reason=reason,
            message='test', status=ContactMessage.STATUS_NEW,
        )
        url = reverse('admin:contact_contactmessage_changelist')
        admin_client.post(url, {
            'action': 'mark_as_read',
            '_selected_action': [msg.pk],
        })
        msg.refresh_from_db()
        assert msg.status == ContactMessage.STATUS_READ

    def test_mark_as_resolved_action(self, admin_client, reason):
        msg = ContactMessage.objects.create(
            first_name='Test', last_name='User',
            email='t2@t.com', reason=reason,
            message='test', status=ContactMessage.STATUS_NEW,
        )
        url = reverse('admin:contact_contactmessage_changelist')
        admin_client.post(url, {
            'action': 'mark_as_resolved',
            '_selected_action': [msg.pk],
        })
        msg.refresh_from_db()
        assert msg.status == ContactMessage.STATUS_RESOLVED
