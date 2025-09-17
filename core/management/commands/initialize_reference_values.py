from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import ReferenceValue, User, Interaction, Badge, UserObjective
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Initialise les valeurs de référence avec les valeurs existantes dans les modèles'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Initialisation des valeurs de référence...'))
        
        with transaction.atomic():
            # Initialiser les statuts d'interaction
            self.initialize_interaction_statuses()
            
            # Initialiser les statuts de badge
            self.initialize_badge_statuses()
            
            # Initialiser les statuts d'objectif
            self.initialize_objective_statuses()
            
            # Initialiser les rôles utilisateur
            self.initialize_user_roles()
            
            # Initialiser les types d'adhérent
            self.initialize_adherent_types()
            
            # Initialiser les types de profession
            self.initialize_profession_types()
            
            # Initialiser les types de téléphone
            self.initialize_phone_types()
            
            # Initialiser les types d'urgence
            self.initialize_emergency_types()
            
            # Initialiser les types d'informations médicales
            self.initialize_medical_info_types()
            
            # Initialiser les types de formation
            self.initialize_formation_types()
            
            # Initialiser les types de distinction
            self.initialize_distinction_types()
            
            # Initialiser les types de langue
            self.initialize_language_types()
            
            # Initialiser les types d'activité
            self.initialize_activity_types()
            
            # Initialiser les catégories d'organisation
            self.initialize_organization_categories()
            
            # Initialiser les centres d'intérêt
            self.initialize_centres_d_interet()
        
        self.stdout.write(self.style.SUCCESS('Initialisation terminée avec succès!'))

    def initialize_interaction_statuses(self):
        """Initialise les statuts d'interaction"""
        self.stdout.write('  - Initialisation des statuts d\'interaction...')
        
        statuses = [
            ('in_progress', 'En cours', 'Interaction en cours de traitement', 1, True, False, True),
            ('completed', 'Terminé', 'Interaction terminée avec succès', 2, True, True, True),
            ('cancelled', 'Annulé', 'Interaction annulée', 3, True, False, True),
        ]
        
        for code, label, description, sort_order, is_active, is_default, is_system in statuses:
            ReferenceValue.objects.get_or_create(
                category='interaction_status',
                code=code,
                defaults={
                    'label': label,
                    'description': description,
                    'sort_order': sort_order,
                    'is_active': is_active,
                    'is_default': is_default,
                    'is_system': is_system,
                }
            )

    def initialize_badge_statuses(self):
        """Initialise les statuts de badge"""
        self.stdout.write('  - Initialisation des statuts de badge...')
        
        statuses = [
            ('active', 'Actif', 'Badge actif et valide', 1, True, True, True),
            ('expired', 'Expiré', 'Badge expiré', 2, True, False, True),
            ('revoked', 'Révoqué', 'Badge révoqué', 3, True, False, True),
        ]
        
        for code, label, description, sort_order, is_active, is_default, is_system in statuses:
            ReferenceValue.objects.get_or_create(
                category='badge_status',
                code=code,
                defaults={
                    'label': label,
                    'description': description,
                    'sort_order': sort_order,
                    'is_active': is_active,
                    'is_default': is_default,
                    'is_system': is_system,
                }
            )

    def initialize_objective_statuses(self):
        """Initialise les statuts d'objectif"""
        self.stdout.write('  - Initialisation des statuts d\'objectif...')
        
        statuses = [
            ('pending', 'En attente', 'Objectif en attente de début', 1, True, True, True),
            ('in_progress', 'En cours', 'Objectif en cours de réalisation', 2, True, False, True),
            ('completed', 'Terminé', 'Objectif terminé avec succès', 3, True, False, True),
            ('failed', 'Échoué', 'Objectif non atteint', 4, True, False, True),
        ]
        
        for code, label, description, sort_order, is_active, is_default, is_system in statuses:
            ReferenceValue.objects.get_or_create(
                category='objective_status',
                code=code,
                defaults={
                    'label': label,
                    'description': description,
                    'sort_order': sort_order,
                    'is_active': is_active,
                    'is_default': is_default,
                    'is_system': is_system,
                }
            )

    def initialize_user_roles(self):
        """Initialise les rôles utilisateur"""
        self.stdout.write('  - Initialisation des rôles utilisateur...')
        
        roles = [
            ('admin', 'Administrateur', 'Accès complet à toutes les fonctionnalités', 1, True, False, True),
            ('superviseur', 'Superviseur', 'Gestion des agents et des données', 2, True, False, True),
            ('agent', 'Agent', 'Saisie et consultation des données', 3, True, True, True),
        ]
        
        for code, label, description, sort_order, is_active, is_default, is_system in roles:
            ReferenceValue.objects.get_or_create(
                category='user_roles',
                code=code,
                defaults={
                    'label': label,
                    'description': description,
                    'sort_order': sort_order,
                    'is_active': is_active,
                    'is_default': is_default,
                    'is_system': is_system,
                }
            )

    def initialize_adherent_types(self):
        """Initialise les types d'adhérent"""
        self.stdout.write('  - Initialisation des types d\'adhérent...')
        
        types = [
            ('physical', 'Personne Physique', 'Adhérent personne physique', 1, True, True, True),
            ('legal', 'Personne Morale', 'Adhérent personne morale', 2, True, False, True),
        ]
        
        for code, label, description, sort_order, is_active, is_default, is_system in types:
            ReferenceValue.objects.get_or_create(
                category='adherent_types',
                code=code,
                defaults={
                    'label': label,
                    'description': description,
                    'sort_order': sort_order,
                    'is_active': is_active,
                    'is_default': is_default,
                    'is_system': is_system,
                }
            )

    def initialize_profession_types(self):
        """Initialise les types de profession"""
        self.stdout.write('  - Initialisation des types de profession...')
        
        professions = [
            ('medecin', 'Médecin', 'Profession médicale', 1, True, False, False),
            ('infirmier', 'Infirmier', 'Profession paramédicale', 2, True, False, False),
            ('enseignant', 'Enseignant', 'Profession d\'enseignement', 3, True, False, False),
            ('commercant', 'Commerçant', 'Profession commerciale', 4, True, False, False),
            ('artisan', 'Artisan', 'Profession artisanale', 5, True, False, False),
            ('fonctionnaire', 'Fonctionnaire', 'Fonction publique', 6, True, False, False),
            ('autre', 'Autre', 'Autre profession', 7, True, True, False),
        ]
        
        for code, label, description, sort_order, is_active, is_default, is_system in professions:
            ReferenceValue.objects.get_or_create(
                category='profession_types',
                code=code,
                defaults={
                    'label': label,
                    'description': description,
                    'sort_order': sort_order,
                    'is_active': is_active,
                    'is_default': is_default,
                    'is_system': is_system,
                }
            )

    def initialize_phone_types(self):
        """Initialise les types de téléphone"""
        self.stdout.write('  - Initialisation des types de téléphone...')
        
        types = [
            ('mobile', 'Mobile', 'Téléphone mobile', 1, True, True, True),
            ('fixe', 'Fixe', 'Téléphone fixe', 2, True, False, True),
            ('bureau', 'Bureau', 'Téléphone de bureau', 3, True, False, True),
        ]
        
        for code, label, description, sort_order, is_active, is_default, is_system in types:
            ReferenceValue.objects.get_or_create(
                category='phone_types',
                code=code,
                defaults={
                    'label': label,
                    'description': description,
                    'sort_order': sort_order,
                    'is_active': is_active,
                    'is_default': is_default,
                    'is_system': is_system,
                }
            )

    def initialize_emergency_types(self):
        """Initialise les types d'urgence"""
        self.stdout.write('  - Initialisation des types d\'urgence...')
        
        types = [
            ('famille', 'Famille', 'Contact familial', 1, True, True, True),
            ('ami', 'Ami', 'Contact amical', 2, True, False, True),
            ('collegue', 'Collègue', 'Contact professionnel', 3, True, False, True),
            ('voisin', 'Voisin', 'Contact de proximité', 4, True, False, True),
        ]
        
        for code, label, description, sort_order, is_active, is_default, is_system in types:
            ReferenceValue.objects.get_or_create(
                category='emergency_types',
                code=code,
                defaults={
                    'label': label,
                    'description': description,
                    'sort_order': sort_order,
                    'is_active': is_active,
                    'is_default': is_default,
                    'is_system': is_system,
                }
            )

    def initialize_medical_info_types(self):
        """Initialise les types d'informations médicales"""
        self.stdout.write('  - Initialisation des types d\'informations médicales...')
        
        types = [
            ('allergie', 'Allergie', 'Allergies connues', 1, True, False, False),
            ('maladie', 'Maladie chronique', 'Maladies chroniques', 2, True, False, False),
            ('medicament', 'Médicament', 'Médicaments en cours', 3, True, False, False),
            ('groupe_sanguin', 'Groupe sanguin', 'Groupe sanguin', 4, True, False, False),
            ('handicap', 'Handicap', 'Handicaps', 5, True, False, False),
            ('aucun', 'Aucun', 'Aucune information médicale particulière', 6, True, True, False),
        ]
        
        for code, label, description, sort_order, is_active, is_default, is_system in types:
            ReferenceValue.objects.get_or_create(
                category='medical_info_types',
                code=code,
                defaults={
                    'label': label,
                    'description': description,
                    'sort_order': sort_order,
                    'is_active': is_active,
                    'is_default': is_default,
                    'is_system': is_system,
                }
            )

    def initialize_formation_types(self):
        """Initialise les types de formation"""
        self.stdout.write('  - Initialisation des types de formation...')
        
        types = [
            ('primaire', 'Primaire', 'Formation primaire', 1, True, False, False),
            ('secondaire', 'Secondaire', 'Formation secondaire', 2, True, False, False),
            ('superieur', 'Supérieur', 'Formation supérieure', 3, True, False, False),
            ('professionnelle', 'Professionnelle', 'Formation professionnelle', 4, True, False, False),
            ('technique', 'Technique', 'Formation technique', 5, True, False, False),
            ('autre', 'Autre', 'Autre type de formation', 6, True, True, False),
        ]
        
        for code, label, description, sort_order, is_active, is_default, is_system in types:
            ReferenceValue.objects.get_or_create(
                category='formation_types',
                code=code,
                defaults={
                    'label': label,
                    'description': description,
                    'sort_order': sort_order,
                    'is_active': is_active,
                    'is_default': is_default,
                    'is_system': is_system,
                }
            )

    def initialize_distinction_types(self):
        """Initialise les types de distinction"""
        self.stdout.write('  - Initialisation des types de distinction...')
        
        types = [
            ('medaille', 'Médaille', 'Médaille ou décoration', 1, True, False, False),
            ('diplome', 'Diplôme', 'Diplôme ou certificat', 2, True, False, False),
            ('recompense', 'Récompense', 'Récompense ou prix', 3, True, False, False),
            ('honneur', 'Honneur', 'Distinction honorifique', 4, True, False, False),
            ('aucune', 'Aucune', 'Aucune distinction particulière', 5, True, True, False),
        ]
        
        for code, label, description, sort_order, is_active, is_default, is_system in types:
            ReferenceValue.objects.get_or_create(
                category='distinction_types',
                code=code,
                defaults={
                    'label': label,
                    'description': description,
                    'sort_order': sort_order,
                    'is_active': is_active,
                    'is_default': is_default,
                    'is_system': is_system,
                }
            )

    def initialize_language_types(self):
        """Initialise les types de langue"""
        self.stdout.write('  - Initialisation des types de langue...')
        
        languages = [
            ('francais', 'Français', 'Langue française', 1, True, True, True),
            ('anglais', 'Anglais', 'Langue anglaise', 2, True, False, True),
            ('espagnol', 'Espagnol', 'Langue espagnole', 3, True, False, True),
            ('allemand', 'Allemand', 'Langue allemande', 4, True, False, True),
            ('italien', 'Italien', 'Langue italienne', 5, True, False, True),
            ('arabe', 'Arabe', 'Langue arabe', 6, True, False, True),
            ('chinois', 'Chinois', 'Langue chinoise', 7, True, False, True),
            ('local', 'Langue locale', 'Langue locale ou dialecte', 8, True, False, True),
        ]
        
        for code, label, description, sort_order, is_active, is_default, is_system in languages:
            ReferenceValue.objects.get_or_create(
                category='language_types',
                code=code,
                defaults={
                    'label': label,
                    'description': description,
                    'sort_order': sort_order,
                    'is_active': is_active,
                    'is_default': is_default,
                    'is_system': is_system,
                }
            )

    def initialize_activity_types(self):
        """Initialise les types d'activité"""
        self.stdout.write('  - Initialisation des types d\'activité...')
        
        activities = [
            ('sante', 'Santé', 'Activité dans le domaine de la santé', 1, True, False, False),
            ('education', 'Éducation', 'Activité dans le domaine de l\'éducation', 2, True, False, False),
            ('commerce', 'Commerce', 'Activité commerciale', 3, True, False, False),
            ('artisanat', 'Artisanat', 'Activité artisanale', 4, True, False, False),
            ('agriculture', 'Agriculture', 'Activité agricole', 5, True, False, False),
            ('services', 'Services', 'Activité de services', 6, True, False, False),
            ('industrie', 'Industrie', 'Activité industrielle', 7, True, False, False),
            ('autre', 'Autre', 'Autre type d\'activité', 8, True, True, False),
        ]
        
        for code, label, description, sort_order, is_active, is_default, is_system in activities:
            ReferenceValue.objects.get_or_create(
                category='activity_types',
                code=code,
                defaults={
                    'label': label,
                    'description': description,
                    'sort_order': sort_order,
                    'is_active': is_active,
                    'is_default': is_default,
                    'is_system': is_system,
                }
            )

    def initialize_organization_categories(self):
        """Initialise les catégories d'organisation"""
        self.stdout.write('  - Initialisation des catégories d\'organisation...')
        
        categories = [
            ('entreprise', 'Entreprise', 'Entreprise privée', 1, True, False, False),
            ('association', 'Association', 'Association à but non lucratif', 2, True, False, False),
            ('ong', 'ONG', 'Organisation non gouvernementale', 3, True, False, False),
            ('institution', 'Institution', 'Institution publique', 4, True, False, False),
            ('cooperative', 'Coopérative', 'Coopérative', 5, True, False, False),
            ('autre', 'Autre', 'Autre type d\'organisation', 6, True, True, False),
        ]
        
        for code, label, description, sort_order, is_active, is_default, is_system in categories:
            ReferenceValue.objects.get_or_create(
                category='organization_categories',
                code=code,
                defaults={
                    'label': label,
                    'description': description,
                    'sort_order': sort_order,
                    'is_active': is_active,
                    'is_default': is_default,
                    'is_system': is_system,
                }
            ) 