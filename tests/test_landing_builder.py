"""Tests pour le Landing Page Builder (sections vitrines éditables par cours)."""

import pytest
from django.test import Client
from django.urls import reverse

from courses.models import Course, LandingSection

pytestmark = pytest.mark.django_db


# ── Fixtures ──────────────────────────────────────────


@pytest.fixture
def course():
    return Course.objects.create(
        title="Formation Test",
        slug="formation-test",
        short_description="Accroche",
        description="Description markdown",
        price=5000,
        is_published=True,
    )


@pytest.fixture
def admin_client():
    from users.models import User

    User.objects.create_superuser(email='admin@test.com', password='pass123')
    client = Client()
    client.login(email='admin@test.com', password='pass123')
    return client


@pytest.fixture
def anon_client():
    return Client()


@pytest.fixture
def student_client():
    from users.models import User

    User.objects.create_user(email='student@test.com', password='pass123')
    client = Client()
    client.login(email='student@test.com', password='pass123')
    return client


# ══════════════════════════════════════════════════════
#  1. Sécurité : seul le staff peut accéder au builder
# ══════════════════════════════════════════════════════


class TestLandingBuilderAccess:
    def test_anonymous_redirected(self, anon_client, course):
        url = reverse('manage_course_landing', kwargs={'course_slug': course.slug})
        resp = anon_client.get(url)
        assert resp.status_code == 302

    def test_student_redirected(self, student_client, course):
        url = reverse('manage_course_landing', kwargs={'course_slug': course.slug})
        resp = student_client.get(url)
        assert resp.status_code == 302

    def test_admin_can_access(self, admin_client, course):
        url = reverse('manage_course_landing', kwargs={'course_slug': course.slug})
        resp = admin_client.get(url)
        assert resp.status_code == 200


# ══════════════════════════════════════════════════════
#  2. Ajout de sections
# ══════════════════════════════════════════════════════


class TestAddLandingSection:
    def test_add_text_section(self, admin_client, course):
        url = reverse('add_landing_section', kwargs={'course_slug': course.slug, 'section_type': 'text'})
        resp = admin_client.get(url)
        assert resp.status_code == 200
        assert b'Texte' in resp.content

    def test_post_text_section(self, admin_client, course):
        url = reverse('add_landing_section', kwargs={'course_slug': course.slug, 'section_type': 'text'})
        resp = admin_client.post(
            url,
            {
                'title': 'Mon histoire',
                'body': '# Introduction\nBienvenue...',
                'background': 'none',
            },
        )
        assert resp.status_code == 200
        assert LandingSection.objects.filter(course=course).count() == 1
        section = LandingSection.objects.first()
        assert section.title == 'Mon histoire'
        assert section.section_type == 'text'
        assert section.order == 1

    def test_add_video_section(self, admin_client, course):
        url = reverse('add_landing_section', kwargs={'course_slug': course.slug, 'section_type': 'video'})
        resp = admin_client.post(
            url,
            {
                'video_id': 'dQw4w9WgXcQ',
                'background': 'none',
            },
        )
        assert resp.status_code == 200
        section = LandingSection.objects.first()
        assert section.section_type == 'video'
        assert section.video_id == 'dQw4w9WgXcQ'

    def test_add_features_section(self, admin_client, course):
        url = reverse('add_landing_section', kwargs={'course_slug': course.slug, 'section_type': 'features'})
        resp = admin_client.post(
            url,
            {
                'title': 'Ce que vous apprendrez',
                'body': '- Point 1\n- Point 2\n- Point 3',
                'background': 'green',
            },
        )
        assert resp.status_code == 200
        section = LandingSection.objects.first()
        assert section.section_type == 'features'
        assert section.background == 'green'

    def test_auto_order_increments(self, admin_client, course):
        """Les sections ajoutées s'empilent dans l'ordre."""
        url_text = reverse('add_landing_section', kwargs={'course_slug': course.slug, 'section_type': 'text'})
        url_video = reverse('add_landing_section', kwargs={'course_slug': course.slug, 'section_type': 'video'})
        admin_client.post(url_text, {'title': 'S1', 'background': 'none'})
        admin_client.post(url_video, {'video_id': 'abc', 'background': 'none'})
        sections = LandingSection.objects.filter(course=course).order_by('order')
        assert sections[0].order == 1
        assert sections[1].order == 2


