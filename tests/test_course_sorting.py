"""
TDD — Tests pour le tri des formations dans la page admin manage_course_list.
Critères de tri : title, price, created_at, is_published, modules_count.
Chaque critère peut être ascendant ou descendant (?sort=field / ?sort=-field).
HTMX partial : si HX-Request, seul le tbody est renvoyé.
"""

import pytest
from django.urls import reverse

from courses.models import Course, Module


@pytest.fixture
def three_courses(db):
    """Crée 3 cours avec des données variées pour tester le tri."""
    c1 = Course.objects.create(
        title="Alpha Python",
        slug="alpha-python",
        short_description="Cours Alpha",
        description="Description",
        price=1000,
        is_published=True,
    )
    c2 = Course.objects.create(
        title="Beta Django",
        slug="beta-django",
        short_description="Cours Beta",
        description="Description",
        price=5000,
        is_published=False,
    )
    c3 = Course.objects.create(
        title="Gamma JS",
        slug="gamma-js",
        short_description="Cours Gamma",
        description="Description",
        price=0,
        is_published=True,
    )
    # Ajouter des modules pour tri par nombre de modules
    Module.objects.create(course=c1, title="M1", order=1)
    Module.objects.create(course=c1, title="M2", order=2)
    Module.objects.create(course=c1, title="M3", order=3)
    # c2 a 1 module
    Module.objects.create(course=c2, title="M1", order=1)
    # c3 n'a aucun module

    return c1, c2, c3


@pytest.mark.django_db
class TestCourseSortingAccess:
    """Seuls les staff peuvent accéder à la page avec tri."""

    def test_anonymous_redirected(self, client):
        resp = client.get(reverse('manage_course_list'), {'sort': 'title'})
        assert resp.status_code == 302

    def test_student_redirected(self, client, student):
        client.force_login(student)
        resp = client.get(reverse('manage_course_list'), {'sort': 'title'})
        assert resp.status_code == 302


@pytest.mark.django_db
class TestSortByTitle:
    """Tri alphabétique par titre."""

    def test_sort_title_asc(self, client, admin_user, three_courses):
        client.force_login(admin_user)
        resp = client.get(reverse('manage_course_list'), {'sort': 'title'})
        content = resp.content.decode()
        assert resp.status_code == 200
        pos_a = content.find("Alpha Python")
        pos_b = content.find("Beta Django")
        pos_c = content.find("Gamma JS")
        assert pos_a < pos_b < pos_c

    def test_sort_title_desc(self, client, admin_user, three_courses):
        client.force_login(admin_user)
        resp = client.get(reverse('manage_course_list'), {'sort': '-title'})
        content = resp.content.decode()
        pos_a = content.find("Alpha Python")
        pos_b = content.find("Beta Django")
        pos_c = content.find("Gamma JS")
        assert pos_c < pos_b < pos_a


@pytest.mark.django_db
class TestSortByPrice:
    """Tri par prix."""

    def test_sort_price_asc(self, client, admin_user, three_courses):
        client.force_login(admin_user)
        resp = client.get(reverse('manage_course_list'), {'sort': 'price'})
        content = resp.content.decode()
        # Gamma (0) < Alpha (1000) < Beta (5000)
        pos_gamma = content.find("Gamma JS")
        pos_alpha = content.find("Alpha Python")
        pos_beta = content.find("Beta Django")
        assert pos_gamma < pos_alpha < pos_beta

    def test_sort_price_desc(self, client, admin_user, three_courses):
        client.force_login(admin_user)
        resp = client.get(reverse('manage_course_list'), {'sort': '-price'})
        content = resp.content.decode()
        pos_gamma = content.find("Gamma JS")
        pos_alpha = content.find("Alpha Python")
        pos_beta = content.find("Beta Django")
        assert pos_beta < pos_alpha < pos_gamma


@pytest.mark.django_db
class TestSortByDate:
    """Tri par date de création."""

    def test_sort_created_at_asc(self, client, admin_user, three_courses):
        """Le plus ancien en premier."""
        client.force_login(admin_user)
        resp = client.get(reverse('manage_course_list'), {'sort': 'created_at'})
        content = resp.content.decode()
        # c1 créé en premier, c3 en dernier
        pos_a = content.find("Alpha Python")
        pos_b = content.find("Beta Django")
        pos_c = content.find("Gamma JS")
        assert pos_a < pos_b < pos_c

    def test_sort_created_at_desc(self, client, admin_user, three_courses):
        """Le plus récent en premier (défaut)."""
        client.force_login(admin_user)
        resp = client.get(reverse('manage_course_list'), {'sort': '-created_at'})
        content = resp.content.decode()
        pos_a = content.find("Alpha Python")
        pos_c = content.find("Gamma JS")
        assert pos_c < pos_a


