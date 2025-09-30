from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.crypto import get_random_string
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import time
from django.db import transaction
from .services import EmailService
import logging


# Custom User Manager
class UserManager(BaseUserManager):
    def create_user(self, email, matricule, first_name, last_name, password=None, **extra_fields):
        """
        Crée et sauvegarde un utilisateur avec email, matricule et mot de passe donnés.
        Si aucun mot de passe n'est fourni, un mot de passe aléatoire est généré.
        """
        if not email:
            raise ValueError('L\'email est obligatoire')
        if not matricule:
            raise ValueError('Le matricule est obligatoire')
        if not first_name or not last_name:
            raise ValueError('Le nom et le prénom sont obligatoires')

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            matricule=matricule,
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )
        
        generated_password = None
        # Générer un mot de passe aléatoire si aucun n'est fourni
        if not password:
            generated_password = get_random_string(12)
            password = generated_password
        
        user.set_password(password)
        user.save(using=self._db)
        
        # Stocker temporairement le mot de passe généré en clair pour l'affichage
        if generated_password:
            user._password_generated = generated_password
        
        # Envoyer l'email de bienvenue si un mot de passe a été généré
        if generated_password:
            try:
                EmailService.send_welcome_email(user, generated_password)
            except Exception as e:
                # Log l'erreur mais ne pas faire échouer la création de l'utilisateur
                logger = logging.getLogger(__name__)
                logger.error(f"Erreur lors de l'envoi de l'email de bienvenue: {str(e)}")
        
        return user

    def create_superuser(self, email, matricule, first_name, last_name, password=None, **extra_fields):
        """
        Crée et sauvegarde un superutilisateur avec email, matricule et mot de passe donnés.
        """
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Le superutilisateur doit avoir is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Le superutilisateur doit avoir is_superuser=True.')

        user = self.create_user(email, matricule, first_name, last_name, password, **extra_fields)
        user.password_last_changed = timezone.now()
        user.save(using=self._db)
        return user
    
    def create_user_by_admin(self, admin_user, email, matricule, first_name, last_name, password=None, **extra_fields):
        """
        Crée un utilisateur par un administrateur avec traçabilité
        """
        if not admin_user.can_manage_users():
            raise ValueError('Seuls les administrateurs peuvent créer des utilisateurs')
        
        extra_fields['created_by'] = admin_user
        extra_fields['password_change_required'] = True  # Force le changement à la première connexion
        
        return self.create_user(email, matricule, first_name, last_name, password, **extra_fields)


