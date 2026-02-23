from django.core.management.base import BaseCommand
from instructors.models import InstructorPlan


PLANS = [
    {
        'name': 'Starter',
        'slug': 'starter',
        'price': 5000,
        'max_courses': 1,
        'max_modules_per_course': 5,
        'max_lessons_per_course': 10,
        'revenue_percent': 70,
        'description': "Idéal pour tester l'enseignement en ligne avec une première formation.",
        'features': "1 formation\nJusqu'à 5 modules\nJusqu'à 10 leçons\n70% des revenus\nSupport par email",
        'is_featured': False,
        'order': 1,
    },
    {
        'name': 'Pro',
        'slug': 'pro',
        'price': 12000,
        'max_courses': 3,
        'max_modules_per_course': 15,
        'max_lessons_per_course': 50,
        'revenue_percent': 80,
        'description': "Pour les instructeurs sérieux qui veulent développer leur catalogue.",
        'features': "3 formations\nJusqu'à 15 modules / formation\nJusqu'à 50 leçons / formation\n80% des revenus\nSupport prioritaire\nBadge Pro sur le profil",
        'is_featured': True,
        'order': 2,
    },
    {
        'name': 'Expert',
        'slug': 'expert',
        'price': 25000,
        'max_courses': 10,
        'max_modules_per_course': 0,  # illimité
        'max_lessons_per_course': 0,  # illimité
        'revenue_percent': 90,
        'description': "L'offre ultime pour les formateurs professionnels. Aucune limite.",
        'features': "10 formations\nModules illimités\nLeçons illimitées\n90% des revenus\nSupport VIP dédié\nBadge Expert sur le profil\nMise en avant dans le catalogue",
        'is_featured': False,
        'order': 3,
    },
]


class Command(BaseCommand):
    help = "Crée les 3 offres instructeur (Starter, Pro, Expert)"

    def handle(self, *args, **options):
        for data in PLANS:
            plan, created = InstructorPlan.objects.update_or_create(
                slug=data['slug'],
                defaults=data,
            )
            verb = 'Créé' if created else 'Mis à jour'
            self.stdout.write(self.style.SUCCESS(f"  {verb} : {plan}"))

        self.stdout.write(self.style.SUCCESS("\n✓ 3 offres instructeur prêtes."))
