import pytest
from django.urls import reverse

@pytest.mark.django_db
class TestSecurity:

    def test_student_cannot_access_builder(self, client, student, course):
        """ Un étudiant ne doit PAS voir le Builder """
        # On crée une leçon pour avoir une URL valide
        module = course.modules.create(title="Mod", order=1)
        lesson = module.lessons.create(title="Lecon", slug="lecon", order=1)
        
        client.force_login(student)
        
        # L'étudiant essaie d'aller sur /manage/...
        url = reverse('manage_lesson_content', args=[course.slug, lesson.slug])
        response = client.get(url)
        
        # Il doit être redirigé (302) vers l'accueil ou login, mais PAS avoir 200 OK
        assert response.status_code != 200
        assert response.status_code == 302

    def test_student_cannot_add_block(self, client, student, course):
        """ Un étudiant ne doit PAS pouvoir poster un bloc """
        module = course.modules.create(title="Mod", order=1)
        lesson = module.lessons.create(title="Lecon", slug="lecon", order=1)
        
        client.force_login(student)
        
        # Il essaie d'ajouter un bloc texte
        url = reverse('add_block', args=[lesson.id, 'text'])
        data = {'text_content': 'HACKED'}
        
        response = client.post(url, data)
        
        # Si tu as bien mis @staff_member_required ou le check is_staff :
        # Ça doit être 302 (Redirect login admin) ou 403 (Interdit)
        # Si c'est 200, C'EST UNE FAILLE DE SÉCURITÉ !
        assert response.status_code in [302, 403] 
        
        # Vérif ultime : Le bloc n'a pas été créé
        assert lesson.blocks.count() == 0