from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.db.models import Count, Q, F, Prefetch
from django.contrib.auth import get_user_model
from django.utils.safestring import mark_safe
from .models import Category
from django.urls import reverse
from markdownx.utils import markdownify

import json
import logging

logger = logging.getLogger(__name__)

from .models import Course, Lesson, StudentProgress, ContentBlock, QuizQuestion, QuizResult, Module, LandingSection, CourseCompletion
from .forms import ContentBlockForm, QuizQuestionForm, CourseForm, InstructorCourseForm, ModuleForm, LessonForm, LandingSectionForm
from .permissions import (
    builder_access_required, get_managed_course, get_managed_course_from_block,
    get_managed_course_from_lesson, get_managed_course_from_section,
    get_managed_course_from_question,
)
from access.models import AccessRequest, ActivationCode, Enrollment, user_has_access
from support.forms import QuestionForm

User = get_user_model()


def _is_course_manager(user, course):
    """L'utilisateur est-il staff ou propriétaire de la formation ?"""
    if not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    return course.instructor_id == user.id


# --- VUES PUBLIQUES (ACCESSIBLES AUX ÉTUDIANTS) ---

def course_list(request):
    courses    = Course.objects.filter(is_published=True, is_featured=True).select_related('category').order_by('-created_at')
    categories = Category.objects.all()
    return render(request, 'courses/index.html', {'courses': courses, 'categories': categories})


def catalogue(request):
    """Page publique /catalogue/ avec tri, recherche et filtre catégorie."""
    ALLOWED_SORTS = {
        'title', '-title',
        'price', '-price',
        'created_at', '-created_at',
    }

    sort         = request.GET.get('sort', '-created_at')
    if sort not in ALLOWED_SORTS:
        sort = '-created_at'

    query        = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()

    categories = Category.objects.all()
    courses    = Course.objects.filter(is_published=True).select_related('category')

    if query:
        courses = courses.filter(Q(title__icontains=query) | Q(short_description__icontains=query))

    if category_slug:
        courses = courses.filter(category__slug=category_slug)

    courses = courses.annotate(
        modules_count=Count('modules', filter=Q(modules__is_published=True))
    ).order_by(sort)

    # HTMX partial : ne renvoyer que la grille
    if request.headers.get('HX-Request'):
        return render(request, 'courses/partials/catalogue_grid.html', {
            'courses': courses,
            'current_sort': sort,
            'search_query': query,
            'current_category': category_slug,
        })

    return render(request, 'courses/catalogue.html', {
        'courses': courses,
        'current_sort': sort,
        'search_query': query,
        'categories': categories,
        'current_category': category_slug,
    })

def course_detail(request, course_slug):
    # Requête légère pour les vérifications de permissions (pas de prefetch inutile)
    course = get_object_or_404(Course.objects.select_related('instructor'), slug=course_slug)
    is_manager = _is_course_manager(request.user, course)
    has_access = user_has_access(request.user, course)

    # Requête complète avec les bonnes précharges selon le rôle
    if is_manager:
        modules_qs = Module.objects.prefetch_related('lessons')
    else:
        modules_qs = Module.objects.filter(is_published=True).prefetch_related(
            Prefetch('lessons', queryset=Lesson.objects.filter(is_published=True))
        )
    course_with_modules = Course.objects.prefetch_related(
        Prefetch('modules', queryset=modules_qs),
        'landing_sections',
    ).get(pk=course.pk)

    completed_lesson_ids = []
    progress_percent = 0
    if request.user.is_authenticated:
        completed_lesson_ids = StudentProgress.objects.filter(
            student=request.user,
            lesson__module__course=course
        ).values_list('lesson_id', flat=True)
        # Compter seulement les leçons publiées pour la progression
        total_lessons = Lesson.objects.filter(
            module__course=course, is_published=True,
            module__is_published=True,
        ).count()
        if total_lessons > 0:
            progress_percent = int((len(completed_lesson_ids) / total_lessons) * 100)

    landing_sections = course_with_modules.landing_sections.filter(is_visible=True)

    # Staff/instructor can force landing preview with ?view=landing
    preview_landing = (
        request.GET.get('view') == 'landing'
        and is_manager
    )

    return render(request, 'courses/course_detail.html', {
        'course': course_with_modules,
        'has_access': has_access,
        'completed_lesson_ids': completed_lesson_ids,
        'progress_percent': progress_percent,
        'landing_sections': landing_sections,
        'preview_landing': preview_landing,
        'is_manager': is_manager,
    })

