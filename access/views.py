from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from courses.models import Course
from django.db import transaction
from .models import AccessRequest, ActivationCode, Coupon, user_has_access
from .forms import AccessRequestForm, CodeActivationForm
from django.http import HttpResponse
from .utils import generate_receipt_pdf

def validate_coupon(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # On récupère ce que tu as tapé et on enlève les espaces autour
    code_input = request.POST.get('promo_code', '').strip()
    
    # --- DEBUG : Regarde ton terminal quand tu tapes ---
    print(f"🔍 Test Code Promo : Reçu='{code_input}'")
    
    context = {'course': course}

    try:
        # CORRECTION ICI : 'code__iexact' ignore les majuscules/minuscules
        coupon = Coupon.objects.get(code__iexact=code_input)
        
        print(f"✅ Trouvé en base : '{coupon.code}'") # Debug

        # Vérification validité (Dates + Actif)
        if not coupon.is_valid:
            print("❌ Code trouvé mais invalide (Date ou Inactif)")
            context['error'] = "Ce code promo a expiré ou n'est pas encore actif."
            context['success'] = False
        else:
            print("💰 Code valide ! Application de la réduction.")
            remise = (course.price * coupon.discount_percent) / 100
            new_price = course.price - remise
            
            context['new_price'] = int(new_price)
            context['coupon'] = coupon
            context['success'] = True
            
    except Coupon.DoesNotExist:
        print("❌ Code introuvable dans la base de données.")
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