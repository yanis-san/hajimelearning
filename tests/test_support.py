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
        from notifications.models import Notification
        lesson, question = lesson_with_question

        client.force_login(student)
        url = reverse('mark_resolved', args=[question.id])

        client.post(url)

        question.refresh_from_db()
        assert question.status == 'RESOLVED'

        # Une notif de type support doit avoir été créée pour l'étudiant
        notif = Notification.objects.filter(
            recipient=student,
            category=Notification.CATEGORY_SUPPORT,
        ).first()
        assert notif is not None
        assert "résolue" in notif.title.lower()

    def test_peer_student_with_course_access_can_reply_when_enabled(self, client, student, course, lesson_with_question, settings):
        """Un camarade inscrit au même cours peut voir et répondre si l'entraide est activée."""
        settings.ALLOW_STUDENT_REPLIES = True
        from users.models import User
        from access.models import AccessRequest

        peer = User.objects.create_user(email='camarade@test.com', password='password123', first_name='Karim')
        # Donner accès au cours payant au camarade
        AccessRequest.objects.create(student=peer, course=course, status='APPROVED')

        lesson, question = lesson_with_question

        client.force_login(peer)
        url = reverse('question_detail', args=[question.id])

        # Le camarade peut accéder à la discussion
        get_res = client.get(url)
        assert get_res.status_code == 200
        assert get_res.context['can_reply'] is True

        # Le camarade poste une réponse d'entraide
        post_res = client.post(url, {'content': 'Essaie de redémarrer ton terminal !'})
        assert post_res.status_code == 302

        reply = Response.objects.latest('id')
        assert reply.author == peer
        assert reply.is_instructor is False
        assert reply.content == 'Essaie de redémarrer ton terminal !'

    def test_outsider_without_course_access_cannot_view_or_reply(self, client, course, lesson_with_question, settings):
        """Un utilisateur externe non inscrit au cours ne peut ni voir ni répondre à la discussion."""
        settings.ALLOW_STUDENT_REPLIES = True
        from users.models import User

        outsider = User.objects.create_user(email='inconnu@test.com', password='password123')
        lesson, question = lesson_with_question

        client.force_login(outsider)
        url = reverse('question_detail', args=[question.id])

        # Accès refusé et redirection
        res = client.get(url, follow=True)
        assert any("inscrit" in m.message.lower() for m in res.context.get('messages', []))
        assert Response.objects.count() == 0

    def test_peer_cannot_reply_when_replies_disabled(self, client, course, lesson_with_question, settings):
        """Si ALLOW_STUDENT_REPLIES est False, le camarade ne peut pas poster de réponse."""
        settings.ALLOW_STUDENT_REPLIES = False
        from users.models import User
        from access.models import AccessRequest

        peer = User.objects.create_user(email='camarade2@test.com', password='password123')
        AccessRequest.objects.create(student=peer, course=course, status='APPROVED')

        lesson, question = lesson_with_question

        client.force_login(peer)
        url = reverse('question_detail', args=[question.id])

        res = client.post(url, {'content': 'Je veux répondre'})
        assert Response.objects.count() == 0

    def test_new_question_sends_email_to_instructor(self, client, student, course, mailoutbox):
        """Quand un étudiant pose une question, un email de notification est envoyé à l'instructeur."""
        from users.models import User
        instructor = User.objects.create_user(email='prof@test.com', password='password123', first_name='Prof')
        course.instructor = instructor
        course.save()

        module = course.modules.create(title="Mod", order=1)
        lesson = module.lessons.create(title="Lec", slug="lec", order=1)

        client.force_login(student)
        url = reverse('ask_question', args=[lesson.id])
        client.post(url, {'title': 'Question urgente', 'content': 'Comment installer pip ?'})

        assert Question.objects.count() == 1
        # L'instructeur doit avoir reçu un email
        instructor_emails = [m for m in mailoutbox if instructor.email in m.to]
        assert len(instructor_emails) >= 1
        email = instructor_emails[0]
        assert "Question urgente" in email.subject or "Question urgente" in email.body
        assert "pip" in email.body

    def test_instructor_reply_sends_email_to_question_author(self, client, admin_user, lesson_with_question, mailoutbox):
        """Quand l'instructeur/admin répond, l'étudiant auteur reçoit un email."""
        lesson, question = lesson_with_question

        client.force_login(admin_user)
        url = reverse('question_detail', args=[question.id])
        mailoutbox.clear()

        client.post(url, {'content': 'Voici la documentation officielle : docs.python.org'})

        # L'étudiant auteur doit avoir reçu un email
        student_emails = [m for m in mailoutbox if question.student.email in m.to]
        assert len(student_emails) >= 1
        email = student_emails[0]
        assert question.title in email.subject or question.title in email.body
        assert "docs.python.org" in email.body

    def test_peer_reply_sends_email_to_author_and_instructor(self, client, student, course, lesson_with_question, mailoutbox, settings):
        """Quand un camarade répond, l'étudiant auteur et l'instructeur sont notifiés par email."""
        settings.ALLOW_STUDENT_REPLIES = True
        from users.models import User
        from access.models import AccessRequest

        instructor = User.objects.create_user(email='prof2@test.com', password='password123')
        course.instructor = instructor
        course.save()

        peer = User.objects.create_user(email='aideur@test.com', password='password123', first_name='Sofiane')
        AccessRequest.objects.create(student=peer, course=course, status='APPROVED')

        lesson, question = lesson_with_question
        client.force_login(peer)
        url = reverse('question_detail', args=[question.id])
        mailoutbox.clear()

        client.post(url, {'content': 'Tu as oublié le double égal =='})

        # 1. L'auteur reçoit un email
        author_emails = [m for m in mailoutbox if question.student.email in m.to]
        assert len(author_emails) >= 1

        # 2. L'instructeur reçoit un email
        instructor_emails = [m for m in mailoutbox if instructor.email in m.to]
        assert len(instructor_emails) >= 1

        # 3. Le camarade qui a écrit la réponse ne reçoit PAS d'email
        peer_emails = [m for m in mailoutbox if peer.email in m.to]
        assert len(peer_emails) == 0