def lesson_detail(request, course_slug, lesson_slug):
    lesson = get_object_or_404(Lesson, module__course__slug=course_slug, slug=lesson_slug)
    course = lesson.module.course
    is_manager = _is_course_manager(request.user, course)

    # Bloquer l'accès aux leçons/modules en brouillon pour les étudiants
    if not is_manager:
        if not lesson.is_published or not lesson.module.is_published:
            messages.error(request, "Cette leçon n'est pas encore disponible.")
            return redirect('course_detail', course_slug=course.slug)

    # SÉCURITÉ ACCÈS (le manager a toujours accès à son propre cours)
    if not is_manager and not lesson.is_free and not user_has_access(request.user, course):
        messages.error(request, "Vous devez acheter ce cours pour voir cette leçon.")
        return redirect('course_detail', course_slug=course.slug)

    # Précharger le sidebar avec filtre brouillon
    if is_manager:
        modules_qs = Module.objects.prefetch_related('lessons')
    else:
        modules_qs = Module.objects.filter(is_published=True).prefetch_related(
            Prefetch('lessons', queryset=Lesson.objects.filter(is_published=True))
        )
    course_for_sidebar = Course.objects.prefetch_related(
        Prefetch('modules', queryset=modules_qs)
    ).get(pk=course.pk)

    completed_lesson_ids = []
    if request.user.is_authenticated:
        completed_lesson_ids = StudentProgress.objects.filter(
            student=request.user,
            lesson__module__course=course
        ).values_list('lesson_id', flat=True)
    
    question_form = QuestionForm()
    has_access = user_has_access(request.user, course)
    
    return render(request, 'courses/lesson_detail.html', {
        'lesson': lesson,
        'course': course_for_sidebar,
        'completed_lesson_ids': completed_lesson_ids,
        'question_form': question_form,
        'has_access': has_access,
        'is_manager': is_manager,
    })

@login_required
def user_dashboard(request):
    enrolled_ids = Enrollment.objects.filter(
        student=request.user
    ).values_list('course_id', flat=True)

    approved_ids = AccessRequest.objects.filter(
        student=request.user, status='APPROVED'
    ).values_list('course_id', flat=True)

    activation_ids = ActivationCode.objects.filter(
        used_by=request.user, is_used=True
    ).values_list('course_id', flat=True)

    my_courses = Course.objects.filter(
        Q(id__in=enrolled_ids) | Q(id__in=approved_ids) | Q(id__in=activation_ids),
        is_published=True,
    ).distinct().order_by('-created_at')

    # Cours complétés → pour afficher le bouton certificat
    completed_course_ids = set(
        CourseCompletion.objects.filter(student=request.user)
        .values_list('course_id', flat=True)
    )

    return render(request, 'courses/dashboard.html', {
        'courses': my_courses,
        'completed_course_ids': completed_course_ids,
    })

