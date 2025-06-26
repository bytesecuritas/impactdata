from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.crypto import get_random_string


# Custom User Manager
class UserManager(BaseUserManager):
    def create_user(self, email, matricule, name, password=None, **extra_fields):
        """
        Crée et sauvegarde un utilisateur avec email, matricule et mot de passe donnés.
        Si aucun mot de passe n'est fourni, un mot de passe aléatoire est généré.
        """
        if not email:
            raise ValueError('L\'email est obligatoire')
        if not matricule:
            raise ValueError('Le matricule est obligatoire')
        if not name:
            raise ValueError('Le nom est obligatoire')

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            matricule=matricule,
            name=name,
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
        
        return user

    def create_superuser(self, email, matricule, name, password=None, **extra_fields):
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

        user = self.create_user(email, matricule, name, password, **extra_fields)
        user.password_last_changed = timezone.now()
        user.save(using=self._db)
        return user
    
    def create_user_by_admin(self, admin_user, email, matricule, name, password=None, **extra_fields):
        """
        Crée un utilisateur par un administrateur avec traçabilité
        """
        if not admin_user.can_manage_users():
            raise ValueError('Seuls les administrateurs peuvent créer des utilisateurs')
        
        extra_fields['created_by'] = admin_user
        extra_fields['password_change_required'] = True  # Force le changement à la première connexion
        
        return self.create_user(email, matricule, name, password, **extra_fields)


# Custom User Model for Personnel Management
class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('admin', 'Administrateur'),
        ('superviseur', 'Gestionnaire des adhérents'),
        ('agent', 'Agent de collecte'),
    )
    
    # Validators
    phone_validator = RegexValidator(
        regex=r'^\+?1?\d{8,15}$',
        message="Le numéro de téléphone doit contenir entre 8 et 15 chiffres et peut commencer par +"
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
    name = models.CharField(max_length=100)
    profession = models.CharField(max_length=50)
    telephone = models.CharField(
        max_length=15, 
        unique=True, 
        validators=[phone_validator]
    )
    email = models.EmailField(unique=True, max_length=100)
    
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
    REQUIRED_FIELDS = ['matricule', 'name', 'telephone', 'profession']
    
    objects = UserManager()
    
    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['name']
    
    def __str__(self):
        return f"Personnel: {self.name} ({self.matricule})"
    
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
        return self.name
    
    def get_short_name(self):
        return self.name
    
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
            self.notes = f"{self.notes}\n[{timezone.now()}] Activé par {admin_user.name}: {reason}"
        self.save()


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
        return f"Session de {self.user.name} - {self.login_time}"


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
        return f"{status} {self.user.name} - {self.get_action_display()} - {self.timestamp}"

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
        self.failed_login_attempts += 1
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
        return self.is_active and self.role == 'admin' and not self.is_account_locked()
    
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
    identifiant = models.CharField(
        max_length=10, 
        unique=True, 
        verbose_name="Identifiant de l'organisation",
        default="ORG0000001"
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
        validators=[User.phone_validator],
        verbose_name="Téléphone"
    )
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE,  # Changé de CASCADE à PROTECT pour éviter les suppressions accidentelles
        related_name='organizations',
        verbose_name="Catégorie"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Organisation'
        verbose_name_plural = 'Organisations'
        ordering = ['name']
    
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
    first_name = models.CharField(max_length=200, verbose_name="Prénom")  # Corrigé
    last_name = models.CharField(max_length=200, verbose_name="Nom")     # Corrigé
    type_adherent = models.CharField(
        max_length=20, 
        choices=TYPE_CHOICES,
        verbose_name="Type d'adhérent"
    )
    
    # Contact Information
    address = models.TextField(verbose_name="Adresse")
    phone1 = models.CharField(
        max_length=20,
        validators=[User.phone_validator],
        verbose_name="Téléphone principal"
    )
    phone2 = models.CharField(
        max_length=20, 
        blank=True,
        validators=[User.phone_validator],
        verbose_name="Téléphone secondaire"
    )
    
    # Membership Information
    join_date = models.DateField(verbose_name="Date d'adhésion")
    organisation = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='adherents',
        verbose_name="Organisation"
    )
    activity_name = models.CharField(max_length=200, verbose_name="Nom de l'activité")
    badge_validity = models.DateField(verbose_name="Validité du badge")
    
    # Media Files
    profile_picture = models.ImageField(
        upload_to='profile_pics/', 
        null=True, 
        blank=True,
        verbose_name="Photo de profil"
    )
    activity_image = models.ImageField(
        upload_to='activity_images/', 
        null=True, 
        blank=True,
        verbose_name="Image de l'activité"
    )
    
    # System Fields
    barcode = models.CharField(
        max_length=50, 
        null=True, 
        blank=True,
        unique=True,
        verbose_name="Code-barres"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Adhérent'
        verbose_name_plural = 'Adhérents'
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['identifiant']),
            models.Index(fields=['badge_validity']),
            models.Index(fields=['join_date']),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.identifiant})"

    def clean(self):
        """Validation personnalisée"""
        super().clean()
        if self.badge_validity and self.join_date:
            if self.badge_validity < self.join_date:
                raise ValidationError({
                    'badge_validity': 'La validité du badge ne peut pas être antérieure à la date d\'adhésion.'
                })

    def save(self, *args, **kwargs):
        """Override save pour appeler clean()"""
        self.clean()
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        """Retourne le nom complet"""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_badge_valid(self):
        """Vérifie si le badge est encore valide"""
        return self.badge_validity >= timezone.now().date()
    
    def get_age_membership(self):
        """Calcule l'ancienneté de l'adhésion en années"""
        from datetime import date
        today = date.today()
        return today.year - self.join_date.year - ((today.month, today.day) < (self.join_date.month, self.join_date.day))


# Updated Interaction Model
class Interaction(models.Model):
    STATUS_CHOICES = (
        ('in_progress', 'En cours'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé'),
    )
    identifiant = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Identifiant"
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
        """Override save pour générer automatiquement le numéro de badge si nécessaire"""
        if not self.badge_number:
            self.badge_number = self.generate_badge_number()
        super().save(*args, **kwargs)
    
    def generate_badge_number(self):
        """Génère un numéro de badge unique"""
        import random
        import string
        
        while True:
            # Format: BADGE-YYYY-XXXXX (ex: BADGE-2024-12345)
            year = timezone.now().year
            random_part = ''.join(random.choices(string.digits, k=5))
            badge_number = f"BADGE-{year}-{random_part}"
            
            # Vérifier si le numéro existe déjà
            if not Badge.objects.filter(badge_number=badge_number).exists():
                return badge_number
    
    @property
    def is_valid(self):
        """Vérifie si le badge est valide"""
        return (
            self.status == 'active' and 
            self.adherent.badge_validity >= timezone.now().date()
        )
    
    def revoke(self, reason="", revoked_by=None):
        """Révoque le badge"""
        self.status = 'revoked'
        if reason:
            self.notes = f"Révoqué le {timezone.now().strftime('%d/%m/%Y')} par {revoked_by}: {reason}"
        self.save()
    
    def reactivate(self, reactivated_by=None):
        """Réactive le badge"""
        self.status = 'active'
        if reactivated_by:
            self.notes = f"Réactivé le {timezone.now().strftime('%d/%m/%Y')} par {reactivated_by}"
        self.save()

