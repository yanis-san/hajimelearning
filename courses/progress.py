"""
Calcul de la progression d'un étudiant dans un cours.

Source unique de vérité pour : % de progression, leçon à reprendre,
navigation précédente/suivante et état « cours terminé ».
Seules les leçons PUBLIÉES (dans des modules publiés) comptent.
"""
from dataclasses import dataclass, field

from django.db.models import Prefetch

from .models import ContentBlock, CourseActivity, Lesson, StudentProgress


def published_lessons(course, include_drafts=False):
    """Leçons du cours dans l'ordre pédagogique (module puis leçon)."""
    qs = Lesson.objects.filter(module__course=course)
    if not include_drafts:
        qs = qs.filter(is_published=True, module__is_published=True)
    return list(qs.select_related('module').order_by('module__order', 'module__id', 'order', 'id'))


def lessons_prefetch(include_drafts=False):
    """Prefetch des leçons d'un module + types de blocs (icônes du sommaire)."""
    qs = Lesson.objects.all()
    if not include_drafts:
        qs = qs.filter(is_published=True)
    qs = qs.prefetch_related(
        Prefetch('blocks', queryset=ContentBlock.objects.only('id', 'lesson_id', 'type', 'order'))
    )
    return Prefetch('lessons', queryset=qs)


@dataclass
class CourseProgress:
    lessons: list = field(default_factory=list)
    completed_ids: set = field(default_factory=set)
    resume_lesson: object = None
    has_activity: bool = False

    @property
    def total(self):
        return len(self.lessons)

    @property
    def done(self):
        return len(self.completed_ids)

    @property
    def remaining(self):
        return max(self.total - self.done, 0)

    @property
    def percent(self):
        if not self.total:
            return 0
        return min(100, int(self.done * 100 / self.total))

    @property
    def is_complete(self):
        return self.total > 0 and self.done >= self.total

    @property
    def is_started(self):
        return self.done > 0 or self.has_activity

    @property
    def total_minutes(self):
        return sum(l.duration_minutes or 0 for l in self.lessons)

    def neighbours(self, lesson):
        """(précédente, suivante) d'une leçon dans le parcours publié."""
        ids = [l.id for l in self.lessons]
        if lesson.id not in ids:
            return None, None
        i = ids.index(lesson.id)
        prev_l = self.lessons[i - 1] if i > 0 else None
        next_l = self.lessons[i + 1] if i + 1 < len(self.lessons) else None
        return prev_l, next_l

    def position(self, lesson):
        """Numéro (1-based) de la leçon dans le parcours, ou None."""
        for i, l in enumerate(self.lessons, start=1):
            if l.id == lesson.id:
                return i
        return None

    def first_incomplete(self, after=None):
        """Première leçon non terminée (éventuellement après une leçon donnée)."""
        start = 0
        if after is not None:
            ids = [l.id for l in self.lessons]
            if after.id in ids:
                start = ids.index(after.id) + 1
        for l in self.lessons[start:]:
            if l.id not in self.completed_ids:
                return l
        if after is not None:
            return self.first_incomplete()
        return None


def get_course_progress(user, course, lessons=None):
    """Construit la progression de `user` dans `course`."""
    if lessons is None:
        lessons = published_lessons(course)
    progress = CourseProgress(lessons=lessons)

    if not getattr(user, 'is_authenticated', False):
        progress.resume_lesson = lessons[0] if lessons else None
        return progress

    lesson_ids = {l.id for l in lessons}
    done = StudentProgress.objects.filter(
        student=user, lesson_id__in=lesson_ids
    ).values_list('lesson_id', flat=True)
    progress.completed_ids = set(done)

    activity = CourseActivity.objects.filter(student=user, course=course).only('last_lesson_id').first()
    last = None
    if activity:
        progress.has_activity = True
        last = next((l for l in lessons if l.id == activity.last_lesson_id), None)

    # Reprise : dernière leçon vue si non terminée, sinon la prochaine non terminée
    if last and last.id not in progress.completed_ids:
        progress.resume_lesson = last
    else:
        progress.resume_lesson = progress.first_incomplete(after=last)

    return progress


def record_visit(user, course, lesson):
    """Mémorise la dernière leçon consultée (pour le bouton « Continuer »)."""
    if not getattr(user, 'is_authenticated', False):
        return
    CourseActivity.objects.update_or_create(
        student=user, course=course, defaults={'last_lesson': lesson}
    )