@login_required
@require_POST
def mark_lesson_complete(request, course_slug, lesson_slug):
    current_lesson = get_object_or_404(Lesson, module__course__slug=course_slug, slug=lesson_slug)
    course = current_lesson.module.course

    # Sécurité : vérifier que l'étudiant a bien accès au cours
    if not _is_course_manager(request.user, course) and not user_has_access(request.user, course):
        messages.error(request, "Vous n'avez pas accès à ce cours.")
        return redirect('course_detail', course_slug=course_slug)

    StudentProgress.objects.get_or_create(student=request.user, lesson=current_lesson)

    # ── Vérification complétion totale du cours ──────────────────────────────
    total_published = Lesson.objects.filter(
        module__course=course, module__is_published=True, is_published=True
    ).count()
    completed_count = StudentProgress.objects.filter(
        student=request.user,
        lesson__module__course=course,
        lesson__is_published=True,
        lesson__module__is_published=True,
    ).count()

    if total_published > 0 and completed_count >= total_published:
        completion, created = CourseCompletion.objects.get_or_create(
            student=request.user, course=course
        )
        if created:
            from .tasks import generate_certificate_pdf
            generate_certificate_pdf.delay(completion.id)

    course_lessons = Lesson.objects.filter(
        module__course=current_lesson.module.course
    ).order_by('module__order', 'order')
    
    lesson_list = list(course_lessons)
    try:
        current_index = lesson_list.index(current_lesson)
        if current_index + 1 < len(lesson_list):
            next_lesson = lesson_list[current_index + 1]
            return redirect('lesson_detail', course_slug=course_slug, lesson_slug=next_lesson.slug)
    except ValueError:
        pass

    messages.success(request, "Félicitations ! Vous avez terminé ce cours.")
    return redirect('course_detail', course_slug=course_slug)


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

    response = HttpResponse(completion.certificate_pdf.read(), content_type='application/pdf')
    filename = f"Certificat_{course.slug}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
@require_POST
def save_quiz_result(request, block_id):
    try:
        data = json.loads(request.body)
        score = data.get('score')
        total = data.get('total')
        block = get_object_or_404(ContentBlock, id=block_id)
        
        QuizResult.objects.update_or_create(
            student=request.user,
            block=block,
            defaults={
                'score': score,
                'total_questions': total
            }
        )
        return JsonResponse({'status': 'success'})
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Données invalides.'}, status=400)
    except Exception:
        logger.exception("Erreur inattendue dans save_quiz_result (block_id=%s)", block_id)
        return JsonResponse({'status': 'error', 'message': 'Une erreur est survenue.'}, status=500)


# --- VUES BUILDER (SÉCURISÉES : STAFF ONLY) ---

@builder_access_required
def manage_lesson_content(request, course_slug, lesson_slug):
    course = get_managed_course(request.user, course_slug)
    lesson = get_object_or_404(Lesson, module__course=course, slug=lesson_slug)
    return render(request, 'courses/manage/builder.html', {'lesson': lesson})


@builder_access_required
@require_POST
def preview_markdown(request):
    """Renvoie le HTML rendu d'un texte Markdown (endpoint HTMX)."""
    text = request.POST.get('text', '')
    if not text.strip():
        return HttpResponse(
            '<p class="text-gray-400 italic text-sm">L\'aperçu apparaîtra ici…</p>'
        )
    html = mark_safe(markdownify(text))
    return HttpResponse(
        f'<div class="prose prose-sm max-w-none prose-headings:text-gray-800 '
        f'prose-p:text-gray-600 prose-a:text-orange-600 prose-strong:text-gray-800 '
        f'prose-table:text-sm">{html}</div>'
    )

@builder_access_required
def add_block(request, lesson_id, block_type):
    lesson, course = get_managed_course_from_lesson(request.user, lesson_id)
    
    if request.method == 'POST':
        form = ContentBlockForm(request.POST, request.FILES)
        if form.is_valid():
            block = form.save(commit=False)
            block.lesson = lesson
            block.type = block_type
            last_block = lesson.blocks.last()
            block.order = last_block.order + 1 if last_block else 1
            block.save()
            block_list_html = render_to_string(
                'courses/manage/partials/block_list.html',
                {'lesson': lesson}, request=request,
            )
            clear_form = '<div id="block-form-container" hx-swap-oob="innerHTML" class="mb-8"></div>'
            return HttpResponse(block_list_html + clear_form)
    else:
        form = ContentBlockForm()

    return render(request, 'courses/manage/partials/block_form.html', {
        'form': form, 
        'lesson': lesson, 
        'block_type': block_type
    })

