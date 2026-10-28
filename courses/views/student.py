"""Vues publiques et espace étudiant : catalogue, leçons, progression, certificat."""

import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Prefetch, Q
from django.http import FileResponse, Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from access.models import AccessRequest, ActivationCode, Enrollment, user_has_access
from support.forms import QuestionForm

from ..models import (
    Category,
    ContentBlock,
    Course,
    CourseCompletion,
    Lesson,
    QuizAttempt,
    QuizResult,
    StudentNote,
    StudentProgress,
)
from ..progress import get_course_progress, get_courses_progress, record_visit
from ..tasks import generate_certificate_pdf
from ._helpers import is_course_manager, modules_queryset

logger = logging.getLogger(__name__)

CATALOGUE_SORTS = frozenset({'title', '-title', 'price', '-price', 'created_at', '-created_at'})


def course_list(request):
    courses = (
        Course.objects.filter(is_published=True, is_featured=True).select_related('category').order_by('-created_at')
    )
    return render(request, 'courses/index.html', {'courses': courses, 'categories': Category.objects.all()})


def catalogue(request):
    """Page publique /catalogue/ avec tri, recherche et filtre catégorie."""
    sort = request.GET.get('sort', '-created_at')
    if sort not in CATALOGUE_SORTS:
        sort = '-created_at'

    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()

    courses = Course.objects.filter(is_published=True).select_related('category')
    if query:
        courses = courses.filter(Q(title__icontains=query) | Q(short_description__icontains=query))
    if category_slug:
        courses = courses.filter(category__slug=category_slug)
    courses = courses.annotate(modules_count=Count('modules', filter=Q(modules__is_published=True))).order_by(sort)

    context = {
        'courses': courses,
        'current_sort': sort,
        'search_query': query,
        'current_category': category_slug,
    }
    # HTMX partial : ne renvoyer que la grille
    if request.headers.get('HX-Request'):
        return render(request, 'courses/partials/catalogue_grid.html', context)

    context['categories'] = Category.objects.all()
    return render(request, 'courses/catalogue.html', context)


def course_detail(request, course_slug):
    course = get_object_or_404(Course.objects.select_related('instructor'), slug=course_slug)
    is_manager = is_course_manager(request.user, course)

    # Un seul chargement du cours avec les bonnes précharges selon le rôle
    course_with_modules = Course.objects.prefetch_related(
        Prefetch('modules', queryset=modules_queryset(is_manager)),
        'landing_sections',
    ).get(pk=course.pk)

    user_progress = None
    completed_lesson_ids = []
    progress_percent = 0
    if request.user.is_authenticated:
        user_progress = get_course_progress(request.user, course)
        completed_lesson_ids = user_progress.completed_ids
        progress_percent = user_progress.percent

    return render(
        request,
        'courses/course_detail.html',
        {
            'course': course_with_modules,
            'has_access': user_has_access(request.user, course),
            'completed_lesson_ids': completed_lesson_ids,
            'progress_percent': progress_percent,
            'user_progress': user_progress,
            'landing_sections': [s for s in course_with_modules.landing_sections.all() if s.is_visible],
            # Staff/instructeur : aperçu de la vitrine avec ?view=landing
            'preview_landing': request.GET.get('view') == 'landing' and is_manager,
            'is_manager': is_manager,
        },
    )


