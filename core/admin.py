from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from .models import User, UserSession, UserActionLog, Category, Organization, Adherent, Interaction, UserObjective, SupervisorStats

from django.utils.crypto import get_random_string
from django.contrib import messages

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['matricule', 'get_full_name', 'email', 'role', 'profession', 'is_active', 'last_login']
    list_filter = ['role', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['matricule', 'first_name', 'last_name', 'email', 'telephone']
    readonly_fields = ['date_joined', 'last_login', 'password_last_changed']
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('matricule', 'first_name', 'last_name', 'email', 'profession', 'fonction', 'telephone')
        }),
        ('Rôle et permissions', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser')
        }),
        ('Sécurité', {
            'fields': ('password_change_required', 'failed_login_attempts', 'account_locked_until')
        }),
        ('Informations système', {
            'fields': ('date_joined', 'last_login', 'password_last_changed', 'created_by', 'last_modified_by'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )

    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Nom complet'

    def save_model(self, request, obj, form, change):
        if not change:  # Si c'est une création d'utilisateur
            # Le mot de passe sera généré dans create_user si non fourni
            user = User.objects.create_user(
                email=obj.email,
                matricule=obj.matricule,
                first_name=obj.first_name,
                last_name=obj.last_name,
                password=form.cleaned_data.get('password1') if form.cleaned_data.get('password1') else None,
                role=obj.role,
                profession=obj.profession,
                fonction=obj.fonction,
                telephone=obj.telephone,
                is_active=obj.is_active,
                is_staff=obj.is_staff,
                is_superuser=obj.is_superuser
            )
            # Si un mot de passe a été généré automatiquement
            if hasattr(user, '_password_generated') and user._password_generated:
                messages.success(request, f'Mot de passe généré pour {user.get_full_name()}: {user._password_generated}')
            return user
        return super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        """Filtre les utilisateurs selon le rôle de l'utilisateur connecté"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        elif request.user.role == 'superviseur':
            # Les superviseurs peuvent voir tous les utilisateurs
            return qs
        else:
            # Les agents ne peuvent voir que leur propre profil
            return qs.filter(id=request.user.id)


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'login_time', 'last_activity', 'is_active']
    list_filter = ['is_active', 'login_time']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'ip_address']
    readonly_fields = ['session_key', 'login_time', 'last_activity']


@admin.register(UserActionLog)
class UserActionLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'timestamp', 'ip_address', 'success']
    list_filter = ['action', 'success', 'timestamp']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'description']
    readonly_fields = ['timestamp']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at', 'updated_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']

    def has_module_permission(self, request):
        """Seuls les administrateurs et les agents peuvent accéder aux catégories"""
        return request.user.is_superuser or request.user.role in ['admin', 'agent']


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['identifiant', 'name', 'category', 'monthly_revenue', 'phone', 'creation_date', 'adherents_count', 'created_by']
    list_filter = ['category', 'creation_date', 'created_by']
    search_fields = ['identifiant', 'name', 'address', 'phone']
    readonly_fields = ['created_at', 'updated_at', 'adherents_count']
    
    def adherents_count(self, obj):
        return obj.get_adherents_count()
    adherents_count.short_description = "Nombre d'adhérents"

    def has_module_permission(self, request):
        """Seuls les administrateurs et les agents peuvent accéder aux organisations"""
        return request.user.is_superuser or request.user.role in ['admin', 'agent']


@admin.register(Adherent)
class AdherentAdmin(admin.ModelAdmin):
    list_display = ['identifiant', 'full_name', 'type_adherent', 'organisation', 'join_date', 'created_at']
    list_filter = ['type_adherent', 'organisation', 'join_date']
    search_fields = ['identifiant', 'first_name', 'last_name', 'phone1']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('identifiant', 'first_name', 'last_name', 'birth_date', 'type_adherent')
        }),
        ('Informations de contact', {
            'fields': ('commune', 'quartier', 'secteur', 'phone1', 'phone2', 'num_urgence1', 'num_urgence2', 'email')
        }),
        ('Informations supplémentaires', {
            'fields': ('medical_info', 'formation_pro', 'distinction', 'langues')
        }),
        ('Adhésion', {
            'fields': ('join_date', 'organisation')
        }),
        ('Médias', {
            'fields': ('profile_picture',)
        }),
        ('Informations système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_module_permission(self, request):
        """Seuls les administrateurs et les superviseurs peuvent accéder aux adhérents"""
        return request.user.is_superuser or request.user.role in ['admin', 'superviseur']

    def has_view_permission(self, request, obj=None):
        """Seuls les administrateurs et les superviseurs peuvent voir les adhérents"""
        return request.user.is_superuser or request.user.role in ['admin', 'superviseur']

    def has_add_permission(self, request):
        """Seuls les administrateurs et les superviseurs peuvent ajouter des adhérents"""
        return request.user.is_superuser or request.user.role in ['admin', 'superviseur']

    def has_change_permission(self, request, obj=None):
        """Seuls les administrateurs et les superviseurs peuvent modifier les adhérents"""
        return request.user.is_superuser or request.user.role in ['admin', 'superviseur']

    def has_delete_permission(self, request, obj=None):
        """Seuls les administrateurs peuvent supprimer les adhérents"""
        return request.user.is_superuser or request.user.role == 'admin'


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ['identifiant', 'personnel', 'adherent', 'status', 'due_date', 'created_at']
    list_filter = ['status', 'created_at', 'due_date']
    search_fields = ['identifiant', 'personnel__first_name', 'personnel__last_name', 'adherent__first_name', 'adherent__last_name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Informations générales', {
            'fields': ('identifiant', 'personnel', 'adherent')
        }),
        ('Détails', {
            'fields': ('report', 'due_date', 'status')
        }),
        ('Informations système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_module_permission(self, request):
        """Seuls les administrateurs et les superviseurs peuvent accéder aux interactions"""
        return request.user.is_superuser or request.user.role in ['admin', 'superviseur']

    def has_view_permission(self, request, obj=None):
        """Seuls les administrateurs et les superviseurs peuvent voir les interactions"""
        return request.user.is_superuser or request.user.role in ['admin', 'superviseur']

    def has_add_permission(self, request):
        """Seuls les administrateurs et les superviseurs peuvent ajouter des interactions"""
        return request.user.is_superuser or request.user.role in ['admin', 'superviseur']

    def has_change_permission(self, request, obj=None):
        """Seuls les administrateurs et les superviseurs peuvent modifier les interactions"""
        return request.user.is_superuser or request.user.role in ['admin', 'superviseur']

    def has_delete_permission(self, request, obj=None):
        """Seuls les administrateurs peuvent supprimer les interactions"""
        return request.user.is_superuser or request.user.role == 'admin'


@admin.register(UserObjective)
class UserObjectiveAdmin(admin.ModelAdmin):
    list_display = ['user', 'objective_type', 'base_value', 'target_increment_display', 'current_value', 'deadline', 'status', 'progress_percentage_display']
    list_filter = ['objective_type', 'status', 'deadline', 'assigned_by']
    search_fields = ['user__first_name', 'user__last_name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'progress_percentage_display', 'base_value', 'target_increment_display']
    
    def target_increment_display(self, obj):
        return f"+{obj.target_increment}"
    target_increment_display.short_description = "À ajouter"
    
    def progress_percentage_display(self, obj):
        return f"{obj.progress_percentage:.1f}%"
    progress_percentage_display.short_description = "Progression"

    def has_module_permission(self, request):
        """Seuls les administrateurs et les superviseurs peuvent accéder aux objectifs"""
        return request.user.is_superuser or request.user.role in ['admin', 'superviseur']


@admin.register(SupervisorStats)
class SupervisorStatsAdmin(admin.ModelAdmin):
    list_display = ['supervisor', 'agent', 'organizations_count', 'adherents_count', 'interactions_count', 'last_updated']
    list_filter = ['supervisor', 'agent', 'last_updated']
    search_fields = ['supervisor__first_name', 'supervisor__last_name', 'agent__first_name', 'agent__last_name']
    readonly_fields = ['last_updated']

    def has_module_permission(self, request):
        """Seuls les administrateurs et les superviseurs peuvent accéder aux statistiques"""
        return request.user.is_superuser or request.user.role in ['admin', 'superviseur']