# Custom User Model for Personnel Management
class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('admin', 'Administrateur'),
        ('superviseur', 'Superviseur'),
        ('agent', 'Agent'),
    )
    
    # Validators
    phone_validator = RegexValidator(
        # Le numéro de téléphone doit contenir 9 chiffres et doit commencer par un 6
        regex=r'^(6)\d{8}$',
        message="Le numéro de téléphone doit contenir 9 chiffres et doit commencer par un 6"
    )
    
    matricule_validator = RegexValidator(
        regex=r'^[A-Z0-9]{3,20}$',
        message="Le matricule doit contenir entre 3 et 20 caractères alphanumériques en majuscules"
    )
    
    # Fields
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='agent')
    matricule = models.CharField(
        max_length=20, 
        unique=True, 
        validators=[matricule_validator],
        help_text="Code unique d'identification du personnel"
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    profession = models.CharField(max_length=50)
    fonction = models.CharField(max_length=50, blank=True, null=True)
    telephone = models.CharField(
        max_length=15, 
        unique=True, 
        validators=[phone_validator]
    )
    email = models.EmailField(unique=True, max_length=100)

    # photo de profil
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        null=True,
        blank=True,
        verbose_name="Photo de profil"
    )
    
    # Adresse et contacts d'urgence
    adresse = models.TextField(
        blank=True,
        verbose_name="Adresse",
        help_text="Adresse complète de l'utilisateur"
    )
    
    # Premier contact d'urgence
    nom_urg1 = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Nom du contact d'urgence 1"
    )
    prenom_urg1 = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Prénom du contact d'urgence 1"
    )
    telephone_urg1 = models.CharField(
        max_length=15,
        blank=True,
        validators=[phone_validator],
        verbose_name="Téléphone du contact d'urgence 1"
    )
    
    # Deuxième contact d'urgence
    nom_urg2 = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Nom du contact d'urgence 2"
    )
    prenom_urg2 = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Prénom du contact d'urgence 2"
    )
    telephone_urg2 = models.CharField(
        max_length=15,
        blank=True,
        validators=[phone_validator],
        verbose_name="Téléphone du contact d'urgence 2"
    )
    
    # System fields for authentication and permissions
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="Désignez si cet utilisateur doit être traité comme actif. "
                  "Décochez plutôt que de supprimer les comptes."
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name="Statut équipe",
        help_text="Désigne si l'utilisateur peut se connecter au site d'administration."
    )
    is_superuser = models.BooleanField(
        default=False,
        verbose_name="Statut superutilisateur",
        help_text="Désigne que cet utilisateur a toutes les permissions sans les assigner explicitement."
    )
    date_joined = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date d'inscription"
    )
    last_login = models.DateTimeField(
        blank=True, 
        null=True,
        verbose_name="Dernière connexion"
    )
    
    # Security fields
    failed_login_attempts = models.PositiveIntegerField(
        default=0,
        verbose_name="Tentatives de connexion échouées"
    )
    account_locked_until = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Compte verrouillé jusqu'à"
    )
    password_change_required = models.BooleanField(
        default=False,
        verbose_name="Changement de mot de passe requis"
    )
    password_last_changed = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Dernière modification du mot de passe"
    )
    
    # Additional profile fields
    created_by = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_users',
        verbose_name="Créé par"
    )
    last_modified_by = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='modified_users',
        verbose_name="Dernière modification par"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Notes administratives",
        help_text="Notes internes pour les administrateurs"
    )
    
    # Configuration for AbstractBaseUser
    USERNAME_FIELD = 'email'  # Utilise l'email pour l'authentification
    REQUIRED_FIELDS = ['matricule', 'first_name', 'last_name', 'telephone', 'profession']
    
    objects = UserManager()
    
    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['first_name', 'last_name']
    
    def __str__(self):
        return f"{self.role}: {self.first_name} {self.last_name} - {self.matricule}"
    
    def has_perm(self, perm, obj=None):
        """L'utilisateur a-t-il une permission spécifique?"""
        if not self.is_active:
            return False
        if self.is_account_locked():
            return False
        return self.is_superuser or self.role == 'admin'
    
    def has_module_perms(self, app_label):
        """L'utilisateur a-t-il des permissions pour voir l'app `app_label`?"""
        if not self.is_active:
            return False
        if self.is_account_locked():
            return False
        return self.is_superuser or self.role == 'admin'
    
    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'
    
    def get_short_name(self):
        return self.last_name
    
    def is_account_locked(self):
        """Vérifie si le compte est temporairement verrouillé"""
        if self.account_locked_until:
            if timezone.now() < self.account_locked_until:
                return True
            else:
                # Déverrouiller automatiquement le compte si la période est expirée
                # Déverrouillage automatique
                self.account_locked_until = None
                self.failed_login_attempts = 0
                self.save(update_fields=['account_locked_until', 'failed_login_attempts'])
        return False
            
    def generate_password_reset_token(self):
        """Génère un token pour la réinitialisation de mot de passe"""
        return default_token_generator.make_token(self)
    
    def get_password_reset_uid(self):
        """Génère l'UID pour la réinitialisation de mot de passe"""
        return urlsafe_base64_encode(force_bytes(self.pk))
    
    def deactivate_user(self, admin_user, reason=""):
        """Désactive un utilisateur avec traçabilité"""
        if not admin_user.can_manage_users():
            raise ValueError('Seuls les administrateurs peuvent désactiver des utilisateurs')
        
        self.is_active = False
        self.last_modified_by = admin_user
        if reason:
            self.notes = f"{self.notes}\n[{timezone.now()}] Désactivé par {admin_user.name}: {reason}"
        self.save()
    
    def activate_user(self, admin_user, reason=""):
        """Active un utilisateur avec traçabilité"""
        if not admin_user.can_manage_users():
            raise ValueError('Seuls les administrateurs peuvent activer des utilisateurs')
        
        self.is_active = True
        self.last_modified_by = admin_user
        self.account_locked_until = None
        self.failed_login_attempts = 0
        if reason:
            self.notes = f"{self.notes}\n[{timezone.now()}] Activé par {admin_user.get_full_name()}: {reason}"
        self.save()
    
    def lock_account(self, duration_hours=24):
        """Verrouille le compte pour une durée spécifiée"""
        from datetime import timedelta
        self.account_locked_until = timezone.now() + timedelta(hours=duration_hours)
        self.save(update_fields=['account_locked_until'])
    
    def unlock_account(self):
        """Déverrouille le compte manuellement"""
        self.account_locked_until = None
        self.failed_login_attempts = 0
        self.save(update_fields=['account_locked_until', 'failed_login_attempts'])
    
    def increment_failed_login(self):
        """Incrémente le compteur de tentatives échouées"""
        current_attempts = self.failed_login_attempts or 0
        self.failed_login_attempts = current_attempts + 1
        if self.failed_login_attempts >= 5:  # Verrouillage après 5 tentatives
            self.lock_account()
        else:
            self.save(update_fields=['failed_login_attempts'])
    
    def reset_failed_login(self):
        """Remet à zéro le compteur de tentatives échouées"""
        if self.failed_login_attempts > 0:
            self.failed_login_attempts = 0
            self.save(update_fields=['failed_login_attempts'])
    
    def can_manage_users(self):
        """Vérifie si l'utilisateur peut gérer d'autres utilisateurs"""
        return self.is_active and (self.role == 'admin' or self.role == 'superviseur') and not self.is_account_locked()
    
    def can_access_data(self, data_type='read'):
        """Vérifie les permissions d'accès aux données selon le rôle"""
        if not self.is_active or self.is_account_locked():
            return False
        
        if self.role == 'admin':
            return True
        elif self.role == 'superviseur':
            # Gestionnaire des adhérents : lecture et saisie seulement
            return data_type in ['read', 'create', 'update_own']
        elif self.role == 'agent':
            # Agent de collecte : lecture seulement
            return data_type in ['read']
        
        return False
    
    def require_password_change(self):
        """Force le changement de mot de passe à la prochaine connexion"""
        self.password_change_required = True
        self.save(update_fields=['password_change_required'])
    
    def set_password(self, raw_password):
        """Override pour traquer les changements de mot de passe"""
        super().set_password(raw_password)
        self.password_last_changed = timezone.now()
        self.password_change_required = False
        self.failed_login_attempts = 0
        self.account_locked_until = None


# Modèle pour le suivi des sessions utilisateurs
class UserSession(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name="Utilisateur"
    )
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField(verbose_name="Adresse IP")
    user_agent = models.TextField(verbose_name="Navigateur")
    login_time = models.DateTimeField(auto_now_add=True, verbose_name="Heure de connexion")
    last_activity = models.DateTimeField(auto_now=True, verbose_name="Dernière activité")
    is_active = models.BooleanField(default=True, verbose_name="Session active")
    
    class Meta:
        verbose_name = 'Session Utilisateur'
        verbose_name_plural = 'Sessions Utilisateurs'
        ordering = ['-login_time']
    
    def __str__(self):
        return f"Session de {self.user} - {self.login_time}"


