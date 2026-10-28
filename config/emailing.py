"""
Envoi d'e-mails HTML « transactionnels » : gabarit de marque, version texte, jamais d'exception.

Un e-mail = un gabarit `templates/emails/<nom>.html` écrit avec les composants `<c-email.*>`
(styles en ligne : exigés par les clients de messagerie). La version texte est générée à partir du HTML.
Un échec d'envoi est journalisé mais ne remonte jamais : il ne doit pas casser l'action de l'utilisateur.
"""

import html
import logging
import re
from dataclasses import dataclass, field

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

SUBJECT_PREFIX = '[Hajime Learning] '


def absolute_url(path):
    """URL absolue du site pour un chemin (les liens d'un e-mail doivent être complets)."""
    return f'{settings.SITE_URL}{path}'


@dataclass
class EmailContent:
    """Description d'un e-mail prêt à être envoyé (séparée de l'envoi pour pouvoir le prévisualiser)."""

    to: list
    subject: str
    template: str
    context: dict = field(default_factory=dict)
    reply_to: list = field(default_factory=list)
    attachments: list = field(default_factory=list)  # [(nom, contenu, mimetype)]


def base_context():
    """Variables de marque (aussi fournies aux e-mails d'allauth par le context processor `branding`)."""
    return {'site_name': 'Hajime Learning', 'site_url': settings.SITE_URL, 'support_email': settings.CONTACT_EMAIL}


def render_html(content):
    """HTML final de l'e-mail (aussi utilisé par la prévisualisation de développement)."""
    context = {**base_context(), **content.context, 'subject': content.subject}
    return render_to_string(f'emails/{content.template}.html', context)


def html_to_text(markup):
    """Version texte brut d'un e-mail HTML : les liens deviennent « texte : adresse »."""
    text = re.sub(r'(?is)<(style|head|title)[^>]*>.*?</\1>', '', markup)
    text = re.sub(r'(?is)<div[^>]*display\s*:\s*none[^>]*>.*?</div>', '', text)  # pré-en-tête caché

    def link(match):
        url, label = match.group(1), re.sub(r'<[^>]+>', '', match.group(2)).strip()
        if url.startswith('mailto:'):
            url = url[len('mailto:') :].split('?')[0]
        return f'{label} : {url}' if label and label != url else url

    text = re.sub(r'(?is)<a\s[^>]*href="([^"]+)"[^>]*>(.*?)</a>', link, text)
    text = re.sub(r'(?i)<br\s*/?>', '\n', text)
    text = re.sub(r'(?i)</(p|h[1-6]|tr|div|table|li)>', '\n\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    lines = [' '.join(line.split()) for line in text.splitlines()]
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(lines)).strip() + '\n'


def send_email(content):
    """Envoie l'e-mail (HTML + texte). Retourne True si accepté par le serveur ; ne lève jamais d'exception."""
    recipients = [address for address in content.to if address]
    if not recipients:
        return False
    try:
        markup = render_html(content)
        message = EmailMultiAlternatives(
            subject=SUBJECT_PREFIX + content.subject,
            body=html_to_text(markup),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients,
            reply_to=content.reply_to or None,
        )
        message.attach_alternative(markup, 'text/html')
        for name, data, mimetype in content.attachments:
            message.attach(name, data, mimetype)
        message.send(fail_silently=False)
    except Exception:
        logger.exception("Échec d'envoi de l'e-mail « %s » à %s", content.template, recipients)
        return False
    return True
