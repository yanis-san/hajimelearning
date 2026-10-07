import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestInstructorSignupClosed:
    """Plateforme mono-formateur : les pages d'inscription instructeur sont fermées."""

    def test_plans_redirect_home_for_visitor(self, client, settings):
        settings.INSTRUCTOR_SIGNUP_ENABLED = False
        resp = client.get(reverse('instructor_plans'))
        assert resp.status_code == 302
        assert resp.url == reverse('course_list')

    def test_request_redirect_home_for_student(self, client, settings, student):
        settings.INSTRUCTOR_SIGNUP_ENABLED = False
        client.force_login(student)
        resp = client.get(reverse('instructor_request', args=['starter']))
        assert resp.status_code == 302
        assert resp.url == reverse('course_list')

    def test_staff_still_has_access(self, client, settings, admin_user):
        settings.INSTRUCTOR_SIGNUP_ENABLED = False
        client.force_login(admin_user)
        resp = client.get(reverse('instructor_plans'))
        assert resp.status_code == 200