# Modèle pour l'historique des actions utilisateurs (audit trail)
class UserActionLog(models.Model):
    ACTION_CHOICES = (
        ('login', 'Connexion'),
        ('logout', 'Déconnexion'),
        ('password_change', 'Changement de mot de passe'),
        ('password_reset', 'Réinitialisation de mot de passe'),
        ('account_locked', 'Compte verrouillé'),
        ('account_unlocked', 'Compte déverrouillé'),
        ('user_created', 'Utilisateur créé'),
        ('user_modified', 'Utilisateur modifié'),
        ('user_deactivated', 'Utilisateur désactivé'),
        ('user_activated', 'Utilisateur activé'),
        ('data_access', 'Accès aux données'),
        ('data_modification', 'Modification des données'),
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='action_logs',
        verbose_name="Utilisateur"
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name="Action"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Horodatage"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="Adresse IP"
    )
    success = models.BooleanField(
        default=True,
        verbose_name="Succès"
    )
    
    class Meta:
        verbose_name = 'Journal des Actions'
        verbose_name_plural = 'Journaux des Actions'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]
    
    def __str__(self):
        status = "✓" if self.success else "✗"
        return f"{status} {self.user} - {self.action} - {self.timestamp}"


# Category Model
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom de la catégorie")
    description = models.TextField(verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Catégorie'
        verbose_name_plural = 'Catégories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


# Organization Model
class Organization(models.Model):
    identifiant = models.IntegerField(
        unique=True, 
        verbose_name="Identifiant de l'organisation",
        editable=False
    )
    name = models.CharField(max_length=150, verbose_name="Nom de l'organisation")
    monthly_revenue = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Chiffre d'affaires mensuel",
        help_text="En devise locale"
    )
    address = models.TextField(verbose_name="Adresse")
    creation_date = models.DateField(
        null=True, 
        blank=True,
        verbose_name="Date de création"
    )
    phone = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        validators=[User.phone_validator],
        verbose_name="Téléphone"
    )
    whatsapp = models.CharField(
        max_length=20, 
        blank=True,
        validators=[User.phone_validator],
        verbose_name="WhatsApp"
    )
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE,
        related_name='organizations',
        verbose_name="Catégorie"
    )
    number_personnel = models.PositiveIntegerField(
        default=1,
        verbose_name="Nombre de personne",
        help_text="Nombre total de personne dans l'organisation"
    )
    infos_annexes = models.TextField(
        blank=True,
        verbose_name="Informations annexes",
        help_text="Informations supplémentaires sur l'organisation"
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_organizations',
        verbose_name="Créé par"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Organisation'
        verbose_name_plural = 'Organisations'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.identifiant:
            last = Organization.objects.order_by('-identifiant').first()
            self.identifiant = (last.identifiant + 1) if last and last.identifiant >= 100 else 100
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.identifiant})"
    
    def get_adherents_count(self):
        """Retourne le nombre d'adhérents de cette organisation"""
        return self.adherents.count()


