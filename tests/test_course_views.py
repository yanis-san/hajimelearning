import pytest
from django.urls import reverse
from access.models import AccessRequest

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
        """ Scénario 4 : Un cours gratuit est ouvert automatiquement """
        client.force_login(student)
        url = reverse('course_detail', args=[free_course.slug])
        response = client.get(url)
        
        # Gratuit = Accès direct
        assert "Inscrit" in response.content.decode()