"""Rendu Markdown sécurisé : le HTML produit est nettoyé avant d'être marqué « safe »."""

import nh3
from django.utils.safestring import mark_safe
from markdownx.utils import markdownify

ALLOWED_TAGS = {
    'a',
    'b',
    'blockquote',
    'br',
    'code',
    'del',
    'details',
    'div',
    'em',
    'h1',
    'h2',
    'h3',
    'h4',
    'h5',
    'h6',
    'hr',
    'i',
    'img',
    'kbd',
    'li',
    'mark',
    'ol',
    'p',
    'pre',
    'rp',
    'rt',
    'ruby',
    's',
    'span',
    'strong',
    'sub',
    'summary',
    'sup',
    'table',
    'tbody',
    'td',
    'tfoot',
    'th',
    'thead',
    'tr',
    'u',
    'ul',
}
ALLOWED_ATTRIBUTES = {
    '*': {'class', 'id'},
    'a': {'href', 'title'},
    'img': {'src', 'alt', 'title', 'width', 'height'},
    'td': {'colspan', 'rowspan', 'align'},
    'th': {'colspan', 'rowspan', 'align'},
}
ALLOWED_URL_SCHEMES = {'http', 'https', 'mailto'}


def sanitize_html(html):
    """Supprime scripts, gestionnaires d'évènements et URL dangereuses (javascript:, data:…)."""
    return nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes=ALLOWED_URL_SCHEMES,
        link_rel='noopener noreferrer',
    )


def render_markdown(text):
    """Markdown → HTML nettoyé (chaîne simple). Utilisé aussi par markdownx pour son aperçu."""
    return sanitize_html(markdownify(text))


def render_markdown_safe(text):
    """Markdown → HTML nettoyé, marqué `safe` pour les templates."""
    return mark_safe(render_markdown(text))  # noqa: S308 — nettoyé par nh3
