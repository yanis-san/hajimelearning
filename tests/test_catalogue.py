"""
TDD — Tests pour la page publique /catalogue/ avec tri et recherche.
Accessible à tous (anon, étudiants, admin).
Seuls les cours publiés sont visibles.
Options de tri : title, price, created_at (défaut: -created_at).
Recherche textuelle par titre.
HTMX partial pour rechargement dynamique de la grille.
"""
import pytest
from django.urls import reverse
from courses.models import Course, Module


@pytest.fixture
def catalogue_courses(db):
    """3 cours publiés + 1 brouillon (non visible)."""
    c1 = Course.objects.create(
        title="Python Débutant",
        slug="python-debutant",
        short_description="Apprenez Python depuis zéro",
        description="Contenu",
        price=3000,
        is_published=True,
    )
    c2 = Course.objects.create(
        title="Django Avancé",
        slug="django-avance",
        short_description="Maîtrisez Django",
        description="Contenu",
        price=5000,
        is_published=True,
    )
    c3 = Course.objects.create(
        title="Alpine JS Gratuit",
        slug="alpine-js-gratuit",
        short_description="Découvrez Alpine JS",
        description="Contenu",
        price=0,
        is_published=True,
    )
    # Brouillon : NE doit PAS apparaître
    c4 = Course.objects.create(
        title="Cours Secret",
        slug="cours-secret",
        short_description="Pas encore prêt",
        description="Contenu",
        price=1000,
        is_published=False,
    )
    # Modules pour c1 (pour démontrer le comptage)
    Module.objects.create(course=c1, title="Intro", order=1)
    Module.objects.create(course=c1, title="Variables", order=2)

    return c1, c2, c3, c4


# ── Accès ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestCatalogueAccess:

    def test_anonymous_can_access(self, client, catalogue_courses):
        resp = client.get(reverse('catalogue'))
        assert resp.status_code == 200

    def test_student_can_access(self, client, student, catalogue_courses):
        client.force_login(student)
        resp = client.get(reverse('catalogue'))
        assert resp.status_code == 200

    def test_admin_can_access(self, client, admin_user, catalogue_courses):
        client.force_login(admin_user)
        resp = client.get(reverse('catalogue'))
        assert resp.status_code == 200


# ── Seuls les cours publiés sont affichés ────────────────

@pytest.mark.django_db
class TestCatalogueOnlyPublished:

    def test_published_courses_visible(self, client, catalogue_courses):
        resp = client.get(reverse('catalogue'))
        content = resp.content.decode()
        assert "Python Débutant" in content
        assert "Django Avancé" in content
        assert "Alpine JS Gratuit" in content

    def test_draft_course_hidden(self, client, catalogue_courses):
        resp = client.get(reverse('catalogue'))
        content = resp.content.decode()
        assert "Cours Secret" not in content


# ── Tri par titre ────────────────────────────────────────

@pytest.mark.django_db
class TestCatalogueSortTitle:

    def test_sort_title_asc(self, client, catalogue_courses):
        resp = client.get(reverse('catalogue'), {'sort': 'title'})
        content = resp.content.decode()
        pos_alpine = content.find("Alpine JS Gratuit")
        pos_django = content.find("Django Avancé")
        pos_python = content.find("Python Débutant")
        assert pos_alpine < pos_django < pos_python

    def test_sort_title_desc(self, client, catalogue_courses):
        resp = client.get(reverse('catalogue'), {'sort': '-title'})
        content = resp.content.decode()
        pos_alpine = content.find("Alpine JS Gratuit")
        pos_python = content.find("Python Débutant")
        assert pos_python < pos_alpine


# ── Tri par prix ─────────────────────────────────────────