# ══════════════════════════════════════════════════════
#  3. Édition de sections
# ══════════════════════════════════════════════════════


class TestEditLandingSection:
    def test_edit_section_get(self, admin_client, course):
        section = LandingSection.objects.create(
            course=course,
            section_type='text',
            order=1,
            title='Ancien',
            body='old content',
        )
        url = reverse('edit_landing_section', kwargs={'section_id': section.id})
        resp = admin_client.get(url)
        assert resp.status_code == 200
        assert b'Ancien' in resp.content

    def test_edit_section_post(self, admin_client, course):
        section = LandingSection.objects.create(
            course=course,
            section_type='text',
            order=1,
            title='Ancien',
            body='old',
        )
        url = reverse('edit_landing_section', kwargs={'section_id': section.id})
        resp = admin_client.post(
            url,
            {
                'title': 'Nouveau',
                'body': 'new content',
                'background': 'gray',
            },
        )
        assert resp.status_code == 200
        section.refresh_from_db()
        assert section.title == 'Nouveau'
        assert section.background == 'gray'


# ══════════════════════════════════════════════════════
#  4. Suppression de sections
# ══════════════════════════════════════════════════════


class TestDeleteLandingSection:
    def test_delete_section(self, admin_client, course):
        section = LandingSection.objects.create(
            course=course,
            section_type='text',
            order=1,
            title='Bye',
        )
        url = reverse('delete_landing_section', kwargs={'section_id': section.id})
        resp = admin_client.post(url)
        assert resp.status_code == 200
        assert LandingSection.objects.count() == 0

    def test_delete_requires_post(self, admin_client, course):
        section = LandingSection.objects.create(
            course=course,
            section_type='text',
            order=1,
        )
        url = reverse('delete_landing_section', kwargs={'section_id': section.id})
        resp = admin_client.get(url)
        assert resp.status_code == 405  # Method not allowed


# ══════════════════════════════════════════════════════
#  5. Réordonnement
# ══════════════════════════════════════════════════════


class TestReorderLandingSections:
    def test_reorder(self, admin_client, course):
        s1 = LandingSection.objects.create(course=course, section_type='text', order=1)
        s2 = LandingSection.objects.create(course=course, section_type='video', order=2)
        s3 = LandingSection.objects.create(course=course, section_type='features', order=3)
        url = reverse('reorder_landing_sections', kwargs={'course_slug': course.slug})
        # Invert order: s3, s1, s2
        resp = admin_client.post(
            url,
            {
                'section_order': [s3.id, s1.id, s2.id],
            },
        )
        assert resp.status_code == 200
        s1.refresh_from_db()
        s2.refresh_from_db()
        s3.refresh_from_db()
        assert s3.order == 1
        assert s1.order == 2
        assert s2.order == 3


# ══════════════════════════════════════════════════════
#  6. Rendu public : sections vs fallback
# ══════════════════════════════════════════════════════


