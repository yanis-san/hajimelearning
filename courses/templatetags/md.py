from django import template
from django.utils.safestring import mark_safe
from markdownx.utils import markdownify
import re

register = template.Library()


@register.filter(name="md")
def render_markdown(value):
    """Convertit du texte Markdown en HTML sécurisé."""
    if not value:
        return ""
    return mark_safe(markdownify(value))


@register.filter(name="first_heading")
def first_heading(value):
    """Extrait le premier titre (# à ######) du contenu markdown."""
    if not value:
        return ""
    match = re.search(r'^#{1,6}\s+(.+)$', value, re.MULTILINE)
    return match.group(1).strip() if match else ""


@register.filter(name="strip_first_heading")
def strip_first_heading(value):
    """Supprime la première ligne de titre markdown du contenu."""
    if not value:
        return ""
    return re.sub(r'^#{1,6}\s+.+\n?', '', value, count=1, flags=re.MULTILINE).lstrip()


@register.filter(name="dict_get")
def dict_get(d, key):
    """Accès à un dict par clé variable dans un template Django."""
    if isinstance(d, dict):
        return d.get(key)


@register.filter(name="faq_items")
def faq_items(value):
    """
    Parse markdown FAQ body into a list of (question, answer_html) tuples.
    Each Q/A is separated by a ### heading.
    Example input:
        ### Comment s'inscrire ?
        Cliquez sur le bouton...
        ### Combien ça coûte ?
        C'est gratuit !
    Returns:
        [('Comment s\'inscrire ?', '<p>Cliquez sur le bouton...</p>'),
         ('Combien ça coûte ?', '<p>C\'est gratuit !</p>')]
    """
    if not value:
        return []

    # Split by ### headings
    parts = re.split(r'^###\s+', value.strip(), flags=re.MULTILINE)
    items = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        lines = part.split('\n', 1)
        question = lines[0].strip()
        answer_md = lines[1].strip() if len(lines) > 1 else ''
        answer_html = markdownify(answer_md) if answer_md else ''
        items.append((question, mark_safe(answer_html)))
    return items


@register.filter(name="testimonial_items")
def testimonial_items(value):
    """
    Parse markdown testimonials body into a list of dicts.
    Format: ### ★★★★★ | Nom Prénom
    Contenu du témoignage.

    Returns:
        [{'stars': '★★★★★', 'name': 'Nom Prénom', 'text_html': '<p>Contenu...</p>'}]
    """
    if not value:
        return []

    parts = re.split(r'^###\s+', value.strip(), flags=re.MULTILINE)
    items = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        lines = part.split('\n', 1)
        header = lines[0].strip()
        text_md = lines[1].strip() if len(lines) > 1 else ''
        text_html = markdownify(text_md) if text_md else ''

        # Parse "★★★★★ | Nom Prénom" or just "Nom Prénom"
        if '|' in header:
            stars, name = header.split('|', 1)
            stars = stars.strip()
            name = name.strip()
        else:
            stars = '★★★★★'
            name = header

        items.append({
            'stars': stars,
            'name': name,
            'text_html': mark_safe(text_html),
        })
    return items
