"""
Catalogue des e-mails transactionnels du site.

Chaque `build_*` reçoit un objet métier et retourne la liste des `EmailContent` à envoyer (sans rien envoyer) :
c'est ce qui permet de les tester et de les prévisualiser. `deliver(nom, pk)` charge l'objet, construit et envoie.
Pour déclencher un e-mail depuis le code : `notifications.tasks.dispatch_email('nom', pk)`.
"""

from django.contrib.auth import get_user_model
from django.urls import reverse

from access.models import AccessRequest
from access.utils import generate_receipt_pdf
from config.emailing import EmailContent, absolute_url, send_email
from contact.models import ContactMessage
from courses.models import CourseCompletion
from instructors.models import InstructorRequest
from support.models import Question, Response


def _full_name(user):
    return user.get_full_name() or user.first_name or user.email


def _first_name(user):
    return user.first_name or user.email


def _superuser_emails(exclude=None):
    """Adresses des superutilisateurs (équipe de la plateforme), hors `exclude`."""
    admins = get_user_model().objects.filter(is_superuser=True, is_active=True).exclude(email='')
    if exclude is not None:
        admins = admins.exclude(pk=exclude.pk)
    return list(admins.values_list('email', flat=True))


def _course_staff_emails(course, author):
    """Destinataires d'une question : l'instructeur du cours, sinon l'équipe de la plateforme."""
    instructor = course.instructor
    if instructor and instructor != author and instructor.email:
        return [instructor.email]
    return _superuser_emails(exclude=author)


# ── Accès aux formations ─────────────────────────────────────────────────────


def _access_context(access_request):
    coupon = access_request.applied_coupon
    return {
        'course': access_request.course,
        'amount': int(
            access_request.final_price if access_request.final_price is not None else access_request.course.price
        ),
        'coupon_code': coupon.code if coupon else '',
    }


def build_access_received(access_request):
    student = access_request.student
    return [
        EmailContent(
            to=[student.email],
            subject='Preuve de paiement bien reçue',
            template='access_received',
            context={
                **_access_context(access_request),
                'first_name': _first_name(student),
                'cta_url': absolute_url(reverse('course_detail', args=[access_request.course.slug])),
            },
        )
    ]


def build_access_admin_alert(access_request):
    student = access_request.student
    return [
        EmailContent(
            to=_superuser_emails(exclude=student),
            subject=f'Paiement à valider : {access_request.course.title}',
            template='access_admin_alert',
            context={
                **_access_context(access_request),
                'student_name': _full_name(student),
                'student_email': student.email,
                'cta_url': absolute_url(reverse('admin:access_accessrequest_change', args=[access_request.pk])),
            },
        )
    ]


def build_access_approved(access_request, with_receipt=True):
    student = access_request.student
    receipt = generate_receipt_pdf(access_request) if with_receipt else b''
    return [
        EmailContent(
            to=[student.email],
            subject=f'Accès validé : {access_request.course.title}',
            template='access_approved',
            context={
                **_access_context(access_request),
                'first_name': _first_name(student),
                'has_receipt': bool(receipt),
                'cta_url': absolute_url(reverse('course_detail', args=[access_request.course.slug])),
            },
            attachments=[(f'Recu_{access_request.pk}.pdf', receipt, 'application/pdf')] if receipt else [],
        )
    ]


def build_access_rejected(access_request):
    student = access_request.student
    return [
        EmailContent(
            to=[student.email],
            subject=f'Paiement non validé : {access_request.course.title}',
            template='access_rejected',
            context={
                **_access_context(access_request),
                'first_name': _first_name(student),
                'admin_note': access_request.admin_note,
                'cta_url': absolute_url(reverse('request_access', args=[access_request.course.pk])),
            },
        )
    ]


# ── Certificat ───────────────────────────────────────────────────────────────


def build_certificate_ready(completion):
    return [
        EmailContent(
            to=[completion.student.email],
            subject=f'Votre certificat est prêt : {completion.course.title}',
            template='certificate_ready',
            context={
                'first_name': _first_name(completion.student),
                'course': completion.course,
                'cta_url': absolute_url(reverse('download_certificate', args=[completion.course.slug])),
            },
        )
    ]


