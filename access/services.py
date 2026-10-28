"""Règles métier de l'accès aux cours : coupons, demandes de paiement, codes d'activation."""

from django.db import transaction
from django.utils import timezone

from .models import AccessRequest, ActivationCode, Coupon


class AccessError(Exception):
    """Erreur métier affichable telle quelle à l'utilisateur."""


def find_valid_coupon(code):
    """Coupon actif correspondant au code saisi (insensible à la casse), sinon AccessError."""
    try:
        coupon = Coupon.objects.get(code__iexact=code.strip())
    except Coupon.DoesNotExist as exc:
        raise AccessError("Code promo inconnu.") from exc
    if not coupon.is_valid:
        raise AccessError("Ce code promo a expiré ou n'est pas encore actif.")
    return coupon


@transaction.atomic
def submit_payment_proof(form, student, course, coupon_id=None):
    """
    Enregistre une demande d'accès avec preuve de paiement.

    `form` est un AccessRequestForm valide (éventuellement lié à une demande refusée à relancer).
    Le prix final est toujours recalculé côté serveur à partir du coupon.
    """
    if form.instance.pk is None and AccessRequest.objects.filter(student=student, course=course).exists():
        raise AccessError("Une demande existe déjà.")

    request = form.save(commit=False)
    request.student = student
    request.course = course
    request.status = AccessRequest.Status.PENDING
    request.admin_note = ""
    request.final_price = course.price
    request.applied_coupon = None

    if coupon_id:
        coupon = Coupon.objects.select_for_update().filter(id=coupon_id).first()
        if coupon and coupon.is_valid:
            request.applied_coupon = coupon
            request.final_price = coupon.discounted_price(course.price)

    request.save()
    return request


@transaction.atomic
def redeem_activation_code(user, course, code):
    """Consomme un code d'activation pour `user`. Lève AccessError si le code est inutilisable."""
    try:
        activation = ActivationCode.objects.select_for_update().get(code=str(code).strip())
    except ActivationCode.DoesNotExist as exc:
        raise AccessError("Code invalide.") from exc

    if activation.course_id != course.id:
        raise AccessError("Code valide mais pour un autre cours.")
    if activation.is_used:
        raise AccessError("Ce code a DÉJÀ été utilisé.")

    activation.is_used = True
    activation.used_by = user
    activation.used_at = timezone.now()
    activation.save()

    # Une demande de paiement antérieure devient sans objet
    AccessRequest.objects.filter(student=user, course=course).delete()
    return activation