def lesson_detail(request, course_slug, lesson_slug):
    lesson = get_object_or_404(
        Lesson.objects.select_related('module__course'),
        module__course__slug=course_slug,
        slug=lesson_slug,
    )
    course = lesson.module.course
    is_manager = is_course_manager(request.user, course)
    has_access = user_has_access(request.user, course)

    # Bloquer l'accès aux leçons/modules en brouillon pour les étudiants
    if not is_manager and (not lesson.is_published or not lesson.module.is_published):
        messages.error(request, "Cette leçon n'est pas encore disponible.")
        return redirect('course_detail', course_slug=course.slug)

    # Le manager a toujours accès à son propre cours
    if not is_manager and not lesson.is_free and not has_access:
        messages.error(request, "Vous devez acheter ce cours pour voir cette leçon.")
        return redirect('course_detail', course_slug=course.slug)

    course_for_sidebar = Course.objects.prefetch_related(
        Prefetch('modules', queryset=modules_queryset(is_manager))
    ).get(pk=course.pk)

    completed_lesson_ids = []
    prev_lesson = next_lesson = None
    blocks = list(lesson.blocks.all())
    if request.user.is_authenticated:
        progress = get_course_progress(request.user, course)
        completed_lesson_ids = progress.completed_ids
        prev_lesson, next_lesson = progress.neighbours(lesson)
        record_visit(request.user, course, lesson)

        # Notes personnelles par bloc
        notes = dict(
            StudentNote.objects.filter(student=request.user, block__in=blocks).values_list('block_id', 'content')
        )
        for block in blocks:
            block.my_note = notes.get(block.id, "")

    return render(
        request,
        'courses/lesson_detail.html',
        {
            'lesson': lesson,
            'course': course_for_sidebar,
            'completed_lesson_ids': completed_lesson_ids,
            'prev_lesson': prev_lesson,
            'next_lesson': next_lesson,
            'question_form': QuestionForm(),
            'has_access': has_access,
            'is_manager': is_manager,
            'blocks': blocks,
        },
    )


@login_required
def user_dashboard(request):
    user = request.user
    my_courses = list(
        Course.objects.filter(
            Q(id__in=Enrollment.objects.filter(student=user).values('course_id'))
            | Q(id__in=AccessRequest.objects.filter(student=user, status='APPROVED').values('course_id'))
            | Q(id__in=ActivationCode.objects.filter(used_by=user, is_used=True).values('course_id'))
            | Q(instructor=user),
            is_published=True,
        )
        .select_related('category')
        .order_by('-created_at')
    )

    progress_by_course = get_courses_progress(user, my_courses)
    for course in my_courses:
        course.user_progress = progress_by_course[course.id]

    # Cours complétés → bouton certificat
    completed_course_ids = set(CourseCompletion.objects.filter(student=user).values_list('course_id', flat=True))
    return render(
        request,
        'courses/dashboard.html',
        {
            'courses': my_courses,
            'completed_course_ids': completed_course_ids,
        },
    )


def _lesson_for_progress(request, course_slug, lesson_slug):
    """(leçon, cours) ; cours vaut None si l'utilisateur ne peut pas modifier sa progression."""
    lesson = get_object_or_404(
        Lesson.objects.select_related('module__course'),
        module__course__slug=course_slug,
        slug=lesson_slug,
    )
    course = lesson.module.course
    if not is_course_manager(request.user, course) and not user_has_access(request.user, course):
        return lesson, None
    return lesson, course


@login_required
@require_POST
def mark_lesson_complete(request, course_slug, lesson_slug):
    current_lesson, course = _lesson_for_progress(request, course_slug, lesson_slug)
    if course is None:
        messages.error(request, "Vous n'avez pas accès à ce cours.")
        return redirect('course_detail', course_slug=course_slug)

    StudentProgress.objects.get_or_create(student=request.user, lesson=current_lesson)

    progress = get_course_progress(request.user, course)
    if progress.is_complete:
        completion, created = CourseCompletion.objects.get_or_create(student=request.user, course=course)
        if created:
            generate_certificate_pdf.delay(completion.id)

    _, next_lesson = progress.neighbours(current_lesson)
    if next_lesson:
        return redirect('lesson_detail', course_slug=course_slug, lesson_slug=next_lesson.slug)

    messages.success(request, "Félicitations ! Vous avez terminé ce cours.")
    return redirect('course_detail', course_slug=course_slug)


@login_required
@require_POST
def unmark_lesson_complete(request, course_slug, lesson_slug):
    current_lesson, course = _lesson_for_progress(request, course_slug, lesson_slug)
    if course is None:
        messages.error(request, "Vous n'avez pas accès à ce cours.")
        return redirect('course_detail', course_slug=course_slug)

    StudentProgress.objects.filter(student=request.user, lesson=current_lesson).delete()

    if not get_course_progress(request.user, course).is_complete:
        CourseCompletion.objects.filter(student=request.user, course=course).delete()

    return redirect('lesson_detail', course_slug=course_slug, lesson_slug=lesson_slug)


