"""
Calcul de la progression d'un étudiant dans un cours.

Source unique de vérité pour : % de progression, leçon à reprendre,
navigation précédente/suivante et état « cours terminé ».
Seules les leçons PUBLIÉES (dans des modules publiés) comptent.
"""

from dataclasses import dataclass, field

from .models import CourseActivity, Lesson, StudentProgress


def published_lessons(course, include_drafts=False):
    """Leçons du cours dans l'ordre pédagogique (module puis leçon)."""
    qs = Lesson.objects.filter(module__course=course)
    if not include_drafts:
        qs = qs.filter(is_published=True, module__is_published=True)
    return list(qs.select_related('module').order_by('module__order', 'module__id', 'order', 'id'))


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
        return sum(entry.duration_minutes or 0 for entry in self.lessons)

    def neighbours(self, lesson):
        """(précédente, suivante) d'une leçon dans le parcours publié."""
        ids = [entry.id for entry in self.lessons]
        if lesson.id not in ids:
            return None, None
        i = ids.index(lesson.id)
        prev_l = self.lessons[i - 1] if i > 0 else None
        next_l = self.lessons[i + 1] if i + 1 < len(self.lessons) else None
        return prev_l, next_l

    def position(self, lesson):
        """Numéro (1-based) de la leçon dans le parcours, ou None."""
        for i, entry in enumerate(self.lessons, start=1):
            if entry.id == lesson.id:
                return i
        return None

    def first_incomplete(self, after=None):
        """Première leçon non terminée (éventuellement après une leçon donnée)."""
        start = 0
        if after is not None:
            ids = [entry.id for entry in self.lessons]
            if after.id in ids:
                start = ids.index(after.id) + 1
        for entry in self.lessons[start:]:
            if entry.id not in self.completed_ids:
                return entry
        if after is not None:
            return self.first_incomplete()
        return None


def _build_progress(lessons, completed_ids, activity):
    """Assemble un CourseProgress à partir de données déjà chargées."""
    progress = CourseProgress(lessons=lessons, completed_ids=completed_ids)
    last = None
    if activity:
        progress.has_activity = True
        last = next((entry for entry in lessons if entry.id == activity.last_lesson_id), None)

    # Reprise : dernière leçon vue si non terminée, sinon la prochaine non terminée
    if last and last.id not in completed_ids:
        progress.resume_lesson = last
    else:
        progress.resume_lesson = progress.first_incomplete(after=last)
    return progress


def get_course_progress(user, course, lessons=None):
    """Construit la progression de `user` dans `course`."""
    if lessons is None:
        lessons = published_lessons(course)

    if not getattr(user, 'is_authenticated', False):
        progress = CourseProgress(lessons=lessons)
        progress.resume_lesson = lessons[0] if lessons else None
        return progress

    completed_ids = set(
        StudentProgress.objects.filter(student=user, lesson_id__in=[entry.id for entry in lessons]).values_list(
            'lesson_id', flat=True
        )
    )
    activity = CourseActivity.objects.filter(student=user, course=course).only('last_lesson_id').first()
    return _build_progress(lessons, completed_ids, activity)


def get_courses_progress(user, courses):
    """Progression de `user` pour plusieurs cours en 3 requêtes (évite le N+1 du tableau de bord)."""
    course_ids = [course.id for course in courses]
    lessons_by_course = {cid: [] for cid in course_ids}
    lessons = (
        Lesson.objects.filter(module__course_id__in=course_ids, is_published=True, module__is_published=True)
        .select_related('module')
        .order_by('module__order', 'module__id', 'order', 'id')
    )
    for lesson in lessons:
        lessons_by_course[lesson.module.course_id].append(lesson)

    completed = set(
        StudentProgress.objects.filter(student=user, lesson__module__course_id__in=course_ids).values_list(
            'lesson_id', flat=True
        )
    )
    activities = {
        activity.course_id: activity
        for activity in CourseActivity.objects.filter(student=user, course_id__in=course_ids).only(
            'course_id', 'last_lesson_id'
        )
    }

    result = {}
    for cid, course_lessons in lessons_by_course.items():
        done = {entry.id for entry in course_lessons} & completed
        result[cid] = _build_progress(course_lessons, done, activities.get(cid))
    return result


def record_visit(user, course, lesson):
    """Mémorise la dernière leçon consultée (pour le bouton « Continuer »)."""
    if not getattr(user, 'is_authenticated', False):
        return
    CourseActivity.objects.update_or_create(student=user, course=course, defaults={'last_lesson': lesson})
