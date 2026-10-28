"""
Outil de non-régression VISUELLE (pas un test de la suite : le fichier ne s'appelle pas test_*.py).

    SNAP_DIR=/tmp/avant pytest tests/snapshots.py -p no:cacheprovider      # capture
    SNAP_DIR=/tmp/apres SNAP_COMPARE=/tmp/avant pytest tests/snapshots.py  # capture + comparaison

Chaque page principale est photographiée (bureau et mobile) puis, si SNAP_COMPARE est défini,
comparée pixel à pixel ; les images de différence sont écrites dans SNAP_DIR/diff.
"""

import os
from pathlib import Path

import pytest
from django.urls import reverse

os.environ.setdefault('DJANGO_ALLOW_ASYNC_UNSAFE', 'true')
pytest.importorskip('playwright')
from playwright.sync_api import sync_playwright  # noqa: E402

from tests.test_e2e import login_as  # noqa: E402

pytestmark = [pytest.mark.django_db(transaction=True)]

FREEZE_CSS = """
*, *::before, *::after { animation: none !important; transition: none !important; caret-color: transparent !important; }
video { visibility: hidden !important; }
"""


@pytest.fixture
def world(db):
    """Jeu de données couvrant tous les types de blocs, de sections et d'écrans."""
    from django.core.files.base import ContentFile

    from access.models import AccessRequest, Coupon, Enrollment
    from contact.models import ContactReason
    from courses.models import Category, ContentBlock, Course, CourseCompletion, StudentProgress
    from instructors.models import InstructorPlan, InstructorProfile, InstructorRequest
    from notifications.models import Notification
    from support.models import Question, Response
    from users.models import User

    admin = User.objects.create_superuser(email='admin@snap.test', password='x', first_name='Ada', last_name='Admin')
    student = User.objects.create_user(email='eleve@snap.test', password='x', first_name='Yanis', last_name='Eleve')
    plan = InstructorPlan.objects.create(
        name='Starter',
        slug='starter',
        price=5000,
        max_courses=3,
        max_modules_per_course=5,
        max_lessons_per_course=10,
        revenue_percent=70,
        is_active=True,
        is_featured=True,
    )
    teacher = User.objects.create_user(email='prof@snap.test', password='x', first_name='Prof', last_name='Sensei')
    InstructorProfile.objects.create(
        user=teacher, plan=plan, max_courses=3, max_modules_per_course=5, max_lessons_per_course=10, revenue_percent=70
    )
    InstructorRequest.objects.create(user=student, plan=plan, payment_proof='x.png')
    category = Category.objects.create(name='Langues', slug='langues')
    course = Course.objects.create(
        title='Japonais N5',
        slug='japonais-n5',
        short_description='Les bases du japonais',
        price=5000,
        description='# Japonais\n\nUn **cours** complet.\n\n- Kana\n- Kanji',
        what_you_will_learn='- Lire\n- Écrire',
        is_published=True,
        is_featured=True,
        instructor=teacher,
        category=category,
        trailer_video_id='dQw4w9WgXcQ',
        meta_description='Cours de japonais',
    )
    free = Course.objects.create(
        title='Intro gratuite',
        slug='intro',
        short_description='Gratuit',
        price=0,
        description='x',
        is_published=True,
        is_featured=True,
        category=category,
    )
    module = course.modules.create(title='Les kana', order=1)
    lesson = module.lessons.create(title='Hiragana', slug='hiragana', order=1, is_free=True, duration_minutes=15)
    lesson2 = module.lessons.create(title='Katakana', slug='katakana', order=2, duration_minutes=20)
    module.lessons.create(title='Brouillon', slug='brouillon', order=3, is_published=False)
    ContentBlock.objects.create(
        lesson=lesson,
        type='text',
        title='Intro',
        order=1,
        text_content='# Bonjour\n\n{日本語|にほんご} est **génial**.\n\n| a | b |\n|---|---|\n| 1 | 2 |',
    )
    ContentBlock.objects.create(lesson=lesson, type='video', title='Vidéo', video_id='dQw4w9WgXcQ', order=2)
    audio = ContentBlock.objects.create(lesson=lesson, type='audio', title='Audio', order=3)
    audio.file_content.save('a.mp3', ContentFile(b'ID3'))
    doc = ContentBlock.objects.create(lesson=lesson, type='file', title='Fiche PDF', order=4)
    doc.file_content.save('f.pdf', ContentFile(b'%PDF'))
    anki = ContentBlock.objects.create(lesson=lesson, type='anki', title='Deck', card_count=120, order=5)
    anki.file_content.save('d.apkg', ContentFile(b'PK'))
    quiz = ContentBlock.objects.create(lesson=lesson, type='quiz', quiz_title='Quiz kana', order=6)
    quiz.questions.create(question_text='あ se lit ?', choice_a='a', choice_b='i', choice_c='u', correct_answer='a')
    for position, (kind, title) in enumerate(
        [
            ('hero', 'Japonais N5'),
            ('text', 'À propos'),
            ('features', 'Points forts'),
            ('text_image', 'Méthode'),
            ('video', 'Démo'),
            ('faq', 'FAQ'),
            ('testimonials', 'Avis'),
            ('image', 'Galerie'),
        ],
        start=1,
    ):
        course.landing_sections.create(
            section_type=kind,
            title=title,
            order=position,
            subtitle='Sous-titre',
            cta_text='S\'inscrire',
            cta_url='#',
            video_id='dQw4w9WgXcQ',
            body='### Q1\nR1\n\n### ★★★★★ | Marie\nSuper' if kind in {'faq', 'testimonials'} else '- a\n- b',
        )
    AccessRequest.objects.create(student=student, course=course, status='APPROVED', final_price=5000)
    Enrollment.objects.create(student=student, course=free)
    StudentProgress.objects.create(student=student, lesson=lesson)
    CourseCompletion.objects.create(student=student, course=free)
    Coupon.objects.create(code='PROMO20', discount_percent=20)
    for label in ('Question', 'Cours particulier'):
        ContactReason.objects.get_or_create(label=label)
    question = Question.objects.create(
        student=student, course=course, lesson=lesson, title='Aide kana', content='Je bloque'
    )
    Response.objects.create(question=question, author=teacher, content='Voici', is_instructor=True)
    Notification.objects.create(recipient=student, title='Bravo', message='Leçon validée', link='/')
    return {
        'admin': admin,
        'student': student,
        'teacher': teacher,
        'course': course,
        'free': free,
        'lesson': lesson,
        'lesson2': lesson2,
        'module': module,
        'question': question,
        'block': quiz,
        'section': course.landing_sections.first(),
    }


