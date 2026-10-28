import json

import pytest
from django.urls import reverse

from courses.models import ContentBlock, QuizResult


@pytest.mark.django_db
class TestQuizLogic:
    @pytest.fixture
    def quiz_block(self, course):
        """Crée un bloc Quiz pour le test"""
        # On a besoin d'un module et d'une leçon pour attacher le bloc
        module = course.modules.create(title="Module Test", order=1)
        lesson = module.lessons.create(title="Leçon Quiz", slug="lecon-quiz", order=1)

        return ContentBlock.objects.create(lesson=lesson, type='quiz', quiz_title="Quiz Test", order=1)

    def test_save_quiz_result_creates_record(self, client, student, quiz_block):
        """Vérifie que l'API sauvegarde bien le score"""
        # 1. On connecte l'étudiant
        client.force_login(student)
        from access.models import AccessRequest

        AccessRequest.objects.create(student=student, course=quiz_block.lesson.module.course, status='APPROVED')

        # 2. On prépare les données (simule le JS)
        data = {'score': 8, 'total': 10}
        url = reverse('save_quiz_result', args=[quiz_block.id])

        # 3. On envoie la requête POST (simule le fetch)
        response = client.post(url, data=json.dumps(data), content_type='application/json')

        # 4. Vérifications
        assert response.status_code == 200
        assert QuizResult.objects.count() == 1

        result = QuizResult.objects.first()
        assert result.student == student
        assert result.score == 8
        assert result.total_questions == 10

    def test_save_quiz_result_updates_existing(self, client, student, quiz_block):
        """Vérifie qu'on écrase l'ancien score (pas de doublon)"""
        client.force_login(student)
        from access.models import AccessRequest

        AccessRequest.objects.create(student=student, course=quiz_block.lesson.module.course, status='APPROVED')
        url = reverse('save_quiz_result', args=[quiz_block.id])

        # Premier essai : 5/10
        client.post(url, json.dumps({'score': 5, 'total': 10}), content_type='application/json')

        # Deuxième essai : 10/10 (Il s'est amélioré)
        client.post(url, json.dumps({'score': 10, 'total': 10}), content_type='application/json')

        # Vérif : Toujours une seule ligne, mais avec le nouveau score
        assert QuizResult.objects.count() == 1
        assert QuizResult.objects.first().score == 10

    def test_save_quiz_result_protected(self, client, quiz_block):
        """Vérifie qu'un inconnu ne peut pas sauvegarder de score"""
        # Pas de login ici
        url = reverse('save_quiz_result', args=[quiz_block.id])
        response = client.post(url, json.dumps({'score': 10, 'total': 10}), content_type='application/json')

        # Doit être redirigé vers le login (302)
        assert response.status_code == 302
        assert QuizResult.objects.count() == 0
