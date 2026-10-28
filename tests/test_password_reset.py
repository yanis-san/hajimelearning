import re

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse

User = get_user_model()


@pytest.mark.django_db
class TestPasswordResetFlow:
    def test_full_password_reset_cycle(self, client, student):
        """Teste tout le cycle : Demande -> Mail -> Changement -> Login"""

        # 1. DEMANDE DE RESET
        url_request = reverse('account_reset_password')
        response = client.post(url_request, {'email': student.email})
        assert response.status_code == 302  # Redirection vers "Email sent"
        assert len(mail.outbox) == 1

        # 2. EXTRACTION DU LIEN DANS L'EMAIL
        email_body = mail.outbox[0].body
        # On cherche l'URL brute
        search = re.search(r'http://testserver(/accounts/password/reset/key/.+/)', email_body)
        assert search is not None, "Lien de reset introuvable dans le mail"
        reset_url = search.group(1)

        # 3. ACCÈS À LA PAGE DE CHANGEMENT
        response = client.get(reset_url, follow=True)

        assert response.status_code == 200
        assert b"Nouveau mot de passe" in response.content

        if response.redirect_chain:
            final_url = response.redirect_chain[-1][0]
        else:
            final_url = reset_url

        # 4. TENTATIVE AVEC MOT DE PASSE FAIBLE (Doit échouer)
        weak_password = "low"
        response = client.post(
            final_url,
            {
                'password1': weak_password,  # <--- CORRECTION ICI (password1)
                'password2': weak_password,  # <--- CORRECTION ICI (password2)
            },
        )
        assert response.status_code == 200

        # 5. TENTATIVE AVEC MOT DE PASSE FORT (Doit réussir)
        strong_password = "NewPassword123!"
        response = client.post(
            final_url,
            {
                'password1': strong_password,  # <--- CORRECTION ICI (password1)
                'password2': strong_password,  # <--- CORRECTION ICI (password2)
            },
        )

        # Debug en cas d'erreur
        if response.status_code != 302:
            print("Erreurs du formulaire :", response.context['form'].errors)

        # Succès = Redirection (302)
        assert response.status_code == 302

        # 6. VÉRIFICATION FINALE
        student.refresh_from_db()
        assert student.check_password(strong_password) is True