def pages(w):
    course, lesson = w['course'], w['lesson']
    anon = [
        ('home', reverse('course_list')),
        ('catalogue', reverse('catalogue')),
        ('contact', reverse('contact')),
        ('login', reverse('account_login')),
        ('signup', reverse('account_signup')),
        ('course-sales', reverse('course_detail', args=[course.slug])),
        ('plans', reverse('instructor_plans')),
    ]
    student = [
        ('student-dashboard', reverse('user_dashboard')),
        ('student-profile', reverse('user_profile')),
        ('student-course', reverse('course_detail', args=[course.slug])),
        ('student-lesson', reverse('lesson_detail', args=[course.slug, lesson.slug])),
        ('student-notifications', reverse('my_notifications')),
        ('student-support', reverse('my_questions')),
        ('student-question', reverse('question_detail', args=[w['question'].id])),
        ('student-access-form', reverse('request_access', args=[w['free'].id])),
        ('student-free-course', reverse('course_detail', args=[w['free'].slug])),
    ]
    admin = [
        ('admin-courses', reverse('manage_course_list')),
        ('admin-course-edit', reverse('manage_course_edit', args=[course.slug])),
        ('admin-course-create', reverse('manage_course_create')),
        ('admin-modules', reverse('manage_course_modules', args=[course.slug])),
        ('admin-lessons', reverse('manage_module_lessons', args=[course.slug, w['module'].id])),
        ('admin-builder', reverse('manage_lesson_content', args=[course.slug, lesson.slug])),
        ('admin-landing', reverse('manage_course_landing', args=[course.slug])),
        ('admin-students', reverse('manage_course_students', args=[course.slug])),
        ('admin-course-landing-preview', reverse('course_detail', args=[course.slug]) + '?view=landing'),
        ('admin-lesson', reverse('lesson_detail', args=[course.slug, lesson.slug])),
    ]
    teacher = [
        ('teacher-dashboard', reverse('instructor_dashboard')),
        ('teacher-questions', reverse('instructor_course_questions', args=[course.slug])),
    ]
    return {'anon': anon, 'student': student, 'admin': admin, 'teacher': teacher}


def shoot(page, name, url, out, mobile=False):
    page.goto(url, wait_until='networkidle')
    page.add_style_tag(content=FREEZE_CSS)
    page.wait_for_timeout(150)
    page.screenshot(path=str(out / f'{name}{"-m" if mobile else ""}.png'), full_page=True)


def compare(out, reference):
    from PIL import Image, ImageChops

    report = []
    (out / 'diff').mkdir(exist_ok=True)
    for shot in sorted(out.glob('*.png')):
        other = reference / shot.name
        if not other.exists():
            report.append((shot.name, 'nouvelle capture'))
            continue
        a, b = Image.open(shot).convert('RGB'), Image.open(other).convert('RGB')
        if a.size != b.size:
            report.append((shot.name, f'taille {b.size} -> {a.size}'))
            continue
        diff = ImageChops.difference(a, b)
        box = diff.getbbox()
        if box:
            changed = sum(1 for px in diff.getdata() if px != (0, 0, 0))
            ratio = changed / (a.size[0] * a.size[1])
            diff.point(lambda v: 255 if v else 0).save(out / 'diff' / shot.name)
            report.append((shot.name, f'{ratio:.2%} des pixels, zone {box}'))
    return report


def test_capture(world, live_server):
    out = Path(os.environ.get('SNAP_DIR', 'snapshots_out'))
    out.mkdir(parents=True, exist_ok=True)
    reference = os.environ.get('SNAP_COMPARE')
    groups = pages(world)
    users = {'anon': None, 'student': world['student'], 'admin': world['admin'], 'teacher': world['teacher']}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for who, items in groups.items():
            for mobile in (False, True):
                if mobile and who not in {'anon', 'student'}:
                    continue
                context = browser.new_context(
                    viewport={'width': 390, 'height': 844} if mobile else {'width': 1280, 'height': 900},
                    locale='fr-FR',
                    timezone_id='Africa/Algiers',
                )
                page = context.new_page()
                page.live_server_url = live_server.url
                if users[who] is not None:
                    login_as(page, users[who])
                for name, path in items:
                    shoot(page, name, live_server.url + path, out, mobile=mobile)
                context.close()
        browser.close()

    if reference:
        report = compare(out, Path(reference))
        print('\n=== COMPARAISON VISUELLE ===')
        for name, info in report:
            print(f'{name:40} {info}')
        print(f'{len(report)} page(s) différente(s)')
