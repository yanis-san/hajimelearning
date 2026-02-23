import pytest
from users.models import User
from courses.models import Course, Module, Lesson
from access.models import AccessRequest
from config.celery import app as celery_app


# --- CELERY : exécution synchrone en tests (pas de broker requis) ---

@pytest.fixture(autouse=True)
def celery_eager():
    """Force Celery à exécuter les tâches en local sans broker."""
    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
    )


# --- UTILISATEURS ---

@pytest.fixture
def student():
    """ Un étudiant lambda """
    return User.objects.create_user(
        email='etudiant@test.com', 
        password='password123',
        first_name='Yanis',
        last_name='Test'
    )

@pytest.fixture
def admin_user():
    """ Un super admin """
    return User.objects.create_superuser(
        email='admin@test.com', 
        password='password123'
    )

# --- CONTENU ---

@pytest.fixture
def course():
    """ Un cours payant standard """
    return Course.objects.create(
        title="Formation Python",
        slug="formation-python",
        # AJOUTE CES CHAMPS :
        short_description="Apprenez Python rapidement",
        description="# Titre\nContenu markdown",
        price=5000,
        is_published=True
    )

@pytest.fixture
def free_course():
    """ Un cours gratuit """
    return Course.objects.create(
        title="Intro Gratuite",
        slug="intro-gratuite",
        # AJOUTE CES CHAMPS :
        short_description="Introduction gratuite",
        description="# Titre\nContenu markdown",
        price=0,
        is_published=True
    )