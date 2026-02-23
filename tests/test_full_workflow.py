import pytest
from django.contrib.auth import get_user_model
from courses.models import Course, Module, Lesson, StudentProgress
from support.models import Question
from notifications.models import Notification

@pytest.mark.django_db
class TestFullNotifications:

    def test_admin_notified_on_question(self, client, student):
        """ Vérifie que l'admin reçoit une notif quand un élève pose une question """
        User = get_user_model()
        
        # CORRECTION : On ne met PAS username, seulement email et password
        admin = User.objects.create_superuser(email="admin@test.com", password="pwd")
        
        # Setup Cours
        course = Course.objects.create(title="Maths", slug="maths")
        module = Module.objects.create(course=course, title="Algèbre")
        lesson = Lesson.objects.create(module=module, title="1+1", slug="un-plus-un")

        # L'étudiant pose une question
        Question.objects.create(
            student=student, course=course, lesson=lesson, 
            title="Help", content="Besoin d'aide"
        )

        # L'admin doit avoir 1 notif
        assert Notification.objects.filter(recipient=admin).count() == 1
        notif = Notification.objects.get(recipient=admin)
        assert "Nouvelle Question" in notif.title
        # On vérifie que l'email de l'étudiant est dans le message
        assert student.email in notif.message

    def test_course_completion_notification(self, student):
        """ 
        Vérifie que si un cours a 2 leçons et qu'on finit la 2ème, 
        on reçoit la notif 'Cours Terminé'. 
        """
        course = Course.objects.create(title="Python Expert", slug="python-expert")
        module = Module.objects.create(course=course, title="Module Unique")
        lesson1 = Lesson.objects.create(module=module, title="L1", slug="l1", order=1)
        lesson2 = Lesson.objects.create(module=module, title="L2", slug="l2", order=2)

        # Finit leçon 1
        StudentProgress.objects.create(student=student, lesson=lesson1)
        assert Notification.objects.filter(recipient=student, title__contains="Leçon validée").count() == 1
        assert Notification.objects.filter(recipient=student, title__contains="Cours COMPLÉTÉ").count() == 0

        # Finit leçon 2
        StudentProgress.objects.create(student=student, lesson=lesson2)
        assert Notification.objects.filter(recipient=student, title__contains="Leçon validée").count() == 2
        assert Notification.objects.filter(recipient=student, title__contains="Cours COMPLÉTÉ").count() == 1