class TestPublicRendering:
    def test_course_with_sections_shows_sections(self, anon_client, course):
        LandingSection.objects.create(
            course=course,
            section_type='text',
            order=1,
            title='Mon histoire unique',
            body='Il était une fois...',
        )
        url = reverse('course_detail', kwargs={'course_slug': course.slug})
        resp = anon_client.get(url)
        assert resp.status_code == 200
        assert 'Mon histoire unique' in resp.content.decode()
        assert 'Il était une fois' in resp.content.decode()

    def test_course_without_sections_shows_fallback(self, anon_client, course):
        """Sans sections, la page utilise description/what_you_will_learn classiques."""
        url = reverse('course_detail', kwargs={'course_slug': course.slug})
        resp = anon_client.get(url)
        assert resp.status_code == 200
        content = resp.content.decode()
        assert 'Description markdown' in content or 'Page de Vente' in content

    def test_section_video_renders_iframe(self, anon_client, course):
        LandingSection.objects.create(
            course=course,
            section_type='video',
            order=1,
            video_id='dQw4w9WgXcQ',
        )
        url = reverse('course_detail', kwargs={'course_slug': course.slug})
        resp = anon_client.get(url)
        assert 'youtube.com/embed/dQw4w9WgXcQ' in resp.content.decode()

    def test_section_features_with_background(self, anon_client, course):
        LandingSection.objects.create(
            course=course,
            section_type='features',
            order=1,
            title='Points forts',
            body='- A\n- B',
            background='green',
        )
        url = reverse('course_detail', kwargs={'course_slug': course.slug})
        resp = anon_client.get(url)
        content = resp.content.decode()
        assert 'Points forts' in content

    def test_sidebar_always_present(self, anon_client, course):
        """La sidebar (prix + CTA) est toujours visible, même avec des sections custom."""
        LandingSection.objects.create(
            course=course,
            section_type='text',
            order=1,
            title='Custom',
        )
        url = reverse('course_detail', kwargs={'course_slug': course.slug})
        resp = anon_client.get(url)
        content = resp.content.decode()
        assert '5000' in content or 'DA' in content

    def test_programme_always_present(self, anon_client, course):
        """L'accordéon programme est toujours affiché en bas."""
        LandingSection.objects.create(
            course=course,
            section_type='text',
            order=1,
            title='Custom',
        )
        url = reverse('course_detail', kwargs={'course_slug': course.slug})
        resp = anon_client.get(url)
        content = resp.content.decode()
        assert 'Programme de la formation' in content


# ══════════════════════════════════════════════════════
#  7. Nouveaux types : Hero, Texte+Image, FAQ
# ══════════════════════════════════════════════════════


class TestHeroSection:
    def test_add_hero_section(self, admin_client, course):
        url = reverse('add_landing_section', kwargs={'course_slug': course.slug, 'section_type': 'hero'})
        resp = admin_client.post(
            url,
            {
                'title': 'Devenez développeur Django',
                'subtitle': 'La formation complète de A à Z',
                'cta_text': "S'inscrire maintenant",
                'cta_url': '#inscription',
                'background': 'dark',
            },
        )
        assert resp.status_code == 200
        section = LandingSection.objects.first()
        assert section.section_type == 'hero'
        assert section.subtitle == 'La formation complète de A à Z'
        assert section.cta_text == "S'inscrire maintenant"
        assert section.cta_url == '#inscription'

    def test_hero_renders_publicly(self, anon_client, course):
        LandingSection.objects.create(
            course=course,
            section_type='hero',
            order=1,
            title='Devenez Pro',
            subtitle='Formation premium',
            cta_text='Inscription',
            cta_url='#inscription',
            background='dark',
        )
        url = reverse('course_detail', kwargs={'course_slug': course.slug})
        resp = anon_client.get(url)
        content = resp.content.decode()
        assert 'Devenez Pro' in content
        assert 'Formation premium' in content
        assert 'Inscription' in content
        assert '#inscription' in content

    def test_hero_form_shows_subtitle_cta(self, admin_client, course):
        url = reverse('add_landing_section', kwargs={'course_slug': course.slug, 'section_type': 'hero'})
        resp = admin_client.get(url)
        content = resp.content.decode()
        assert 'Sous-titre' in content
        assert 'Texte du bouton' in content


