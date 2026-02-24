import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.http import HttpResponse
from django.views.decorators.http import require_POST

from courses.models import Course
from .models import AccessRequest, ActivationCode, Coupon, Enrollment, user_has_access
from .forms import AccessRequestForm, CodeActivationForm
from .utils import generate_receipt_pdf

logger = logging.getLogger(__name__)

@require_POST
def validate_coupon(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    code_input = request.POST.get('promo_code', '').strip()
    logger.debug("Validate coupon: code='%s'", code_input)

    context = {'course': course}

    try:
        coupon = Coupon.objects.get(code__iexact=code_input)

        if not coupon.is_valid:
            logger.debug("Coupon '%s' found but invalid.", coupon.code)
            context['error'] = "Ce code promo a expiré ou n'est pas encore actif."
            context['success'] = False
        else:
            logger.debug("Coupon '%s' valid, applying discount.", coupon.code)
            remise = (course.price * coupon.discount_percent) / 100
            new_price = course.price - remise

            context['new_price'] = int(new_price)
            context['coupon'] = coupon
            context['success'] = True

    except Coupon.DoesNotExist:
        logger.debug("Coupon code '%s' not found.", code_input)
        context['error'] = "Code promo inconnu."
        context['success'] = False

    return render(request, 'access/partials/price_display.html', context)


@login_required
@transaction.atomic # <--- SÉCURITÉ 1 : Tout ou rien
def request_course_access(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if user_has_access(request.user, course):
        messages.info(request, "Vous avez déjà accès.")
        return redirect('course_detail', course_slug=course.slug)

    # Gestion de la demande existante (Reset si rejetée)
    existing_req = AccessRequest.objects.filter(student=request.user, course=course).first()
    
    if existing_req and existing_req.status == 'PENDING':
        return render(request, 'access/request_pending.html', {'course': course})

    if existing_req and existing_req.status == 'REJECTED':
        proof_form = AccessRequestForm(instance=existing_req)
    else:
        proof_form = AccessRequestForm()
        
    code_form = CodeActivationForm()

    if request.method == 'POST':
        
        # --- CAS A : PAIEMENT PREUVE ---
        if 'submit_proof' in request.POST:
            if existing_req and existing_req.status == 'REJECTED':
                proof_form = AccessRequestForm(request.POST, request.FILES, instance=existing_req)
            else:
                proof_form = AccessRequestForm(request.POST, request.FILES)

            if proof_form.is_valid():
                # On vérifie encore une fois le doublon au dernier moment
                # (Sauf si on update une rejetée)
                if not existing_req and AccessRequest.objects.filter(student=request.user, course=course).exists():
                     messages.warning(request, "Une demande existe déjà.")
                     return redirect('course_detail', course_slug=course.slug)

                req = proof_form.save(commit=False)
                req.student = request.user
                req.course = course
                req.status = 'PENDING'
                req.admin_note = "" 
                
                # Gestion Coupon
                coupon_id = request.POST.get('valid_coupon_id')
                req.final_price = course.price 

                if coupon_id:
                    try:
                        # On verrouille le coupon aussi au cas où
                        coupon = Coupon.objects.select_for_update().get(id=coupon_id)
                        if coupon.is_valid:
                            req.applied_coupon = coupon
                            remise = (course.price * coupon.discount_percent) / 100
                            req.final_price = course.price - remise
                    except Coupon.DoesNotExist:
                        pass
                
                req.save()
                return render(request, 'access/request_success.html', {'course': course})

        # --- CAS B : CODE ACTIVATION (Anti-Banane) ---
        elif 'submit_code' in request.POST:
            code_form = CodeActivationForm(request.POST)
            if code_form.is_valid():
                code_input = code_form.cleaned_data['code'].strip()
                try:
                    # SÉCURITÉ 2 : select_for_update()
                    # Ça dit à la base de données : "Bloque cette ligne tant que je n'ai pas fini"
                    # Si quelqu'un d'autre essaie de lire ce code en même temps, il doit attendre.
                    activation = ActivationCode.objects.select_for_update().get(code=code_input)
                    
                    if activation.course != course:
                        messages.error(request, "Code valide mais pour un autre cours.")
                    elif activation.is_used:
                        messages.error(request, "Ce code a DÉJÀ été utilisé.")
                    else:
                        activation.is_used = True
                        activation.used_by = request.user
                        activation.used_at = timezone.now()
                        activation.save()
                        
                        # Nettoyage si demande existante
                        if existing_req:
                            existing_req.delete()
                            
                        messages.success(request, "Accès débloqué !")
                        return redirect('course_detail', course_slug=course.slug)
                        
                except ActivationCode.DoesNotExist:
                    messages.error(request, "Code invalide.")

    return render(request, 'access/request_form.html', {
        'proof_form': proof_form,
        'code_form': code_form,
        'course': course
    })


@login_required
def enroll_free_course(request, course_id):
    """Inscription à un cours gratuit."""
    course = get_object_or_404(Course, id=course_id, price=0, is_published=True)

    if user_has_access(request.user, course):
        messages.info(request, "Vous êtes déjà inscrit à ce cours.")
        return redirect('course_detail', course_slug=course.slug)

    Enrollment.objects.get_or_create(student=request.user, course=course)
    messages.success(request, f"Vous êtes maintenant inscrit à « {course.title} » !")
    return redirect('course_detail', course_slug=course.slug)


@login_required
def download_receipt(request, request_id):
    # On récupère la demande (ou 404 si elle n'existe pas)
    access_req = get_object_or_404(AccessRequest, id=request_id)
    
    # SÉCURITÉ : C'est bien mon reçu ?
    if access_req.student != request.user:
        return redirect('user_dashboard')
        
    # Génération du PDF
    pdf_content = generate_receipt_pdf(access_req)
    
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Recu_{access_req.id}.pdf"'
    return response