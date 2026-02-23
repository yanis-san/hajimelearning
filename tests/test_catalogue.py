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
from courses.models import Course, Module, Category


@pytest.fixture
def category_python(db):
    return Category.objects.create(name="Python", slug="python", order=1)


@pytest.fixture
def category_web(db):
    return Category.objects.create(name="Web", slug="web", order=2)


@pytest.fixture
def courses_with_categories(db, category_python, category_web):
    """2 cours catégorisés + 1 sans catégorie, tous publiés."""
    c1 = Course.objects.create(
        title="Python Débutant",
        slug="python-debutant-cat",
        short_description="Apprenez Python",
        description="Contenu",
        price=3000,
        is_published=True,
        category=category_python,
    )
    c2 = Course.objects.create(
        title="Django Avancé",
        slug="django-avance-cat",
        short_description="Maîtrisez Django",
        description="Contenu",
        price=5000,
        is_published=True,
        category=category_web,
    )
    c3 = Course.objects.create(
        title="Alpine JS Gratuit",
        slug="alpine-js-gratuit-cat",
        short_description="Découvrez Alpine JS",
        description="Contenu",
        price=0,
        is_published=True,
        category=None,
    )
    return c1, c2, c3


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


# ── Filtrage par catégorie ─────────────────────────────

@pytest.mark.django_db
class TestCatalogueCategoryFilter:

    def test_category_filter_shows_matching_only(self, client, courses_with_categories):
        """?category=python ne retourne que les cours de cette catégorie."""
        resp = client.get(reverse('catalogue'), {'category': 'python'})
        content = resp.content.decode()
        assert "Python Débutant" in content
        assert "Django Avancé" not in content

    def test_category_filter_htmx_partial(self, client, courses_with_categories):
        """HTMX + ?category retourne le partial sans <html>."""
        resp = client.get(
            reverse('catalogue'),
            {'category': 'python'},
            HTTP_HX_REQUEST='true',
        )
        content = resp.content.decode()
        assert '<html' not in content.lower()
        assert "Python Débutant" in content
        assert "Django Avancé" not in content

    def test_category_filter_htmx_web(self, client, courses_with_categories):
        resp = client.get(
            reverse('catalogue'),
            {'category': 'web'},
            HTTP_HX_REQUEST='true',
        )
        content = resp.content.decode()
        assert "Django Avancé" in content
        assert "Python Débutant" not in content

    def test_unknown_category_returns_empty_state(self, client, courses_with_categories):
        """Une catégorie inexistante affiche le message vide."""
        resp = client.get(reverse('catalogue'), {'category': 'inexistant'})
        content = resp.content.decode()
        assert "Aucune formation" in content

    def test_no_category_shows_all_published(self, client, courses_with_categories):
        resp = client.get(reverse('catalogue'))
        content = resp.content.decode()
        assert "Python Débutant" in content
        assert "Django Avancé" in content
        assert "Alpine JS Gratuit" in content

    def test_category_filter_combined_with_sort(self, client, courses_with_categories):
        """?category + ?sort fonctionnent ensemble."""
        resp = client.get(reverse('catalogue'), {'category': 'python', 'sort': 'title'})
        assert resp.status_code == 200
        assert "Python Débutant" in resp.content.decode()


# ── Pills HTMX — pas de redirection native ──────────────

@pytest.mark.django_db
class TestCataloguePillsHTMX:

    def test_pills_have_hx_get_attribute(self, client, courses_with_categories):
        """Les pills ont hx-get, pas de <a href> redirigé."""
        resp = client.get(reverse('catalogue'))
        content = resp.content.decode()
        assert 'hx-get' in content

    def test_pills_are_not_redirect_links(self, client, courses_with_categories):
        """Aucun <a href=/catalogue/?category= ne doit exister (causerait une redirection)."""
        resp = client.get(reverse('catalogue'))
        content = resp.content.decode()
        assert '<a href="/catalogue/?category=' not in content

    def test_category_names_shown_in_pills(self, client, courses_with_categories, category_python, category_web):
        resp = client.get(reverse('catalogue'))
        content = resp.content.decode()
        assert category_python.name in content
        assert category_web.name in content

    def test_pill_toutes_has_hx_get(self, client, courses_with_categories):
        """La pill 'Toutes' pointe vers {% url 'catalogue' %} via hx-get."""
        resp = client.get(reverse('catalogue'))
        content = resp.content.decode()
        # hx-get doit contenir l'URL du catalogue
        assert 'hx-get="/catalogue/"' in content or 'hx-get="/catalogue' in content


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