@builder_access_required
def edit_block(request, block_id):
    block, course = get_managed_course_from_block(request.user, block_id)
    
    if request.method == 'POST':
        form = ContentBlockForm(request.POST, request.FILES, instance=block)
        if form.is_valid():
            form.save()
            block_list_html = render_to_string(
                'courses/manage/partials/block_list.html',
                {'lesson': block.lesson}, request=request,
            )
            clear_form = '<div id="block-form-container" hx-swap-oob="innerHTML" class="mb-8"></div>'
            return HttpResponse(block_list_html + clear_form)
    else:
        form = ContentBlockForm(instance=block)

    return render(request, 'courses/manage/partials/block_form.html', {
        'form': form, 
        'block': block, 
        'block_type': block.type
    })

@builder_access_required
@require_POST
def delete_block(request, block_id):
    block, course = get_managed_course_from_block(request.user, block_id)
    lesson = block.lesson
    block.delete()
    return render(request, 'courses/manage/partials/block_list.html', {'lesson': lesson})

@builder_access_required
def order_block(request, block_id, direction):
    # Cette vue est obsolète si tu utilises le Drag & Drop (update_block_order), mais on la garde au cas où
    block, course = get_managed_course_from_block(request.user, block_id)
    lesson = block.lesson
    if direction == 'up':
        prev_block = lesson.blocks.filter(order__lt=block.order).order_by('-order').first()
        if prev_block:
            block.order, prev_block.order = prev_block.order, block.order
            block.save()
            prev_block.save()
    elif direction == 'down':
        next_block = lesson.blocks.filter(order__gt=block.order).order_by('order').first()
        if next_block:
            block.order, next_block.order = next_block.order, block.order
            block.save()
            next_block.save()
    return render(request, 'courses/manage/partials/block_list.html', {'lesson': lesson})

@builder_access_required
@require_POST
def update_block_order(request):
    block_ids = request.POST.getlist('block_order')
    for index, block_id in enumerate(block_ids):
        ContentBlock.objects.filter(id=block_id).update(order=index + 1)
    return HttpResponse("Ordre mis à jour")

@builder_access_required
def add_quiz_question(request, block_id):
    block, course = get_managed_course_from_block(request.user, block_id)
    if request.method == 'POST':
        form = QuizQuestionForm(request.POST)
        if form.is_valid():
            q = form.save(commit=False)
            q.block = block
            q.save()
            return render(request, 'courses/manage/partials/quiz_question_list.html', {'block': block})
    else:
        form = QuizQuestionForm()
    return render(request, 'courses/manage/partials/quiz_question_form.html', {
        'form': form, 'block': block
    })

@builder_access_required
def delete_quiz_question(request, question_id):
    question, course = get_managed_course_from_question(request.user, question_id)
    block = question.block
    question.delete()
    return render(request, 'courses/manage/partials/quiz_question_list.html', {'block': block})


