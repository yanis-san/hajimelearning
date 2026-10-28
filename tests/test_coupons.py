from datetime import timedelta

import pytest
from django.utils import timezone

from access.models import Coupon


@pytest.mark.django_db
class TestCouponLogic:
    def test_coupon_calculation(self):
        """Teste si -20% sur 5000 DA donne bien 4000 DA"""
        # On n'a pas besoin de créer un cours en BDD pour tester des maths,
        # mais on teste la logique qu'on utilise dans la vue.
        price = 5000
        percent = 20
        remise = (price * percent) / 100
        new_price = price - remise
        assert new_price == 4000

    def test_coupon_is_valid_standard(self):
        """Un coupon actif sans date est valide"""
        coupon = Coupon.objects.create(code="TEST20", discount_percent=20, is_active=True)
        assert coupon.is_valid is True

    def test_coupon_expired(self):
        """Un coupon dont la date de fin est passée doit être invalide"""
        yesterday = timezone.now() - timedelta(days=1)
        coupon = Coupon.objects.create(
            code="EXPIRED",
            discount_percent=20,
            valid_until=yesterday,  # Périmé hier
        )
        assert coupon.is_valid is False

    def test_coupon_future(self):
        """Un coupon qui commence demain ne doit pas marcher aujourd'hui"""
        tomorrow = timezone.now() + timedelta(days=1)
        coupon = Coupon.objects.create(
            code="FUTUR",
            discount_percent=20,
            valid_from=tomorrow,  # Commence demain
        )
        assert coupon.is_valid is False

    def test_coupon_disabled(self):
        """Un coupon désactivé manuellement ne doit pas marcher"""
        coupon = Coupon.objects.create(
            code="OFF",
            discount_percent=20,
            is_active=False,  # Décoché dans l'admin
        )
        assert coupon.is_valid is False
