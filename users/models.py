from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.db import models

# Assure-toi que le fichier validators.py existe bien dans l'app courses
from courses.validators import IMAGE_EXTENSIONS, FileSizeValidator, get_upload_path

from .managers import CustomUserManager


class User(AbstractUser):

    # --- LISTE DES PAYS ---
    class Country(models.TextChoices):
        # Afrique du Nord & Moyen-Orient
        ALGERIA = 'DZ', 'Algérie'
        MOROCCO = 'MA', 'Maroc'
        TUNISIA = 'TN', 'Tunisie'
        EGYPT = 'EG', 'Égypte'
        SAUDI_ARABIA = 'SA', 'Arabie Saoudite'
        UAE = 'AE', 'Émirats Arabes Unis'
        QATAR = 'QA', 'Qatar'

        # Europe
        FRANCE = 'FR', 'France'
        BELGIUM = 'BE', 'Belgique'
        SWITZERLAND = 'CH', 'Suisse'
        GERMANY = 'DE', 'Allemagne'
        UK = 'GB', 'Royaume-Uni'
        SPAIN = 'ES', 'Espagne'
        ITALY = 'IT', 'Italie'

        # Amériques
        CANADA = 'CA', 'Canada'
        USA = 'US', 'États-Unis'
        BRAZIL = 'BR', 'Brésil'

        # Asie
        CHINA = 'CN', 'Chine'
        JAPAN = 'JP', 'Japon'
        TURKEY = 'TR', 'Turquie'
        MALAYSIA = 'MY', 'Malaisie'
        INDONESIA = 'ID', 'Indonésie'

        # Afrique (Autres)
        SENEGAL = 'SN', 'Sénégal'
        IVORY_COAST = 'CI', 'Côte d\'Ivoire'
        MALI = 'ML', 'Mali'

        # Reste du monde
        OTHER = 'OTHER', 'Autre pays'

    class Gender(models.TextChoices):
        MALE = 'M', 'Homme'
        FEMALE = 'F', 'Femme'

    # --- CHAMPS DE BASE ---
    username = None
    email = models.EmailField('adresse email', unique=True)

    # --- PHOTO DE PROFIL (AVATAR) ---
    avatar = models.ImageField(
        "Photo de profil",
        upload_to=get_upload_path, # Renommage sécurisé
        blank=True, null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=IMAGE_EXTENSIONS),
            FileSizeValidator(max_mb=2) # Max 2 Mo
        ]
    )

    # --- INFOS ---
    phone_number = models.CharField("Téléphone", max_length=20, blank=True, help_text="Format: +213...")
    address = models.CharField("Adresse", max_length=255, blank=True)
    city = models.CharField("Ville", max_length=100, blank=True)

    country = models.CharField(
        "Pays",
        max_length=5,
        choices=Country.choices,
        default=Country.ALGERIA
    )

    # --- INFOS DÉMOGRAPHIQUES ---
    gender = models.CharField("Sexe", max_length=1, choices=Gender.choices, blank=True, null=True)
    birth_date = models.DateField("Date de naissance", blank=True, null=True)

    # --- CONFIG DJANGO ---
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        country_code = self.country if self.country else "?"
        return f"{full_name} ({self.email}) [{country_code}]" if full_name else self.email