@builder_access_required
def manage_course_students(request, course_slug):
    course = get_managed_course(request.user, course_slug)

    students = User.objects.filter(
        Q(accessrequest__course=course, accessrequest__status='APPROVED') |
        Q(activationcode__course=course, activationcode__is_used=True) |
        Q(enrollments__course=course)
    ).distinct()

    # Structure du cours : modules + leçons (publiés ou tous pour le manager)
    modules = Module.objects.filter(course=course).prefetch_related(
        Prefetch('lessons', queryset=Lesson.objects.order_by('order'))
    ).order_by('order')

    all_lessons = Lesson.objects.filter(module__course=course)
    total_lessons = all_lessons.count()

    # Quiz blocks : tous les blocs de type quiz de ce cours
    quiz_blocks = ContentBlock.objects.filter(
        lesson__module__course=course, type='quiz'
    ).select_related('lesson')

    # Structure annotée pour le template : modules → leçons → quiz_blocks
    quiz_blocks_list = list(quiz_blocks)
    modules_structure = []
    for module in modules:
        lessons_data = []
        for lesson in module.lessons.all():
            lesson_quizzes = [b for b in quiz_blocks_list if b.lesson_id == lesson.id]
            lessons_data.append({'lesson': lesson, 'quiz_blocks': lesson_quizzes})
        modules_structure.append({'module': module, 'lessons': lessons_data})

    student_stats = []

    for student in students:
        # Leçons complétées
        completed_ids = set(
            StudentProgress.objects.filter(
                student=student, lesson__module__course=course
            ).values_list('lesson_id', flat=True)
        )

        last_progress = StudentProgress.objects.filter(
            student=student, lesson__module__course=course
        ).order_by('-completed_at').first()
        last_active = last_progress.completed_at if last_progress else student.last_login

        percent = int((len(completed_ids) / total_lessons) * 100) if total_lessons > 0 else 0

        # Résultats quiz : {block_id: {'score': x, 'total': y, 'percent': z}}
        quiz_results = {}
        for qr in QuizResult.objects.filter(student=student, block__in=quiz_blocks):
            pct = int((qr.score / qr.total_questions) * 100) if qr.total_questions else 0
            quiz_results[qr.block_id] = {
                'score': qr.score,
                'total': qr.total_questions,
                'percent': pct,
            }

        student_stats.append({
            'user': student,
            'percent': percent,
            'completed': len(completed_ids),
            'completed_ids': completed_ids,
            'last_active': last_active,
            'quiz_results': quiz_results,
        })

    student_stats.sort(key=lambda x: x['percent'], reverse=True)

    return render(request, 'courses/manage/students_stats.html', {
        'course': course,
        'student_stats': student_stats,
        'total_lessons': total_lessons,
        'modules_structure': modules_structure,
    })


# ── VUES ADMIN CRUD (STAFF ONLY) ────────────────────

@staff_member_required
def manage_course_list(request):
    """Liste de tous les cours pour l'admin, avec tri et recherche."""
    ALLOWED_SORTS = {
        'title', '-title',
        'price', '-price',
        'created_at', '-created_at',
        'is_published', '-is_published',
        'modules_count', '-modules_count',
    }

    sort = request.GET.get('sort', '-created_at')
    if sort not in ALLOWED_SORTS:
        sort = '-created_at'

    query = request.GET.get('q', '').strip()

    courses = Course.objects.annotate(modules_count=Count('modules'))

    if query:
        courses = courses.filter(Q(title__icontains=query))

    courses = courses.order_by(sort)

    # HTMX partial : ne renvoyer que le tbody
    if request.headers.get('HX-Request'):
        return render(request, 'courses/manage/partials/course_table_body.html', {
            'courses': courses,
            'current_sort': sort,
            'search_query': query,
        })

    return render(request, 'courses/manage/course_list.html', {
        'courses': courses,
        'current_sort': sort,
        'search_query': query,
    })


@staff_member_required
def manage_course_create(request):
    """Créer un nouveau cours."""
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save()
            messages.success(request, f'Cours « {course.title} » créé avec succès.')
            return redirect('manage_course_modules', course_slug=course.slug)
    else:
        form = CourseForm()
    return render(request, 'courses/manage/course_form.html', {
        'form': form,
        'is_edit': False,
    })


