"""Gestion des formations : liste, création, édition, suppression, suivi des étudiants."""

from collections import defaultdict

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.db.models import Count, Prefetch, Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from access.models import AccessRequest

from ..forms import CourseForm, InstructorCourseForm
from ..models import ContentBlock, Course, Lesson, Module, QuizResult, StudentProgress
from ..permissions import builder_access_required, get_managed_course

User = get_user_model()

COURSE_SORTS = frozenset(
    {
        'title',
        '-title',
        'price',
        '-price',
        'created_at',
        '-created_at',
        'is_published',
        '-is_published',
        'modules_count',
        '-modules_count',
    }
)

SAVE_INDICATOR_TEMPLATE = 'courses/manage/partials/save_indicator.html'


@staff_member_required
def manage_course_list(request):
    """Liste de tous les cours pour l'admin, avec tri et recherche."""
    sort = request.GET.get('sort', '-created_at')
    if sort not in COURSE_SORTS:
        sort = '-created_at'
    query = request.GET.get('q', '').strip()

    courses = Course.objects.annotate(modules_count=Count('modules'))
    if query:
        courses = courses.filter(title__icontains=query)

    context = {'courses': courses.order_by(sort), 'current_sort': sort, 'search_query': query}
    # HTMX partial : ne renvoyer que le tbody
    if request.headers.get('HX-Request'):
        return render(request, 'courses/manage/partials/course_table_body.html', context)
    return render(request, 'courses/manage/course_list.html', context)


@staff_member_required
def manage_course_create(request):
    """Créer un nouveau cours."""
    form = CourseForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        course = form.save()
        messages.success(request, f'Cours « {course.title} » créé avec succès.')
        return redirect('manage_course_modules', course_slug=course.slug)
    return render(request, 'courses/manage/course_form.html', {'form': form, 'is_edit': False})


@builder_access_required
def manage_course_edit(request, course_slug):
    """Éditer un cours existant."""
    course = get_managed_course(request.user, course_slug)
    form_class = CourseForm if request.user.is_superuser else InstructorCourseForm
    is_htmx = bool(request.headers.get('HX-Request'))

    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=course)
        if form.is_valid():
            course = form.save()
            if is_htmx:
                return render(request, SAVE_INDICATOR_TEMPLATE, {'ok': True})
            messages.success(request, f'Cours « {course.title} » mis à jour.')
            return redirect('manage_course_list' if request.user.is_staff else 'instructor_dashboard')
        if is_htmx:
            return render(request, SAVE_INDICATOR_TEMPLATE, {'ok': False}, status=400)
    else:
        form = form_class(instance=course)

    return render(request, 'courses/manage/course_form.html', {'form': form, 'course': course, 'is_edit': True})


@builder_access_required
@require_POST
def manage_course_delete(request, course_slug):
    """Supprimer un cours (HTMX inline : la ligne est retirée via hx-swap="outerHTML")."""
    get_managed_course(request.user, course_slug).delete()
    return HttpResponse('')


@builder_access_required
def manage_course_students(request, course_slug):
    """Suivi des étudiants d'un cours : progression et résultats de quiz."""
    course = get_managed_course(request.user, course_slug)

    students = User.objects.filter(
        Q(accessrequest__course=course, accessrequest__status=AccessRequest.Status.APPROVED)
        | Q(activationcode__course=course, activationcode__is_used=True)
        | Q(enrollments__course=course)
    ).distinct()

    total_lessons = Lesson.objects.filter(module__course=course).count()
    quiz_blocks = list(ContentBlock.objects.filter(lesson__module__course=course, type='quiz').select_related('lesson'))
    quizzes_by_lesson = defaultdict(list)
    for block in quiz_blocks:
        quizzes_by_lesson[block.lesson_id].append(block)

    # Structure du cours pour le template : modules → leçons → quiz
    modules = (
        Module.objects.filter(course=course)
        .prefetch_related(Prefetch('lessons', queryset=Lesson.objects.order_by('order')))
        .order_by('order')
    )
    modules_structure = [
        {
            'module': module,
            'lessons': [
                {'lesson': lesson, 'quiz_blocks': quizzes_by_lesson[lesson.id]} for lesson in module.lessons.all()
            ],
        }
        for module in modules
    ]

    # Pré-chargement en bloc (pas de N+1)
    completed_by_student = defaultdict(set)
    last_active_by_student = {}
    for student_id, lesson_id, completed_at in StudentProgress.objects.filter(
        lesson__module__course=course
    ).values_list('student_id', 'lesson_id', 'completed_at'):
        completed_by_student[student_id].add(lesson_id)
        last_active_by_student[student_id] = max(completed_at, last_active_by_student.get(student_id, completed_at))

    quiz_results_by_student = defaultdict(dict)
    for student_id, block_id, score, total in QuizResult.objects.filter(block__in=quiz_blocks).values_list(
        'student_id', 'block_id', 'score', 'total_questions'
    ):
        quiz_results_by_student[student_id][block_id] = {
            'score': score,
            'total': total,
            'percent': int(score * 100 / total) if total else 0,
        }

    student_stats = []
    for student in students:
        completed_ids = completed_by_student.get(student.id, set())
        student_stats.append(
            {
                'user': student,
                'percent': int(len(completed_ids) * 100 / total_lessons) if total_lessons else 0,
                'completed': len(completed_ids),
                'completed_ids': completed_ids,
                'last_active': last_active_by_student.get(student.id, student.last_login),
                'quiz_results': quiz_results_by_student.get(student.id, {}),
            }
        )
    student_stats.sort(key=lambda stat: stat['percent'], reverse=True)

    return render(
        request,
        'courses/manage/students_stats.html',
        {
            'course': course,
            'student_stats': student_stats,
            'total_lessons': total_lessons,
            'modules_structure': modules_structure,
        },
    )