class TestTextImageSection:
    def test_add_text_image_section(self, admin_client, course):
        url = reverse('add_landing_section', kwargs={'course_slug': course.slug, 'section_type': 'text_image'})
        resp = admin_client.post(
            url,
            {
                'title': 'Apprenez à votre rythme',
                'body': 'Un contenu riche et complet.',
                'image_position': 'left',
                'background': 'none',
            },
        )
        assert resp.status_code == 200
        section = LandingSection.objects.first()
        assert section.section_type == 'text_image'
        assert section.image_position == 'left'

    def test_text_image_renders_publicly(self, anon_client, course):
        LandingSection.objects.create(
            course=course,
            section_type='text_image',
            order=1,
            title='Apprendre en pratiquant',
            body='Grâce à nos exercices...',
            image_position='right',
        )
        url = reverse('course_detail', kwargs={'course_slug': course.slug})
        resp = anon_client.get(url)
        content = resp.content.decode()
        assert 'Apprendre en pratiquant' in content
        assert 'nos exercices' in content

    def test_text_image_position_left_renders(self, anon_client, course):
        LandingSection.objects.create(
            course=course,
            section_type='text_image',
            order=1,
            title='Skills',
            body='Content',
            image_position='left',
        )
        url = reverse('course_detail', kwargs={'course_slug': course.slug})
        resp = anon_client.get(url)
        assert 'flex-row-reverse' in resp.content.decode()

    def test_text_image_position_right_renders(self, anon_client, course):
        LandingSection.objects.create(
            course=course,
            section_type='text_image',
            order=1,
            title='Skills',
            body='Content',
            image_position='right',
        )
        url = reverse('course_detail', kwargs={'course_slug': course.slug})
        resp = anon_client.get(url)
        content = resp.content.decode()
        assert 'md:flex-row' in content

    def test_text_image_form_shows_position(self, admin_client, course):
        url = reverse('add_landing_section', kwargs={'course_slug': course.slug, 'section_type': 'text_image'})
        resp = admin_client.get(url)
        assert "Position de l'image" in resp.content.decode()


class TestFaqSection:
    def test_add_faq_section(self, admin_client, course):
        url = reverse('add_landing_section', kwargs={'course_slug': course.slug, 'section_type': 'faq'})
        resp = admin_client.post(
            url,
            {
                'title': 'Questions fréquentes',
                'body': '### Comment ça marche ?\nVous suivez les cours à votre rythme.\n\n### C\'est payant ?\nOui, 5000 DA.',
                'background': 'gray',
            },
        )
        assert resp.status_code == 200
        section = LandingSection.objects.first()
        assert section.section_type == 'faq'
        assert section.title == 'Questions fréquentes'

    def test_faq_renders_questions(self, anon_client, course):
        LandingSection.objects.create(
            course=course,
            section_type='faq',
            order=1,
            title='FAQ',
            body='### Comment s\'inscrire ?\nCliquez sur le bouton.\n\n### Combien ça coûte ?\n5000 DA.',
        )
        url = reverse('course_detail', kwargs={'course_slug': course.slug})
        resp = anon_client.get(url)
        content = resp.content.decode()
        assert 'FAQ' in content
        assert "Comment s&#x27;inscrire" in content or "Comment s'inscrire" in content
        assert '5000 DA' in content

    def test_faq_form_shows_hint(self, admin_client, course):
        url = reverse('add_landing_section', kwargs={'course_slug': course.slug, 'section_type': 'faq'})
        resp = admin_client.get(url)
        content = resp.content.decode()
        assert '### Question' in content

    def test_faq_empty_body_no_error(self, anon_client, course):
        """Une FAQ sans body ne doit pas crasher."""
        LandingSection.objects.create(
            course=course,
            section_type='faq',
            order=1,
            title='FAQ vide',
            body='',
        )
        url = reverse('course_detail', kwargs={'course_slug': course.slug})
        resp = anon_client.get(url)
        assert resp.status_code == 200
        assert 'FAQ vide' in resp.content.decode()


# ══════════════════════════════════════════════════════
#  8. faq_items template filter
# ══════════════════════════════════════════════════════


class TestFaqItemsFilter:
    def test_parses_multiple_questions(self):
        from courses.templatetags.md import faq_items

        result = faq_items('### Q1\nAnswer 1\n\n### Q2\nAnswer 2')
        assert len(result) == 2
        assert result[0][0] == 'Q1'
        assert result[1][0] == 'Q2'
        assert 'Answer 1' in result[0][1]
        assert 'Answer 2' in result[1][1]

    def test_empty_body(self):
        from courses.templatetags.md import faq_items

        assert faq_items('') == []
        assert faq_items(None) == []

    def test_single_question(self):
        from courses.templatetags.md import faq_items

        result = faq_items('### Seule question\nRéponse unique.')
        assert len(result) == 1
        assert result[0][0] == 'Seule question'

    def test_question_without_answer(self):
        from courses.templatetags.md import faq_items

        result = faq_items('### Question sans réponse')
        assert len(result) == 1
        assert result[0][0] == 'Question sans réponse'