@builder_access_required
def manage_course_edit(request, course_slug):
    """Éditer un cours existant."""
    course = get_managed_course(request.user, course_slug)
    FormClass = CourseForm if request.user.is_superuser else InstructorCourseForm
    if request.method == 'POST':
        form = FormClass(request.POST, request.FILES, instance=course)
        if form.is_valid():
            course = form.save()
            messages.success(request, f'Cours « {course.title} » mis à jour.')
            if request.user.is_staff:
                return redirect('manage_course_list')
            return redirect('instructor_dashboard')
    else:
        form = FormClass(instance=course)
    return render(request, 'courses/manage/course_form.html', {
        'form': form,
        'course': course,
        'is_edit': True,
    })


@builder_access_required
@require_POST
def manage_course_delete(request, course_slug):
    """Supprimer un cours (HTMX inline)."""
    course = get_managed_course(request.user, course_slug)
    course.delete()
    return HttpResponse('')  # Row removed via hx-swap="outerHTML"


@builder_access_required
def manage_course_modules(request, course_slug):
    """Gérer les modules d'un cours."""
    course = get_managed_course(request.user, course_slug)
    course = Course.objects.prefetch_related('modules__lessons').get(pk=course.pk)
    form = ModuleForm()

    if request.method == 'POST':
        form = ModuleForm(request.POST)
        if form.is_valid():
            module = form.save(commit=False)
            module.course = course
            last = course.modules.last()
            module.order = last.order + 1 if last else 1
            module.save()
            # Re-fetch pour inclure le nouveau module dans le prefetch
            course = Course.objects.prefetch_related('modules__lessons').get(pk=course.pk)
            # HTMX: return just the module list partial
            if request.headers.get('HX-Request'):
                return render(request, 'courses/manage/partials/module_list.html', {'course': course})
            return redirect('manage_course_modules', course_slug=course.slug)

    return render(request, 'courses/manage/modules.html', {
        'course': course,
        'form': form,
    })


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
    module = get_object_or_404(Module, id=module_id, course=course)
    module.delete()
    return render(request, 'courses/manage/partials/module_list.html', {'course': course})


@builder_access_required
@require_POST
def manage_module_reorder(request, course_slug):
    """Réordonner les modules (HTMX + SortableJS)."""
    module_ids = request.POST.getlist('module_order')
    for index, mid in enumerate(module_ids):
        Module.objects.filter(id=mid).update(order=index + 1)
    return HttpResponse('OK')


@builder_access_required
def manage_module_lessons(request, course_slug, module_id):
    """Gérer les leçons d'un module."""
    course = get_managed_course(request.user, course_slug)
    module = get_object_or_404(Module.objects.prefetch_related('lessons'), id=module_id, course=course)
    form = LessonForm()

    if request.method == 'POST':
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.module = module
            last = module.lessons.last()
            lesson.order = last.order + 1 if last else 1
            lesson.save()
            # Re-fetch pour inclure la nouvelle leçon dans le prefetch
            module = get_object_or_404(Module.objects.prefetch_related('lessons'), id=module_id, course=course)
            if request.headers.get('HX-Request'):
                return render(request, 'courses/manage/partials/lesson_list.html', {
                    'module': module, 'course': course,
                })
            return redirect('manage_module_lessons', course_slug=course.slug, module_id=module.id)

    return render(request, 'courses/manage/lessons.html', {
        'course': course,
        'module': module,
        'form': form,
    })


@builder_access_required
@require_POST
def manage_lesson_edit(request, course_slug, module_id, lesson_id):
    """Éditer titre/slug/is_free d'une leçon (HTMX inline)."""
    course = get_managed_course(request.user, course_slug)
    module = get_object_or_404(Module, id=module_id, course=course)
    lesson = get_object_or_404(Lesson, id=lesson_id, module=module)

    lesson.title = request.POST.get('title', lesson.title).strip()
    slug = request.POST.get('slug', '').strip()
    if slug:
        lesson.slug = slug
    lesson.is_free = 'is_free' in request.POST
    lesson.is_published = 'is_published' in request.POST
    lesson.save()

    return render(request, 'courses/manage/partials/lesson_list.html', {
        'module': module, 'course': course,
    })


