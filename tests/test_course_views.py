import pytest
from django.urls import reverse

from access.models import AccessRequest
from courses.models import Category, Course


@pytest.mark.django_db
class TestCourseDetailView:

    def test_visitor_sees_landing_page(self, client, course):
        """ Scénario 1 : Un inconnu voit la page de vente (Prix, Trailer) """
        url = reverse('course_detail', args=[course.slug])
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        # Il doit voir le prix et le marketing
        assert "Prix :" in content or "DA" in content
        assert "Débloquer l'accès" in content or "Rejoindre" in content
        assert course.short_description in content

        # Il ne doit PAS voir le badge inscrit
        assert "Inscrit" not in content

    def test_student_no_access_sees_landing_page(self, client, student, course):
        """ Scénario 2 : Un étudiant connecté (sans payer) voit aussi la page de vente """
        client.force_login(student)
        url = reverse('course_detail', args=[course.slug])
        response = client.get(url)

        # Il doit toujours voir le bouton payer
        assert "Débloquer l'accès" in response.content.decode()
        assert "Inscrit" not in response.content.decode()

    def test_student_with_access_sees_dashboard(self, client, student, course):
        """ Scénario 3 : Un étudiant qui a payé voit le Dashboard """
        # On simule le paiement validé
        AccessRequest.objects.create(student=student, course=course, status='APPROVED')

        client.force_login(student)
        url = reverse('course_detail', args=[course.slug])
        response = client.get(url)
        content = response.content.decode()

        assert "Inscrit" in content

        # On vérifie qu'on ne voit PLUS le prix (preuve qu'on est en mode étudiant)
        assert "Prix :" not in content

    def test_free_course_is_open(self, client, student, free_course):
        """ Scénario 4 : Un cours gratuit est accessible après inscription explicite """
        from access.models import Enrollment
        Enrollment.objects.create(student=student, course=free_course)
        client.force_login(student)
        url = reverse('course_detail', args=[free_course.slug])
        response = client.get(url)

        # Inscrit = Accès accordé
        assert "Inscrit" in response.content.decode()


# ── Homepage — catégories & pills HTMX ──────────────────

@pytest.mark.django_db
class TestHomepageCategories:

    def test_categories_in_context(self, client):
        """La vue course_list expose 'categories' au template."""
        cat = Category.objects.create(name="Python", slug="python")
        Course.objects.create(
            title="Cours Python", slug="cours-python",
            short_description="Desc", description="Contenu",
            price=1000, is_published=True, is_featured=True, category=cat,
        )
        resp = client.get(reverse('course_list'))
        assert resp.status_code == 200
        assert 'categories' in resp.context
        assert cat in resp.context['categories']

    def test_homepage_pills_have_hx_get(self, client):
        """Les pills de la homepage utilisent hx-get pour filtrer sur place."""
        Category.objects.create(name="Web", slug="web")
        resp = client.get(reverse('course_list'))
        content = resp.content.decode()
        assert 'hx-get' in content

    def test_homepage_pills_not_redirect_links(self, client):
        """Aucun <a href=/catalogue/?category= sur la homepage (évite la redirection)."""
        Category.objects.create(name="Web", slug="web")
        resp = client.get(reverse('course_list'))
        content = resp.content.decode()
        assert '<a href="/catalogue/?category=' not in content

    def test_homepage_shows_featured_courses(self, client):
        """La homepage n'affiche que les cours is_featured=True."""
        Course.objects.create(
            title="Cours En Vedette", slug="en-vedette",
            short_description="Desc", description="Contenu",
            price=1000, is_published=True, is_featured=True,
        )
        Course.objects.create(
            title="Cours Normal", slug="normal",
            short_description="Desc", description="Contenu",
            price=500, is_published=True, is_featured=False,
        )
        resp = client.get(reverse('course_list'))
        content = resp.content.decode()
        assert "Cours En Vedette" in content
        assert "Cours Normal" not in content

    def test_homepage_htmx_category_filter_returns_partial(self, client):
        """Un appel HTMX avec ?category filtre sur place (retourne un partial)."""
        cat = Category.objects.create(name="Python", slug="python")
        Course.objects.create(
            title="Cours Python", slug="cours-python-htmx",
            short_description="Desc", description="Contenu",
            price=1000, is_published=True, category=cat,
        )
        resp = client.get(
            reverse('catalogue'),
            {'category': 'python'},
            HTTP_HX_REQUEST='true',
        )
        content = resp.content.decode()
        assert '<html' not in content.lower()
        assert "Cours Python" in content


@pytest.mark.django_db
class TestHomepageVideoOptimization:

    def test_homepage_videos_have_performance_attributes(self, client):
        """Les vidéos de la homepage doivent être optimisées pour le chargement et le réseau."""
        resp = client.get(reverse('course_list'))
        assert resp.status_code == 200
        content = resp.content.decode()

        # 1. hero.mp4 : au-dessus de la ligne de flottaison, préchargement allégé des métadonnées
        assert 'videos/hero.mp4' in content
        assert 'preload="metadata"' in content

        # 2. other.mp4 et presentation.mp4 : sous la ligne de flottaison, différées avec preload="none"
        assert 'videos/other.mp4' in content
        assert 'videos/presentation.mp4' in content
        # Au moins deux vidéos ont preload="none"
        assert content.count('preload="none"') >= 2

        # 3. Observateur d'intersection pour lancer/mettre en pause au scroll
        assert 'IntersectionObserver' in content or 'x-intersect' in content