# ══════════════════════════════════════════════════════
#  9. Dupliquer une section
# ══════════════════════════════════════════════════════


class TestDuplicateLandingSection:
    def test_duplicate_creates_clone(self, admin_client, course):
        section = LandingSection.objects.create(
            course=course,
            section_type='text',
            order=1,
            title='Original',
            body='Contenu original',
            background='gray',
            css_class='custom-class',
        )
        url = reverse('duplicate_landing_section', kwargs={'section_id': section.id})
        resp = admin_client.post(url)
        assert resp.status_code == 200
        assert LandingSection.objects.filter(course=course).count() == 2
        clone = LandingSection.objects.filter(course=course).exclude(id=section.id).first()
        assert clone.title == 'Original'
        assert clone.body == 'Contenu original'
        assert clone.section_type == 'text'
        assert clone.background == 'gray'
        assert clone.css_class == 'custom-class'

    def test_duplicate_places_after_original(self, admin_client, course):
        s1 = LandingSection.objects.create(course=course, section_type='text', order=1, title='S1')
        s2 = LandingSection.objects.create(course=course, section_type='text', order=2, title='S2')
        s3 = LandingSection.objects.create(course=course, section_type='text', order=3, title='S3')
        url = reverse('duplicate_landing_section', kwargs={'section_id': s1.id})
        admin_client.post(url)
        # Clone should be at order 2, s2 pushed to 3, s3 to 4
        clone = LandingSection.objects.filter(course=course).exclude(id__in=[s1.id, s2.id, s3.id]).first()
        assert clone.order == 2
        s2.refresh_from_db()
        s3.refresh_from_db()
        assert s2.order == 3
        assert s3.order == 4

    def test_duplicate_preserves_hero_fields(self, admin_client, course):
        section = LandingSection.objects.create(
            course=course,
            section_type='hero',
            order=1,
            title='Hero',
            subtitle='Sub',
            cta_text='CTA',
            cta_url='#url',
            background='dark',
        )
        url = reverse('duplicate_landing_section', kwargs={'section_id': section.id})
        admin_client.post(url)
        clone = LandingSection.objects.filter(course=course).exclude(id=section.id).first()
        assert clone.section_type == 'hero'
        assert clone.subtitle == 'Sub'
        assert clone.cta_text == 'CTA'
        assert clone.cta_url == '#url'

    def test_duplicate_preserves_visibility(self, admin_client, course):
        section = LandingSection.objects.create(
            course=course,
            section_type='text',
            order=1,
            title='Hidden',
            is_visible=False,
        )
        url = reverse('duplicate_landing_section', kwargs={'section_id': section.id})
        admin_client.post(url)
        clone = LandingSection.objects.filter(course=course).exclude(id=section.id).first()
        assert clone.is_visible is False

    def test_duplicate_requires_post(self, admin_client, course):
        section = LandingSection.objects.create(
            course=course,
            section_type='text',
            order=1,
        )
        url = reverse('duplicate_landing_section', kwargs={'section_id': section.id})
        resp = admin_client.get(url)
        assert resp.status_code == 405

    def test_duplicate_requires_staff(self, student_client, course):
        section = LandingSection.objects.create(
            course=course,
            section_type='text',
            order=1,
        )
        url = reverse('duplicate_landing_section', kwargs={'section_id': section.id})
        resp = student_client.post(url)
        assert resp.status_code == 302


# ══════════════════════════════════════════════════════
#  10. Visibilité on/off (brouillon)
# ══════════════════════════════════════════════════════


