import pytest
from django.urls import reverse
from courses.models import Course

@pytest.mark.django_db
class TestSEO:

    @pytest.fixture
    def published_course(self):
        return Course.objects.create(
            title="Cours SEO",
            slug="cours-seo",
            price=1000,
            is_published=True,
            meta_description="Apprenez le SEO facilement."
        )

    def test_sitemap_xml_is_generated(self, client, published_course):
        """ Vérifie que le fichier sitemap.xml existe et contient le cours """
        response = client.get('/sitemap.xml')
        
        assert response.status_code == 200
        assert 'application/xml' in response['Content-Type'] or 'text/xml' in response['Content-Type']
        # On vérifie que l'URL du cours est dans le XML
        assert f"/course/{published_course.slug}/" in response.content.decode()

    def test_meta_tags_on_course_page(self, client, published_course):
        """ Vérifie que les balises meta s'affichent bien sur la page """
        url = reverse('course_detail', args=[published_course.slug])
        response = client.get(url)
        content = response.content.decode()
        
        # Vérif Title
        assert f"<title>{published_course.title} | Hajime Learning</title>" in content
        # Vérif Description
        assert f'name="description" content="{published_course.meta_description}"' in content