@pytest.mark.django_db
class TestCatalogueSortPrice:

    def test_sort_price_asc(self, client, catalogue_courses):
        resp = client.get(reverse('catalogue'), {'sort': 'price'})
        content = resp.content.decode()
        # Alpine (0) < Python (3000) < Django (5000)
        pos_alpine = content.find("Alpine JS Gratuit")
        pos_python = content.find("Python Débutant")
        pos_django = content.find("Django Avancé")
        assert pos_alpine < pos_python < pos_django

    def test_sort_price_desc(self, client, catalogue_courses):
        resp = client.get(reverse('catalogue'), {'sort': '-price'})
        content = resp.content.decode()
        pos_django = content.find("Django Avancé")
        pos_alpine = content.find("Alpine JS Gratuit")
        assert pos_django < pos_alpine


# ── Tri par date ─────────────────────────────────────────

@pytest.mark.django_db
class TestCatalogueSortDate:

    def test_default_is_newest_first(self, client, catalogue_courses):
        """Sans ?sort, les plus récents apparaissent d'abord."""
        resp = client.get(reverse('catalogue'))
        content = resp.content.decode()
        # c3 (Alpine) créé en dernier → apparaît avant c1 (Python)
        pos_alpine = content.find("Alpine JS Gratuit")
        pos_python = content.find("Python Débutant")
        assert pos_alpine < pos_python

    def test_sort_created_at_asc(self, client, catalogue_courses):
        resp = client.get(reverse('catalogue'), {'sort': 'created_at'})
        content = resp.content.decode()
        pos_python = content.find("Python Débutant")
        pos_alpine = content.find("Alpine JS Gratuit")
        assert pos_python < pos_alpine


# ── Tri invalide → défaut ───────────────────────────────

@pytest.mark.django_db
class TestCatalogueInvalidSort:

    def test_invalid_sort_fallback(self, client, catalogue_courses):
        resp = client.get(reverse('catalogue'), {'sort': 'hacked'})
        assert resp.status_code == 200


# ── Recherche ────────────────────────────────────────────

@pytest.mark.django_db
class TestCatalogueSearch:

    def test_search_finds_match(self, client, catalogue_courses):
        resp = client.get(reverse('catalogue'), {'q': 'python'})
        content = resp.content.decode()
        assert "Python Débutant" in content
        assert "Django Avancé" not in content

    def test_search_empty_returns_all(self, client, catalogue_courses):
        resp = client.get(reverse('catalogue'), {'q': ''})
        content = resp.content.decode()
        assert "Python Débutant" in content
        assert "Django Avancé" in content

    def test_search_no_results(self, client, catalogue_courses):
        resp = client.get(reverse('catalogue'), {'q': 'zzzznothing'})
        content = resp.content.decode()
        assert "Aucune formation" in content


# ── HTMX partial ────────────────────────────────────────

@pytest.mark.django_db
class TestCatalogueHTMX:

    def test_htmx_returns_partial(self, client, catalogue_courses):
        resp = client.get(
            reverse('catalogue'),
            {'sort': 'title'},
            HTTP_HX_REQUEST='true',
        )
        content = resp.content.decode()
        assert '<html' not in content.lower()
        assert "Python Débutant" in content

    def test_htmx_respects_sort(self, client, catalogue_courses):
        resp = client.get(
            reverse('catalogue'),
            {'sort': '-price'},
            HTTP_HX_REQUEST='true',
        )
        content = resp.content.decode()
        pos_django = content.find("Django Avancé")
        pos_alpine = content.find("Alpine JS Gratuit")
        assert pos_django < pos_alpine


# ── Page dédiée (pas le hero) ────────────────────────────

@pytest.mark.django_db
class TestCatalogueIsDedicated:

    def test_has_catalogue_title(self, client, catalogue_courses):
        """La page doit avoir un titre 'Catalogue' visible."""
        resp = client.get(reverse('catalogue'))
        content = resp.content.decode()
        assert "Catalogue" in content

    def test_no_hero_section(self, client, catalogue_courses):
        """La page Catalogue ne doit PAS afficher le hero de la homepage."""
        resp = client.get(reverse('catalogue'))
        content = resp.content.decode()
        # Le hero a ce texte spécifique — il ne doit pas être dans le body
        assert "concrètement." not in content