# Adherent Model
class Adherent(models.Model):
    TYPE_CHOICES = (
        ('physical', 'Personne Physique'),
        ('legal', 'Personne Morale'),
    )
    
    # Personal Information
    identifiant = models.CharField(
        max_length=20, 
        unique=True,
        verbose_name="Identifiant unique"
    )
    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    last_name = models.CharField(max_length=100, verbose_name="Nom")
    birth_date = models.DateField(
        null=True, 
        blank=True,
        verbose_name="Date de naissance"
    )
    type_adherent = models.CharField(
        max_length=20, 
        choices=TYPE_CHOICES,
        verbose_name="Type d'adhérent"
    )
    
    # Contact Information
    commune = models.TextField(verbose_name="Commune")
    quartier = models.TextField(verbose_name="Quartier")
    secteur = models.TextField(verbose_name="Secteur")

    phone1 = models.CharField(
        max_length=15,
        unique=True,
        validators=[User.phone_validator],
        verbose_name="Téléphone principal"
    )
    phone2 = models.CharField(
        max_length=15, 
        blank=True,
        validators=[User.phone_validator],
        verbose_name="Téléphone secondaire"
    )

    num_urgence1 = models.CharField(
        max_length=15, 
        blank=True,
        validators=[User.phone_validator],
        verbose_name="Numéro d'urgence"
    )
    num_urgence2 = models.CharField(
        max_length=15, 
        blank=True,
        validators=[User.phone_validator],
        verbose_name="Numéro d'urgence 2"
    )
    
    email = models.EmailField(
        max_length=100, 
        blank=True,
        verbose_name="Email"
    )

    medical_info = models.TextField(
        blank=True,
        verbose_name="Informations médicales",
        help_text="Informations médicales importantes pour l'adhérent"
    )

    formation_pro = models.TextField(
        blank=True,
        verbose_name="Formation professionnelle",
        help_text="Détails sur la formation professionnelle de l'adhérent"
    )

    distinction = models.TextField(
        blank=True,
        verbose_name="Distinction",
        help_text="Distinctions ou récompenses reçues par l'adhérent"
    )
    centres_interet = models.ManyToManyField(
        'ReferenceValue',
        blank=True,
        related_name='adherents_centres_interet',
        verbose_name="Centres d'intérêt",
        help_text="Centres d'intérêt de l'adhérent (sélection multiple possible)"
    )
    langues = models.TextField(
        blank=True,
        verbose_name="Langues parlées",
        help_text="Langues que l'adhérent parle"
    )
    
    # Membership Information
    join_date = models.DateField(verbose_name="Date d'adhésion")
    organisation = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='adherents',
        verbose_name="Organisation"
    )
    activity_name = models.CharField(
        max_length=200, 
        verbose_name="Nom de l'activité",
        help_text="Activité principale de l'adhérent",
        blank=True,
        null=True
    )
    badge_validity = models.DateField(
        verbose_name="Validité du badge",
        help_text="Date de validité du badge d'adhérent",
        blank=True,
        null=True
    )

    # Media Files
    profile_picture = models.ImageField(
        upload_to='profile_pics/', 
        null=True, 
        blank=True,
        verbose_name="Photo de profil"
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_adherents',
        verbose_name="Créé par"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Adhérent'
        verbose_name_plural = 'Adhérents'
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['identifiant']),
            models.Index(fields=['join_date']),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.identifiant})"

    def clean(self):
        """Validation personnalisée"""
        super().clean()
        # Générer automatiquement l'identifiant si pas fourni
        if not self.identifiant:
            self.generate_identifiant()

    def save(self, *args, **kwargs):
        """Override save pour générer l'identifiant automatiquement"""
        if not self.identifiant:
            self.generate_identifiant()
        super().save(*args, **kwargs)

    def generate_identifiant(self):
        """Génère automatiquement l'identifiant basé sur l'organisation et le rang"""
        if not self.organisation:
            return
            
        # Utiliser une transaction pour éviter les conditions de course
        with transaction.atomic():
            # Trouver le prochain numéro disponible pour cette organisation
            # Exclure l'instance actuelle si elle a déjà un ID
            queryset = Adherent.objects.filter(organisation=self.organisation)
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)
                
            existing_identifiants = queryset.values_list('identifiant', flat=True)
            
            # Extraire les numéros existants
            existing_numbers = []
            for identifiant in existing_identifiants:
                try:
                    # Format attendu: "XXX-YYY" où XXX est l'ID org et YYY le numéro
                    parts = identifiant.split('-')
                    if len(parts) == 2 and parts[0] == f"{self.organisation.identifiant:03d}":
                        existing_numbers.append(int(parts[1]))
                except (ValueError, IndexError):
                    continue
            
            # Trouver le prochain numéro disponible
            next_number = 1
            if existing_numbers:
                next_number = max(existing_numbers) + 1
            
            # Générer l'identifiant et vérifier qu'il n'existe pas déjà
            max_attempts = 100
            attempt = 0
            while attempt < max_attempts:
                identifiant = f"{self.organisation.identifiant:03d}-{next_number:03d}"
                # Vérifier que cet identifiant n'existe pas déjà
                if not Adherent.objects.filter(identifiant=identifiant).exists():
                    self.identifiant = identifiant
                    return
                next_number += 1
                attempt += 1
            
            # En cas d'échec, utiliser un timestamp
            timestamp = int(time.time()) % 10000
            self.identifiant = f"{self.organisation.identifiant:03d}-{timestamp:04d}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_age_membership(self):
        """Calcule l'âge d'adhésion en jours"""
        if self.join_date:
            from datetime import date
            return (date.today() - self.join_date).days
        return 0
    
    def get_age(self):
        """Calcule l'âge de l'adhérent en années"""
        if self.birth_date:
            from datetime import date
            return (date.today() - self.birth_date).days // 365
        return None
    
    def is_badge_valid(self):
        if self.badge_validity is None:
            return False
        return self.badge_validity > timezone.now().date()


# Updated Interaction Model
class Interaction(models.Model):
    STATUS_CHOICES = (
        ('in_progress', 'En cours'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé'),
    )
    identifiant = models.IntegerField(
        unique=True,
        verbose_name="Identifiant",
        editable=False
    )
    date_enregistrement = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'enregistrement"
    )
    auteur = models.ForeignKey(
        'User',
        null=True,
        on_delete=models.SET_NULL,
        related_name='interactions_created',
        verbose_name="Auteur"
    )
    personnel = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='interactions',
        verbose_name="Personnel"
    )
    adherent = models.ForeignKey(
        'Adherent',
        on_delete=models.CASCADE,
        related_name='interactions',
        verbose_name="Adhérent"
    )
    report = models.TextField(verbose_name="Rapport")
    due_date = models.DateTimeField(verbose_name="Date d'échéance")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='in_progress',
        verbose_name="Statut"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mis à jour le")

    class Meta:
        verbose_name = 'Interaction'
        verbose_name_plural = 'Interactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['identifiant']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Interaction {self.identifiant} - {self.adherent.full_name}"

    def clean(self):
        """Validation personnalisée"""
        super().clean()
        if self.due_date and self.due_date < timezone.now():
            raise ValidationError({
                'due_date': 'La date d\'échéance ne peut pas être dans le passé.'
            })
    
    def save(self, *args, **kwargs):
        if not self.identifiant:
            last = Interaction.objects.order_by('-identifiant').first()
            self.identifiant = (last.identifiant + 1) if last and int(last.identifiant) >= 100 else 100
        super().save(*args, **kwargs)


