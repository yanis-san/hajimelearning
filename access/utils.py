from django.template.loader import render_to_string
from io import BytesIO


def generate_receipt_pdf(access_request):
    """ Génère le PDF du reçu et retourne les bytes """
    from weasyprint import HTML

    html_string = render_to_string('access/receipt_pdf.html', {
        'request': access_request,
    })
    
    # On génère le PDF en mémoire (RAM)
    pdf_file = BytesIO()
    HTML(string=html_string).write_pdf(target=pdf_file)
    
    # On remet le curseur au début du fichier pour pouvoir le lire
    pdf_file.seek(0)
    return pdf_file.getvalue()