# ── Demandes d'instructeur ───────────────────────────────────────────────────


def build_instructor_approved(instructor_request):
    return [
        EmailContent(
            to=[instructor_request.user.email],
            subject='Votre espace instructeur est activé',
            template='instructor_approved',
            context={
                'first_name': _first_name(instructor_request.user),
                'plan': instructor_request.plan,
                'cta_url': absolute_url(reverse('instructor_dashboard')),
            },
        )
    ]


def build_instructor_rejected(instructor_request):
    return [
        EmailContent(
            to=[instructor_request.user.email],
            subject="Votre demande d'espace instructeur",
            template='instructor_rejected',
            context={
                'first_name': _first_name(instructor_request.user),
                'plan': instructor_request.plan,
                'admin_note': instructor_request.admin_note,
                'cta_url': absolute_url(reverse('instructor_plans')),
            },
        )
    ]


# ── Support ──────────────────────────────────────────────────────────────────


def build_question_new(question):
    return [
        EmailContent(
            to=_course_staff_emails(question.course, question.student),
            subject=f'Nouvelle question : {question.title}',
            template='question_new',
            context={
                'question': question,
                'course': question.course,
                'lesson': question.lesson,
                'student_name': _full_name(question.student),
                'cta_url': absolute_url(reverse('question_detail', args=[question.pk])),
            },
        )
    ]


def build_question_reply(response):
    question, author = response.question, response.author
    course = question.course
    author_name = 'Votre Sensei' if response.is_instructor else _full_name(author)
    url = absolute_url(reverse('question_detail', args=[question.pk]))

    recipients = []
    if question.student != author and question.student.email:
        recipients.append(question.student)
    instructor = course.instructor
    if instructor and instructor not in (author, question.student) and instructor.email:
        recipients.append(instructor)

    return [
        EmailContent(
            to=[user.email],
            subject=f'Nouvelle réponse : {question.title}',
            template='question_reply',
            context={
                'first_name': _first_name(user),
                'question': question,
                'course': course,
                'response': response,
                'author_name': author_name,
                'cta_url': url,
            },
        )
        for user in recipients
    ]


# ── Contact ──────────────────────────────────────────────────────────────────


def build_contact_message(message):
    """Message pour l'équipe ; `Reply-To` = l'expéditeur, pour répondre directement depuis la messagerie."""
    from django.conf import settings

    return [
        EmailContent(
            to=[settings.CONTACT_EMAIL],
            subject=f'Contact : {message.reason or "Sans motif"}',
            template='contact_message',
            reply_to=[message.email],
            context={
                'message': message,
                'reason': message.reason or 'Sans motif',
                'cta_url': f'mailto:{message.email}?subject=Re: {message.reason or "Votre message"}',
            },
        )
    ]


def build_contact_receipt(message):
    return [
        EmailContent(
            to=[message.email],
            subject='Nous avons bien reçu votre message',
            template='contact_receipt',
            context={
                'message': message,
                'reason': message.reason or 'Sans motif',
                'cta_url': absolute_url(reverse('catalogue')),
            },
        )
    ]


# ── Registre ─────────────────────────────────────────────────────────────────

EMAILS = {
    'access_received': (AccessRequest, build_access_received),
    'access_admin_alert': (AccessRequest, build_access_admin_alert),
    'access_approved': (AccessRequest, build_access_approved),
    'access_rejected': (AccessRequest, build_access_rejected),
    'certificate_ready': (CourseCompletion, build_certificate_ready),
    'instructor_approved': (InstructorRequest, build_instructor_approved),
    'instructor_rejected': (InstructorRequest, build_instructor_rejected),
    'question_new': (Question, build_question_new),
    'question_reply': (Response, build_question_reply),
    'contact_message': (ContactMessage, build_contact_message),
    'contact_receipt': (ContactMessage, build_contact_receipt),
}


def deliver(name, pk):
    """Charge l'objet, construit l'e-mail `name` et l'envoie. Retourne le nombre d'e-mails acceptés."""
    model, builder = EMAILS[name]
    obj = model.objects.filter(pk=pk).first()
    if obj is None:
        return 0
    return sum(send_email(content) for content in builder(obj))