# Badge Model
class Badge(models.Model):
    STATUS_CHOICES = (
        ('active', 'Actif'),
        ('expired', 'Expiré'),
        ('revoked', 'Révoqué'),
    )
    
    adherent = models.ForeignKey(
        Adherent,
        on_delete=models.CASCADE,
        related_name='badges',
        verbose_name="Adhérent"
    )
    badge_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Numéro de badge"
    )
    qr_code = models.ImageField(
        upload_to='badge_qr_codes/',
        null=True,
        blank=True,
        verbose_name="QR Code"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name="Statut"
    )
    issued_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'émission"
    )
    issued_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issued_badges',
        verbose_name="Émis par"
    )
    activity_name = models.CharField(max_length=100, verbose_name="Nom de l'activité")
    badge_validity = models.DateField(verbose_name="Validité du badge")
    activity_image = models.ImageField(
        upload_to='activity_images/', 
        null=True, 
        blank=True,
        verbose_name="Image de l'activité"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Notes"
    )
    
    class Meta:
        verbose_name = 'Badge'
        verbose_name_plural = 'Badges'
        ordering = ['-issued_date']
        indexes = [
            models.Index(fields=['badge_number']),
            models.Index(fields=['status']),
            models.Index(fields=['issued_date']),
        ]
    
    def __str__(self):
        return f"Badge {self.badge_number} - {self.adherent.full_name}"
    
    def save(self, *args, **kwargs):
        if not self.badge_number:
            self.badge_number = self.generate_badge_number()
        super().save(*args, **kwargs)
    
    def generate_badge_number(self):
        import random
        import string
        while True:
            year = timezone.now().year
            random_part = ''.join(random.choices(string.digits, k=5))
            badge_number = f"BADGE-{year}-{random_part}"
            if not Badge.objects.filter(badge_number=badge_number).exists():
                return badge_number
    @property
    def is_valid(self):
        from datetime import date
        return (
            self.status == 'active' and 
            self.adherent.badge_validity is not None and
            self.adherent.badge_validity >= date.today()
        )
    def revoke(self, reason="", revoked_by=None):
        self.status = 'revoked'
        if reason:
            self.notes = f"Révoqué le {timezone.now().strftime('%d/%m/%Y')} par {revoked_by}: {reason}"
        self.save()
    def reactivate(self, reactivated_by=None):
        self.status = 'active'
        if reactivated_by:
            self.notes = f"Réactivé le {timezone.now().strftime('%d/%m/%Y')} par {reactivated_by}"
        self.save()


class UserObjective(models.Model):
    """Modèle pour les objectifs assignés aux utilisateurs par les superviseurs"""
    STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminé'),
        ('failed', 'Échoué'),
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='objectives',
        verbose_name="Utilisateur"
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_objectives',
        verbose_name="Assigné par"
    )
    objective_type = models.CharField(
        max_length=20,
        choices=[
            ('organizations', 'Nombre d\'organisations'),
            ('adherents', 'Nombre d\'adhérents'),
            ('interactions', 'Nombre d\'interactions'),
        ],
        verbose_name="Type d'objectif"
    )
    target_value = models.PositiveIntegerField(verbose_name="Valeur cible")
    current_value = models.PositiveIntegerField(default=0, verbose_name="Valeur actuelle")
    base_value = models.PositiveIntegerField(default=0, verbose_name="Valeur de base")
    deadline = models.DateField(verbose_name="Date limite")
    description = models.TextField(blank=True, verbose_name="Description")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Statut"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Objectif Utilisateur'
        verbose_name_plural = 'Objectifs Utilisateurs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Objectif {self.objective_type} pour {self.user.get_full_name()}"
    
    def save(self, *args, **kwargs):
        """Override save pour calculer automatiquement la valeur de base et la valeur cible"""
        if not self.pk:  # Nouvel objectif
            self.calculate_base_value()
            # La valeur cible devient : base_value + target_value (ce qui était saisi)
            base_val = self.base_value or 0
            target_val = self.target_value or 0
            self.target_value = base_val + target_val
        super().save(*args, **kwargs)
    
    def calculate_base_value(self):
        """Calcule la valeur de base (ce qui existait déjà avant l'objectif)"""
        if self.objective_type == 'organizations':
            self.base_value = Organization.objects.filter(created_by=self.user).count()
        elif self.objective_type == 'adherents':
            self.base_value = Adherent.objects.filter(created_by=self.user).count()
        elif self.objective_type == 'interactions':
            self.base_value = Interaction.objects.filter(auteur=self.user).count()
    
    def update_progress(self):
        """Met à jour la progression de l'objectif"""
        total_count = 0
        if self.objective_type == 'organizations':
            total_count = Organization.objects.filter(created_by=self.user).count()
        elif self.objective_type == 'adherents':
            total_count = Adherent.objects.filter(created_by=self.user).count()
        elif self.objective_type == 'interactions':
            total_count = Interaction.objects.filter(auteur=self.user).count()
        
        # La valeur actuelle est ce qui a été créé après l'assignation de l'objectif
        base_val = self.base_value or 0
        self.current_value = max(0, total_count - base_val)
        
        # Mettre à jour le statut
        target_increment = (self.target_value or 0) - base_val
        if self.current_value >= target_increment:
            self.status = 'completed'
        elif timezone.now().date() > self.deadline:
            self.status = 'failed'
        elif self.current_value > 0:
            self.status = 'in_progress'
        else:
            self.status = 'pending'
        
        self.save()
    
    @classmethod
    def update_all_objectives(cls):
        """Met à jour tous les objectifs actifs"""
        objectives = cls.objects.filter(status__in=['pending', 'in_progress'])
        updated_count = 0
        
        for objective in objectives:
            old_status = objective.status
            old_value = objective.current_value
            
            objective.update_progress()
            
            # Vérifier si quelque chose a changé
            if (objective.status != old_status or objective.current_value != old_value):
                updated_count += 1
        
        return updated_count
    
    @classmethod
    def update_objectives_for_user(cls, user):
        """Met à jour tous les objectifs d'un utilisateur spécifique"""
        objectives = cls.objects.filter(
            user=user,
            status__in=['pending', 'in_progress']
        )
        updated_count = 0
        
        for objective in objectives:
            old_status = objective.status
            old_value = objective.current_value
            
            objective.update_progress()
            
            # Vérifier si quelque chose a changé
            if (objective.status != old_status or objective.current_value != old_value):
                updated_count += 1
        
        return updated_count
    
    @property
    def progress_percentage(self):
        """Calcule le pourcentage de progression"""
        base_val = self.base_value or 0
        target_val = self.target_value or 0
        target_increment = target_val - base_val
        if target_increment == 0:
            return 0
        return min(100, (self.current_value / target_increment) * 100)
    
    @property
    def is_overdue(self):
        """Vérifie si l'objectif est en retard"""
        from datetime import date
        return date.today() > self.deadline and self.status != 'completed'
    
    @property
    def target_increment(self):
        """Retourne l'incrément cible (ce qui doit être ajouté)"""
        base_val = self.base_value or 0
        target_val = self.target_value or 0
        return target_val - base_val

