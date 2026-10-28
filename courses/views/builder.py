"""Builder de leçons : blocs de contenu, questions de quiz, modules et leçons."""

import json

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from ..forms import ContentBlockForm, LessonForm, ModuleForm, QuizQuestionForm
from ..markdown import render_markdown_safe
from ..models import ContentBlock, Course, Lesson, Module
from ..permissions import (
    builder_access_required,
    get_managed_course,
    get_managed_course_from_block,
    get_managed_course_from_lesson,
    get_managed_course_from_question,
)
from ._helpers import apply_order, is_autosave, limit_reached_response, next_order, plan_limit_reached

BLOCK_LIST_TEMPLATE = 'courses/manage/partials/block_list.html'


# ── Aperçu Markdown ─────────────────────────────────


@builder_access_required
@require_POST
def preview_markdown(request):
    """Renvoie le HTML rendu d'un texte Markdown (endpoint HTMX)."""
    text = request.POST.get('text', '')
    if not text.strip():
        return render(request, 'courses/manage/partials/markdown_preview.html', {'empty': True})
    return render(request, 'courses/manage/partials/markdown_preview.html', {'html': render_markdown_safe(text)})


# ── Blocs de contenu ────────────────────────────────


def _save_block_response(request, lesson, block, created):
    """
    Réponse commune à la création / l'édition d'un bloc.

    Auto-enregistrement : la liste est rafraîchie et l'évènement `builder-saved` (en-tête HX-Trigger)
    informe l'éditeur. Enregistrement explicite : la liste est rafraîchie et le formulaire fermé.
    """
    if not is_autosave(request):
        return render(request, 'courses/manage/partials/block_saved.html', {'lesson': lesson})

    detail = {'savedAt': timezone.localtime().strftime('%H:%M:%S'), 'blockId': block.id}
    if created:
        detail['editUrl'] = reverse('edit_block', args=[block.id])
    response = render(request, BLOCK_LIST_TEMPLATE, {'lesson': lesson})
    response['HX-Trigger'] = json.dumps({'builder-saved': detail})
    return response


@builder_access_required
def add_block(request, lesson_id, block_type):
    lesson, _course = get_managed_course_from_lesson(request.user, lesson_id)

    if request.method == 'POST':
        form = ContentBlockForm(request.POST, request.FILES)
        if form.is_valid():
            block = form.save(commit=False)
            block.lesson = lesson
            block.type = block_type
            block.order = next_order(lesson.blocks)
            block.save()
            return _save_block_response(request, lesson, block, created=True)
        if is_autosave(request):
            return HttpResponse(status=422)
    else:
        form = ContentBlockForm()

    return render(
        request,
        'courses/manage/partials/block_form.html',
        {
            'form': form,
            'lesson': lesson,
            'block_type': block_type,
        },
    )


@builder_access_required
def edit_block(request, block_id):
    block, _course = get_managed_course_from_block(request.user, block_id)

    if request.method == 'POST':
        form = ContentBlockForm(request.POST, request.FILES, instance=block)
        if form.is_valid():
            form.save()
            return _save_block_response(request, block.lesson, block, created=False)
        if is_autosave(request):
            return HttpResponse(status=422)
    else:
        form = ContentBlockForm(instance=block)

    return render(
        request,
        'courses/manage/partials/block_form.html',
        {
            'form': form,
            'block': block,
            'block_type': block.type,
        },
    )


@builder_access_required
@require_POST
def delete_block(request, block_id):
    block, _course = get_managed_course_from_block(request.user, block_id)
    lesson = block.lesson
    block.delete()
    return render(request, BLOCK_LIST_TEMPLATE, {'lesson': lesson})