@builder_access_required
@require_POST
def manage_lesson_delete(request, course_slug, module_id, lesson_id):
    """Supprimer une leçon (HTMX)."""
    course = get_managed_course(request.user, course_slug)
    module = get_object_or_404(Module, id=module_id, course=course)
    lesson = get_object_or_404(Lesson, id=lesson_id, module=module)
    lesson.delete()
    return render(request, 'courses/manage/partials/lesson_list.html', {
        'module': module, 'course': course,
    })


@builder_access_required
@require_POST
def manage_lesson_reorder(request, course_slug, module_id):
    """Réordonner les leçons (HTMX + SortableJS)."""
    lesson_ids = request.POST.getlist('lesson_order')
    for index, lid in enumerate(lesson_ids):
        Lesson.objects.filter(id=lid).update(order=index + 1)
    return HttpResponse('OK')


# ── LANDING PAGE BUILDER ──────────────────────────────

@builder_access_required
def manage_course_landing(request, course_slug):
    """Page builder pour les sections vitrine d'un cours."""
    course = get_managed_course(request.user, course_slug)
    course = Course.objects.prefetch_related('landing_sections').get(pk=course.pk)
    if request.user.is_staff:
        courses_url = reverse('manage_course_list')
        course_edit_url = reverse('manage_course_edit', args=[course.slug])
    else:
        courses_url = reverse('instructor_dashboard')
        course_edit_url = reverse('instructor_course_edit', args=[course.slug])
    return render(request, 'courses/manage/landing_builder.html', {
        'course': course,
        'courses_url': courses_url,
        'course_edit_url': course_edit_url,
    })


@builder_access_required
def add_landing_section(request, course_slug, section_type):
    """Ajouter une section (GET → formulaire, POST → sauvegarde)."""
    course = get_managed_course(request.user, course_slug)

    if request.method == 'POST':
        form = LandingSectionForm(request.POST, request.FILES)
        if form.is_valid():
            section = form.save(commit=False)
            section.course = course
            section.section_type = section_type
            last = course.landing_sections.last()
            section.order = last.order + 1 if last else 1
            section.save()
            # HTMX : renvoyer la liste + vider le formulaire
            section_list_html = render_to_string(
                'courses/manage/partials/landing_section_list.html',
                {'course': course}, request=request,
            )
            clear_form = '<div id="section-form-container" hx-swap-oob="innerHTML" class="mb-8"></div>'
            return HttpResponse(section_list_html + clear_form)
    else:
        form = LandingSectionForm()

    return render(request, 'courses/manage/partials/landing_section_form.html', {
        'form': form,
        'course': course,
        'section_type': section_type,
    })


@builder_access_required
def edit_landing_section(request, section_id):
    """Éditer une section existante."""
    section, course = get_managed_course_from_section(request.user, section_id)
    course = section.course

    if request.method == 'POST':
        form = LandingSectionForm(request.POST, request.FILES, instance=section)
        if form.is_valid():
            form.save()
            section_list_html = render_to_string(
                'courses/manage/partials/landing_section_list.html',
                {'course': course}, request=request,
            )
            clear_form = '<div id="section-form-container" hx-swap-oob="innerHTML" class="mb-8"></div>'
            return HttpResponse(section_list_html + clear_form)
    else:
        form = LandingSectionForm(instance=section)

    return render(request, 'courses/manage/partials/landing_section_form.html', {
        'form': form,
        'course': course,
        'section': section,
        'section_type': section.section_type,
    })


@builder_access_required
@require_POST
def delete_landing_section(request, section_id):
    """Supprimer une section."""
    section, course = get_managed_course_from_section(request.user, section_id)
    course = section.course
    section.delete()
    return render(request, 'courses/manage/partials/landing_section_list.html', {
        'course': course,
    })