class SupervisorStats(models.Model):
    """Modèle pour stocker les statistiques des superviseurs"""
    supervisor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='supervisor_stats',
        verbose_name="Superviseur"
    )
    agent = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='agent_stats',
        verbose_name="Agent"
    )
    organizations_count = models.PositiveIntegerField(default=0, verbose_name="Nombre d'organisations")
    categories_count = models.PositiveIntegerField(default=0, verbose_name="Nombre de catégories")
    adherents_count = models.PositiveIntegerField(default=0, verbose_name="Nombre d'adhérents")
    interactions_count = models.PositiveIntegerField(default=0, verbose_name="Nombre d'interactions")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")
    
    class Meta:
        verbose_name = 'Statistique Superviseur'
        verbose_name_plural = 'Statistiques Superviseurs'
        unique_together = ['supervisor', 'agent']
        ordering = ['-last_updated']
    
    def __str__(self):
        return f"Stats de {self.agent.get_full_name()} pour {self.supervisor.get_full_name()}"
    
    def update_stats(self):
        """Met à jour les statistiques de l'agent"""
        self.organizations_count = Organization.objects.filter(created_by=self.agent).count()
        self.categories_count = Category.objects.filter(
            organizations__created_by=self.agent
        ).distinct().count()
        self.adherents_count = Adherent.objects.filter(created_by=self.agent).count()
        self.interactions_count = Interaction.objects.filter(personnel=self.agent).count()
        self.save()


# Signaux pour mettre à jour automatiquement les objectifs
@receiver(post_save, sender=Organization)
def update_objectives_on_organization_save(sender, instance, created, **kwargs):
    """Met à jour les objectifs quand une organisation est créée ou modifiée"""
    if created and instance.created_by:
        # Mettre à jour tous les objectifs de type 'organizations' pour cet utilisateur
        objectives = UserObjective.objects.filter(
            user=instance.created_by,
            objective_type='organizations',
            status__in=['pending', 'in_progress']
        )
        for objective in objectives:
            objective.update_progress()

@receiver(post_delete, sender=Organization)
def update_objectives_on_organization_delete(sender, instance, **kwargs):
    """Met à jour les objectifs quand une organisation est supprimée"""
    if instance.created_by:
        objectives = UserObjective.objects.filter(
            user=instance.created_by,
            objective_type='organizations',
            status__in=['pending', 'in_progress']
        )
        for objective in objectives:
            objective.update_progress()

@receiver(post_save, sender=Adherent)
def update_objectives_on_adherent_save(sender, instance, created, **kwargs):
    """Met à jour les objectifs quand un adhérent est créé ou modifié"""
    if created and instance.created_by:
        # Mettre à jour tous les objectifs de type 'adherents' pour le créateur de l'organisation
        objectives = UserObjective.objects.filter(
            user=instance.created_by,
            objective_type='adherents',
            status__in=['pending', 'in_progress']
        )
        for objective in objectives:
            objective.update_progress()

@receiver(post_delete, sender=Adherent)
def update_objectives_on_adherent_delete(sender, instance, **kwargs):
    """Met à jour les objectifs quand un adhérent est supprimé"""
    if instance.created_by:
        objectives = UserObjective.objects.filter(
            user=instance.created_by,
            objective_type='adherents',
            status__in=['pending', 'in_progress']
        )
        for objective in objectives:
            objective.update_progress()

@receiver(post_save, sender=Interaction)
def update_objectives_on_interaction_save(sender, instance, created, **kwargs):
    """Met à jour les objectifs quand une interaction est créée ou modifiée"""
    if created and instance.personnel:
        # Mettre à jour tous les objectifs de type 'interactions' pour cet utilisateur
        objectives = UserObjective.objects.filter(
            user=instance.personnel,
            objective_type='interactions',
            status__in=['pending', 'in_progress']
        )
        for objective in objectives:
            objective.update_progress()

@receiver(post_delete, sender=Interaction)
def update_objectives_on_interaction_delete(sender, instance, **kwargs):
    """Met à jour les objectifs quand une interaction est supprimée"""
    if instance.personnel:
        objectives = UserObjective.objects.filter(
            user=instance.personnel,
            objective_type='interactions',
            status__in=['pending', 'in_progress']
        )
        for objective in objectives:
            objective.update_progress()


# ==================== MODÈLES POUR LES PARAMÈTRES DE L'APPLICATION ====================