@builder_access_required
def order_block(request, block_id, direction):
    """Déplace un bloc d'un cran (alternative au glisser-déposer)."""
    block, _course = get_managed_course_from_block(request.user, block_id)
    lesson = block.lesson

    if direction == 'up':
        neighbour = lesson.blocks.filter(order__lt=block.order).order_by('-order').first()
    elif direction == 'down':
        neighbour = lesson.blocks.filter(order__gt=block.order).order_by('order').first()
    else:
        neighbour = None

    if neighbour:
        block.order, neighbour.order = neighbour.order, block.order
        ContentBlock.objects.bulk_update([block, neighbour], ['order'])
    return render(request, BLOCK_LIST_TEMPLATE, {'lesson': lesson})


@builder_access_required
@require_POST
def update_block_order(request):
    """Réordonne les blocs (SortableJS) — limité aux blocs que l'utilisateur gère."""
    blocks = ContentBlock.objects.all()
    if not request.user.is_staff:
        blocks = blocks.filter(lesson__module__course__instructor=request.user)
    apply_order(blocks, request.POST.getlist('block_order'))
    return render(request, 'courses/manage/partials/order_saved.html', {'saved_at': timezone.localtime()})


# ── Questions de quiz ───────────────────────────────


@builder_access_required
def add_quiz_question(request, block_id):
    block, _course = get_managed_course_from_block(request.user, block_id)
    if request.method == 'POST':
        form = QuizQuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.block = block
            question.save()
            return render(request, 'courses/manage/partials/quiz_question_list.html', {'block': block})
    else:
        form = QuizQuestionForm()
    return render(request, 'courses/manage/partials/quiz_question_form.html', {'form': form, 'block': block})


@builder_access_required
def delete_quiz_question(request, question_id):
    question, _course = get_managed_course_from_question(request.user, question_id)
    block = question.block
    question.delete()
    return render(request, 'courses/manage/partials/quiz_question_list.html', {'block': block})


# ── Page du builder ─────────────────────────────────


@builder_access_required
def manage_lesson_content(request, course_slug, lesson_slug):
    course = get_managed_course(request.user, course_slug)
    lesson = get_object_or_404(Lesson, module__course=course, slug=lesson_slug)
    return render(request, 'courses/manage/builder.html', {'lesson': lesson})


# ── Modules ─────────────────────────────────────────


def _course_with_modules(course):
    return Course.objects.prefetch_related('modules__lessons').get(pk=course.pk)


@builder_access_required
def manage_course_modules(request, course_slug):
    """Gérer les modules d'un cours."""
    course = get_managed_course(request.user, course_slug)
    form = ModuleForm(request.POST or None)

    if request.method == 'POST' and plan_limit_reached(request.user, course, 'modules'):
        return limit_reached_response(request, reverse('manage_course_modules', args=[course.slug]))

    if request.method == 'POST' and form.is_valid():
        module = form.save(commit=False)
        module.course = course
        module.order = next_order(course.modules)
        module.save()
        if request.headers.get('HX-Request'):
            return render(request, 'courses/manage/partials/module_list.html', {'course': _course_with_modules(course)})
        return redirect('manage_course_modules', course_slug=course.slug)

    return render(
        request,
        'courses/manage/modules.html',
        {
            'course': _course_with_modules(course),
            'form': form,
        },
    )


@builder_access_required
@require_POST
def manage_module_edit(request, course_slug, module_id):
    """Renommer un module (HTMX inline)."""
    course = get_managed_course(request.user, course_slug)
    module = get_object_or_404(Module, id=module_id, course=course)
    title = request.POST.get('title', '').strip()
    if title:
        module.title = title
    module.is_published = 'is_published' in request.POST
    module.save()
    return render(request, 'courses/manage/partials/module_list.html', {'course': course})


@builder_access_required
@require_POST
def manage_module_delete(request, course_slug, module_id):
    """Supprimer un module (HTMX)."""
    course = get_managed_course(request.user, course_slug)
    get_object_or_404(Module, id=module_id, course=course).delete()
    return render(request, 'courses/manage/partials/module_list.html', {'course': course})