@builder_access_required
@require_POST
def reorder_landing_sections(request, course_slug):
    """Réordonner les sections (HTMX + SortableJS)."""
    section_ids = request.POST.getlist('section_order')
    for index, sid in enumerate(section_ids):
        LandingSection.objects.filter(id=sid).update(order=index + 1)
    return HttpResponse('OK')


@builder_access_required
@require_POST
def duplicate_landing_section(request, section_id):
    """Dupliquer une section existante."""
    original, course = get_managed_course_from_section(request.user, section_id)
    course = original.course
    # Clone
    clone = LandingSection(
        course=course,
        section_type=original.section_type,
        title=original.title,
        body=original.body,
        video_id=original.video_id,
        subtitle=original.subtitle,
        cta_text=original.cta_text,
        cta_url=original.cta_url,
        image_position=original.image_position,
        css_class=original.css_class,
        background=original.background,
        is_visible=original.is_visible,
    )
    # Image : point to same file (not deep copy)
    if original.image:
        clone.image = original.image
    # Place right after original
    clone.order = original.order + 1
    clone.save()
    # Shift subsequent sections
    LandingSection.objects.filter(
        course=course, order__gte=clone.order
    ).exclude(id=clone.id).update(order=F('order') + 1)

    return render(request, 'courses/manage/partials/landing_section_list.html', {
        'course': course,
    })


@builder_access_required
@require_POST
def toggle_landing_section_visibility(request, section_id):
    """Basculer la visibilité d'une section (brouillon / visible)."""
    section, course = get_managed_course_from_section(request.user, section_id)
    section.is_visible = not section.is_visible
    section.save(update_fields=['is_visible'])
    return render(request, 'courses/manage/partials/landing_section_list.html', {
        'course': section.course,
    })


@builder_access_required
@require_POST
def prefill_landing_template(request, course_slug):
    """Pré-remplir la vitrine avec un template de 6 sections type."""
    course = get_managed_course(request.user, course_slug)

    # Ne rien faire si des sections existent déjà
    if course.landing_sections.exists():
        return render(request, 'courses/manage/partials/landing_section_list.html', {
            'course': course,
        })

    template_sections = [
        {
            'section_type': 'hero',
            'title': course.title,
            'subtitle': course.short_description,
            'cta_text': "S'inscrire maintenant",
            'cta_url': '#inscription',
            'background': 'dark',
        },
        {
            'section_type': 'text',
            'title': 'À propos de cette formation',
            'body': course.description or 'Décrivez votre formation ici...',
            'background': 'none',
        },
        {
            'section_type': 'features',
            'title': 'Ce que vous allez apprendre',
            'body': course.what_you_will_learn or '- Point fort 1\n- Point fort 2\n- Point fort 3',
            'background': 'green',
        },
        {
            'section_type': 'text_image',
            'title': 'Une méthode progressive',
            'body': 'Décrivez votre approche pédagogique et ce qui rend cette formation unique.',
            'image_position': 'right',
            'background': 'gray',
        },
        {
            'section_type': 'testimonials',
            'title': 'Ce que disent nos étudiants',
            'body': '### ★★★★★ | Marie D.\nExcellente formation, très bien structurée !\n\n### ★★★★☆ | Ahmed K.\nJ\'ai beaucoup appris, je recommande.',
            'background': 'none',
        },
        {
            'section_type': 'faq',
            'title': 'Questions fréquentes',
            'body': '### Comment s\'inscrire ?\nCliquez sur le bouton d\'inscription en haut de page.\n\n### Combien de temps ai-je accès ?\nVous avez un accès illimité une fois inscrit.',
            'background': 'gray',
        },
    ]

    for i, data in enumerate(template_sections, start=1):
        LandingSection.objects.create(course=course, order=i, **data)

    return render(request, 'courses/manage/partials/landing_section_list.html', {
        'course': course,
    })