class RolePermission(models.Model):
    """Modèle pour définir les permissions spécifiques à chaque rôle"""
    PERMISSION_CHOICES = [
        # Gestion des utilisateurs
        ('user_create', 'Créer des utilisateurs'),
        ('user_edit', 'Modifier des utilisateurs'),
        ('user_delete', 'Supprimer des utilisateurs'),
        ('user_view', 'Voir les utilisateurs'),
        ('user_activate', 'Activer/Désactiver des utilisateurs'),
        
        # Gestion des adhérents
        ('adherent_create', 'Créer des adhérents'),
        ('adherent_edit', 'Modifier des adhérents'),
        ('adherent_delete', 'Supprimer des adhérents'),
        ('adherent_view', 'Voir les adhérents'),
        
        # Gestion des organisations
        ('organization_create', 'Créer des organisations'),
        ('organization_edit', 'Modifier des organisations'),
        ('organization_delete', 'Supprimer des organisations'),
        ('organization_view', 'Voir les organisations'),
        
        # Gestion des interactions
        ('interaction_create', 'Créer des interactions'),
        ('interaction_edit', 'Modifier des interactions'),
        ('interaction_delete', 'Supprimer des interactions'),
        ('interaction_view', 'Voir les interactions'),
        
        # Gestion des badges
        ('badge_create', 'Créer des badges'),
        ('badge_edit', 'Modifier des badges'),
        ('badge_delete', 'Supprimer des badges'),
        ('badge_view', 'Voir les badges'),
        ('badge_revoke', 'Révoquer des badges'),
        
        # Gestion des objectifs
        ('objective_create', 'Créer des objectifs'),
        ('objective_edit', 'Modifier des objectifs'),
        ('objective_delete', 'Supprimer des objectifs'),
        ('objective_view', 'Voir les objectifs'),
        
        # Gestion des paramètres
        ('settings_view', 'Voir les paramètres'),
        ('settings_edit', 'Modifier les paramètres'),
        ('settings_roles', 'Gérer les rôles'),
        ('settings_references', 'Gérer les valeurs de référence'),
        
        # Rapports et statistiques
        ('reports_view', 'Voir les rapports'),
        ('reports_export', 'Exporter les rapports'),
        ('stats_view', 'Voir les statistiques'),
        
        # Administration système
        ('system_admin', 'Administration système'),
        ('data_backup', 'Sauvegarde des données'),
        ('data_restore', 'Restauration des données'),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=User.ROLE_CHOICES,
        verbose_name="Rôle"
    )
    permission = models.CharField(
        max_length=50,
        choices=PERMISSION_CHOICES,
        verbose_name="Permission"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Permission de Rôle'
        verbose_name_plural = 'Permissions de Rôles'
        unique_together = ['role', 'permission']
        ordering = ['role', 'permission']
    
    def __str__(self):
        role_display = dict(User.ROLE_CHOICES).get(self.role, self.role)
        permission_display = dict(self.PERMISSION_CHOICES).get(self.permission, self.permission)
        return f"{role_display} - {permission_display}"


class ReferenceValue(models.Model):
    """Modèle pour gérer les valeurs de référence (listes déroulantes)"""
    CATEGORY_CHOICES = [
        ('interaction_status', 'Statuts d\'interaction'),
        ('profession_types', 'Types de profession'),
        ('adherent_types', 'Types d\'adhérent'),
        ('organization_categories', 'Catégories d\'organisation'),
        ('badge_status', 'Statuts de badge'),
        ('objective_status', 'Statuts d\'objectif'),
        ('user_roles', 'Rôles utilisateur'),
        ('phone_types', 'Types de téléphone'),
        ('emergency_types', 'Types d\'urgence'),
        ('medical_info_types', 'Types d\'informations médicales'),
        ('formation_types', 'Types de formation'),
        ('distinction_types', 'Types de distinction'),
        ('language_types', 'Types de langue'),
        ('activity_types', 'Types d\'activité'),
        ('centres_d_interet', 'Centres d\'intérêt'),
    ]
    
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        verbose_name="Catégorie"
    )
    code = models.CharField(
        max_length=20,
        verbose_name="Code"
    )
    label = models.CharField(
        max_length=100,
        verbose_name="Libellé"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordre de tri"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name="Valeur par défaut"
    )
    is_system = models.BooleanField(
        default=False,
        verbose_name="Valeur système"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_references',
        verbose_name="Créé par"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Valeur de Référence'
        verbose_name_plural = 'Valeurs de Référence'
        unique_together = ['category', 'code']
        ordering = ['category', 'sort_order', 'label']
    
    def __str__(self):
        category_display = dict(self.CATEGORY_CHOICES).get(self.category, self.category)
        return f"{category_display} - {self.label}"
    
    def save(self, *args, **kwargs):
        # Si c'est la valeur par défaut, désactiver les autres valeurs par défaut de la même catégorie
        if self.is_default:
            ReferenceValue.objects.filter(
                category=self.category,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
    
    @classmethod
    def get_choices_for_category(cls, category):
        """Retourne les choix pour une catégorie donnée"""
        return cls.objects.filter(
            category=category,
            is_active=True
        ).order_by('sort_order', 'label').values_list('code', 'label')


class GeneralParameter(models.Model):
    """Modèle pour les paramètres généraux de l'application"""
    PARAMETER_CHOICES = [
        # Informations de l'organisation
        ('organization_name', 'Nom de l\'organisation'),
        ('organization_address', 'Adresse de l\'organisation'),
        ('organization_phone', 'Téléphone de l\'organisation'),
        ('organization_email', 'Email de l\'organisation'),
        ('organization_website', 'Site web de l\'organisation'),
        ('organization_logo', 'Logo de l\'organisation'),
        
        # Configuration système
        ('timezone', 'Fuseau horaire'),
        ('date_format', 'Format de date'),
        ('time_format', 'Format d\'heure'),
        ('language', 'Langue par défaut'),
        ('currency', 'Devise'),
        ('currency_symbol', 'Symbole de devise'),
        
        # Configuration email
        ('email_host', 'Serveur SMTP'),
        ('email_port', 'Port SMTP'),
        ('email_username', 'Nom d\'utilisateur email'),
        ('email_password', 'Mot de passe email'),
        ('email_use_tls', 'Utiliser TLS'),
        ('email_from_address', 'Adresse email d\'expédition'),
        ('email_from_name', 'Nom d\'expédition email'),
        
        # Configuration sécurité
        ('password_min_length', 'Longueur minimale des mots de passe'),
        ('password_require_special', 'Mots de passe avec caractères spéciaux'),
        ('session_timeout', 'Délai d\'expiration de session (minutes)'),
        ('max_login_attempts', 'Nombre maximum de tentatives de connexion'),
        ('account_lockout_duration', 'Durée de verrouillage de compte (heures)'),
        
        # Configuration interface
        ('items_per_page', 'Nombre d\'éléments par page'),
        ('enable_notifications', 'Activer les notifications'),
        ('enable_audit_log', 'Activer le journal d\'audit'),
        ('enable_backup', 'Activer la sauvegarde automatique'),
        ('backup_frequency', 'Fréquence de sauvegarde (jours)'),
        
        # Configuration métier
        ('default_interaction_duration', 'Durée par défaut des interactions (heures)'),
        ('interaction_reminder_days', 'Rappel d\'interaction (jours avant échéance)'),
        ('badge_validity_days', 'Validité par défaut des badges (jours)'),
        ('max_organizations_per_agent', 'Nombre maximum d\'organisations par agent'),
        ('max_adherents_per_organization', 'Nombre maximum d\'adhérents par organisation'),
    ]
    
    PARAMETER_TYPES = [
        ('text', 'Texte'),
        ('number', 'Nombre'),
        ('boolean', 'Booléen'),
        ('email', 'Email'),
        ('url', 'URL'),
        ('file', 'Fichier'),
        ('select', 'Liste déroulante'),
        ('textarea', 'Zone de texte'),
        ('date', 'Date'),
        ('time', 'Heure'),
        ('datetime', 'Date et heure'),
    ]
    
    parameter_key = models.CharField(
        max_length=50,
        choices=PARAMETER_CHOICES,
        unique=True,
        verbose_name="Clé du paramètre"
    )
    parameter_type = models.CharField(
        max_length=20,
        choices=PARAMETER_TYPES,
        verbose_name="Type de paramètre"
    )
    value = models.TextField(
        verbose_name="Valeur"
    )
    default_value = models.TextField(
        blank=True,
        verbose_name="Valeur par défaut"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    is_required = models.BooleanField(
        default=False,
        verbose_name="Obligatoire"
    )
    is_system = models.BooleanField(
        default=False,
        verbose_name="Paramètre système"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_parameters',
        verbose_name="Créé par"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Paramètre Général'
        verbose_name_plural = 'Paramètres Généraux'
        ordering = ['parameter_key']
    
    def __str__(self):
        parameter_display = dict(self.PARAMETER_CHOICES).get(self.parameter_key, self.parameter_key)
        return f"{parameter_display}: {self.value}"
    
    def get_typed_value(self):
        """Retourne la valeur avec le bon type"""
        value_str = str(self.value)
        if self.parameter_type == 'boolean':
            return value_str.lower() in ('true', '1', 'yes', 'on')
        elif self.parameter_type == 'number':
            try:
                return int(value_str) if '.' not in value_str else float(value_str)
            except ValueError:
                return 0
        elif self.parameter_type == 'date':
            try:
                from datetime import datetime
                return datetime.strptime(value_str, '%Y-%m-%d').date()
            except ValueError:
                return None
        elif self.parameter_type == 'time':
            try:
                from datetime import datetime
                return datetime.strptime(value_str, '%H:%M:%S').time()
            except ValueError:
                return None
        elif self.parameter_type == 'datetime':
            try:
                from datetime import datetime
                return datetime.strptime(value_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return None
        else:
            return value_str
    
    @classmethod
    def get_value(cls, key, default=None):
        """Récupère la valeur d'un paramètre"""
        try:
            param = cls.objects.get(parameter_key=key)
            return param.get_typed_value()
        except cls.DoesNotExist:
            return default
    
    @classmethod
    def set_value(cls, key, value, created_by=None):
        """Définit la valeur d'un paramètre"""
        param, created = cls.objects.get_or_create(
            parameter_key=key,
            defaults={
                'parameter_type': 'text',
                'value': str(value),
                'created_by': created_by
            }
        )
        if not created:
            param.value = str(value)
            param.save()
        return param


class SystemLog(models.Model):
    """Modèle pour le journal système (audit trail)"""
    LOG_LEVELS = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Information'),
        ('WARNING', 'Avertissement'),
        ('ERROR', 'Erreur'),
        ('CRITICAL', 'Critique'),
    ]
    
    LOG_CATEGORIES = [
        ('user_management', 'Gestion des utilisateurs'),
        ('data_management', 'Gestion des données'),
        ('system_config', 'Configuration système'),
        ('security', 'Sécurité'),
        ('backup', 'Sauvegarde'),
        ('email', 'Email'),
        ('api', 'API'),
        ('general', 'Général'),
    ]
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Horodatage"
    )
    level = models.CharField(
        max_length=10,
        choices=LOG_LEVELS,
        verbose_name="Niveau"
    )
    category = models.CharField(
        max_length=20,
        choices=LOG_CATEGORIES,
        verbose_name="Catégorie"
    )
    message = models.TextField(
        verbose_name="Message"
    )
    details = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Détails"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Utilisateur"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="Adresse IP"
    )
    user_agent = models.TextField(
        blank=True,
        null=True,
        verbose_name="User Agent"
    )
    
    class Meta:
        verbose_name = 'Journal Système'
        verbose_name_plural = 'Journaux Système'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['level']),
            models.Index(fields=['category']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        message_preview = str(self.message)[:50] if self.message else ""
        return f"[{self.level}] {self.category}: {message_preview}"
    
    @classmethod
    def log(cls, level, category, message, user=None, details=None, ip_address=None, user_agent=None):
        """Méthode utilitaire pour créer une entrée de journal"""
        return cls.objects.create(
            level=level,
            category=category,
            message=message,
            user=user,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent or ''
        )

