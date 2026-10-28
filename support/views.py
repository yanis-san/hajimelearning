from collections import defaultdict

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from access.models import AccessRequest, ActivationCode, Enrollment, user_has_access
from courses.models import Course, Lesson

from .forms import QuestionForm, ResponseForm
from .models import Question


def _is_course_instructor(user, course):
    """Vérifie si l'utilisateur est instructeur ou staff de ce cours."""
    if not user.is_authenticated:
        return False
    return user.is_staff or course.instructor_id == user.id


@login_required
@require_POST
def ask_question(request, lesson_id):
    """Traite le formulaire de question envoyé depuis une leçon."""
    lesson = get_object_or_404(Lesson.objects.select_related('module__course'), id=lesson_id)
    course = lesson.module.course
    lesson_url = redirect('lesson_detail', course_slug=course.slug, lesson_slug=lesson.slug)

    # Seuls les étudiants ayant accès au cours (ou à une leçon gratuite) peuvent poser une question
    if not (lesson.is_free or user_has_access(request.user, course)):
        messages.error(request, "Vous devez avoir accès à ce cours pour poser une question.")
        return redirect('course_detail', course_slug=course.slug)

    form = QuestionForm(request.POST)
    if form.is_valid():
        question = form.save(commit=False)
        question.student = request.user
        question.course = course
        question.lesson = lesson
        question.save()
        messages.success(request, "Votre question a été envoyée ! Un instructeur vous répondra bientôt.")
    return lesson_url


@login_required
def question_detail(request, question_id):
    """Page de discussion : Question + Réponses"""
    question = get_object_or_404(Question, id=question_id)

    is_author = request.user == question.student
    is_staff = request.user.is_staff
    is_course_instructor = _is_course_instructor(request.user, question.course)
    has_course_access = user_has_access(request.user, question.course)

    # ── Sécurité d'accès ──
    # Seuls l'auteur, le staff, l'instructeur du cours ou un élève inscrit au cours peuvent accéder
    if not (is_author or is_staff or is_course_instructor or has_course_access):
        messages.error(request, "Vous devez être inscrit à ce cours pour accéder à cette discussion.")
        return redirect('user_dashboard')

    allow_others = getattr(settings, 'ALLOW_STUDENT_REPLIES', True)
    can_reply = is_author or is_staff or is_course_instructor or (allow_others and has_course_access)

    # Gestion de la réponse
    if request.method == 'POST':
        if can_reply:
            form = ResponseForm(request.POST)
            if form.is_valid():
                response = form.save(commit=False)
                response.question = question
                response.author = request.user
                response.is_instructor = is_staff or is_course_instructor
                response.save()

                # Si c'est l'étudiant qui répond, on peut remettre en OPEN si c'était RESOLVED
                if is_author and question.status == 'RESOLVED':
                    question.status = 'OPEN'
                    question.save()

                messages.success(request, "Réponse publiée.")
                return redirect('question_detail', question_id=question.id)
        else:
            messages.error(request, "Les réponses sont désactivées pour les autres étudiants.")
            form = ResponseForm()

    else:
        form = ResponseForm()

    return render(
        request,
        'support/question_detail.html',
        {
            'question': question,
            'form': form,
            'can_reply': can_reply,
            'is_course_instructor': is_course_instructor,
        },
    )


@login_required
def my_questions(request):
    """Hub support étudiant : ses questions + celles des autres par cours inscrit."""
    enrolled_ids = Enrollment.objects.filter(student=request.user).values_list('course_id', flat=True)
    approved_ids = AccessRequest.objects.filter(student=request.user, status='APPROVED').values_list(
        'course_id', flat=True
    )
    activation_ids = ActivationCode.objects.filter(used_by=request.user, is_used=True).values_list(
        'course_id', flat=True
    )

    enrolled_courses = (
        Course.objects.filter(
            Q(id__in=enrolled_ids) | Q(id__in=approved_ids) | Q(id__in=activation_ids),
            is_published=True,
        )
        .distinct()
        .order_by('title')
    )

    # Une seule requête pour toutes les questions des cours suivis, regroupées en Python
    questions_by_course = defaultdict(list)
    for question in (
        Question.objects.filter(course__in=enrolled_courses)
        .select_related('student', 'lesson')
        .prefetch_related('responses')
        .order_by('-updated_at')
    ):
        questions_by_course[question.course_id].append(question)

    courses_data = []
    for course in enrolled_courses:
        all_questions = questions_by_course[course.id]
        my_questions = [q for q in all_questions if q.student_id == request.user.id]
        courses_data.append(
            {
                'course': course,
                'all_questions': all_questions,
                'my_questions': my_questions,
                'total': len(all_questions),
                'my_count': len(my_questions),
                'open_count': sum(1 for q in all_questions if q.status != 'RESOLVED'),
            }
        )

    # Questions hors cours inscrit (cours gratuits ou edge cases)
    my_other_qs = (
        Question.objects.filter(student=request.user)
        .exclude(course__in=enrolled_courses)
        .select_related('course', 'lesson')
        .prefetch_related('responses')
        .order_by('-updated_at')
    )

    return render(
        request,
        'support/my_questions.html',
        {
            'courses_data': courses_data,
            'my_other_questions': list(my_other_qs),
            'total_open': Question.objects.filter(student=request.user).exclude(status='RESOLVED').count(),
        },
    )


@login_required
@require_POST
def mark_resolved(request, question_id):
    question = get_object_or_404(Question, id=question_id)

    is_course_instructor = _is_course_instructor(request.user, question.course)

    if request.user == question.student or request.user.is_staff or is_course_instructor:
        if question.status != 'RESOLVED':
            question.status = 'RESOLVED'
            question.save()
            messages.success(request, "La discussion a été marquée comme résolue.")
    else:
        messages.error(request, "Vous n'avez pas la permission de fermer ce ticket.")

    return redirect('question_detail', question_id=question.id)


@login_required
def instructor_course_questions(request, course_slug):
    """Questions des étudiants pour un cours donné (instructeur ou staff)."""
    course = get_object_or_404(Course, slug=course_slug)

    if not _is_course_instructor(request.user, course):
        messages.error(request, "Accès refusé.")
        return redirect('instructor_dashboard')

    status_filter = request.GET.get('status', 'open')
    questions_qs = Question.objects.filter(course=course).select_related('student', 'lesson').order_by('-updated_at')

    if status_filter == 'resolved':
        questions = questions_qs.filter(status='RESOLVED')
    else:
        questions = questions_qs.exclude(status='RESOLVED')

    open_count = questions_qs.exclude(status='RESOLVED').count()
    resolved_count = questions_qs.filter(status='RESOLVED').count()

    return render(
        request,
        'support/instructor_course_questions.html',
        {
            'course': course,
            'questions': questions,
            'status_filter': status_filter,
            'open_count': open_count,
            'resolved_count': resolved_count,
        },
    )