@builder_access_required
@require_POST
def manage_module_reorder(request, course_slug):
    """Réordonner les modules (HTMX + SortableJS)."""
    course = get_managed_course(request.user, course_slug)
    apply_order(Module.objects.filter(course=course), request.POST.getlist('module_order'))
    return HttpResponse(status=204)


# ── Leçons ──────────────────────────────────────────


def _unique_lesson_slug(course, wanted, exclude_id=None):
    """Slug de leçon unique dans le cours (les URLs publiques sont /cours/leçon)."""
    base = slugify(wanted)[:45] or 'lecon'
    existing = Lesson.objects.filter(module__course=course)
    if exclude_id:
        existing = existing.exclude(id=exclude_id)
    taken = set(existing.filter(slug__startswith=base).values_list('slug', flat=True))
    slug, suffix = base, 2
    while slug in taken:
        slug = f'{base}-{suffix}'
        suffix += 1
    return slug


def _module_with_lessons(module_id, course):
    return get_object_or_404(Module.objects.prefetch_related('lessons'), id=module_id, course=course)


@builder_access_required
def manage_module_lessons(request, course_slug, module_id):
    """Gérer les leçons d'un module."""
    course = get_managed_course(request.user, course_slug)
    module = _module_with_lessons(module_id, course)
    form = LessonForm(request.POST or None)

    if request.method == 'POST' and plan_limit_reached(request.user, course, 'lessons'):
        return limit_reached_response(request, reverse('manage_module_lessons', args=[course.slug, module.id]))

    if request.method == 'POST' and form.is_valid():
        lesson = form.save(commit=False)
        lesson.module = module
        lesson.slug = _unique_lesson_slug(course, lesson.slug or lesson.title)
        lesson.order = next_order(module.lessons)
        lesson.save()
        if request.headers.get('HX-Request'):
            return render(
                request,
                'courses/manage/partials/lesson_list.html',
                {
                    'module': _module_with_lessons(module_id, course),
                    'course': course,
                },
            )
        return redirect('manage_module_lessons', course_slug=course.slug, module_id=module.id)

    return render(request, 'courses/manage/lessons.html', {'course': course, 'module': module, 'form': form})


@builder_access_required
@require_POST
def manage_lesson_edit(request, course_slug, module_id, lesson_id):
    """Éditer titre/slug/is_free d'une leçon (HTMX inline)."""
    course = get_managed_course(request.user, course_slug)
    module = get_object_or_404(Module, id=module_id, course=course)
    lesson = get_object_or_404(Lesson, id=lesson_id, module=module)

    title = request.POST.get('title', '').strip()
    if title:
        lesson.title = title
    slug = request.POST.get('slug', '').strip()
    if slug and slug != lesson.slug:
        lesson.slug = _unique_lesson_slug(course, slug, exclude_id=lesson.id)
    lesson.is_free = 'is_free' in request.POST
    lesson.is_published = 'is_published' in request.POST
    lesson.save()

    return render(request, 'courses/manage/partials/lesson_list.html', {'module': module, 'course': course})


@builder_access_required
@require_POST
def manage_lesson_delete(request, course_slug, module_id, lesson_id):
    """Supprimer une leçon (HTMX)."""
    course = get_managed_course(request.user, course_slug)
    module = get_object_or_404(Module, id=module_id, course=course)
    get_object_or_404(Lesson, id=lesson_id, module=module).delete()
    return render(request, 'courses/manage/partials/lesson_list.html', {'module': module, 'course': course})


@builder_access_required
@require_POST
def manage_lesson_reorder(request, course_slug, module_id):
    """Réordonner les leçons (HTMX + SortableJS)."""
    course = get_managed_course(request.user, course_slug)
    module = get_object_or_404(Module, id=module_id, course=course)
    apply_order(Lesson.objects.filter(module=module), request.POST.getlist('lesson_order'))
    return HttpResponse(status=204)
