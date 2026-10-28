"""Rendu PDF (xhtml2pdf) des templates HTML, feuilles de style statiques comprises."""
import logging
from io import BytesIO

from django.contrib.staticfiles import finders
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def _resolve_static(uri, rel):
    """Convertit une URL /static/... en chemin disque pour xhtml2pdf."""
    from django.conf import settings

    if uri.startswith(settings.STATIC_URL):
        return finders.find(uri[len(settings.STATIC_URL):]) or uri
    return uri


def render_pdf(template_name, context):
    """Rend un template en PDF et retourne les octets (b"" en cas d'erreur)."""
    from xhtml2pdf import pisa

    html = render_to_string(template_name, context)
    buffer = BytesIO()
    status = pisa.CreatePDF(html, dest=buffer, link_callback=_resolve_static)
    if status.err:
        logger.error("Échec de génération PDF pour %s", template_name)
        return b""
    return buffer.getvalue()
