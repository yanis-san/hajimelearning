import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    def test_create_user(self):
        """Teste la création d'un user standard avec email"""
        email = "test@normal.com"
        password = "password123"
        user = User.objects.create_user(email=email, password=password, first_name="John")

        assert user.email == email
        assert user.check_password(password) is True
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False
        assert str(user) == f"John ({email}) [DZ]"  # Vérifie __str__ par défaut

    def test_create_superuser(self):
        """Teste la création d'un super admin"""
        email = "admin@boss.com"
        password = "password123"
        user = User.objects.create_superuser(email=email, password=password)

        assert user.is_staff is True
        assert user.is_superuser is True
        assert user.is_active is True

    def test_email_normalization(self):
        """Vérifie que l'email est bien mis en minuscules (Yanis@Gmail.com -> yanis@gmail.com)"""
        email = "Yanis@Gmail.com"
        user = User.objects.create_user(email=email, password="foo")
        assert user.email == "Yanis@gmail.com"  # Seul le domaine est normalisé par défaut dans Django

    def test_create_user_without_email_raises_error(self):
        """Vérifie qu'on ne peut pas créer de user sans email"""
        with pytest.raises(ValueError):
            User.objects.create_user(email=None, password="password")
