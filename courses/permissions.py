"""
Permissions pour le builder de cours.
Permet aux staff ET aux instructeurs (propriétaires) d'utiliser le builder.
"""
from functools import wraps
from django.shortcuts import get_object_or_404, redirect
from django.http import Http404
from .models import Course, ContentBlock, LandingSection, QuizQuestion, Module, Lesson


def _has_builder_access(user):
    """Vérifie si l'utilisateur a accès au builder (staff ou instructeur actif)."""
    if not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    try:
        return user.instructor_profile.is_active
    except Exception:
        return False


def builder_access_required(view_func):
    """Décorateur : autorise staff + instructeurs actifs."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not _has_builder_access(request.user):
            return redirect('account_login')
        return view_func(request, *args, **kwargs)
    return wrapper


def get_managed_course(user, course_slug):
    """
    Récupère un cours pour le builder.
    - Staff : n'importe quel cours
    - Instructeur : seulement ses propres cours
    """
    if user.is_staff:
        return get_object_or_404(Course, slug=course_slug)
    return get_object_or_404(Course, slug=course_slug, instructor=user)


def get_managed_course_from_block(user, block_id):
    """Récupère le cours via un ContentBlock, avec vérification d'accès."""
    block = get_object_or_404(ContentBlock, id=block_id)
    course = block.lesson.module.course
    _check_course_access(user, course)
    return block, course


def get_managed_course_from_lesson(user, lesson_id):
    """Récupère le cours via une Lesson (par ID), avec vérification d'accès."""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.module.course
    _check_course_access(user, course)
    return lesson, course


def get_managed_course_from_section(user, section_id):
    """Récupère le cours via une LandingSection, avec vérification d'accès."""
    section = get_object_or_404(LandingSection, id=section_id)
    course = section.course
    _check_course_access(user, course)
    return section, course


def get_managed_course_from_question(user, question_id):
    """Récupère le cours via une QuizQuestion, avec vérification d'accès."""
    question = get_object_or_404(QuizQuestion, id=question_id)
    course = question.block.lesson.module.course
    _check_course_access(user, course)
    return question, course


def _check_course_access(user, course):
    """Lève Http404 si l'utilisateur n'a pas accès au cours."""
    if user.is_staff:
        return
    if course.instructor != user:
        raise Http404