@login_required
@require_POST
def save_block_note(request, course_slug, block_id):
    """Enregistre (ou supprime si vide) la note personnelle d'un étudiant sur un bloc."""
    block = get_object_or_404(
        ContentBlock.objects.select_related('lesson__module__course'),
        pk=block_id,
        lesson__module__course__slug=course_slug,
    )
    lesson = block.lesson
    course = lesson.module.course

    if not (is_course_manager(request.user, course) or lesson.is_free or user_has_access(request.user, course)):
        return JsonResponse({'ok': False, 'error': 'forbidden'}, status=403)

    content = request.POST.get('note_content', '').strip()
    if content:
        StudentNote.objects.update_or_create(student=request.user, block=block, defaults={'content': content})
    else:
        StudentNote.objects.filter(student=request.user, block=block).delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'content': content})
    return redirect('lesson_detail', course_slug=course_slug, lesson_slug=lesson.slug)


@login_required
def download_certificate(request, course_slug):
    """Télécharge le certificat PDF de complétion d'un cours."""
    course = get_object_or_404(Course, slug=course_slug, is_published=True)
    completion = get_object_or_404(CourseCompletion, student=request.user, course=course)

    if not completion.certificate_pdf:
        messages.warning(
            request,
            "Votre certificat est en cours de génération, revenez dans quelques instants.",
        )
        return redirect('user_dashboard')

    try:
        pdf = completion.certificate_pdf.open('rb')
    except FileNotFoundError:
        # Fichier absent du stockage protégé (ex. ancien certificat) : on le régénère
        generate_certificate_pdf.delay(completion.id)
        messages.warning(request, "Votre certificat est en cours de régénération, revenez dans quelques instants.")
        return redirect('user_dashboard')

    return FileResponse(
        pdf, as_attachment=True, filename=f"Certificat_{course.slug}.pdf", content_type='application/pdf'
    )


@login_required
@require_POST
def save_quiz_result(request, block_id):
    try:
        data = json.loads(request.body)
        score, total = int(data['score']), int(data['total'])
    except (ValueError, KeyError, TypeError):
        return JsonResponse({'status': 'error', 'message': 'Données invalides.'}, status=400)
    if total <= 0 or not 0 <= score <= total:
        return JsonResponse({'status': 'error', 'message': 'Score invalide.'}, status=400)

    block = get_object_or_404(ContentBlock.objects.select_related('lesson__module__course'), id=block_id)
    course = block.lesson.module.course
    if not is_course_manager(request.user, course) and not user_has_access(request.user, course):
        return JsonResponse({'status': 'error', 'message': 'Accès refusé.'}, status=403)

    QuizResult.objects.update_or_create(
        student=request.user,
        block=block,
        defaults={'score': score, 'total_questions': total},
    )
    QuizAttempt.objects.create(student=request.user, block=block, score=score, total_questions=total)
    return JsonResponse({'status': 'success'})


@login_required
def download_protected_media(request, block_id, field_name):
    """Sert les fichiers protégés (file_content ou related_file) après contrôle d'accès."""
    block = get_object_or_404(ContentBlock.objects.select_related('lesson__module__course'), id=block_id)
    course = block.lesson.module.course

    has_access = is_course_manager(request.user, course) or user_has_access(request.user, course)
    if not has_access and not block.lesson.is_free:
        return HttpResponseForbidden("Accès refusé. Vous devez être inscrit au cours.")

    if field_name not in ('file_content', 'related_file'):
        raise Http404("Champ inconnu.")
    file_field = getattr(block, field_name)
    if not file_field or not file_field.name:
        raise Http404("Fichier introuvable.")

    try:
        return FileResponse(file_field.open('rb'), as_attachment=True, filename=file_field.name.split('/')[-1])
    except FileNotFoundError as exc:
        raise Http404("Le fichier physique n'existe plus.") from exc
