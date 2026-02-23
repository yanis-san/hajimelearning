import pytest
from access.models import user_has_access, AccessRequest, ActivationCode

'''
Sécurité de base : Un étudiant lambda ne peut pas voir un cours payant (refused_by_default).

Super-pouvoir Admin : Toi (l'admin), tu peux tout voir, tout le temps (allowed_for_admin).

Logique Freemium : Si le prix est 0 DA, la porte est ouverte (allowed_if_free).

Paiement CCP : Si tu as cliqué sur "Approved", la porte s'ouvre (allowed_with_approved).

Anti-Fraude : Si l'étudiant a envoyé la preuve mais que tu n'as pas encore validé ("Pending"), la porte reste fermée (refused_with_pending).

Code Cadeau : Si le code d'activation est bon, la porte s'ouvre (allowed_with_activation_code).
'''

# Le marqueur 'django_db' autorise le test à toucher la base de données
@pytest.mark.django_db
class TestAccessLogic:

    def test_access_refused_by_default(self, student, course):
        """ Cas 1 : Un étudiant sans rien n'a pas accès au cours payant """
        assert user_has_access(student, course) is False

    def test_access_allowed_for_admin(self, admin_user, course):
        """ Cas 2 : L'admin a toujours accès """
        assert user_has_access(admin_user, course) is True

    def test_access_allowed_if_free(self, student, free_course):
        """ Cas 3 : Tout le monde a accès à un cours gratuit """
        assert user_has_access(student, free_course) is True

    def test_access_allowed_with_approved_request(self, student, course):
        """ Cas 4 : Accès via paiement validé (CCP) """
        # On simule une demande VALIDÉE
        AccessRequest.objects.create(
            student=student, 
            course=course, 
            status='APPROVED'
        )
        assert user_has_access(student, course) is True

    def test_access_refused_with_pending_request(self, student, course):
        """ Cas 5 : Accès refusé si paiement en attente """
        AccessRequest.objects.create(
            student=student, 
            course=course, 
            status='PENDING'
        )
        assert user_has_access(student, course) is False

    def test_access_allowed_with_activation_code(self, student, course):
        """ Cas 6 : Accès via Code d'activation """
        ActivationCode.objects.create(
            course=course,
            code="PROMO-TEST",
            is_used=True,
            used_by=student
        )
        assert user_has_access(student, course) is True