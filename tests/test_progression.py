import pytest

from courses.models import StudentProgress


@pytest.mark.django_db
class TestProgression:

    def test_mark_lesson_complete_creates_record(self, student, course):
        """ Vérifie que finir une leçon crée une ligne dans la base """
        # On crée un module et une leçon (via les fixtures ou manuellement)
        module = course.modules.create(title="Module Test", order=1)
        lesson = module.lessons.create(title="Leçon 1", slug="lecon-1", order=1)

        # Au début, pas de progression
        assert StudentProgress.objects.filter(student=student, lesson=lesson).exists() is False

        # On simule la validation
        StudentProgress.objects.create(student=student, lesson=lesson)

        # Maintenant ça doit exister
        assert StudentProgress.objects.filter(student=student, lesson=lesson).exists() is True

    def test_progression_unique(self, student, course):
        """ Vérifie qu'on ne peut pas valider 2 fois la même leçon (pas de doublons) """
        module = course.modules.create(title="Module Test", order=1)
        lesson = module.lessons.create(title="Leçon 1", slug="lecon-1", order=1)

        # Première validation
        StudentProgress.objects.create(student=student, lesson=lesson)

        # Deuxième validation (via get_or_create comme dans la vue)
        obj, created = StudentProgress.objects.get_or_create(student=student, lesson=lesson)

        # Ça ne doit pas avoir créé une nouvelle ligne
        assert created is False
        assert StudentProgress.objects.filter(student=student, lesson=lesson).count() == 1
