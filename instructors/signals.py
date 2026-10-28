from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import InstructorProfile, InstructorRequest


@receiver(post_save, sender=InstructorRequest)
def create_instructor_profile_on_approval(sender, instance, **kwargs):
    """
    Quand une demande est approuvée, créer (ou réactiver) le profil instructeur.
    Les limites sont snapshotées depuis le plan au moment de l'approbation.
    """
    if instance.status != InstructorRequest.Status.APPROVED:
        return

    plan = instance.plan
    profile, created = InstructorProfile.objects.update_or_create(
        user=instance.user,
        defaults={
            'plan': plan,
            'max_courses': plan.max_courses,
            'max_modules_per_course': plan.max_modules_per_course,
            'max_lessons_per_course': plan.max_lessons_per_course,
            'revenue_percent': plan.revenue_percent,
            'is_active': True,
        },
    )
