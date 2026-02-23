import pytest
from django.urls import reverse
from support.models import Question, Response

@pytest.mark.django_db
class TestSupportSystem:

    @pytest.fixture
    def lesson_with_question(self, student, course):
        """ Une leçon avec une question déjà posée """
        module = course.modules.create(title="Mod", order=1)
        lesson = module.lessons.create(title="Lec", slug="lec", order=1)
        question = Question.objects.create(
            student=student,
            course=course,
            lesson=lesson,
            title="Help me",
            content="I am stuck"
        )
        return lesson, question

    def test_student_can_ask_question(self, client, student, course):
        """ Un étudiant peut poster une question """
        module = course.modules.create(title="Mod", order=1)
        lesson = module.lessons.create(title="Lec", slug="lec", order=1)
        
        client.force_login(student)
        url = reverse('ask_question', args=[lesson.id])
        
        data = {'title': 'Bug Python', 'content': 'Erreur ligne 40'}
        response = client.post(url, data, follow=True)
        
        assert response.status_code == 200
        assert Question.objects.count() == 1
        q = Question.objects.first()
        assert q.title == 'Bug Python'
        assert q.status == 'OPEN'

    def test_instructor_reply_marks_as_official(self, client, admin_user, lesson_with_question):
        """ Une réponse de l'admin doit être marquée 'is_instructor' """
        lesson, question = lesson_with_question
        
        client.force_login(admin_user)
        url = reverse('question_detail', args=[question.id])
        
        data = {'content': 'Voici la solution...'}
        client.post(url, data)
        
        assert Response.objects.count() == 1
        reply = Response.objects.first()
        assert reply.is_instructor is True
        assert reply.author == admin_user

    def test_resolve_question(self, client, student, lesson_with_question):
        """ L'étudiant peut marquer sa propre question comme résolue """
        lesson, question = lesson_with_question
        
        client.force_login(student)
        url = reverse('mark_resolved', args=[question.id])
        
        client.post(url)
        
        question.refresh_from_db()
        assert question.status == 'RESOLVED'