from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from config import throttle
from courses.models import Course

from .forms import AccessRequestForm, CodeActivationForm
from .models import AccessRequest, Enrollment, user_has_access
from .services import AccessError, find_valid_coupon, redeem_activation_code, submit_payment_proof
from .utils import generate_receipt_pdf


@require_POST
def validate_coupon(request, course_id):
    """Aperçu du prix avec un code promo (HTMX)."""
    course = get_object_or_404(Course, id=course_id)
    context = {'course': course, 'success': False}

    if not throttle.allow(request, 'coupon', limit=10, window=60):
        context['error'] = "Trop de tentatives. Réessayez dans une minute."
        return render(request, 'access/partials/price_display.html', context)

    try:
        coupon = find_valid_coupon(request.POST.get('promo_code', ''))
    except AccessError as exc:
        context['error'] = str(exc)
    else:
        context.update(success=True, coupon=coupon, new_price=int(coupon.discounted_price(course.price)))

    return render(request, 'access/partials/price_display.html', context)


@login_required
def request_course_access(request, course_id):
    """Demande d'accès à un cours payant : preuve de paiement ou code d'activation."""
    course = get_object_or_404(Course, id=course_id, is_published=True)

    if user_has_access(request.user, course):
        messages.info(request, "Vous avez déjà accès.")
        return redirect('course_detail', course_slug=course.slug)

    existing_req = AccessRequest.objects.filter(student=request.user, course=course).first()
    if existing_req and existing_req.status == AccessRequest.Status.PENDING:
        return render(request, 'access/request_pending.html', {'course': course})

    # Une demande refusée est rouverte : le formulaire repart de l'existante
    retry = existing_req if existing_req and existing_req.status == AccessRequest.Status.REJECTED else None
    proof_form = AccessRequestForm(instance=retry)
    code_form = CodeActivationForm()

    if request.method == 'POST' and 'submit_proof' in request.POST:
        proof_form = AccessRequestForm(request.POST, request.FILES, instance=retry)
        if proof_form.is_valid():
            try:
                submit_payment_proof(proof_form, request.user, course, request.POST.get('valid_coupon_id'))
            except AccessError as exc:
                messages.warning(request, str(exc))
                return redirect('course_detail', course_slug=course.slug)
            return render(request, 'access/request_success.html', {'course': course})

    elif request.method == 'POST' and 'submit_code' in request.POST:
        code_form = CodeActivationForm(request.POST)
        if not throttle.allow(request, 'activation-code', limit=5, window=600):
            messages.error(request, "Trop de tentatives. Réessayez dans quelques minutes.")
        elif code_form.is_valid():
            try:
                redeem_activation_code(request.user, course, code_form.cleaned_data['code'])
            except AccessError as exc:
                messages.error(request, str(exc))
            else:
                messages.success(request, "Accès débloqué !")
                return redirect('course_detail', course_slug=course.slug)

    return render(
        request, 'access/request_form.html', {'proof_form': proof_form, 'code_form': code_form, 'course': course}
    )


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
    """Reçu PDF : réservé à l'étudiant concerné, une fois le paiement validé."""
    access_req = get_object_or_404(
        AccessRequest.objects.select_related('course', 'applied_coupon'),
        id=request_id,
        student=request.user,
        status=AccessRequest.Status.APPROVED,
    )
    response = HttpResponse(generate_receipt_pdf(access_req), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Recu_{access_req.id}.pdf"'
    return response
