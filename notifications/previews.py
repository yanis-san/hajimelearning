"""Prévisualisation des e-mails en développement (`/__emails__/`) avec des objets d'exemple non enregistrés."""

from access.models import AccessRequest, Coupon
from config.emailing import absolute_url
from contact.models import ContactMessage, ContactReason
from courses.models import Course, CourseCompletion, Lesson
from instructors.models import InstructorPlan, InstructorRequest
from support.models import Question, Response
from users.models import User

from . import emails
from .preferences import preferences_url


def _samples():
    student = User(pk=1, email='yanis@example.com', first_name='Yanis', last_name='Benali')
    teacher = User(pk=2, email='sensei@example.com', first_name='Sensei', last_name='Tanaka')
    course = Course(pk=1, title='Japonais N5', slug='japonais-n5', price=5000, instructor=teacher)
    lesson = Lesson(pk=1, title='Hiragana')
    access = AccessRequest(
        pk=1,
        student=student,
        course=course,
        final_price=4000,
        applied_coupon=Coupon(code='PROMO20'),
        admin_note="La capture est floue : merci d'envoyer le reçu complet.",
    )
    question = Question(
        pk=1,
        student=student,
        course=course,
        lesson=lesson,
        title='Différence あ / お ?',
        content="Je confonds toujours les deux.\nAuriez-vous une astuce ?",
    )
    response = Response(
        pk=1, question=question, author=teacher, is_instructor=True, content="Pense au trait de gauche !"
    )
    instructor_request = InstructorRequest(
        pk=1,
        user=student,
        plan=InstructorPlan(name='Starter'),
        admin_note='Le justificatif est illisible.',
    )
    message = ContactMessage(
        pk=1,
        first_name='Yanis',
        last_name='Benali',
        email='yanis@example.com',
        reason=ContactReason(label='Cours particulier'),
        message='Bonjour,\nJe souhaite des cours en visio.',
    )
    completion = CourseCompletion(pk=1, student=student, course=course)
    return {
        'access_received': emails.build_access_received(access),
        'access_admin_alert': emails.build_access_admin_alert(access),
        'access_approved': emails.build_access_approved(access, with_receipt=False),
        'access_rejected': emails.build_access_rejected(access),
        'certificate_ready': emails.build_certificate_ready(completion),
        'instructor_approved': emails.build_instructor_approved(instructor_request),
        'instructor_rejected': emails.build_instructor_rejected(instructor_request),
        'question_new': emails.build_question_new(question),
        'question_reply': emails.build_question_reply(response),
        'contact_message': emails.build_contact_message(message),
        'contact_receipt': emails.build_contact_receipt(message),
    }


def preview_contents():
    """Nom → premier `EmailContent` de chaque e-mail du catalogue, construit avec des données d'exemple."""
    contents = {}
    for name, built in _samples().items():
        if not built:
            continue
        content = built[0]
        category = emails.EMAILS[name][2]
        if category != emails.ESSENTIAL:  # montre le pied de page de désabonnement des e-mails facultatifs
            content.unsubscribe_url = absolute_url('/notifications/unsubscribe/exemple/')
            content.preferences_url = preferences_url()
        contents[name] = content
    return contents