@pytest.mark.django_db
class TestSortByPublished:
    """Tri par statut de publication."""

    def test_sort_published_asc(self, client, admin_user, three_courses):
        """Non-publiés d'abord (False=0 < True=1)."""
        client.force_login(admin_user)
        resp = client.get(reverse('manage_course_list'), {'sort': 'is_published'})
        content = resp.content.decode()
        # Beta (non publié) doit apparaître avant Alpha et Gamma (publiés)
        pos_beta = content.find("Beta Django")
        pos_alpha = content.find("Alpha Python")
        assert pos_beta < pos_alpha


@pytest.mark.django_db
class TestSortByModuleCount:
    """Tri par nombre de modules (annotation)."""

    def test_sort_modules_asc(self, client, admin_user, three_courses):
        client.force_login(admin_user)
        resp = client.get(reverse('manage_course_list'), {'sort': 'modules_count'})
        content = resp.content.decode()
        # Gamma (0) < Beta (1) < Alpha (3)
        pos_gamma = content.find("Gamma JS")
        pos_beta = content.find("Beta Django")
        pos_alpha = content.find("Alpha Python")
        assert pos_gamma < pos_beta < pos_alpha

    def test_sort_modules_desc(self, client, admin_user, three_courses):
        client.force_login(admin_user)
        resp = client.get(reverse('manage_course_list'), {'sort': '-modules_count'})
        content = resp.content.decode()
        pos_gamma = content.find("Gamma JS")
        pos_alpha = content.find("Alpha Python")
        assert pos_alpha < pos_gamma


@pytest.mark.django_db
class TestDefaultSort:
    """Sans paramètre ?sort, tri par -created_at (plus récent en premier)."""

    def test_default_order(self, client, admin_user, three_courses):
        client.force_login(admin_user)
        resp = client.get(reverse('manage_course_list'))
        content = resp.content.decode()
        pos_a = content.find("Alpha Python")
        pos_c = content.find("Gamma JS")
        # Gamma créé en dernier → apparaît en premier
        assert pos_c < pos_a


@pytest.mark.django_db
class TestInvalidSort:
    """Un paramètre ?sort invalide retombe sur le défaut."""

    def test_invalid_sort_field(self, client, admin_user, three_courses):
        client.force_login(admin_user)
        resp = client.get(reverse('manage_course_list'), {'sort': 'hacked_field'})
        assert resp.status_code == 200


@pytest.mark.django_db
class TestHTMXPartialResponse:
    """HTMX renvoie seulement le partial (tbody) pour les tris dynamiques."""

    def test_htmx_returns_partial(self, client, admin_user, three_courses):
        client.force_login(admin_user)
        resp = client.get(
            reverse('manage_course_list'),
            {'sort': 'title'},
            HTTP_HX_REQUEST='true',
        )
        assert resp.status_code == 200
        content = resp.content.decode()
        # Le partial ne doit PAS contenir le layout complet (pas de <html>)
        assert '<html' not in content.lower()
        # Mais il doit contenir les cours
        assert 'Alpha Python' in content

    def test_htmx_respects_sort(self, client, admin_user, three_courses):
        client.force_login(admin_user)
        resp = client.get(
            reverse('manage_course_list'),
            {'sort': '-price'},
            HTTP_HX_REQUEST='true',
        )
        content = resp.content.decode()
        pos_beta = content.find("Beta Django")
        pos_gamma = content.find("Gamma JS")
        assert pos_beta < pos_gamma


@pytest.mark.django_db
class TestSearchFilter:
    """Recherche textuelle par titre."""

    def test_search_finds_matching_course(self, client, admin_user, three_courses):
        client.force_login(admin_user)
        resp = client.get(reverse('manage_course_list'), {'q': 'alpha'})
        content = resp.content.decode()
        assert 'Alpha Python' in content
        assert 'Beta Django' not in content

    def test_search_empty_returns_all(self, client, admin_user, three_courses):
        client.force_login(admin_user)
        resp = client.get(reverse('manage_course_list'), {'q': ''})
        content = resp.content.decode()
        assert 'Alpha Python' in content
        assert 'Beta Django' in content
        assert 'Gamma JS' in content

    def test_search_no_results(self, client, admin_user, three_courses):
        client.force_login(admin_user)
        resp = client.get(reverse('manage_course_list'), {'q': 'zzzznothing'})
        content = resp.content.decode()
        assert 'Aucun cours' in content
