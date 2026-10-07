from functools import wraps

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q

from courses.models import Course, Module, Lesson
from courses.forms import InstructorCourseForm
from .models import InstructorPlan, InstructorRequest, InstructorProfile
from .forms import InstructorRequestForm
from .decorators import instructor_required


def signup_open_required(view_func):
    """Redirige vers l'accueil si l'inscription instructeur est fermée (sauf staff)."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not getattr(settings, 'INSTRUCTOR_SIGNUP_ENABLED', True) and not request.user.is_staff:
            return redirect('course_list')
        return view_func(request, *args, **kwargs)
    return _wrapped


@signup_open_required
def instructor_plans(request):
    """Page publique : les 3 offres pour devenir instructeur."""
    plans = InstructorPlan.objects.filter(is_active=True)

    # Vérifie si l'utilisateur a déjà un profil ou une demande en cours
    has_profile = False
    has_pending = False
    current_plan = None
    if request.user.is_authenticated:
        profile = InstructorProfile.objects.filter(
            user=request.user, is_active=True
        ).first()
        has_profile = profile is not None
        current_plan = profile.plan if profile else None
        has_pending = InstructorRequest.objects.filter(
            user=request.user, status='PENDING'
        ).exists()

    return render(request, 'instructors/plans.html', {
        'plans': plans,
        'has_profile': has_profile,
        'has_pending': has_pending,
        'current_plan': current_plan,
    })


@signup_open_required
@login_required
def instructor_request(request, plan_slug):
    """Formulaire de demande pour un plan spécifique (inscription ou upgrade)."""
    plan = get_object_or_404(InstructorPlan, slug=plan_slug, is_active=True)

    # Déjà instructeur actif sur ce même plan ou un plan supérieur ?
    current_profile = InstructorProfile.objects.filter(
        user=request.user, is_active=True
    ).first()
    if current_profile and current_profile.plan == plan:
        messages.info(request, "Vous êtes déjà sur cette offre.")
        return redirect('instructor_dashboard')

    # Demande déjà en cours ?
    if InstructorRequest.objects.filter(user=request.user, status='PENDING').exists():
        messages.info(request, "Vous avez déjà une demande en cours de validation.")
        return redirect('instructor_request_pending')

    is_upgrade = current_profile is not None

    if request.method == 'POST':
        form = InstructorRequestForm(request.POST, request.FILES)
        if form.is_valid():
            req = form.save(commit=False)
            req.user = request.user
            req.plan = plan
            req.save()
            return redirect('instructor_request_pending')
    else:
        form = InstructorRequestForm()

    return render(request, 'instructors/request_form.html', {
        'plan': plan,
        'form': form,
        'is_upgrade': is_upgrade,
        'current_plan': current_profile.plan if is_upgrade else None,
    })


@login_required
def instructor_request_pending(request):
    """Page d'attente après soumission de la demande."""
    pending = InstructorRequest.objects.filter(
        user=request.user, status='PENDING'
    ).first()
    return render(request, 'instructors/request_pending.html', {
        'request_obj': pending,
    })


@instructor_required
def instructor_dashboard(request):
    """Dashboard instructeur : ses formations + limites + compteurs."""
    profile = request.user.instructor_profile

    my_courses = (
        Course.objects.filter(instructor=request.user)
        .annotate(
            modules_count=Count('modules', distinct=True),
            lessons_count=Count('modules__lessons', distinct=True),
            students_count=Count(
                'accessrequest',
                filter=Q(accessrequest__status='APPROVED'),
                distinct=True,
            ) + Count('enrollments', distinct=True),
        )
        .order_by('-created_at')
    )

    # Totaux globaux
    total_modules = sum(c.modules_count for c in my_courses)
    total_lessons = sum(c.lessons_count for c in my_courses)
    total_students = sum(c.students_count for c in my_courses)

    return render(request, 'instructors/dashboard.html', {
        'profile': profile,
        'my_courses': my_courses,
        'total_modules': total_modules,
        'total_lessons': total_lessons,
        'total_students': total_students,
    })


@instructor_required
def instructor_course_create(request):
    """Créer une formation en tant qu'instructeur (avec vérification des limites)."""
    profile = request.user.instructor_profile

    if not profile.can_create_course:
        messages.error(request, "Vous avez atteint le nombre maximum de formations pour votre offre.")
        return redirect('instructor_dashboard')

    if request.method == 'POST':
        form = InstructorCourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = request.user
            course.save()
            messages.success(request, f'Formation « {course.title} » créée !')
            return redirect('instructor_dashboard')
    else:
        form = InstructorCourseForm()

    return render(request, 'instructors/course_form.html', {
        'form': form,
        'profile': profile,
        'is_edit': False,
    })


@instructor_required
def instructor_course_edit(request, course_slug):
    """Modifier une formation en tant qu'instructeur."""
    course = get_object_or_404(Course, slug=course_slug, instructor=request.user)

    if request.method == 'POST':
        form = InstructorCourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f'Formation « {course.title} » mise à jour.')
            return redirect('instructor_dashboard')
    else:
        form = InstructorCourseForm(instance=course)

    return render(request, 'instructors/course_form.html', {
        'form': form,
        'course': course,
        'profile': request.user.instructor_profile,
        'is_edit': True,
    })