class TestToggleLandingSectionVisibility:
    def test_toggle_hides_visible_section(self, admin_client, course):
        section = LandingSection.objects.create(
            course=course,
            section_type='text',
            order=1,
            title='Visible',
            is_visible=True,
        )
        url = reverse('toggle_landing_section_visibility', kwargs={'section_id': section.id})
        resp = admin_client.post(url)
        assert resp.status_code == 200
        section.refresh_from_db()
        assert section.is_visible is False

    def test_toggle_shows_hidden_section(self, admin_client, course):
        section = LandingSection.objects.create(
            course=course,
            section_type='text',
            order=1,
            title='Hidden',
            is_visible=False,
        )
        url = reverse('toggle_landing_section_visibility', kwargs={'section_id': section.id})
        resp = admin_client.post(url)
        assert resp.status_code == 200
        section.refresh_from_db()
        assert section.is_visible is True

    def test_hidden_section_not_shown_publicly(self, anon_client, course):
        LandingSection.objects.create(
            course=course,
            section_type='text',
            order=1,
            title='Section visible',
            body='Contenu public',
            is_visible=True,
        )
        LandingSection.objects.create(
            course=course,
            section_type='text',
            order=2,
            title='Section cachée',
            body='Contenu secret',
            is_visible=False,
        )
        url = reverse('course_detail', kwargs={'course_slug': course.slug})
        resp = anon_client.get(url)
        content = resp.content.decode()
        assert 'Section visible' in content
        assert 'Section cachée' not in content
        assert 'Contenu secret' not in content

    def test_hidden_section_shown_in_builder(self, admin_client, course):
        LandingSection.objects.create(
            course=course,
            section_type='text',
            order=1,
            title='Brouillon',
            is_visible=False,
        )
        url = reverse('manage_course_landing', kwargs={'course_slug': course.slug})
        resp = admin_client.get(url)
        content = resp.content.decode()
        assert 'Brouillon' in content

    def test_toggle_requires_post(self, admin_client, course):
        section = LandingSection.objects.create(
            course=course,
            section_type='text',
            order=1,
        )
        url = reverse('toggle_landing_section_visibility', kwargs={'section_id': section.id})
        resp = admin_client.get(url)
        assert resp.status_code == 405

    def test_toggle_requires_staff(self, student_client, course):
        section = LandingSection.objects.create(
            course=course,
            section_type='text',
            order=1,
        )
        url = reverse('toggle_landing_section_visibility', kwargs={'section_id': section.id})
        resp = student_client.post(url)
        assert resp.status_code == 302


# ══════════════════════════════════════════════════════
#  11. Templates prédéfinis (prefill)
# ══════════════════════════════════════════════════════


class TestPrefillLandingTemplate:
    def test_prefill_creates_six_sections(self, admin_client, course):
        url = reverse('prefill_landing_template', kwargs={'course_slug': course.slug})
        resp = admin_client.post(url)
        assert resp.status_code == 200
        assert LandingSection.objects.filter(course=course).count() == 6

    def test_prefill_creates_correct_types(self, admin_client, course):
        url = reverse('prefill_landing_template', kwargs={'course_slug': course.slug})
        admin_client.post(url)
        types = list(
            LandingSection.objects.filter(course=course).order_by('order').values_list('section_type', flat=True)
        )
        assert types == ['hero', 'text', 'features', 'text_image', 'testimonials', 'faq']

    def test_prefill_uses_course_data(self, admin_client, course):
        url = reverse('prefill_landing_template', kwargs={'course_slug': course.slug})
        admin_client.post(url)
        hero = LandingSection.objects.get(course=course, section_type='hero')
        assert hero.title == course.title
        assert hero.subtitle == course.short_description
        text = LandingSection.objects.get(course=course, section_type='text')
        assert text.body == course.description

    def test_prefill_does_nothing_if_sections_exist(self, admin_client, course):
        LandingSection.objects.create(
            course=course,
            section_type='text',
            order=1,
            title='Existant',
        )
        url = reverse('prefill_landing_template', kwargs={'course_slug': course.slug})
        admin_client.post(url)
        # Should NOT create 6 new sections — only the existing 1
        assert LandingSection.objects.filter(course=course).count() == 1

    def test_prefill_requires_post(self, admin_client, course):
        url = reverse('prefill_landing_template', kwargs={'course_slug': course.slug})
        resp = admin_client.get(url)
        assert resp.status_code == 405

    def test_prefill_requires_staff(self, student_client, course):
        url = reverse('prefill_landing_template', kwargs={'course_slug': course.slug})
        resp = student_client.post(url)
        assert resp.status_code == 302


