from config.pdf import render_pdf


def generate_receipt_pdf(access_request):
    """Génère le PDF du reçu et retourne les bytes."""
    return render_pdf('access/receipt_pdf.html', {'request': access_request})
