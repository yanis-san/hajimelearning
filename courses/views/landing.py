"""Builder de la page vitrine d'un cours (sections de landing page)."""

from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_POST

from ..forms import LandingSectionForm
from ..models import Course, LandingSection
from ..permissions import builder_access_required, get_managed_course, get_managed_course_from_section
from ._helpers import apply_order, next_order

SECTION_LIST_TEMPLATE = 'courses/manage/partials/landing_section_list.html'
SECTION_FORM_TEMPLATE = 'courses/manage/partials/landing_section_form.html'

# Sections créées par « Pré-remplir avec un modèle » (le contenu dépend du cours)
SECTION_TEMPLATE_SPECS = (
    {
        'section_type': 'hero',
        'cta_text': "S'inscrire maintenant",
        'cta_url': '#inscription',
        'background': 'dark',
    },
    {
        'section_type': 'text',
        'title': 'À propos de cette formation',
        'background': 'none',
    },
    {
        'section_type': 'features',
        'title': 'Ce que vous allez apprendre',
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
        'body': (
            "### ★★★★★ | Marie D.\nExcellente formation, très bien structurée !\n\n"
            "### ★★★★☆ | Ahmed K.\nJ'ai beaucoup appris, je recommande."
        ),
        'background': 'none',
    },
    {
        'section_type': 'faq',
        'title': 'Questions fréquentes',
        'body': (
            "### Comment s'inscrire ?\nCliquez sur le bouton d'inscription en haut de page.\n\n"
            "### Combien de temps ai-je accès ?\nVous avez un accès illimité une fois inscrit."
        ),
        'background': 'gray',
    },
)


def _section_list(request, course):
    return render(request, SECTION_LIST_TEMPLATE, {'course': course})


def _section_saved_response(request, course):
    """Liste rafraîchie + formulaire vidé (swap hors-bande)."""
    return render(request, 'courses/manage/partials/landing_section_saved.html', {'course': course})


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
    return render(
        request,
        'courses/manage/landing_builder.html',
        {
            'course': course,
            'courses_url': courses_url,
            'course_edit_url': course_edit_url,
        },
    )


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
            section.order = next_order(course.landing_sections)
            section.save()
            return _section_saved_response(request, course)
    else:
        form = LandingSectionForm()

    return render(request, SECTION_FORM_TEMPLATE, {'form': form, 'course': course, 'section_type': section_type})


@builder_access_required
def edit_landing_section(request, section_id):
    """Éditer une section existante."""
    section, course = get_managed_course_from_section(request.user, section_id)

    if request.method == 'POST':
        form = LandingSectionForm(request.POST, request.FILES, instance=section)
        if form.is_valid():
            form.save()
            return _section_saved_response(request, course)
    else:
        form = LandingSectionForm(instance=section)

    return render(
        request,
        SECTION_FORM_TEMPLATE,
        {
            'form': form,
            'course': course,
            'section': section,
            'section_type': section.section_type,
        },
    )


@builder_access_required
@require_POST
def delete_landing_section(request, section_id):
    """Supprimer une section."""
    section, course = get_managed_course_from_section(request.user, section_id)
    section.delete()
    return _section_list(request, course)


@builder_access_required
@require_POST
def reorder_landing_sections(request, course_slug):
    """Réordonner les sections (HTMX + SortableJS)."""
    course = get_managed_course(request.user, course_slug)
    apply_order(LandingSection.objects.filter(course=course), request.POST.getlist('section_order'))
    return HttpResponse(status=204)


@builder_access_required
@require_POST
def duplicate_landing_section(request, section_id):
    """Dupliquer une section existante, placée juste après l'originale."""
    original, course = get_managed_course_from_section(request.user, section_id)

    # Les sections suivantes sont décalées avant l'insertion du clone
    LandingSection.objects.filter(course=course, order__gt=original.order).update(order=F('order') + 1)
    LandingSection.objects.create(
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
        image=original.image.name,  # même fichier, pas de copie
        order=original.order + 1,
    )
    return _section_list(request, course)


@builder_access_required
@require_POST
def toggle_landing_section_visibility(request, section_id):
    """Basculer la visibilité d'une section (brouillon / visible)."""
    section, course = get_managed_course_from_section(request.user, section_id)
    section.is_visible = not section.is_visible
    section.save(update_fields=['is_visible'])
    return _section_list(request, course)


@builder_access_required
@require_POST
def prefill_landing_template(request, course_slug):
    """Pré-remplir la vitrine avec un modèle de 6 sections (si elle est vide)."""
    course = get_managed_course(request.user, course_slug)

    if not course.landing_sections.exists():
        # Contenu issu du cours, injecté dans le modèle
        dynamic = {
            'hero': {'title': course.title, 'subtitle': course.short_description},
            'text': {'body': course.description or 'Décrivez votre formation ici...'},
            'features': {'body': course.what_you_will_learn or '- Point fort 1\n- Point fort 2\n- Point fort 3'},
        }
        LandingSection.objects.bulk_create(
            [
                LandingSection(course=course, order=position, **{**spec, **dynamic.get(spec['section_type'], {})})
                for position, spec in enumerate(SECTION_TEMPLATE_SPECS, start=1)
            ]
        )

    return _section_list(request, course)