# ══════════════════════════════════════════════════════
#  12. Section Témoignages
# ══════════════════════════════════════════════════════


class TestTestimonialsSection:
    def test_add_testimonials_section(self, admin_client, course):
        url = reverse('add_landing_section', kwargs={'course_slug': course.slug, 'section_type': 'testimonials'})
        resp = admin_client.post(
            url,
            {
                'title': 'Témoignages',
                'body': '### ★★★★★ | Marie D.\nExcellent !\n\n### ★★★★☆ | Ahmed K.\nTrès bien.',
                'background': 'none',
            },
        )
        assert resp.status_code == 200
        section = LandingSection.objects.first()
        assert section.section_type == 'testimonials'
        assert section.title == 'Témoignages'

    def test_testimonials_renders_publicly(self, anon_client, course):
        LandingSection.objects.create(
            course=course,
            section_type='testimonials',
            order=1,
            title='Avis étudiants',
            body='### ★★★★★ | Sophie L.\nFormation incroyable, j\'ai tout compris !',
        )
        url = reverse('course_detail', kwargs={'course_slug': course.slug})
        resp = anon_client.get(url)
        content = resp.content.decode()
        assert 'Avis étudiants' in content
        assert 'Sophie L.' in content
        assert 'tout compris' in content

    def test_testimonials_form_shows_hint(self, admin_client, course):
        url = reverse('add_landing_section', kwargs={'course_slug': course.slug, 'section_type': 'testimonials'})
        resp = admin_client.get(url)
        content = resp.content.decode()
        assert '★★★★★' in content or 'Nom' in content

    def test_testimonials_empty_body(self, anon_client, course):
        LandingSection.objects.create(
            course=course,
            section_type='testimonials',
            order=1,
            title='Témoignages vide',
            body='',
        )
        url = reverse('course_detail', kwargs={'course_slug': course.slug})
        resp = anon_client.get(url)
        assert resp.status_code == 200


# ══════════════════════════════════════════════════════
#  13. testimonial_items template filter
# ══════════════════════════════════════════════════════


class TestTestimonialItemsFilter:
    def test_parses_multiple_testimonials(self):
        from courses.templatetags.md import testimonial_items

        result = testimonial_items('### ★★★★★ | Marie\nSuper !\n\n### ★★★★☆ | Ahmed\nBien.')
        assert len(result) == 2
        assert result[0]['name'] == 'Marie'
        assert result[0]['stars'] == '★★★★★'
        assert 'Super' in result[0]['text_html']
        assert result[1]['name'] == 'Ahmed'
        assert result[1]['stars'] == '★★★★☆'

    def test_empty_body(self):
        from courses.templatetags.md import testimonial_items

        assert testimonial_items('') == []
        assert testimonial_items(None) == []

    def test_name_without_stars(self):
        from courses.templatetags.md import testimonial_items

        result = testimonial_items('### Jean Dupont\nTrès bien.')
        assert len(result) == 1
        assert result[0]['name'] == 'Jean Dupont'
        assert result[0]['stars'] == '★★★★★'  # Default stars

    def test_single_testimonial(self):
        from courses.templatetags.md import testimonial_items

        result = testimonial_items('### ★★★★★ | Unique\nSeul avis.')
        assert len(result) == 1
        assert result[0]['name'] == 'Unique'

    def test_testimonial_without_text(self):
        from courses.templatetags.md import testimonial_items

        result = testimonial_items('### ★★★★★ | Silencieux')
        assert len(result) == 1
        assert result[0]['name'] == 'Silencieux'
        assert result[0]['text_html'] == ''
