from django import template
from django.utils.safestring import mark_safe
from markdownx.utils import markdownify
import re

register = template.Library()


def convert_furigana(text):
    """
    Convertit différentes syntaxes de furigana en balises HTML <ruby><rt>...</rt></ruby>.
    Prend en charge :
    1. {漢字|かんじ}              -> <ruby>漢字<rt>かんじ</rt></ruby>
    2. {日本語|に|ほん|ご}         -> <ruby>日<rt>に</rt></ruby><ruby>本<rt>ほん</rt></ruby><ruby>語<rt>ご</rt></ruby> (distribution par kanji)
    3. [漢字]{かんじ}              -> <ruby>漢字<rt>かんじ</rt></ruby>
    4. [日本語]{に|ほん|ご}         -> <ruby>日<rt>に</rt></ruby><ruby>本<rt>ほん</rt></ruby><ruby>語<rt>ご</rt></ruby>
    5. ｜漢字《かんじ》             -> <ruby>漢字<rt>かんじ</rt></ruby> (Standard Aozora Bunko avec séparateur | ou ｜)
    6. 漢字《かんじ》              -> <ruby>漢字<rt>かんじ</rt></ruby> (Raccourci kanji + double chevrons 《》)
    """
    if not text:
        return ""

    def _replace_split(base, reading):
        base = base.strip()
        reading = reading.strip()
        if '|' in reading:
            parts = [p.strip() for p in reading.split('|')]
            if len(base) == len(parts):
                return ''.join(f'<ruby>{k}<rt>{r}</rt></ruby>' for k, r in zip(base, parts))
        return f'<ruby>{base}<rt>{reading}</rt></ruby>'

    # 1. Syntaxe {kanji|furigana}
    text = re.sub(
        r'\{([^{|\n]+)\|([^{}\n]+)\}',
        lambda m: _replace_split(m.group(1), m.group(2)),
        text
    )

    # 2. Syntaxe [kanji]{furigana}
    text = re.sub(
        r'\[([^\]\n]+)\]\{([^{}\n]+)\}',
        lambda m: _replace_split(m.group(1), m.group(2)),
        text
    )

    # 3. Syntaxe Aozora Bunko avec pipe: ｜base《reading》 ou |base《reading》
    text = re.sub(
        r'[｜\|]([^《\n]+)《([^》\n]+)》',
        lambda m: _replace_split(m.group(1), m.group(2)),
        text
    )

    # 4. Syntaxe directe Kanji《furigana》
    text = re.sub(
        r'([\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff々〆ヵヶ]+)《([^》\n]+)》',
        lambda m: _replace_split(m.group(1), m.group(2)),
        text
    )

    return text


@register.filter(name="furigana")
def furigana_filter(value):
    """Convertit les annotations furigana en HTML sécurisé."""
    if not value:
        return ""
    return mark_safe(convert_furigana(str(value)))


@register.filter(name="md")
def render_markdown(value):
    """Convertit du texte Markdown avec furigana en HTML sécurisé."""
    if not value:
        return ""
    processed = convert_furigana(str(value))
    return mark_safe(markdownify(processed))


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
        question = convert_furigana(lines[0].strip())
        answer_md = lines[1].strip() if len(lines) > 1 else ''
        answer_html = markdownify(convert_furigana(answer_md)) if answer_md else ''
        items.append((mark_safe(question), mark_safe(answer_html)))
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
        text_html = markdownify(convert_furigana(text_md)) if text_md else ''

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
            'name': mark_safe(convert_furigana(name)),
            'text_html': mark_safe(text_html),
        })
    return items
