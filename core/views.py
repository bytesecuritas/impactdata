from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.core.paginator import Paginator
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.http import FileResponse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
import os
import json
from datetime import datetime, timedelta
from .models import User, Adherent, Organization, Category, Interaction, Badge, UserObjective, SupervisorStats, GeneralParameter, ReferenceValue, RolePermission, SystemLog
from .forms import (
    GeneralParameterForm, ReferenceValueImportForm, SystemLogFilterForm, UserProfileForm, CustomPasswordChangeForm, AdherentForm, OrganizationForm, 
    CategoryForm, InteractionForm, UserForm, UserRegistrationForm, UserEditForm,
    BadgeForm, ProfileEditForm, AdherentSearchForm, OrganizationSearchForm, UserObjectiveForm,
    InteractionSearchForm, RolePermissionForm, BulkRolePermissionForm, ReferenceValueForm,
    ParameterBackupForm
)
from .services import EmailService
import calendar
import qrcode
from io import BytesIO
from django.core.files import File
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from django.template.loader import render_to_string
from django.conf import settings
import base64
from PIL import Image, ImageDraw, ImageFont
import imgkit
from html2image import Html2Image
import io
import os

# ==================== SYSTÈME DE PERMISSIONS ====================

def has_permission(user, permission_code):
    """
    Vérifie si un utilisateur a une permission spécifique.
    
    Args:
        user: L'utilisateur à vérifier
        permission_code: Le code de permission (ex: 'adherent_create', 'user_view')
    
    Returns:
        bool: True si l'utilisateur a la permission, False sinon
    """
    if not user.is_authenticated:
        return False
    
    # Les superutilisateurs ont toutes les permissions
    if user.is_superuser:
        return True
    
    # Vérifier la permission dans la base de données
    try:
        permission = RolePermission.objects.get(
            role=user.role,
            permission=permission_code,
            is_active=True
        )
        return True
    except RolePermission.DoesNotExist:
        return False

def require_permission(permission_code):
    """
    Décorateur pour exiger une permission spécifique.
    
    Args:
        permission_code: Le code de permission requis
    
    Returns:
        function: Le décorateur
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not has_permission(request.user, permission_code):
                messages.error(request, f"Vous n'avez pas la permission d'accéder à cette fonctionnalité.")
                return HttpResponseForbidden("Permission refusée")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

class PermissionRequiredMixin:
    """
    Mixin pour les vues basées sur les classes qui nécessitent une permission spécifique.
    """
    permission_required = None
    
    def dispatch(self, request, *args, **kwargs):
        if self.permission_required and not has_permission(request.user, self.permission_required):
            messages.error(request, f"Vous n'avez pas la permission d'accéder à cette fonctionnalité.")
            raise PermissionDenied("Permission refusée")
        return super().dispatch(request, *args, **kwargs)

def get_user_permissions(user):
    """
    Récupère toutes les permissions actives d'un utilisateur.
    
    Args:
        user: L'utilisateur
    
    Returns:
        list: Liste des codes de permissions
    """
    if not user.is_authenticated:
        return []
    
    if user.is_superuser:
        # Retourner toutes les permissions possibles
        return [choice[0] for choice in RolePermission.PERMISSION_CHOICES]
    
    permissions = RolePermission.objects.filter(
        role=user.role,
        is_active=True
    ).values_list('permission', flat=True)
    
    return list(permissions)

def can_access_data(user, data_type='read', target_user=None):
    """
    Vérifie les permissions d'accès aux données selon le rôle et les permissions configurées.
    
    Args:
        user: L'utilisateur qui demande l'accès
        data_type: Type d'accès ('read', 'create', 'update', 'delete')
        target_user: L'utilisateur cible (pour les données utilisateur)
    
    Returns:
        bool: True si l'accès est autorisé, False sinon
    """
    if not user.is_authenticated:
        return False
    
    # Les superutilisateurs ont accès à tout
    if user.is_superuser:
        return True
    
    # Mapper les types d'accès aux permissions
    permission_mapping = {
        'read': {
            'user': 'user_view',
            'adherent': 'adherent_view',
            'organization': 'organization_view',
            'interaction': 'interaction_view',
            'badge': 'badge_view',
            'objective': 'objective_view',
            'settings': 'settings_view',
            'reports': 'reports_view',
            'stats': 'stats_view',
        },
        'create': {
            'user': 'user_create',
            'adherent': 'adherent_create',
            'organization': 'organization_create',
            'interaction': 'interaction_create',
            'badge': 'badge_create',
            'objective': 'objective_create',
        },
        'update': {
            'user': 'user_edit',
            'adherent': 'adherent_edit',
            'organization': 'organization_edit',
            'interaction': 'interaction_edit',
            'badge': 'badge_edit',
            'objective': 'objective_edit',
        },
        'delete': {
            'user': 'user_delete',
            'adherent': 'adherent_delete',
            'organization': 'organization_delete',
            'interaction': 'interaction_delete',
            'badge': 'badge_delete',
            'objective': 'objective_delete',
        }
    }
    
    # Vérifier la permission correspondante
    if data_type in permission_mapping:
        for data_category, permission_code in permission_mapping[data_type].items():
            if has_permission(user, permission_code):
                return True
    
    # Cas spécial pour les données utilisateur
    if target_user and data_type in ['read', 'update']:
        if user == target_user:
            return True  # Un utilisateur peut toujours voir/modifier son propre profil
        elif user.role == 'superviseur' and target_user.role == 'agent':
            # Les superviseurs peuvent voir les agents qu'ils ont créés
            if target_user.created_by == user:
                return True
    
    return False

# ==================== FONCTIONS EXISTANTES (MISE À JOUR) ====================

def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

def is_supervisor(user):
    return user.is_authenticated and user.role == 'superviseur'

def is_agent(user):
    return user.is_authenticated and user.role == 'agent'

def can_manage_users(user):
    """Vérifie si l'utilisateur peut gérer les utilisateurs"""
    return has_permission(user, 'user_create') or has_permission(user, 'user_edit') or has_permission(user, 'user_view')

def can_access_user_data(user, target_user):
    """Vérifie si l'utilisateur peut accéder aux données d'un autre utilisateur"""
    if user.is_superuser:
        return True
    elif has_permission(user, 'user_view'):
        if user.role == 'superviseur':
            # Les superviseurs peuvent voir les agents qu'ils ont créés ou qui leur sont assignés
            return target_user.role == 'agent' and (
                target_user.created_by == user or 
                target_user in user.created_users.filter(role='agent')
            )
        elif user.role == 'admin':
            return True
        elif user.role == 'agent':
            # Les agents ne peuvent voir que leur propre profil
            return user == target_user
    return False

def login_view(request):
    """Vue de connexion personnalisée"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if email and password:
            user = authenticate(request, username=email, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, f'Bienvenue {user.get_full_name()}!')
                    
                    # Redirection selon le rôle
                    if user.is_superuser or user.role == 'admin':
                        return redirect('core:admin_dashboard')
                    elif user.role == 'superviseur':
                        return redirect('core:superviseur_dashboard')
                    elif user.role == 'agent':
                        return redirect('core:agent_dashboard')
                    else:
                        return redirect('core:dashboard')
                else:
                    messages.error(request, 'Votre compte est désactivé.')
            else:
                messages.error(request, 'Email ou mot de passe incorrect.')
        else:
            messages.error(request, 'Veuillez remplir tous les champs.')
    
    return render(request, 'core/auth/login.html', {})

@login_required
def logout_view(request):
    """Vue de déconnexion"""
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('core:login')

@login_required
def dashboard(request):
    """Tableau de bord général"""
    if request.user.is_superuser or request.user.role == 'admin':
        return redirect('core:admin_dashboard')
    elif request.user.role == 'superviseur':
        return redirect('core:superviseur_dashboard')
    elif request.user.role == 'agent':
        return redirect('core:agent_dashboard')
    else:
        return redirect('core:login')

@login_required
def admin_dashboard(request):
    """Tableau de bord administrateur"""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden("Accès refusé")
    
    # Données de base
    total_users = User.objects.count()
    total_adherents = Adherent.objects.count()
    total_organizations = Organization.objects.count()
    total_categories = Category.objects.count()
    
    # Données pour les graphiques
    # 1. Répartition par catégorie
    category_stats = Category.objects.annotate(
        org_count=Count('organizations')
    ).values('name', 'org_count').order_by('-org_count')[:5]
    
    # 2. Évolution des adhérents (6 derniers mois)
    adherents_evolution = []
    months_labels = []
    
    for i in range(6):
        date = datetime.now() - timedelta(days=30*i)
        month_start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = month_start.replace(day=calendar.monthrange(date.year, date.month)[1], hour=23, minute=59, second=59)
        
        count = Adherent.objects.filter(
            created_at__gte=month_start,
            created_at__lte=month_end
        ).count()
        
        adherents_evolution.insert(0, count)
        months_labels.insert(0, date.strftime('%b'))
    
    # 3. Répartition des rôles utilisateurs
    roles_stats = User.objects.values('role').annotate(
        count=Count('id')
    ).values('role', 'count')
    
    # 4. Top 5 des organisations par nombre d'adhérents
    top_organizations = Organization.objects.annotate(
        adherent_count=Count('adherents')
    ).order_by('-adherent_count')[:5]
    
    context = {
        'total_users': total_users,
        'total_adherents': total_adherents,
        'total_organizations': total_organizations,
        'total_categories': total_categories,
        'recent_adherents': Adherent.objects.order_by('-created_at')[:5],
        'recent_organizations': Organization.objects.order_by('-created_at')[:5],
        'now': timezone.now(),
        
        # Données pour les graphiques (sérialisées en JSON)
        'category_stats': json.dumps([cat['name'] for cat in category_stats]),
        'category_data': json.dumps([cat['org_count'] for cat in category_stats]),
        'adherents_evolution': json.dumps(adherents_evolution),
        'months_labels': json.dumps(months_labels),
        'roles_labels': json.dumps([role['role'].title() for role in roles_stats]),
        'roles_data': json.dumps([role['count'] for role in roles_stats]),
        'top_organizations_labels': json.dumps([org['name'][:15] for org in top_organizations.values('name', 'adherent_count')]),
        'top_organizations_data': json.dumps([org['adherent_count'] for org in top_organizations.values('name', 'adherent_count')]),
    }
    return render(request, 'core/dashboard/admin_dashboard.html', context)

@login_required
def superviseur_dashboard(request):
    """Tableau de bord superviseur"""
    if not is_supervisor(request.user) and not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé")
    
    # Obtenir les agents assignés au superviseur
    assigned_agents = User.objects.filter(
        Q(created_by=request.user) & Q(role='agent')
    ).filter(role='agent')
    
    # Statistiques des agents
    agents_stats = []
    for agent in assigned_agents:
        stats, created = SupervisorStats.objects.get_or_create(
            supervisor=request.user,
            agent=agent
        )
        stats.update_stats()
        agents_stats.append(stats)
    
    # Objectifs assignés - mettre à jour la progression
    objectives = UserObjective.objects.filter(
        assigned_by=request.user
    ).order_by('-created_at')[:10]
    # Mettre à jour la progression de tous les objectifs assignés par ce superviseur
    for objective in objectives:
        objective.update_progress()
    
    # Statistiques globales
    total_organizations = sum(stats.organizations_count for stats in agents_stats)
    total_adherents = sum(stats.adherents_count for stats in agents_stats)
    total_interactions = sum(stats.interactions_count for stats in agents_stats)
    
    context = {
        'assigned_agents': assigned_agents,
        'agents_stats': agents_stats,
        'objectives': objectives,
        'total_organizations': total_organizations,
        'total_adherents': total_adherents,
        'total_interactions': total_interactions,
        'now': timezone.now(),
    }
    return render(request, 'core/dashboard/superviseur_dashboard.html', context)

@login_required
def agent_dashboard(request):
    """Tableau de bord agent"""
    if not is_agent(request.user):
        return HttpResponseForbidden("Accès refusé")
    
    # Statistiques de l'agent
    organizations_count = Organization.objects.filter(created_by=request.user).count()
    adherents_count = Adherent.objects.filter(created_by=request.user).count()
    interactions_count = Interaction.objects.filter(personnel=request.user).count()
    
    # Objectifs assignés - mettre à jour la progression
    objectives = UserObjective.objects.filter(user=request.user).order_by('-created_at')
    # Mettre à jour la progression de tous les objectifs de cet agent
    for objective in objectives:
        objective.update_progress()
    
    # Dernières activités
    recent_organizations = Organization.objects.filter(created_by=request.user).order_by('-created_at')[:5]
    recent_adherents = Adherent.objects.filter(created_by=request.user).order_by('-created_at')[:5]
    recent_interactions = Interaction.objects.filter(personnel=request.user).order_by('-created_at')[:5]
    
    context = {
        'organizations_count': organizations_count,
        'adherents_count': adherents_count,
        'interactions_count': interactions_count,
        'objectives': objectives,
        'recent_organizations': recent_organizations,
        'recent_adherents': recent_adherents,
        'recent_interactions': recent_interactions,
        'now': timezone.now(),
    }
    return render(request, 'core/dashboard/agent_dashboard.html', context)

@login_required
def profile(request):
    """Vue pour afficher le profil de l'utilisateur"""
    user = request.user
    context = {
        'user': user,
    }
    return render(request, 'core/profile/profile.html', context)

@login_required
def edit_profile(request):
    """Vue pour modifier son profil"""
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre profil a été mis à jour avec succès.')
            return redirect('core:profile')
    else:
        form = ProfileEditForm(instance=request.user)
    
    return render(request, 'core/profile/edit_profile.html', {'form': form})

@login_required
def change_password(request):
    """Vue pour changer son mot de passe"""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Mettre à jour la session pour éviter la déconnexion
            update_session_auth_hash(request, user)
            messages.success(request, 'Votre mot de passe a été changé avec succès.')
            return redirect('core:profile')
    else:
        form = CustomPasswordChangeForm(request.user)
    
    return render(request, 'core/profile/change_password.html', {'form': form})

# Vues pour les adhérents
@login_required
@require_permission('adherent_view')
def adherent_list(request):
    """Liste des adhérents avec recherche et filtres avancés"""
    adherents = Adherent.objects.select_related('organisation', 'created_by').prefetch_related('centres_interet').all()
    
    # Formulaire de recherche
    search_form = AdherentSearchForm(request.GET)
    
    # Appliquer les filtres (même si le formulaire n'est pas complètement valide)
    # On récupère les valeurs directement de request.GET pour la recherche
    if request.GET:
        # Recherche globale (fonctionne toujours)
        search = request.GET.get('search', '').strip()
        if search:
            # Séparer la requête en mots pour recherche multi-mots
            query_words = search.split()
            adherent_query = Q()
            
            # Si plusieurs mots, essayer de chercher prénom + nom
            if len(query_words) >= 2:
                # Chercher toutes les combinaisons possibles de prénom et nom
                for i in range(len(query_words)):
                    for j in range(i+1, len(query_words)+1):
                        potential_first_name = ' '.join(query_words[:i+1])
                        potential_last_name = ' '.join(query_words[i+1:j])
                        
                        if potential_first_name and potential_last_name:
                            adherent_query |= (
                                Q(first_name__icontains=potential_first_name) &
                                Q(last_name__icontains=potential_last_name)
                            ) | (
                                Q(first_name__icontains=potential_last_name) &
                                Q(last_name__icontains=potential_first_name)
                            )
            
            # Ajouter aussi la recherche classique sur tous les champs
            adherent_query |= (
                Q(last_name__icontains=search) |
                Q(first_name__icontains=search) |
                Q(identifiant__icontains=search) |
                Q(phone1__icontains=search) |
                Q(phone2__icontains=search) |
                Q(email__icontains=search) |
                Q(commune__icontains=search) |
                Q(quartier__icontains=search) |
                Q(secteur__icontains=search)
            )
            
            adherents = adherents.filter(adherent_query).distinct()
    
    # Appliquer les autres filtres si le formulaire est valide
    if search_form.is_valid():
        # Filtres spécifiques
        type_adherent = search_form.cleaned_data.get('type_adherent')
        if type_adherent:
            adherents = adherents.filter(type_adherent=type_adherent)
        
        organisation = search_form.cleaned_data.get('organisation')
        if organisation:
            adherents = adherents.filter(organisation=organisation)
        
        # Localisation
        commune = search_form.cleaned_data.get('commune')
        if commune:
            adherents = adherents.filter(commune__icontains=commune)
        
        quartier = search_form.cleaned_data.get('quartier')
        if quartier:
            adherents = adherents.filter(quartier__icontains=quartier)
        
        secteur = search_form.cleaned_data.get('secteur')
        if secteur:
            adherents = adherents.filter(secteur__icontains=secteur)
        
        # Dates d'adhésion
        join_date_from = search_form.cleaned_data.get('join_date_from')
        if join_date_from:
            adherents = adherents.filter(join_date__gte=join_date_from)
        
        join_date_to = search_form.cleaned_data.get('join_date_to')
        if join_date_to:
            adherents = adherents.filter(join_date__lte=join_date_to)
        
        # Statut du badge
        badge_status = search_form.cleaned_data.get('badge_status')
        if badge_status:
            from datetime import date, timedelta
            today = date.today()
            
            if badge_status == 'valid':
                adherents = adherents.filter(
                    badge_validity__isnull=False,
                    badge_validity__gte=today
                )
            elif badge_status == 'expired':
                adherents = adherents.filter(
                    Q(badge_validity__isnull=True) |
                    Q(badge_validity__lt=today)
                )
            elif badge_status == 'expiring_soon':
                # Expire dans les 30 prochains jours
                thirty_days_later = today + timedelta(days=30)
                adherents = adherents.filter(
                    badge_validity__gte=today,
                    badge_validity__lte=thirty_days_later
                )
        
        # Centres d'intérêt
        centres_interet = search_form.cleaned_data.get('centres_interet')
        if centres_interet:
            # Filtrer les adhérents qui ont au moins un des centres d'intérêt sélectionnés
            adherents = adherents.filter(centres_interet__in=centres_interet).distinct()
        
        # Situation médicale (recherche textuelle)
        medical_info = search_form.cleaned_data.get('medical_info')
        if medical_info:
            adherents = adherents.filter(medical_info__icontains=medical_info)
        
        # Distinction (recherche textuelle)
        distinction = search_form.cleaned_data.get('distinction')
        if distinction:
            adherents = adherents.filter(distinction__icontains=distinction)
        
        # Catégorie d'organisation
        organisation_category = search_form.cleaned_data.get('organisation_category')
        if organisation_category:
            adherents = adherents.filter(organisation__category=organisation_category)
        
        # Activité
        activity_name = search_form.cleaned_data.get('activity_name')
        if activity_name:
            adherents = adherents.filter(activity_name__icontains=activity_name)
        
        # Créé par
        created_by = search_form.cleaned_data.get('created_by')
        if created_by:
            adherents = adherents.filter(created_by=created_by)
    
    # Tri par défaut
    adherents = adherents.order_by('last_name', 'first_name')
    
    # Pagination
    paginator = Paginator(adherents, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'adherents': page_obj,
        'total_count': adherents.count(),
        'can_create': has_permission(request.user, 'adherent_create'),
        'can_edit': has_permission(request.user, 'adherent_edit'),
        'can_delete': has_permission(request.user, 'adherent_delete'),
    }
    return render(request, 'core/adherents/adherent_list.html', context)

@login_required
@require_permission('adherent_view')
def adherent_detail(request, adherent_id):
    """Détail d'un adhérent"""
    try:
        adherent = Adherent.objects.get(id=adherent_id)
        interactions = adherent.interactions.all().order_by('-created_at')
    except Adherent.DoesNotExist:
        messages.error(request, 'Adhérent non trouvé.')
        return redirect('core:adherent_list')
    
    context = {
        'adherent': adherent,
        'interactions': interactions,
        'can_edit': has_permission(request.user, 'adherent_edit'),
        'can_delete': has_permission(request.user, 'adherent_delete'),
        'can_gen_badge': has_permission(request.user, 'badge_create')
    }
    return render(request, 'core/adherents/adherent_detail.html', context)

@login_required
def adherent_interactions(request, adherent_id):
    """Afficher toutes les interactions d'un adhérent spécifique"""
    adherent = get_object_or_404(Adherent, id=adherent_id)
    
    # Récupérer toutes les interactions de cet adhérent
    interactions = Interaction.objects.filter(adherent=adherent).select_related(
        'personnel', 'auteur'
    ).order_by('-created_at')
    
    # Statistiques des interactions
    total_interactions = interactions.count()
    completed_interactions = interactions.filter(status='completed').count()
    in_progress_interactions = interactions.filter(status='in_progress').count()
    overdue_interactions = interactions.filter(
        due_date__lt=timezone.now(),
        status__in=['in_progress', 'pending']
    ).count()
    
    # Pagination
    paginator = Paginator(interactions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'adherent': adherent,
        'interactions': page_obj,
        'total_interactions': total_interactions,
        'completed_interactions': completed_interactions,
        'in_progress_interactions': in_progress_interactions,
        'overdue_interactions': overdue_interactions,
        'now': timezone.now(),
    }
    return render(request, 'core/adherents/adherent_interactions.html', context)

# Vues pour les organisations (agents et admins)
@login_required
@require_permission('organization_view')
def organization_list(request):
    """Liste des organisations"""
    organizations = Organization.objects.all().order_by('name')
    context = {
        'organizations': organizations,
        'total_organizations': organizations.count(),
        'total_personel': Organization.objects.aggregate(Sum('number_personnel'))['number_personnel__sum'] or 0,
        'total_revenue': Organization.objects.aggregate(Sum('monthly_revenue'))['monthly_revenue__sum'] or 0,
        'can_create': has_permission(request.user, 'organization_create'),
        'can_edit': has_permission(request.user, 'organization_edit'),
        'can_delete': has_permission(request.user, 'organization_delete'),
    }
    return render(request, 'core/organizations/organization_list.html', context)

@login_required
@require_permission('organization_view')
def organization_detail(request, organization_id):
    """Détail d'une organisation"""
    try:
        organization = Organization.objects.get(id=organization_id)
        adherents = organization.adherents.all().order_by('last_name', 'first_name')
    except Organization.DoesNotExist:
        messages.error(request, 'Organisation non trouvée.')
        return redirect('core:organization_list')
    
    context = {
        'organization': organization,
        'adherents': adherents,
        'can_edit': has_permission(request.user, 'organization_edit'),
        'can_delete': has_permission(request.user, 'organization_delete'),
    }
    return render(request, 'core/organizations/organization_detail.html', context)

# Vues pour les catégories
@login_required
@require_permission('organization_view')  # Utilise organization_view car les catégories sont liées aux organisations
def category_list(request):
    """Liste des catégories"""
    categories = Category.objects.all().order_by('name')
    context = {
        'categories': categories,
        'total_categories': categories.count(),
        'can_create': has_permission(request.user, 'organization_create'),
        'can_edit': has_permission(request.user, 'organization_edit'),
        'can_delete': has_permission(request.user, 'organization_delete'),
    }
    return render(request, 'core/categories/category_list.html', context)

# Vues pour les interactions
@login_required
@require_permission('interaction_view')
def interaction_list(request):
    """Liste des interactions avec recherche avancée"""
    
    # Initialiser le formulaire de recherche
    search_form = InteractionSearchForm(request.GET)
    
    # Base queryset
    interactions = Interaction.objects.select_related('personnel', 'adherent', 'auteur').all()
    
    # Appliquer les filtres si le formulaire est valide
    if search_form.is_valid():
        personnel = search_form.cleaned_data.get('personnel')
        adherent = search_form.cleaned_data.get('adherent')
        auteur = search_form.cleaned_data.get('auteur')
        status = search_form.cleaned_data.get('status')
        due_date_from = search_form.cleaned_data.get('due_date_from')
        due_date_to = search_form.cleaned_data.get('due_date_to')
        keywords = search_form.cleaned_data.get('keywords')
        overdue_only = search_form.cleaned_data.get('overdue_only')
        due_soon = search_form.cleaned_data.get('due_soon')
        
        # Filtres
        if personnel:
            interactions = interactions.filter(personnel=personnel)
        
        if adherent:
            interactions = interactions.filter(adherent=adherent)
        
        if auteur:
            interactions = interactions.filter(auteur=auteur)
        
        if status:
            interactions = interactions.filter(status=status)
        
        if due_date_from:
            interactions = interactions.filter(due_date__date__gte=due_date_from)
        
        if due_date_to:
            interactions = interactions.filter(due_date__date__lte=due_date_to)
        
        if keywords:
            interactions = interactions.filter(report__icontains=keywords)
        
        if overdue_only:
            interactions = interactions.filter(
                due_date__lt=timezone.now(),
                status__in=['in_progress', 'pending']
            )
        
        if due_soon:
            # Interactions dont l'échéance est dans les 7 prochains jours
            from datetime import timedelta
            seven_days_from_now = timezone.now() + timedelta(days=7)
            interactions = interactions.filter(
                due_date__gte=timezone.now(),
                due_date__lte=seven_days_from_now,
                status__in=['in_progress', 'pending']
            )
    
    # Tri par défaut
    interactions = interactions.order_by('-created_at')
    
    # Calculer le nombre total filtré avant la pagination
    filtered_count = interactions.count()
    
    # Pagination
    paginator = Paginator(interactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Notifications pour les interactions en retard ou proches de l'échéance
    # UTILISER les interactions FILTRÉES au lieu de toutes les interactions
    notifications = []
    
    # Interactions en retard (à partir des interactions déjà filtrées)
    overdue_interactions = interactions.filter(
        due_date__lt=timezone.now(),
        status__in=['in_progress', 'pending']
    )
    
    if overdue_interactions.exists():
        notifications.append({
            'type': 'danger',
            'message': f'{overdue_interactions.count()} interaction(s) en retard',
            'count': overdue_interactions.count()
        })
    
    # Interactions dont l'échéance approche (7 jours) (à partir des interactions déjà filtrées)
    from datetime import timedelta
    seven_days_from_now = timezone.now() + timedelta(days=7)
    due_soon_interactions = interactions.filter(
        due_date__gte=timezone.now(),
        due_date__lte=seven_days_from_now,
        status__in=['in_progress', 'pending']
    )
    
    if due_soon_interactions.exists():
        notifications.append({
            'type': 'warning',
            'message': f'{due_soon_interactions.count()} interaction(s) avec échéance proche',
            'count': due_soon_interactions.count()
        })
    
    context = {
        'interactions': page_obj,
        'total_interactions': Interaction.objects.count(),
        'filtered_count': filtered_count,
        'search_form': search_form,
        'notifications': notifications,
        'overdue_interactions': overdue_interactions[:5],  # Limiter à 5 pour l'affichage
        'due_soon_interactions': due_soon_interactions[:5],
        'now': timezone.now(),
        'can_create': has_permission(request.user, 'interaction_create'),
        'can_edit': has_permission(request.user, 'interaction_edit'),
        'can_delete': has_permission(request.user, 'interaction_delete'),
    }
    return render(request, 'core/interactions/interaction_list.html', context)

@login_required
@require_permission('interaction_view')
def interaction_detail(request, interaction_id):
    """Détail d'une interaction"""
    try:
        interaction = Interaction.objects.get(id=interaction_id)
    except Interaction.DoesNotExist:
        messages.error(request, 'Interaction non trouvée.')
        return redirect('core:interaction_list')
    
    context = {
        'interaction': interaction,
        'can_edit': has_permission(request.user, 'interaction_edit'),
        'can_delete': has_permission(request.user, 'interaction_delete'),
    }
    return render(request, 'core/interactions/interaction_detail.html', context)

@login_required
def interaction_notifications(request):
    """Afficher les notifications d'interactions en retard ou proches de l'échéance"""
    # Interactions en retard
    overdue_interactions = Interaction.objects.filter(
        due_date__lt=timezone.now(),
        status__in=['in_progress', 'pending']
    ).select_related('personnel', 'adherent', 'auteur').order_by('due_date')
    
    # Interactions dont l'échéance approche (7 jours)
    from datetime import timedelta
    seven_days_from_now = timezone.now() + timedelta(days=7)
    due_soon_interactions = Interaction.objects.filter(
        due_date__gte=timezone.now(),
        due_date__lte=seven_days_from_now,
        status__in=['in_progress', 'pending']
    ).select_related('personnel', 'adherent', 'auteur').order_by('due_date')
    
    # Filtrer selon le rôle de l'utilisateur
    if request.user.role == 'agent':
        overdue_interactions = overdue_interactions.filter(
            Q(personnel=request.user) | Q(auteur=request.user)
            )
        due_soon_interactions = due_soon_interactions.filter(
            Q(personnel=request.user) | Q(auteur=request.user)
            )
    elif request.user.role == 'superviseur':
        # Les superviseurs voient les interactions de leurs agents
        overdue_interactions = overdue_interactions.filter(
            Q(personnel=request.user) | Q(auteur=request.user) |
            Q(personnel__created_by=request.user) | Q(auteur__created_by=request.user)
        )
        due_soon_interactions = due_soon_interactions.filter(
            Q(personnel=request.user) | Q(auteur=request.user) |
            Q(personnel__created_by=request.user) | Q(auteur__created_by=request.user)
        )
    
    context = {
        'overdue_interactions': overdue_interactions,
        'due_soon_interactions': due_soon_interactions,
        'total_overdue': overdue_interactions.count(),
        'total_due_soon': due_soon_interactions.count(),
        'now': timezone.now(),
    }
    return render(request, 'core/interactions/interaction_notifications.html', context)

# ==================== CRUD ADHÉRENTS ====================

@login_required
@require_permission('adherent_create')
def check_phone_availability(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        if phone:
            exists = Adherent.objects.filter(phone1=phone).exists()
            return JsonResponse({'available': not exists, 'phone': phone, 'message': 'Numéro disponible' if not exists else 'Ce numéro est déjà utilisé'})
        return JsonResponse({'error': 'Numéro de téléphone requis'}, status=400)
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

@login_required
@require_permission('adherent_create')
def phone_verification_step(request):
    """Étape de vérification du numéro de téléphone avant l'ajout d'adhérent"""
    if request.method == 'POST':
        phone = request.POST.get('phone')
        if phone:
            # Vérifier si le numéro existe déjà
            exists = Adherent.objects.filter(phone1=phone).exists()
            if exists:
                messages.error(request, f'Le numéro de téléphone {phone} est déjà utilisé par un autre adhérent.')
                return render(request, 'core/adherents/phone_verification.html', {
                    'phone': phone,
                    'error': True
                })
            else:
                # Numéro disponible, rediriger vers le formulaire d'ajout avec le numéro pré-rempli
                messages.success(request, f'Le numéro {phone} est disponible. Vous pouvez maintenant créer l\'adhérent.')
                return redirect('core:adherent_create_with_phone', phone=phone)
        else:
            messages.error(request, 'Veuillez saisir un numéro de téléphone.')
    
    return render(request, 'core/adherents/phone_verification.html')

@login_required
@require_permission('adherent_create')
def adherent_create_with_phone(request, phone):
    """Créer un adhérent avec un numéro de téléphone pré-vérifié"""
    if request.method == 'POST':
        form = AdherentForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            try:
                adherent = form.save(commit=False)
                adherent.created_by = request.user
                adherent.save()
                messages.success(request, 'Adhérent créé avec succès.')
                return redirect('core:adherent_detail', adherent_id=adherent.id)
            except Exception as e:
                messages.error(request, f'Erreur lors de la création: {str(e)}')
    else:
        # Pré-remplir le formulaire avec le numéro vérifié
        initial_data = {'phone1': phone}
        form = AdherentForm(user=request.user, initial=initial_data)
    
    return render(request, 'core/adherents/adherent_form.html', {
        'form': form,
        'title': 'Créer un adhérent',
        'phone_verified': True,
        'verified_phone': phone
    })

@login_required
@require_permission('adherent_edit')
def adherent_update(request, adherent_id):
    """Modifier un adhérent"""
    adherent = get_object_or_404(Adherent, id=adherent_id)

    # Vérifier que l'agent ne peut modifier que ses propres adhérents
    if request.user.role == 'agent' and adherent.created_by != request.user:
        return HttpResponseForbidden("Accès refusé: vous ne pouvez modifier que les adhérents créer par vous même.")
    
    if request.method == 'POST':
        form = AdherentForm(request.POST, request.FILES, instance=adherent, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Adhérent mis à jour avec succès.')
            return redirect('core:adherent_detail', adherent_id=adherent.id)
    else:
        form = AdherentForm(instance=adherent, user=request.user)
    
    return render(request, 'core/adherents/adherent_form.html', {
        'form': form,
        'title': 'Modifier l\'adhérent'
    })

@login_required
@require_permission('adherent_delete')
def adherent_delete(request, adherent_id):
    """Supprimer un adhérent"""
    adherent = get_object_or_404(Adherent, id=adherent_id)

    # Vérifier que l'agent ne peut supprimer que ses propres adhérents
    if request.user.role == 'agent' and adherent.created_by != request.user:
        return HttpResponseForbidden("Accès refusé: vous ne pouvez supprimer que les adhérents créer par vous même.")
    
    if request.method == 'POST':
        adherent.delete()
        messages.success(request, 'Adhérent supprimé avec succès.')
        return redirect('core:adherent_list')
    
    return render(request, 'core/adherents/adherent_confirm_delete.html', {'adherent': adherent})

# ==================== CRUD ORGANISATIONS ====================

@login_required
@require_permission('organization_create')
def organization_create(request):
    """Créer une nouvelle organisation"""
    if request.method == 'POST':
        form = OrganizationForm(request.POST)
        if form.is_valid():
            organization = form.save(commit=False)
            organization.created_by = request.user
            organization.save()
            messages.success(request, 'Organisation créée avec succès.')
            return redirect('core:organization_detail', organization_id=organization.id)
    else:
        form = OrganizationForm()
    
    return render(request, 'core/organizations/organization_form.html', {'form': form, 'title': 'Créer une organisation'})

@login_required
@require_permission('organization_edit')
def organization_update(request, organization_id):
    """Modifier une organisation"""
    organization = get_object_or_404(Organization, id=organization_id)
    
    # Vérifier que l'agent ne peut modifier que ses propres organisations
    if request.user.role == 'agent' and organization.created_by != request.user:
        return HttpResponseForbidden("Accès refusé: vous ne pouvez modifier que les organisations créer par vous même.")
    
    if request.method == 'POST':
        form = OrganizationForm(request.POST, instance=organization)
        if form.is_valid():
            form.save()
            messages.success(request, 'Organisation mise à jour avec succès.')
            return redirect('core:organization_detail', organization_id=organization.id)
    else:
        form = OrganizationForm(instance=organization)
    
    return render(request, 'core/organizations/organization_form.html', {'form': form, 'title': 'Modifier l\'organisation'})

@login_required
@require_permission('organization_delete')
def organization_delete(request, organization_id):
    """Supprimer une organisation"""
    organization = get_object_or_404(Organization, id=organization_id)
    
    # Vérifier que l'agent ne peut supprimer que ses propres organisations
    if request.user.role == 'agent' and organization.created_by != request.user:
        return HttpResponseForbidden("Accès refusé: vous ne pouvez supprimer que les organisations créer par vous même.")
    
    if request.method == 'POST':
        organization.delete()
        messages.success(request, 'Organisation supprimée avec succès.')
        return redirect('core:organization_list')
    
    return render(request, 'core/organizations/organization_confirm_delete.html', {'organization': organization})

# ==================== CRUD CATÉGORIES ====================

@login_required
@require_permission('organization_create')
def category_create(request):
    """Créer une nouvelle catégorie"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Catégorie "{category.name}" créée avec succès.')
            return redirect('core:category_list')
    else:
        form = CategoryForm()
    
    context = {
        'form': form,
        'title': 'Créer une nouvelle catégorie',
        'submit_text': 'Créer la catégorie'
    }
    return render(request, 'core/categories/category_form.html', context)

@login_required
@require_permission('organization_edit')
def category_update(request, category_id):
    """Modifier une catégorie"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'Catégorie "{category.name}" modifiée avec succès.')
            return redirect('core:category_list')
    else:
        form = CategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'title': f'Modifier la catégorie {category.name}',
        'submit_text': 'Mettre à jour'
    }
    return render(request, 'core/categories/category_form.html', context)

@login_required
@require_permission('organization_delete')
def category_delete(request, category_id):
    """Supprimer une catégorie"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        category_name = category.name
        category.delete()
        messages.success(request, f'Catégorie "{category_name}" supprimée avec succès.')
        return redirect('core:category_list')
    
    context = {
        'category': category,
        'title': f'Supprimer la catégorie {category.name}'
    }
    return render(request, 'core/categories/category_confirm_delete.html', context)

# ==================== CRUD INTERACTIONS ====================

@login_required
def interaction_create(request):
    """Créer une nouvelle interaction"""
    # if not (is_admin(request.user) or is_agent(request.user) or is_supervisor(request.user)):
    #     return HttpResponseForbidden("Accès refusé")
    
    if request.method == 'POST':
        form = InteractionForm(request.POST, user=request.user)
        if form.is_valid():
            interaction = form.save(commit=False)
            interaction.auteur = request.user
            interaction.save()
            messages.success(request, 'Interaction créée avec succès.')
            return redirect('core:interaction_detail', interaction_id=interaction.id)
    else:
        form = InteractionForm(user=request.user)
    
    return render(request, 'core/interactions/interaction_form.html', {'form': form, 'title': 'Créer une interaction'})

@login_required
def interaction_update(request, interaction_id):
    """Modifier une interaction"""
    
    interaction = get_object_or_404(Interaction, id=interaction_id)
    
    # Vérifier que l'agent ne peut modifier que ses propres interactions
    if is_agent(request.user) and (interaction.auteur != request.user and interaction.personnel != request.user) :
        return HttpResponseForbidden("Accès refusé: vous ne pouvez modifier que les interactions où vous êtes auteur ou personnel assigné.")
    
    if request.method == 'POST':
        form = InteractionForm(request.POST, instance=interaction, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Interaction mise à jour avec succès.')
            return redirect('core:interaction_detail', interaction_id=interaction.id)
    else:
        form = InteractionForm(instance=interaction, user=request.user)
    
    return render(request, 'core/interactions/interaction_form.html', {'form': form, 'title': 'Modifier l\'interaction'})

@login_required
def interaction_delete(request, interaction_id):
    """Supprimer une interaction"""
    
    interaction = get_object_or_404(Interaction, id=interaction_id)
    
    # Vérifier que l'agent ne peut supprimer que ses propres interactions
    if is_agent(request.user) and (interaction.auteur != request.user and interaction.personnel != request.user) :
        return HttpResponseForbidden("Accès refusé: vous ne pouvez supprimer que les interactions où vous êtes auteur ou personnel assigné.")
    
    if request.method == 'POST':
        interaction.delete()
        messages.success(request, 'Interaction supprimée avec succès.')
        return redirect('core:interaction_list')
    
    return render(request, 'core/interactions/interaction_confirm_delete.html', {'interaction': interaction})

# User Management Views (Admin only)
class UserListView(PermissionRequiredMixin, ListView):
    permission_required = 'user_view'
    model = User
    template_name = 'core/users/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = User.objects.all()
        
        # Filtrage selon le rôle de l'utilisateur connecté
        if self.request.user.role == 'admin':
            # Les admins voient tous les utilisateurs
            pass
        elif self.request.user.role == 'superviseur':
            # Les superviseurs voient seulement les agents qui sont créés par eux ou qui leur sont assignés
            queryset = queryset.filter(
                Q(role='agent') & Q(created_by=self.request.user)
            )
        elif self.request.user.role == 'agent':
            # Les agents ne voient que leur propre profil
            queryset = queryset.filter(pk=self.request.user.pk)
        
        # Filtres de recherche
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(matricule__icontains=search) |
                Q(email__icontains=search)
            )
        
        role_filter = self.request.GET.get('role')
        if role_filter:
            queryset = queryset.filter(role=role_filter)
        
        status_filter = self.request.GET.get('status')
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('first_name', 'last_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_create_users'] = can_manage_users(self.request.user)
        return context

class UserDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'user_view'
    model = User
    template_name = 'core/users/user_detail.html'
    context_object_name = 'user_obj'
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not can_access_user_data(self.request.user, obj):
            raise PermissionDenied("Vous n'avez pas la permission d'accéder à ces données.")
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_obj = self.get_object()
        
        # Calculer les statistiques de l'utilisateur
        if user_obj.role == 'agent':
            context['stats'] = {
                'organizations_count': Organization.objects.filter(created_by=user_obj).count(),
                'adherents_count': Adherent.objects.filter(created_by=user_obj).count(),
                'interactions_count': Interaction.objects.filter(personnel=user_obj).count(),
                'categories_count': Category.objects.filter(
                    organizations__created_by=user_obj
                ).distinct().count(),
            }
        else:
            context['stats'] = {
                'organizations_count': 0,
                'adherents_count': 0,
                'interactions_count': 0,
                'categories_count': 0,
            }
        
        return context

class UserCreateView(PermissionRequiredMixin, CreateView):
    permission_required = 'user_create'
    model = User
    template_name = 'core/users/user_form.html'
    form_class = UserRegistrationForm
    
    def dispatch(self, request, *args, **kwargs):
        if not can_manage_users(request.user):
            raise PermissionDenied("Vous n'avez pas la permission de créer des utilisateurs.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Limiter les choix de rôle selon l'utilisateur connecté
        if self.request.user.role == 'superviseur':
            form.fields['role'].choices = [('agent', 'Agent')]
            form.fields['role'].initial = 'agent'
        # Si c'est un admin qui créer un agent voir seulement les superviseurs
        if self.request.user.is_superuser or self.request.user.role == 'admin':
            form.fields['created_by'].queryset = User.objects.filter(role='superviseur')
        return form
    
    def form_valid(self, form):
        user = form.save(commit=False)
        if not user.created_by:
            user.created_by = self.request.user
        user.save()
        
        # Afficher le mot de passe généré si applicable et envoyer l'email
        if hasattr(user, '_password_generated'):
            # Envoyer l'email de bienvenue
            if EmailService.send_welcome_email(user, user._password_generated, self.request):
                messages.success(
                    self.request,
                    f"Utilisateur créé avec succès. Un email avec les informations de connexion a été envoyé à {user.email}"
                )
            else:
                messages.warning(
                    self.request,
                    f"Utilisateur créé avec succès, mais l'envoi de l'email a échoué. Mot de passe généré : {user._password_generated}"
                )
        else:
            messages.success(self.request, "Utilisateur créé avec succès.")
        
        return redirect('core:user_detail', pk=user.pk)

class UserUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = 'user_edit'
    model = User
    template_name = 'core/users/user_form.html'
    form_class = UserEditForm
    
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not can_access_user_data(request.user, obj):
            raise PermissionDenied("Vous n'avez pas la permission de modifier cet utilisateur.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_class(self):
        if self.request.user.role == 'admin':
            return UserEditForm
        else:
            return UserForm
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Configurer le champ created_by pour les admins
        if self.request.user.role == 'admin' or self.request.user.is_superuser:
            # Les admins peuvent assigner des superviseurs comme créateurs
            form.fields['created_by'].queryset = User.objects.filter(role='superviseur')
            form.fields['created_by'].label = "Assigné à (Superviseur)"
            form.fields['created_by'].help_text = "Sélectionnez le superviseur responsable de cet agent"
        
        return form
    
    def form_valid(self, form):
        user = form.save(commit=False)
        user.last_modified_by = self.request.user
        user.save()
        messages.success(self.request, "Utilisateur mis à jour avec succès.")
        return redirect('core:user_detail', pk=user.pk)

class UserDeleteView(PermissionRequiredMixin, DeleteView):
    permission_required = 'user_delete'
    model = User
    template_name = 'core/users/user_confirm_delete.html'
    context_object_name = 'user_obj'
    success_url = reverse_lazy('core:user_list')

    def dispatch(self, request, *args, **kwargs):
        user_obj = self.get_object()
        # Empêcher la suppression de soi-même
        if request.user == user_obj:
            messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
            raise PermissionDenied("Suppression de soi-même interdite.")
        # Empêcher la suppression du dernier admin
        if user_obj.role == 'admin':
            admin_count = User.objects.filter(role='admin', is_active=True).count()
            if admin_count <= 1:
                messages.error(request, "Impossible de supprimer le dernier administrateur.")
                raise PermissionDenied("Suppression du dernier administrateur interdite.")
        if not is_admin(request.user):
            raise PermissionDenied("Seuls les administrateurs peuvent supprimer des utilisateurs.")
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Utilisateur supprimé avec succès.")
        return super().delete(request, *args, **kwargs)

@login_required
@require_permission('badge_view')
def badge_list(request):
    """Liste des badges"""
    # if request.user.role not in ['agent', 'admin'] and not request.user.is_superuser:
    #     return HttpResponseForbidden("Accès refusé")
    
    badges = Badge.objects.select_related('adherent', 'issued_by').all()
    
    # Filtres
    status_filter = request.GET.get('status')
    if status_filter:
        badges = badges.filter(status=status_filter)
    
    # Filtre par échéance
    validity_filter = request.GET.get('validity')
    if validity_filter:
        from datetime import date, timedelta
        today = date.today()
        
        if validity_filter == 'expired':
            # Badges expirés
            badges = badges.filter(adherent__badge_validity__lt=today)
        elif validity_filter == 'expiring_soon':
            # Badges expirant dans les 30 prochains jours
            thirty_days_later = today + timedelta(days=30)
            badges = badges.filter(
                adherent__badge_validity__gte=today,
                adherent__badge_validity__lte=thirty_days_later
            )
        elif validity_filter == 'valid':
            # Badges valides (pas expirés)
            badges = badges.filter(adherent__badge_validity__gte=today)
        elif validity_filter == 'expiring_week':
            # Badges expirant dans les 7 prochains jours
            week_later = today + timedelta(days=7)
            badges = badges.filter(
                adherent__badge_validity__gte=today,
                adherent__badge_validity__lte=week_later
            )
        elif validity_filter == 'expiring_month':
            # Badges expirant dans les 30 prochains jours
            month_later = today + timedelta(days=30)
            badges = badges.filter(
                adherent__badge_validity__gte=today,
                adherent__badge_validity__lte=month_later
            )
    
    # Tri par défaut
    badges = badges.order_by('-issued_date')
    
    context = {
        'badges': badges,
        'status_choices': Badge.STATUS_CHOICES,
        'validity_choices': [
            ('', 'Toutes les échéances'),
            ('valid', 'Badges valides'),
            ('expired', 'Badges expirés'),
            ('expiring_week', 'Expire dans 7 jours'),
            ('expiring_month', 'Expire dans 30 jours'),
        ],
        'current_status': status_filter,
        'current_validity': validity_filter,
    }
    return render(request, 'core/badges/badge_list.html', context)

@login_required
@require_permission('badge_view')
def badge_detail(request, badge_id):
    """Afficher les détails d'un badge"""
    # if request.user.role not in ['agent', 'admin'] and not request.user.is_superuser:
    #     return HttpResponseForbidden("Accès refusé")
    
    try:
        badge = Badge.objects.filter(id=badge_id).first()
        if not badge:
            raise Http404("Badge non trouvé")
    except Badge.MultipleObjectsReturned:
        # En cas de doublons, prendre le plus récent
        badge = Badge.objects.filter(id=badge_id).order_by('-issued_date').first()
    
    context = {
        'badge': badge,
    }
    return render(request, 'core/badges/badge_detail.html', context)

@login_required
@require_permission('badge_view')
def badge_card(request, badge_id):
    """Afficher le badge comme une carte d'identité"""
    # if request.user.role not in ['agent', 'admin'] and not request.user.is_superuser:
    #     return HttpResponseForbidden("Accès refusé")
    
    try:
        badge = Badge.objects.filter(id=badge_id).first()
        if not badge:
            raise Http404("Badge non trouvé")
    except Badge.MultipleObjectsReturned:
        # En cas de doublons, prendre le plus récent
        badge = Badge.objects.filter(id=badge_id).order_by('-issued_date').first()
    
    context = {
        'badge': badge,
    }
    return render(request, 'core/badges/badge_card.html', context)

@login_required
@require_permission('badge_create')
def generate_badge(request, adherent_id):
    """Générer un badge pour un adhérent (avec option de régénération)"""
    adherent = get_object_or_404(Adherent, id=adherent_id)
    force = request.GET.get('force') == '1'
    
    # Supprimer tous les badges actifs ET révoqués si force
    if force:
        old_badges = Badge.objects.filter(adherent=adherent, status__in=['active', 'revoked'])
        count = old_badges.count()
        old_badges.delete()
        if count:
            messages.info(request, f"{count} badge(s) précédent(s) supprimé(s) automatiquement.")
    else:
        # Vérifier s'il y a des badges actifs
        existing_badges = Badge.objects.filter(adherent=adherent, status='active')
        existing_badge = existing_badges.first()  # Prendre le premier pour la vérification
        if existing_badge and existing_badge.is_valid:
            messages.warning(request, f"{adherent.full_name} a déjà un badge actif valide jusqu'au {adherent.badge_validity}.")
            return redirect('core:adherent_detail', adherent_id=adherent_id)
    
    # Vérifier que l'adhérent a bien une activité et une validité de badge
    if not adherent.activity_name or not adherent.badge_validity:
        messages.error(request, "Veuillez d'abord renseigner l'activité et la validité du badge pour cet adhérent.")
        return redirect('core:adherent_detail', adherent_id=adherent_id)
    
    if request.method == 'POST':
        try:
            # Récupérer l'image d'activité si fournie
            activity_image = request.FILES.get('activity_image')
            
            badge = Badge.objects.create(
                adherent=adherent,
                issued_by=request.user,
                badge_validity=adherent.badge_validity,
                activity_name=adherent.activity_name,
                notes=f"Badge généré le {timezone.now().strftime('%d/%m/%Y à %H:%M')}"
            )
            
            # Sauvegarder l'image d'activité si fournie
            if activity_image:
                badge.activity_image = activity_image
                badge.save()
            
            badge.refresh_from_db()
            qr_data = f"ADHERENT:{adherent.identifiant}|BADGE:{badge.badge_number}|VALID:{adherent.badge_validity}"
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill='black', back_color='white')
            img_io = BytesIO()
            img.save(img_io, 'PNG')
            img_io.seek(0)
            filename = f"qr_badge_{badge.badge_number}.png"
            badge.qr_code.save(filename, File(img_io), save=True)
            badge.refresh_from_db()
            if badge.id:
                messages.success(request, f"Badge {badge.badge_number} généré avec succès pour {adherent.full_name}.")
                return redirect('core:badge_detail', badge_id=badge.id)
            else:
                messages.error(request, "Erreur : le badge n'a pas pu être créé correctement.")
                return redirect('core:adherent_detail', adherent_id=adherent_id)
        except Exception as e:
            messages.error(request, f"Erreur lors de la génération du badge: {str(e)}")
            return redirect('core:adherent_detail', adherent_id=adherent_id)
    
    context = {
        'adherent': adherent,
    }
    return render(request, 'core/badges/badge_generation.html', context)

@login_required
@require_permission('badge_revoke')
def revoke_badge(request, badge_id):
    """Révoquer un badge"""
    # if request.user.role not in ['agent', 'admin'] and not request.user.is_superuser:
    #     return HttpResponseForbidden("Accès refusé")
    
    try:
        badge = Badge.objects.filter(id=badge_id).first()
        if not badge:
            raise Http404("Badge non trouvé")
    except Badge.MultipleObjectsReturned:
        # En cas de doublons, prendre le plus récent
        badge = Badge.objects.filter(id=badge_id).order_by('-issued_date').first()
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        badge.revoke(reason=reason, revoked_by=request.user.get_full_name())
        messages.success(request, f"Badge {badge.badge_number} révoqué avec succès.")
        return redirect('core:badge_list')
    
    context = {
        'badge': badge,
    }
    return render(request, 'core/badges/badge_revoke.html', context)

@login_required
@require_permission('badge_edit')
def reactivate_badge(request, badge_id):
    """Réactiver un badge"""
    # if request.user.role not in ['agent', 'admin'] and not request.user.is_superuser:
    #     return HttpResponseForbidden("Accès refusé")
    
    try:
        badge = Badge.objects.filter(id=badge_id).first()
        if not badge:
            raise Http404("Badge non trouvé")
    except Badge.MultipleObjectsReturned:
        # En cas de doublons, prendre le plus récent
        badge = Badge.objects.filter(id=badge_id).order_by('-issued_date').first()
    
    badge.reactivate(reactivated_by=request.user.get_full_name())
    messages.success(request, f"Badge {badge.badge_number} réactivé avec succès.")
    return redirect('core:badge_list')

@login_required
@require_permission('badge_view')
def download_badge_pdf(request, badge_id):
    """Télécharger le badge en PDF"""
    # if request.user.role not in ['agent', 'admin'] and not request.user.is_superuser:
    #     return HttpResponseForbidden("Accès refusé")
    
    try:
        badge = Badge.objects.filter(id=badge_id).first()
        if not badge:
            raise Http404("Badge non trouvé")
    except Badge.MultipleObjectsReturned:
        # En cas de doublons, prendre le plus récent
        badge = Badge.objects.filter(id=badge_id).order_by('-issued_date').first()
    
    # Créer le PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="badge_{badge.badge_number}.pdf"'
    
    # Créer le document PDF
    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.grey,
        fontName='Helvetica'
    )
    
    # Titre principal
    elements.append(Paragraph("BADGE D'ADHÉRENT", title_style))
    elements.append(Paragraph("Impact Data Platform", subtitle_style))
    elements.append(Spacer(1, 20))
    
    # Créer un tableau pour le badge avec image
    badge_data = []
    
    # En-tête avec numéro de badge
    badge_data.append([
        Paragraph(f"<b>Numéro de Badge:</b> {badge.badge_number}", styles['Normal']),
        Paragraph(f"<b>Statut:</b> {badge.get_status_display()}", styles['Normal'])
    ])
    
    # Informations de l'adhérent
    badge_data.append([
        Paragraph(f"<b>Nom complet:</b> {badge.adherent.full_name}", styles['Normal']),
        Paragraph(f"<b>Identifiant:</b> {badge.adherent.identifiant}", styles['Normal'])
    ])
    
    badge_data.append([
        Paragraph(f"<b>Organisation:</b> {badge.adherent.organisation.name}", styles['Normal']),
        Paragraph(f"<b>Activité:</b> {badge.adherent.activity_name}", styles['Normal'])
    ])
    
    badge_data.append([
        Paragraph(f"<b>Type:</b> {badge.adherent.get_type_adherent_display()}", styles['Normal']),
        Paragraph(f"<b>Date d'adhésion:</b> {badge.adherent.join_date.strftime('%d/%m/%Y')}", styles['Normal'])
    ])
    
    badge_data.append([
        Paragraph(f"<b>Date d'émission:</b> {badge.issued_date.strftime('%d/%m/%Y')}", styles['Normal']),
        Paragraph(f"<b>Validité jusqu'au:</b> {badge.adherent.badge_validity.strftime('%d/%m/%Y')}", styles['Normal'])
    ])
    
    if badge.issued_by:
        badge_data.append([
            Paragraph(f"<b>Émis par:</b> {badge.issued_by.get_full_name()}", styles['Normal']),
            Paragraph("", styles['Normal'])  # Cellule vide pour l'alignement
        ])
    
    # Créer le tableau principal
    badge_table = Table(badge_data, colWidths=[8*cm, 8*cm])
    badge_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(badge_table)
    elements.append(Spacer(1, 30))
    
    # Section pour l'image de profil si disponible
    if badge.adherent.profile_picture:
        elements.append(Paragraph("<b>Photo de profil:</b>", styles['Heading3']))
        elements.append(Spacer(1, 10))
        
        # Note: Pour inclure l'image dans le PDF, il faudrait utiliser Image de reportlab
        # Mais cela nécessiterait des modifications plus complexes
        elements.append(Paragraph(f"<i>Photo disponible: {badge.adherent.profile_picture.name}</i>", styles['Normal']))
        elements.append(Spacer(1, 20))
    
    # Section pour le QR code si disponible
    if badge.qr_code:
        elements.append(Paragraph("<b>QR Code:</b>", styles['Heading3']))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"<i>QR Code disponible: {badge.qr_code.name}</i>", styles['Normal']))
        elements.append(Spacer(1, 20))
    
    # Notes si présentes
    if badge.notes:
        elements.append(Paragraph("<b>Notes:</b>", styles['Heading3']))
        elements.append(Paragraph(badge.notes, styles['Normal']))
        elements.append(Spacer(1, 20))
    
    # Footer
    elements.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.grey,
        fontName='Helvetica'
    )
    elements.append(Paragraph(f"Document généré le {timezone.now().strftime('%d/%m/%Y à %H:%M')}", footer_style))
    
    # Construire le PDF
    doc.build(elements)
    return response

@login_required
@require_permission('badge_view')
def download_badge_jpg(request, badge_id):
    """Télécharger le badge en JPG - EXACTEMENT comme le HTML avec html2image"""
    try:
        badge = Badge.objects.filter(id=badge_id).first()
        if not badge:
            raise Http404("Badge non trouvé")
    except Badge.MultipleObjectsReturned:
        # En cas de doublons, prendre le plus récent
        badge = Badge.objects.filter(id=badge_id).order_by('-issued_date').first()
    
    # Générer le HTML du badge
    html_content = render_to_string('core/badges/badge_card.html', {
        'badge': badge,
        'static_url': settings.STATIC_URL,
    })
    
    try:
        # Utiliser html2image comme méthode principale
        hti = Html2Image()
        
        # Configuration pour correspondre exactement au design
        hti.size = (400, 600)
        hti.output_path = '/tmp'  # Dossier temporaire
        
        # Configuration avancée pour un rendu optimal
        hti.browser_executable = None  # Utiliser le navigateur par défaut
        hti.custom_flags = [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor'
        ]
        
        # Vérifier si le navigateur est disponible
        try:
            # Essayer de trouver Chrome sur Windows
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME', '')),
            ]
            
            chrome_found = False
            for path in chrome_paths:
                if os.path.exists(path):
                    hti.browser_executable = path
                    chrome_found = True
                    break
            
            if not chrome_found:
                # Essayer la détection automatique
                hti.browser_executable = hti.browser_executable or hti.get_browser_executable()
                
        except Exception as e:
            print(f"Erreur détection navigateur: {str(e)}")
            # Si pas de navigateur, passer directement à imgkit
            raise Exception("Aucun navigateur compatible trouvé")
        
        # Capturer l'image
        print(f"Utilisation du navigateur: {hti.browser_executable}")
        hti.screenshot(html_str=html_content, save_as=f'badge_{badge.badge_number}.jpg')
        
        # Lire le fichier généré
        image_path = f'/tmp/badge_{badge.badge_number}.jpg'
        with open(image_path, 'rb') as f:
            img_data = f.read()
        
        # Supprimer le fichier temporaire
        try:
            os.remove(image_path)
        except:
            pass
        
        # Créer la réponse HTTP
        response = HttpResponse(img_data, content_type='image/jpeg')
        response['Content-Disposition'] = f'attachment; filename="badge_{badge.badge_number}.jpg"'
        
        return response
        
    except Exception as e:
        # Log l'erreur pour diagnostic
        print(f"Erreur html2image: {str(e)}")
        
        # Fallback vers imgkit si html2image échoue
        try:
            messages.warning(request, f"Erreur avec html2image: {str(e)}. Utilisation d'imgkit.")
            return download_badge_jpg_imgkit(request, badge_id)
        except Exception as e2:
            # Fallback vers la méthode PIL si imgkit échoue aussi
            print(f"Erreur imgkit: {str(e2)}")
            messages.warning(request, f"Erreur avec imgkit: {str(e2)}. Utilisation de la méthode PIL.")
            return download_badge_jpg_pil(request, badge_id)

def download_badge_jpg_imgkit(request, badge_id):
    """Méthode de fallback imgkit pour générer le badge JPG"""
    try:
        badge = Badge.objects.filter(id=badge_id).first()
        if not badge:
            raise Http404("Badge non trouvé")
    except Badge.MultipleObjectsReturned:
        badge = Badge.objects.filter(id=badge_id).order_by('-issued_date').first()
    
    # Générer le HTML du badge
    html_content = render_to_string('core/badges/badge_card.html', {
        'badge': badge,
        'static_url': settings.STATIC_URL,
    })
    
    # Configuration imgkit pour correspondre exactement au design
    options = {
        'width': 400,
        'height': 600,
        'quality': 95,
        'format': 'jpg',
        'encoding': 'UTF-8',
        'enable-local-file-access': None,
        'disable-smart-shrinking': None,
        'zoom': 1.0,
        'margin-top': '0',
        'margin-right': '0',
        'margin-bottom': '0',
        'margin-left': '0',
        'no-outline': None,
        'no-background': None,
    }
    
    try:
        # Convertir le HTML en image JPG
        img_data = imgkit.from_string(html_content, False, options=options)
        
        # Créer la réponse HTTP
        response = HttpResponse(img_data, content_type='image/jpeg')
        response['Content-Disposition'] = f'attachment; filename="badge_{badge.badge_number}.jpg"'
        
        return response
        
    except Exception as e:
        print(f"Erreur imgkit: {str(e)}")
        raise e

def download_badge_jpg_pil(request, badge_id):
    """Méthode de fallback PIL pour générer le badge JPG"""
    try:
        badge = Badge.objects.filter(id=badge_id).first()
        if not badge:
            raise Http404("Badge non trouvé")
    except Badge.MultipleObjectsReturned:
        badge = Badge.objects.filter(id=badge_id).order_by('-issued_date').first()
    
    # Dimensions exactes du HTML
    width, height = 400, 600
    
    # Créer l'image avec fond blanc
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        # Polices similaires au HTML
        font_large = ImageFont.truetype("arial.ttf", 24)
        font_medium = ImageFont.truetype("arial.ttf", 16)
        font_small = ImageFont.truetype("arial.ttf", 12)
        font_title = ImageFont.truetype("arial.ttf", 14)
        font_subtitle = ImageFont.truetype("arial.ttf", 10)
        font_name = ImageFont.truetype("arial.ttf", 20)
        font_job = ImageFont.truetype("arial.ttf", 24)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_title = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()
        font_name = ImageFont.load_default()
        font_job = ImageFont.load_default()
    
    # 1. EN-TÊTE - Drapeau guinéen
    header_height = 65
    band_width = width // 3
    
    # Drapeau guinéen avec les mêmes couleurs
    draw.rectangle([0, 0, band_width, header_height], fill='#e74c3c')  # Rouge
    draw.rectangle([band_width, 0, 2*band_width, header_height], fill='#f1c40f')  # Jaune
    draw.rectangle([2*band_width, 0, width, header_height], fill='#27ae60')  # Vert
    
    # Texte de l'en-tête
    draw.text((20, 15), "RÉPUBLIQUE DE GUINÉE", fill='white', font=font_title)
    draw.text((20, 35), "Travail – Justice – Solidarité", fill='white', font=font_subtitle)
    
    # Logo Guinée
    logo_x = width - 70
    logo_y = 7
    draw.ellipse([logo_x, logo_y, logo_x + 50, logo_y + 50], fill='white', outline='white')
    draw.text((logo_x + 15, logo_y + 15), "GN", fill='#2c3e50', font=font_medium)
    
    # 2. ZONE PRINCIPALE
    main_start = header_height + 16
    main_padding = 16
    
    # Section gauche (60% de la largeur)
    left_section_x = main_padding
    left_section_y = main_start
    left_section_width = int(width * 0.6) - main_padding
    
    # Logo Impact Data
    logo_height = 45
    logo_width = 120
    draw.rectangle([left_section_x, left_section_y, left_section_x + logo_width, left_section_y + logo_height], 
                   fill='white', outline='#d1d5db', width=2)
    draw.text((left_section_x + 10, left_section_y + 15), "IMPACT DATA", fill='#2c3e50', font=font_medium)
    
    # Titre du métier
    job_title_y = left_section_y + logo_height + 15
    job_title = badge.adherent.organisation.name.upper() if badge.adherent.organisation else "ACTIVITÉ"
    draw.text((left_section_x, job_title_y), job_title, fill='#27ae60', font=font_job)
    
    # Sous-titre pour mécanique
    if badge.adherent.organisation and badge.adherent.organisation.name.upper() == "MÉCANIQUE":
        subtitle_y = job_title_y + 30
        draw.text((left_section_x, subtitle_y), "(TRICYCLE)", fill='#2c3e50', font=font_medium)
    
    # 3. SECTION DROITE - QR Code et Photo
    right_section_x = left_section_x + left_section_width + 20
    right_section_y = main_start + 20
    
    # QR Code
    qr_size = 100
    qr_x = right_section_x
    qr_y = right_section_y
    draw.rectangle([qr_x, qr_y, qr_x + qr_size, qr_y + qr_size], 
                   fill='white', outline='#2c3e50', width=2)
    draw.text((qr_x + 35, qr_y + 40), "QR", fill='#2c3e50', font=font_medium)
    
    # Activité sous le QR
    activity_y = qr_y + qr_size + 8
    activity_text = badge.adherent.activity_name or "Activité"
    draw.text((qr_x + 20, activity_y), activity_text, fill='#e74c3c', font=font_medium)
    
    # Photo de profil
    photo_size = 120
    photo_x = qr_x + qr_size + 20
    photo_y = right_section_y
    
    draw.ellipse([photo_x, photo_y, photo_x + photo_size, photo_y + photo_size], 
                 fill='#f8f9fa', outline='#e74c3c', width=4)
    draw.text((photo_x + 50, photo_y + 50), "PHOTO", fill='#6c757d', font=font_medium)
    
    # 4. INFORMATIONS PERSONNELLES
    info_start_y = photo_y + photo_size + 15
    
    # Nom de l'adhérent
    name_y = info_start_y
    name_width = draw.textlength(badge.adherent.full_name, font=font_name)
    name_x = (width - name_width) // 2
    draw.text((name_x, name_y), badge.adherent.full_name, fill='#2c3e50', font=font_name)
    
    # ID avec chiffres dans des cercles
    id_y = name_y + 30
    id_label = "ID:"
    id_label_width = draw.textlength(id_label, font=font_medium)
    
    id_digits = str(badge.adherent.identifiant)
    total_id_width = id_label_width + 5 + len(id_digits) * 30 + 10 + 40
    id_start_x = (width - total_id_width) // 2
    
    draw.text((id_start_x, id_y), id_label, fill='#2c3e50', font=font_medium)
    
    digit_x = id_start_x + id_label_width + 5
    for i, digit in enumerate(id_digits):
        circle_x = digit_x + i * 30
        draw.ellipse([circle_x, id_y - 5, circle_x + 25, id_y + 20], 
                     fill='#17a2b8', outline='#17a2b8')
        draw.text((circle_x + 8, id_y), digit, fill='white', font=font_small)
    
    # Suffix du badge
    suffix_x = digit_x + len(id_digits) * 30 + 10
    suffix_text = badge.badge_number[-3:] if len(badge.badge_number) >= 3 else badge.badge_number
    draw.rectangle([suffix_x, id_y - 5, suffix_x + 40, id_y + 20], 
                   fill='#6c757d', outline='#6c757d')
    draw.text((suffix_x + 5, id_y), suffix_text, fill='white', font=font_small)
    
    # Contact
    contact_y = id_y + 30
    phone_text = badge.adherent.phone1
    lieu_text = badge.adherent.commune.upper()
    
    phone_width = draw.textlength(phone_text, font=font_medium)
    lieu_width = draw.textlength(lieu_text, font=font_medium)
    total_contact_width = phone_width + 15 + lieu_width
    
    contact_start_x = (width - total_contact_width) // 2
    draw.text((contact_start_x, contact_y), phone_text, fill='#2c3e50', font=font_medium)
    draw.text((contact_start_x + phone_width + 15, contact_y), lieu_text, fill='#e74c3c', font=font_medium)
    
    # 5. IMAGE URGENCE
    urgence_y = height - 140
    urgence_height = 90
    draw.rectangle([20, urgence_y, width - 20, urgence_y + urgence_height], 
                   fill='#f8f9fa', outline='#e5e7eb')
    draw.text((width // 2 - 30, urgence_y + 35), "URGENCE", fill='#dc2626', font=font_large)
    
    # 6. FOOTER
    footer_y = height - 35
    draw.rectangle([0, footer_y, width, height], fill='white', outline='#e5e7eb')
    
    footer_logo_x = 16
    footer_logo_y = footer_y + 5
    draw.rectangle([footer_logo_x, footer_logo_y, footer_logo_x + 45, footer_logo_y + 45], 
                   fill='white', outline='#e5e7eb')
    draw.text((footer_logo_x + 5, footer_logo_y + 15), "IMPACT", fill='#2c3e50', font=font_small)
    
    validite_text = f"Validité {badge.badge_validity.strftime('%B %Y')}"
    validite_width = draw.textlength(validite_text, font=font_small)
    validite_x = width - validite_width - 16
    draw.text((validite_x, footer_y + 15), validite_text, fill='#2c3e50', font=font_small)
    
    # Convertir l'image en bytes
    img_io = BytesIO()
    img.save(img_io, format='JPEG', quality=95)
    img_io.seek(0)
    
    # Créer la réponse HTTP
    response = HttpResponse(img_io.getvalue(), content_type='image/jpeg')
    response['Content-Disposition'] = f'attachment; filename="badge_{badge.badge_number}.jpg"'
    
    return response

@login_required
@require_permission('badge_view')
def badge_qr_scan(request):
    """Scanner un QR code de badge"""
    # if request.user.role not in ['superviseur', 'admin', 'agent'] and not request.user.is_superuser:
    #     return HttpResponseForbidden("Accès refusé")
    
    if request.method == 'POST':
        qr_data = request.POST.get('qr_data', '')
        
        try:
            # Parser les données du QR code
            # Format: ADHERENT:ID|BADGE:NUMBER|VALID:DATE
            parts = qr_data.split('|')
            adherent_id = None
            badge_number = None
            
            for part in parts:
                if part.startswith('ADHERENT:'):
                    adherent_id = part.split(':')[1]
                elif part.startswith('BADGE:'):
                    badge_number = part.split(':')[1]
            
            if adherent_id and badge_number:
                adherent = Adherent.objects.get(identifiant=adherent_id)
                # Utiliser filter() et prendre le badge actif le plus récent
                badges = Badge.objects.filter(badge_number=badge_number).order_by('-issued_date')
                if badges.exists():
                    badge = badges.first()  # Prendre le plus récent
                else:
                    raise Badge.DoesNotExist()
                
                context = {
                    'adherent': adherent,
                    'badge': badge,
                    'is_valid': badge.is_valid,
                    'scanned_data': qr_data,
                    'now': timezone.now(),
                }
                return render(request, 'core/badges/badge_scan_result.html', context)
            else:
                messages.error(request, "Données QR code invalides.")
                
        except (Adherent.DoesNotExist, Badge.DoesNotExist):
            messages.error(request, "Badge ou adhérent non trouvé.")
        except Exception as e:
            messages.error(request, f"Erreur lors du scan: {str(e)}")
    
    return render(request, 'core/badges/badge_scan.html')

# Objective Management Views (Supervisor only)
class ObjectiveListView(PermissionRequiredMixin, ListView):
    permission_required = 'objective_view'
    model = UserObjective
    template_name = 'core/objectives/objective_list.html'
    context_object_name = 'objectives'
    paginate_by = 20
    
    def get_queryset(self):
        # Mettre à jour automatiquement tous les objectifs avant de les afficher
        UserObjective.update_all_objectives()
        
        if self.request.user.role == 'admin':
            return UserObjective.objects.all().order_by('-created_at')
        elif self.request.user.role == 'superviseur':
            return UserObjective.objects.filter(assigned_by=self.request.user).order_by('-created_at')
        else:
            return UserObjective.objects.filter(user=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_create_objectives'] = self.request.user.role in ['admin', 'superviseur']
        return context

class ObjectiveDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'objective_view'
    model = UserObjective
    template_name = 'core/objectives/objective_detail.html'
    context_object_name = 'objective'
    
    def get_queryset(self):
        if self.request.user.role == 'admin':
            return UserObjective.objects.all()
        elif self.request.user.role == 'superviseur':
            return UserObjective.objects.filter(assigned_by=self.request.user)
        else:
            return UserObjective.objects.filter(user=self.request.user)
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Mettre à jour la progression de cet objectif spécifique
        obj.update_progress()
        return obj

class ObjectiveCreateView(PermissionRequiredMixin, CreateView):
    permission_required = 'objective_create'
    model = UserObjective
    template_name = 'core/objectives/objective_form.html'
    form_class = UserObjectiveForm
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.role in ['admin', 'superviseur']:
            raise PermissionDenied("Seuls les administrateurs et superviseurs peuvent créer des objectifs.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.user.role == 'superviseur':
            # Les superviseurs ne peuvent assigner des objectifs qu'aux agents qu'ils ont créés
            form.fields['user'].queryset = User.objects.filter(
                role='agent',
                created_by=self.request.user
            )
        return form
    
    def form_valid(self, form):
        objective = form.save(commit=False)
        objective.assigned_by = self.request.user
        objective.save()
        messages.success(self.request, "Objectif créé avec succès.")
        return redirect('core:objective_detail', pk=objective.pk)
    
    def form_invalid(self, form):
        print("❌ Formulaire invalide :", form.errors)
        return super().form_invalid(form)

class ObjectiveUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = 'objective_edit'
    model = UserObjective
    template_name = 'core/objectives/objective_form.html'
    form_class = UserObjectiveForm
    
    def get_queryset(self):
        if self.request.user.role == 'admin':
            return UserObjective.objects.all()
        elif self.request.user.role == 'superviseur':
            return UserObjective.objects.filter(assigned_by=self.request.user)
        else:
            # return UserObjective.objects.filter(user=self.request.user)
            raise PermissionDenied("Vous n'avez pas les permissions pour modifier les objectifs.")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.user.role=='superviseur':
            form.fields['user'].queryset = User.objects.filter(
                role='agent',
                created_by=self.request.user
            )
        return form
    
    def form_valid(self, form):
        messages.success(self.request, "Objectif mis à jour avec succès.")
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('core:objective_detail', kwargs={'pk': self.object.pk})

class ObjectiveDeleteView(PermissionRequiredMixin, DeleteView):
    permission_required = 'objective_delete'
    model = UserObjective
    template_name = 'core/objectives/objective_confirm_delete.html'
    context_object_name = 'objective'
    success_url = reverse_lazy('core:objective_list')
    
    def get_queryset(self):
        if self.request.user.role == 'admin':
            return UserObjective.objects.all()
        elif self.request.user.role == 'superviseur':
            return UserObjective.objects.filter(assigned_by=self.request.user)
        else:
            # return UserObjective.objects.filter(user=self.request.user)
            raise PermissionDenied("Vous n'avez pas les permissions pour supprimer les objectifs.")
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Objectif supprimé avec succès.")
        return super().delete(request, *args, **kwargs)

@login_required
def objective_actions(request, pk):
    """Vue pour afficher les actions effectuées par un agent pour un objectif"""
    try:
        objective = UserObjective.objects.get(pk=pk)
    except UserObjective.DoesNotExist:
        messages.error(request, "Objectif non trouvé.")
        return redirect('core:objective_list')
    
    # Vérifier les permissions
    if request.user.role == 'agent':
        if objective.user != request.user:
            raise PermissionDenied("Vous ne pouvez voir que vos propres objectifs.")
    elif request.user.role == 'superviseur':
        if objective.assigned_by != request.user:
            raise PermissionDenied("Vous ne pouvez voir que les objectifs que vous avez assignés.")
    # Admin peut voir tous les objectifs
    
    # Récupérer les éléments créés par l'agent pour cet objectif
    agent = objective.user
    objective_created_at = objective.created_at
    
    # Filtrer les éléments créés après l'assignation de l'objectif
    actions = []
    
    if objective.objective_type == 'organizations':
        organizations = Organization.objects.filter(
            created_by=agent,
            # created_at__gte=objective_created_at
        ).order_by('-created_at')
        
        for org in organizations:
            actions.append({
                'type': 'organization',
                'object': org,
                'created_at': org.created_at,
                'title': org.name,
                'description': f"Organisation créée dans la catégorie {org.category.name}",
                'url': reverse('core:organization_detail', kwargs={'organization_id': org.id})
            })
    
    elif objective.objective_type == 'adherents':
        adherents = Adherent.objects.filter(
            created_by=agent,
            # created_at__gte=objective_created_at
        ).order_by('-created_at')
        
        for adherent in adherents:
            actions.append({
                'type': 'adherent',
                'object': adherent,
                'created_at': adherent.created_at,
                'title': adherent.full_name,
                'description': f"Adhérent ajouté à {adherent.organisation.name}",
                'url': reverse('core:adherent_detail', kwargs={'adherent_id': adherent.id})
            })
    
    elif objective.objective_type == 'interactions':
        interactions = Interaction.objects.filter(
            auteur=agent,
            # created_at__gte=objective_created_at
        ).order_by('-created_at')
        
        for interaction in interactions:
            actions.append({
                'type': 'interaction',
                'object': interaction,
                'created_at': interaction.created_at,
                'title': f"Interaction avec {interaction.adherent.full_name}",
                'description': f"Statut: {interaction.get_status_display()}",
                'url': reverse('core:interaction_detail', kwargs={'interaction_id': interaction.id})
            })
    
    context = {
        'objective': objective,
        'actions': actions,
        'agent': agent,
        'total_actions': len(actions),
        'objective_type_display': objective.get_objective_type_display(),
    }
    
    return render(request, 'core/objectives/objective_actions.html', context)

@login_required
def refresh_objectives(request):
    """Vue pour rafraîchir manuellement les objectifs"""
    if request.user.role not in ['admin', 'superviseur']:
        return HttpResponseForbidden("Accès refusé")
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        
        if user_id:
            # Rafraîchir les objectifs d'un utilisateur spécifique
            try:
                user = User.objects.get(id=user_id)
                updated_count = UserObjective.update_objectives_for_user(user)
                messages.success(request, f"Objectifs de {user.get_full_name()} mis à jour ({updated_count} modification(s)).")
            except User.DoesNotExist:
                messages.error(request, "Utilisateur non trouvé.")
        else:
            # Rafraîchir tous les objectifs assignés par ce superviseur
            if request.user.role == 'superviseur':
                objectives = UserObjective.objects.filter(assigned_by=request.user)
                updated_count = 0
                for objective in objectives:
                    old_status = objective.status
                    old_value = objective.current_value
                    objective.update_progress()
                    if (objective.status != old_status or objective.current_value != old_value):
                        updated_count += 1
                messages.success(request, f"Tous les objectifs mis à jour ({updated_count} modification(s)).")
            else:
                # Admin peut rafraîchir tous les objectifs
                updated_count = UserObjective.update_all_objectives()
                messages.success(request, f"Tous les objectifs mis à jour ({updated_count} modification(s)).")
        
        return redirect('core:objective_list')
    
    # GET request - afficher la page de rafraîchissement
    if request.user.role == 'superviseur':
        agents = User.objects.filter(role='agent', created_by=request.user)
    else:
        agents = User.objects.filter(role='agent')
    
    context = {
        'agents': agents,
    }
    return render(request, 'core/objectives/refresh_objectives.html', context)

# ==================== PASSWORD RESET VIEWS ====================

def password_reset_request(request):
    """Vue pour demander la réinitialisation de mot de passe"""
    if request.method == 'POST':
        email = request.POST.get('email')
        matricule = request.POST.get('matricule')
        
        if email and matricule:
            try:
                user = User.objects.get(email=email, matricule=matricule)
                if user.is_active:
                    # Générer le token et l'URL de réinitialisation
                    token = default_token_generator.make_token(user)
                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    
                    # Construire l'URL de réinitialisation
                    current_site = get_current_site(request)
                    reset_url = f"http://{current_site.domain}{reverse_lazy('core:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})}"
                    
                    # Envoyer l'email
                    if EmailService.send_password_reset_email(user, reset_url, request):
                        messages.success(request, 'Un email de réinitialisation a été envoyé à votre adresse email.')
                        return redirect('core:password_reset_done')
                    else:
                        messages.error(request, 'Erreur lors de l\'envoi de l\'email. Veuillez réessayer.')
                else:
                    messages.error(request, 'Ce compte est désactivé.')
            except User.DoesNotExist:
                messages.error(request, 'Aucun utilisateur trouvé avec ces informations.')
        else:
            messages.error(request, 'Veuillez remplir tous les champs.')
    
    return render(request, 'core/auth/password_reset_request.html')

def password_reset_confirm(request, uidb64, token):
    """Vue pour confirmer la réinitialisation de mot de passe"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            
            if password1 and password2:
                if password1 == password2:
                    if len(password1) >= 8:
                        user.set_password(password1)
                        user.save()
                        messages.success(request, 'Votre mot de passe a été changé avec succès.')
                        return redirect('core:password_reset_complete')
                    else:
                        messages.error(request, 'Le mot de passe doit contenir au moins 8 caractères.')
                else:
                    messages.error(request, 'Les mots de passe ne correspondent pas.')
            else:
                messages.error(request, 'Veuillez remplir tous les champs.')
    else:
        messages.error(request, 'Le lien de réinitialisation est invalide ou a expiré.')
        return redirect('core:password_reset_request')
    
    return render(request, 'core/auth/password_reset_confirm.html')

def password_reset_done(request):
    """Vue affichée après l'envoi de l'email de réinitialisation"""
    return render(request, 'core/auth/password_reset_done.html')

def password_reset_complete(request):
    """Vue affichée après la réinitialisation réussie du mot de passe"""
    return render(request, 'core/auth/password_reset_complete.html')

# ==================== VUES POUR LES PARAMÈTRES DE L'APPLICATION ====================

@login_required
@require_permission('settings_view')
def settings_dashboard(request):
    """Tableau de bord des paramètres de l'application"""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden("Accès refusé")
    
    # Statistiques des paramètres
    total_parameters = GeneralParameter.objects.count()
    total_references = ReferenceValue.objects.count()
    total_permissions = RolePermission.objects.count()
    recent_logs = SystemLog.objects.order_by('-timestamp')[:10]
    
    # Paramètres critiques
    critical_parameters = GeneralParameter.objects.filter(
        parameter_key__in=['organization_name', 'timezone', 'email_host']
    )
    
    # Valeurs de référence par catégorie
    reference_categories = ReferenceValue.objects.values('category').annotate(
        count=Count('id')
    ).order_by('category')
    
    context = {
        'total_parameters': total_parameters,
        'total_references': total_references,
        'total_permissions': total_permissions,
        'recent_logs': recent_logs,
        'critical_parameters': critical_parameters,
        'reference_categories': reference_categories,
        'now': timezone.now(),
    }
    return render(request, 'core/settings/settings_dashboard.html', context)


# ==================== VUES AJAX POUR LES SUGGESTIONS ====================

def personnel_search_api(request):
    """API pour la recherche de personnel par matricule, prénom ou nom"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        # Si pas de requête ou moins de 2 caractères, retourner tous les éléments
        personnel = User.objects.filter(is_active=True).order_by('matricule')
    else:
        # Recherche dans les champs matricule, first_name, last_name
        personnel = User.objects.filter(
            Q(matricule__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).filter(is_active=True).order_by('matricule')
    
    results = []
    for person in personnel:
        results.append({
            'id': person.id,
            'text': f"{person.matricule} - {person.get_full_name()}",
            'matricule': person.matricule,
            'name': person.get_full_name()
        })
    
    return JsonResponse({'results': results})


def adherent_search_api(request):
    """API pour la recherche d'adhérents par ID, matricule, téléphone, prénom ou nom"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        # Si pas de requête ou moins de 2 caractères, retourner quelques éléments
        adherents = Adherent.objects.all().order_by('id')
    else:
        # Séparer la requête en mots pour recherche multi-mots
        query_words = query.split()
        adherent_query = Q()
        
        # Si plusieurs mots, essayer de chercher prénom + nom
        if len(query_words) >= 2:
            for i in range(len(query_words)):
                for j in range(i+1, len(query_words)+1):
                    potential_first_name = ' '.join(query_words[:i+1])
                    potential_last_name = ' '.join(query_words[i+1:j])
                    
                    if potential_first_name and potential_last_name:
                        adherent_query |= (
                            Q(first_name__icontains=potential_first_name) &
                            Q(last_name__icontains=potential_last_name)
                        ) | (
                            Q(first_name__icontains=potential_last_name) &
                            Q(last_name__icontains=potential_first_name)
                        )
        
        # Ajouter aussi la recherche classique
        adherent_query |= (
            Q(id__icontains=query) |
            Q(identifiant__icontains=query) |
            Q(phone1__icontains=query) |
            Q(phone2__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )
        
        adherents = Adherent.objects.filter(adherent_query).distinct().order_by('last_name', 'first_name')
    
    results = []
    for adherent in adherents:
        profile_picture_url = adherent.profile_picture.url if adherent.profile_picture else None
        results.append({
            'id': adherent.id,
            'text': f"ID: {adherent.identifiant} - {adherent.first_name} {adherent.last_name}",
            'identifiant': adherent.identifiant,
            'name': f"{adherent.first_name} {adherent.last_name}",
            'phone': adherent.phone1 or adherent.phone2,
            'profile_picture': profile_picture_url
        })
    
    return JsonResponse({'results': results})


def organization_search_api(request):
    """API pour la recherche d'organisations par nom"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        # Si pas de requête ou moins de 2 caractères, retourner tous les éléments
        organizations = Organization.objects.all().order_by('name')
    else:
        # Recherche dans les champs name et identifiant
        organizations = Organization.objects.filter(
            Q(name__icontains=query) |
            Q(identifiant__icontains=query)
        ).order_by('name')[:500]
    
    results = []
    for org in organizations:
        results.append({
            'id': org.id,
            'text': f"{org.name} ({org.identifiant})",
            'name': org.name,
            'identifiant': org.identifiant
        })
    
    return JsonResponse({'results': results})


def category_search_api(request):
    """API pour la recherche de catégories par nom"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        # Si pas de requête ou moins de 2 caractères, retourner tous les éléments
        categories = Category.objects.all().order_by('name')
    else:
        # Recherche dans le champ name
        categories = Category.objects.filter(
            name__icontains=query
        ).order_by('name')
    
    results = []
    for category in categories:
        results.append({
            'id': category.id,
            'text': category.name,
            'name': category.name
        })
    
    return JsonResponse({'results': results})

# ==================== GESTION DES RÔLES ET PERMISSIONS ====================

@login_required
@require_permission('settings_roles')
def role_permissions_list(request):
    """Liste des permissions de rôles"""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden("Accès refusé")
    
    # Grouper par rôle
    roles_data = {}
    for role_code, role_name in User.ROLE_CHOICES:
        permissions = RolePermission.objects.filter(role=role_code).order_by('permission')
        roles_data[role_name] = {
            'code': role_code,
            'permissions': permissions,
            'active_count': permissions.filter(is_active=True).count(),
            'total_count': permissions.count()
        }
    
    context = {
        'roles_data': roles_data,
        'total_permissions': RolePermission.objects.count(),
        'active_permissions': RolePermission.objects.filter(is_active=True).count(),
    }
    return render(request, 'core/settings/role_permissions_list.html', context)

@login_required
@require_permission('settings_roles')
def role_permission_create(request):
    """Créer une nouvelle permission de rôle"""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden("Accès refusé")
    
    if request.method == 'POST':
        form = RolePermissionForm(request.POST)
        if form.is_valid():
            permission = form.save()
            role_display = dict(User.ROLE_CHOICES).get(permission.role, permission.role)
            permission_display = dict(RolePermission.PERMISSION_CHOICES).get(permission.permission, permission.permission)
            SystemLog.log(
                'INFO', 'system_config', 
                f'Permission créée: {role_display} - {permission_display}',
                user=request.user
            )
            messages.success(request, 'Permission créée avec succès.')
            return redirect('core:role_permissions_list')
    else:
        form = RolePermissionForm()
    
    return render(request, 'core/settings/role_permission_form.html', {
        'form': form, 
        'title': 'Créer une permission'
    })

@login_required
@require_permission('settings_roles')
def role_permission_update(request, permission_id):
    """Modifier une permission de rôle"""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden("Accès refusé")
    
    permission = get_object_or_404(RolePermission, id=permission_id)
    
    if request.method == 'POST':
        form = RolePermissionForm(request.POST, instance=permission)
        if form.is_valid():
            form.save()
            role_display = dict(User.ROLE_CHOICES).get(permission.role, permission.role)
            permission_display = dict(RolePermission.PERMISSION_CHOICES).get(permission.permission, permission.permission)
            SystemLog.log(
                'INFO', 'system_config', 
                f'Permission modifiée: {role_display} - {permission_display}',
                user=request.user
            )
            messages.success(request, 'Permission mise à jour avec succès.')
            return redirect('core:role_permissions_list')
    else:
        form = RolePermissionForm(instance=permission)
    
    return render(request, 'core/settings/role_permission_form.html', {
        'form': form, 
        'title': 'Modifier la permission'
    })

@login_required
@require_permission('settings_roles')
def role_permission_delete(request, permission_id):
    """Supprimer une permission de rôle"""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden("Accès refusé")
    
    permission = get_object_or_404(RolePermission, id=permission_id)
    
    if request.method == 'POST':
        permission.delete()
        role_display = dict(User.ROLE_CHOICES).get(permission.role, permission.role)
        permission_display = dict(RolePermission.PERMISSION_CHOICES).get(permission.permission, permission.permission)
        SystemLog.log(
            'INFO', 'system_config', 
            f'Permission supprimée: {role_display} - {permission_display}',
            user=request.user
        )
        messages.success(request, 'Permission supprimée avec succès.')
        return redirect('core:role_permissions_list')
    
    return render(request, 'core/settings/role_permission_confirm_delete.html', {
        'permission': permission
    })

@login_required
@require_permission('settings_roles')
def bulk_role_permissions(request):
    """Assignation en masse de permissions"""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden("Accès refusé")
    
    if request.method == 'POST':
        form = BulkRolePermissionForm(request.POST)
        if form.is_valid():
            role = form.cleaned_data['role']
            permissions = form.cleaned_data['permissions']
            action = form.cleaned_data['action']
            
            if action == 'add':
                # Ajouter les permissions
                for permission_code in permissions:
                    RolePermission.objects.get_or_create(
                        role=role,
                        permission=permission_code,
                        defaults={'is_active': True}
                    )
                message = f"{len(permissions)} permission(s) ajoutée(s) au rôle {dict(User.ROLE_CHOICES)[role]}"
            
            elif action == 'remove':
                # Retirer les permissions
                RolePermission.objects.filter(
                    role=role,
                    permission__in=permissions
                ).delete()
                message = f"{len(permissions)} permission(s) retirée(s) du rôle {dict(User.ROLE_CHOICES)[role]}"
            
            elif action == 'replace':
                # Remplacer toutes les permissions
                RolePermission.objects.filter(role=role).delete()
                for permission_code in permissions:
                    RolePermission.objects.create(
                        role=role,
                        permission=permission_code,
                        is_active=True
                    )
                message = f"Toutes les permissions du rôle {dict(User.ROLE_CHOICES)[role]} ont été remplacées"
            
            SystemLog.log(
                'INFO', 'system_config', 
                f'Permissions en masse: {message}',
                user=request.user
            )
            messages.success(request, message)
            return redirect('core:role_permissions_list')
    else:
        form = BulkRolePermissionForm()
    
    return render(request, 'core/settings/bulk_role_permissions.html', {'form': form})

# ==================== GESTION DES VALEURS DE RÉFÉRENCE ====================

@login_required
@require_permission('settings_references')
def reference_values_list(request):
    """Liste des valeurs de référence"""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden("Accès refusé")
    
    category_filter = request.GET.get('category')
    if category_filter:
        references = ReferenceValue.objects.filter(category=category_filter)
    else:
        references = ReferenceValue.objects.all()
    
    references = references.order_by('category', 'sort_order', 'label')
    
    # Grouper par catégorie avec statistiques
    categories_data = {}
    for reference in references:
        if reference.category not in categories_data:
            categories_data[reference.category] = {
                'references': [],
                'total_count': 0,
                'active_count': 0
            }
        categories_data[reference.category]['references'].append(reference)
        categories_data[reference.category]['total_count'] += 1
        if reference.is_active:
            categories_data[reference.category]['active_count'] += 1
    
    # Calculer les statistiques globales
    total_references = ReferenceValue.objects.count()
    active_references = ReferenceValue.objects.filter(is_active=True).count()
    categories_count = len(categories_data)
    system_references = ReferenceValue.objects.filter(is_system=True).count()
    
    context = {
        'categories_data': categories_data,
        'category_choices': ReferenceValue.CATEGORY_CHOICES,
        'selected_category': category_filter,
        'total_references': total_references,
        'active_references': active_references,
        'categories_count': categories_count,
        'system_references': system_references,
    }
    return render(request, 'core/settings/reference_values_list.html', context)

@login_required
@require_permission('settings_references')
def reference_value_create(request):
    """Créer une nouvelle valeur de référence"""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden("Accès refusé")
    
    if request.method == 'POST':
        form = ReferenceValueForm(request.POST)
        if form.is_valid():
            reference = form.save(commit=False)
            reference.created_by = request.user
            reference.save()
            category_display = dict(ReferenceValue.CATEGORY_CHOICES).get(reference.category, reference.category)
            SystemLog.log(
                'INFO', 'system_config', 
                f'Valeur de référence créée: {category_display} - {reference.label}',
                user=request.user
            )
            messages.success(request, 'Valeur de référence créée avec succès.')
            return redirect('core:reference_values_list')
    else:
        form = ReferenceValueForm()
    
    return render(request, 'core/settings/reference_value_form.html', {
        'form': form, 
        'title': 'Créer une valeur de référence'
    })

@login_required
@require_permission('settings_references')
def reference_value_update(request, reference_id):
    """Modifier une valeur de référence"""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden("Accès refusé")
    
    reference = get_object_or_404(ReferenceValue, id=reference_id)
    
    if request.method == 'POST':
        form = ReferenceValueForm(request.POST, instance=reference)
        if form.is_valid():
            form.save()
            category_display = dict(ReferenceValue.CATEGORY_CHOICES).get(reference.category, reference.category)
            SystemLog.log(
                'INFO', 'system_config', 
                f'Valeur de référence modifiée: {category_display} - {reference.label}',
                user=request.user
            )
            messages.success(request, 'Valeur de référence mise à jour avec succès.')
            return redirect('core:reference_values_list')
    else:
        form = ReferenceValueForm(instance=reference)
    
    return render(request, 'core/settings/reference_value_form.html', {
        'form': form, 
        'title': 'Modifier la valeur de référence'
    })

@login_required
@require_permission('settings_references')
def reference_value_delete(request, reference_id):
    """Supprimer une valeur de référence"""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden("Accès refusé")
    
    reference = get_object_or_404(ReferenceValue, id=reference_id)
    
    if request.method == 'POST':
        reference.delete()
        category_display = dict(ReferenceValue.CATEGORY_CHOICES).get(reference.category, reference.category)
        SystemLog.log(
            'INFO', 'system_config', 
            f'Valeur de référence supprimée: {category_display} - {reference.label}',
            user=request.user
        )
        messages.success(request, 'Valeur de référence supprimée avec succès.')
        return redirect('core:reference_values_list')
    
    return render(request, 'core/settings/reference_value_confirm_delete.html', {
        'reference': reference
    })

@login_required
@require_permission('settings_references')
def reference_value_import(request):
    """Importer des valeurs de référence depuis un fichier CSV"""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden("Accès refusé")

    if request.method == 'POST':
        form = ReferenceValueImportForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.cleaned_data['category']
            csv_file = form.cleaned_data['csv_file']
            replace_existing = form.cleaned_data['replace_existing']
            
            try:
                import csv
                from io import StringIO
                
                # Lire le fichier CSV
                content = csv_file.read().decode('utf-8')
                csv_reader = csv.reader(StringIO(content))
                
                imported_count = 0
                for row in csv_reader:
                    if len(row) >= 2:  # Au moins code et label
                        code, label = row[0], row[1]
                        description = row[2] if len(row) > 2 else ''
                        sort_order = int(row[3]) if len(row) > 3 and row[3].isdigit() else 0
                        is_active = row[4].lower() == 'true' if len(row) > 4 else True
                        is_default = row[5].lower() == 'true' if len(row) > 5 else False
                        is_system = row[6].lower() == 'true' if len(row) > 6 else False
                        
                        if replace_existing:
                            ReferenceValue.objects.filter(
                                category=category,
                                code=code
                            ).delete()
                        
                        reference, created = ReferenceValue.objects.get_or_create(
                            category=category,
                            code=code,
                            defaults={
                                'label': label,
                                'description': description,
                                'sort_order': sort_order,
                                'is_active': is_active,
                                'is_default': is_default,
                                'is_system': is_system,
                                'created_by': request.user
                            }
                        )
                        
                        if not created:
                            reference.label = label
                            reference.description = description
                            reference.sort_order = sort_order
                            reference.is_active = is_active
                            reference.is_default = is_default
                            reference.is_system = is_system
                            reference.save()
                        
                        imported_count += 1
                
                SystemLog.log(
                    'INFO', 'system_config', 
                    f'Import de {imported_count} valeurs de référence pour la catégorie {dict(ReferenceValue.CATEGORY_CHOICES)[category]}',
                    user=request.user
                )
                messages.success(request, f'{imported_count} valeurs de référence importées avec succès.')
                return redirect('core:reference_values_list')
                
            except Exception as e:
                messages.error(request, f'Erreur lors de l\'import: {str(e)}')
    else:
        form = ReferenceValueImportForm()
    
    return render(request, 'core/settings/reference_value_import.html', {'form': form})

# ==================== GESTION DES PARAMÈTRES GÉNÉRAUX ====================

@login_required
@require_permission('settings_view')
def general_parameters_list(request):
    """Liste des paramètres généraux"""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden("Accès refusé")
    
    # Grouper par catégorie
    parameters_data = {}
    for param in GeneralParameter.objects.all().order_by('parameter_key'):
        category = get_parameter_category(param.parameter_key)
        if category not in parameters_data:
            parameters_data[category] = []
        parameters_data[category].append(param)
    
    context = {
        'parameters_data': parameters_data,
        'total_parameters': GeneralParameter.objects.count(),
        'system_parameters': GeneralParameter.objects.filter(is_system=True).count(),
    }
    return render(request, 'core/settings/general_parameters_list.html', context)

def get_parameter_category(parameter_key):
    """Détermine la catégorie d'un paramètre"""
    if parameter_key.startswith('organization_'):
        return 'Informations de l\'organisation'
    elif parameter_key.startswith('email_'):
        return 'Configuration email'
    elif parameter_key.startswith('password_') or parameter_key.startswith('session_') or parameter_key.startswith('max_') or parameter_key.startswith('account_'):
        return 'Configuration sécurité'
    elif parameter_key in ['timezone', 'date_format', 'time_format', 'language', 'currency', 'currency_symbol']:
        return 'Configuration système'
    elif parameter_key.startswith('enable_') or parameter_key.startswith('items_per_') or parameter_key.startswith('backup_'):
        return 'Configuration interface'
    elif parameter_key.startswith('default_') or parameter_key.startswith('interaction_') or parameter_key.startswith('badge_') or parameter_key.startswith('max_'):
        return 'Configuration métier'
    else:
        return 'Autres'

@login_required
@require_permission('settings_edit')
def general_parameter_create(request):
    """Créer un nouveau paramètre général"""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden("Accès refusé")
    
    if request.method == 'POST':
        form = GeneralParameterForm(request.POST)
        if form.is_valid():
            parameter = form.save(commit=False)
            parameter.created_by = request.user
            parameter.save()
            parameter_display = dict(GeneralParameter.PARAMETER_CHOICES).get(parameter.parameter_key, parameter.parameter_key)
            SystemLog.log(
                'INFO', 'system_config', 
                f'Paramètre créé: {parameter_display}',
                user=request.user
            )
            messages.success(request, 'Paramètre créé avec succès.')
            return redirect('core:general_parameters_list')
    else:
        form = GeneralParameterForm()
    
    return render(request, 'core/settings/general_parameter_form.html', {
        'form': form, 
        'title': 'Créer un paramètre'
    })

@login_required
@require_permission('settings_edit')
def general_parameter_update(request, parameter_id):
    """Modifier un paramètre général"""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden("Accès refusé")
    
    parameter = get_object_or_404(GeneralParameter, id=parameter_id)
    
    if request.method == 'POST':
        form = GeneralParameterForm(request.POST, instance=parameter)
        if form.is_valid():
            old_value = parameter.value
            form.save()
            parameter_display = dict(GeneralParameter.PARAMETER_CHOICES).get(parameter.parameter_key, parameter.parameter_key)
            SystemLog.log(
                'INFO', 'system_config', 
                f'Paramètre modifié: {parameter_display} (ancienne valeur: {old_value}, nouvelle valeur: {parameter.value})',
                user=request.user
            )
            messages.success(request, 'Paramètre mis à jour avec succès.')
            return redirect('core:general_parameters_list')
    else:
        form = GeneralParameterForm(instance=parameter)
    
    return render(request, 'core/settings/general_parameter_form.html', {
        'form': form, 
        'title': 'Modifier le paramètre'
    })

@login_required
@require_permission('settings_edit')
def general_parameter_delete(request, parameter_id):
    """Supprimer un paramètre général"""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden("Accès refusé")
    
    parameter = get_object_or_404(GeneralParameter, id=parameter_id)
    
    if parameter.is_system:
        messages.error(request, 'Impossible de supprimer un paramètre système.')
        return redirect('core:general_parameters_list')
    
    if request.method == 'POST':
        parameter.delete()
        parameter_display = dict(GeneralParameter.PARAMETER_CHOICES).get(parameter.parameter_key, parameter.parameter_key)
        SystemLog.log(
            'INFO', 'system_config', 
            f'Paramètre supprimé: {parameter_display}',
            user=request.user
        )
        messages.success(request, 'Paramètre supprimé avec succès.')
        return redirect('core:general_parameters_list')
    
    return render(request, 'core/settings/general_parameter_confirm_delete.html', {
        'parameter': parameter
    })

# ==================== GESTION DES JOURNAUX SYSTÈME ====================

@login_required
@require_permission('system_admin')
def system_logs_list(request):
    """Liste des journaux système"""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden("Accès refusé")
    
    # Filtres
    filter_form = SystemLogFilterForm(request.GET)
    logs = SystemLog.objects.all()
    
    if filter_form.is_valid():
        level = filter_form.cleaned_data.get('level')
        category = filter_form.cleaned_data.get('category')
        user = filter_form.cleaned_data.get('user')
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        message = filter_form.cleaned_data.get('message')
        
        if level:
            logs = logs.filter(level=level)
        if category:
            logs = logs.filter(category=category)
        if user:
            logs = logs.filter(user=user)
        if date_from:
            logs = logs.filter(timestamp__date__gte=date_from)
        if date_to:
            logs = logs.filter(timestamp__date__lte=date_to)
        if message:
            logs = logs.filter(message__icontains=message)
    
    # Pagination
    paginator = Paginator(logs.order_by('-timestamp'), 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'logs': page_obj,
        'filter_form': filter_form,
        'total_logs': SystemLog.objects.count(),
        'error_logs': SystemLog.objects.filter(level__in=['ERROR', 'CRITICAL']).count(),
        'today_logs': SystemLog.objects.filter(timestamp__date=timezone.now().date()).count(),
    }
    return render(request, 'core/settings/system_logs_list.html', context)

@login_required
@require_permission('system_admin')
def system_log_detail(request, log_id):
    """Détail d'un journal système"""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden("Accès refusé")
    
    log = get_object_or_404(SystemLog, id=log_id)
    
    context = {
        'log': log,
    }
    return render(request, 'core/settings/system_log_detail.html', context)

@login_required
@require_permission('system_admin')
def system_logs_export(request):
    """Exporter les journaux système"""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden("Accès refusé")
    
    # Appliquer les mêmes filtres que la liste
    filter_form = SystemLogFilterForm(request.GET)
    logs = SystemLog.objects.all()
    
    if filter_form.is_valid():
        level = filter_form.cleaned_data.get('level')
        category = filter_form.cleaned_data.get('category')
        user = filter_form.cleaned_data.get('user')
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        message = filter_form.cleaned_data.get('message')
        
        if level:
            logs = logs.filter(level=level)
        if category:
            logs = logs.filter(category=category)
        if user:
            logs = logs.filter(user=user)
        if date_from:
            logs = logs.filter(timestamp__date__gte=date_from)
        if date_to:
            logs = logs.filter(timestamp__date__lte=date_to)
        if message:
            logs = logs.filter(message__icontains=message)
    
    logs = logs.order_by('-timestamp')
    
    # Créer le fichier CSV
    import csv
    from io import StringIO
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="system_logs_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Horodatage', 'Niveau', 'Catégorie', 'Message', 'Utilisateur', 'Adresse IP'])
    
    for log in logs:
        writer.writerow([
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            log.get_level_display(),
            log.get_category_display(),
            log.message,
            log.user.get_full_name() if log.user else '',
            log.ip_address or ''
        ])
    
    SystemLog.log(
        'INFO', 'system_config', 
        f'Export des journaux système ({logs.count()} entrées)',
        user=request.user
    )
    
    return response

@login_required
@require_permission('system_admin')
def system_logs_clear(request):
    """Vider les journaux système"""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden("Accès refusé")
    
    if request.method == 'POST':
        # Supprimer les logs de plus de 30 jours
        cutoff_date = timezone.now() - timedelta(days=30)
        deleted_count = SystemLog.objects.filter(timestamp__lt=cutoff_date).count()
        SystemLog.objects.filter(timestamp__lt=cutoff_date).delete()
        
        SystemLog.log(
            'INFO', 'system_config', 
            f'Nettoyage des journaux système ({deleted_count} entrées supprimées)',
            user=request.user
        )
        messages.success(request, f'{deleted_count} entrées de journal supprimées.')
        return redirect('core:system_logs_list')
    
    return render(request, 'core/settings/system_logs_clear.html')

# ==================== SAUVEGARDE ET RESTAURATION ====================

@login_required
@require_permission('data_backup')
def settings_backup(request):
    """Sauvegarder les paramètres"""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden("Accès refusé")
    
    if request.method == 'POST':
        form = ParameterBackupForm(request.POST)
        if form.is_valid():
            include_system_params = form.cleaned_data['include_system_params']
            include_reference_values = form.cleaned_data['include_reference_values']
            include_role_permissions = form.cleaned_data['include_role_permissions']
            format_type = form.cleaned_data['format']
            
            # Préparer les données
            backup_data = {}
            
            if include_system_params:
                backup_data['parameters'] = list(GeneralParameter.objects.values())
            
            if include_reference_values:
                backup_data['reference_values'] = list(ReferenceValue.objects.values())
            
            if include_role_permissions:
                backup_data['role_permissions'] = list(RolePermission.objects.values())
            
            # Créer le fichier de sauvegarde
            import json
            from datetime import datetime
            
            filename = f"settings_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            response = HttpResponse(
                json.dumps(backup_data, indent=2, default=str),
                content_type='application/json'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            SystemLog.log(
                'INFO', 'system_config', 
                f'Sauvegarde des paramètres créée: {filename}',
                user=request.user
            )
            
            return response
    else:
        form = ParameterBackupForm()
    
    return render(request, 'core/settings/settings_backup.html', {'form': form})

@login_required
@require_permission('data_restore')
def settings_restore(request):
    """Restaurer les paramètres"""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden("Accès refusé")
    
    if request.method == 'POST':
        backup_file = request.FILES.get('backup_file')
        if backup_file:
            try:
                import json
                content = backup_file.read().decode('utf-8')
                backup_data = json.loads(content)
                
                restored_count = 0
                
                # Restaurer les paramètres
                if 'parameters' in backup_data:
                    for param_data in backup_data['parameters']:
                        param_data.pop('id', None)  # Supprimer l'ID existant
                        param_data.pop('created_at', None)
                        param_data.pop('updated_at', None)
                        param_data['created_by'] = request.user
                        
                        GeneralParameter.objects.get_or_create(
                            parameter_key=param_data['parameter_key'],
                            defaults=param_data
                        )
                        restored_count += 1
                
                # Restaurer les valeurs de référence
                if 'reference_values' in backup_data:
                    for ref_data in backup_data['reference_values']:
                        ref_data.pop('id', None)
                        ref_data.pop('created_at', None)
                        ref_data.pop('updated_at', None)
                        ref_data['created_by'] = request.user
                        
                        ReferenceValue.objects.get_or_create(
                            category=ref_data['category'],
                            code=ref_data['code'],
                            defaults=ref_data
                        )
                        restored_count += 1
                
                # Restaurer les permissions de rôles
                if 'role_permissions' in backup_data:
                    for perm_data in backup_data['role_permissions']:
                        perm_data.pop('id', None)
                        perm_data.pop('created_at', None)
                        perm_data.pop('updated_at', None)
                        
                        RolePermission.objects.get_or_create(
                            role=perm_data['role'],
                            permission=perm_data['permission'],
                            defaults=perm_data
                        )
                        restored_count += 1
                
                SystemLog.log(
                    'INFO', 'system_config', 
                    f'Restauration des paramètres: {restored_count} éléments restaurés',
                    user=request.user
                )
                messages.success(request, f'{restored_count} éléments restaurés avec succès.')
                return redirect('core:settings_dashboard')
                
            except Exception as e:
                messages.error(request, f'Erreur lors de la restauration: {str(e)}')
        else:
            messages.error(request, 'Veuillez sélectionner un fichier de sauvegarde.')
    
    return render(request, 'core/settings/settings_restore.html')

@login_required
def user_permissions(request, user_id):
    """Affiche les permissions d'un utilisateur spécifique"""
    if not (request.user.is_superuser or has_permission(request.user, 'user_view')):
        return HttpResponseForbidden("Accès refusé")
    
    user_obj = get_object_or_404(User, id=user_id)
    
    # Récupérer toutes les permissions pour le rôle de l'utilisateur
    permissions = RolePermission.objects.filter(role=user_obj.role).order_by('permission')
    
    # Grouper les permissions par catégorie
    permissions_by_category = {}
    for permission in permissions:
        category = get_permission_category(permission.permission)
        if category not in permissions_by_category:
            permissions_by_category[category] = []
        permissions_by_category[category].append(permission)
    
    # Statistiques
    total_permissions = permissions.count()
    active_permissions = permissions.filter(is_active=True).count()
    inactive_permissions = total_permissions - active_permissions
    
    context = {
        'user_obj': user_obj,
        'permissions_by_category': permissions_by_category,
        'total_permissions': total_permissions,
        'active_permissions': active_permissions,
        'inactive_permissions': inactive_permissions,
    }
    
    return render(request, 'core/settings/user_permissions.html', context)

def get_permission_category(permission_code):
    """Retourne la catégorie d'une permission"""
    category_mapping = {
        # Gestion des utilisateurs
        'user_create': 'Gestion des utilisateurs',
        'user_edit': 'Gestion des utilisateurs',
        'user_delete': 'Gestion des utilisateurs',
        'user_view': 'Gestion des utilisateurs',
        'user_activate': 'Gestion des utilisateurs',
        
        # Gestion des adhérents
        'adherent_create': 'Gestion des adhérents',
        'adherent_edit': 'Gestion des adhérents',
        'adherent_delete': 'Gestion des adhérents',
        'adherent_view': 'Gestion des adhérents',
        
        # Gestion des organisations
        'organization_create': 'Gestion des organisations',
        'organization_edit': 'Gestion des organisations',
        'organization_delete': 'Gestion des organisations',
        'organization_view': 'Gestion des organisations',
        
        # Gestion des interactions
        'interaction_create': 'Gestion des interactions',
        'interaction_edit': 'Gestion des interactions',
        'interaction_delete': 'Gestion des interactions',
        'interaction_view': 'Gestion des interactions',
        
        # Gestion des badges
        'badge_create': 'Gestion des badges',
        'badge_edit': 'Gestion des badges',
        'badge_delete': 'Gestion des badges',
        'badge_view': 'Gestion des badges',
        'badge_revoke': 'Gestion des badges',
        
        # Gestion des objectifs
        'objective_create': 'Gestion des objectifs',
        'objective_edit': 'Gestion des objectifs',
        'objective_delete': 'Gestion des objectifs',
        'objective_view': 'Gestion des objectifs',
        
        # Gestion des paramètres
        'settings_view': 'Gestion des paramètres',
        'settings_edit': 'Gestion des paramètres',
        'settings_roles': 'Gestion des paramètres',
        'settings_references': 'Gestion des paramètres',
        
        # Rapports et statistiques
        'reports_view': 'Rapports et statistiques',
        'reports_export': 'Rapports et statistiques',
        'stats_view': 'Rapports et statistiques',
        
        # Administration système
        'system_admin': 'Administration système',
        'data_backup': 'Administration système',
        'data_restore': 'Administration système',
    }
    
    return category_mapping.get(permission_code, 'Autres')

# ==================== RECHERCHE GLOBALE ====================

@login_required
def global_search(request):
    """
    Vue de recherche globale dans toute la plateforme.
    Gère les recherches avec plusieurs mots (ex: "mory koulibaly")
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'all')
    
    results = {
        'adherents': [],
        'organizations': [],
        'users': [],
        'interactions': [],
        'badges': []
    }
    
    if query:
        # Séparer la requête en mots pour recherche multi-mots
        query_words = query.split()
        
        # Recherche dans les adhérents
        if search_type in ['all', 'adherents']:
            adherent_query = Q()
            
            # Si plusieurs mots, essayer de chercher prénom + nom
            if len(query_words) >= 2:
                # Chercher toutes les combinaisons possibles de prénom et nom
                for i in range(len(query_words)):
                    for j in range(i+1, len(query_words)+1):
                        potential_first_name = ' '.join(query_words[:i+1])
                        potential_last_name = ' '.join(query_words[i+1:j])
                        
                        if potential_first_name and potential_last_name:
                            adherent_query |= (
                                Q(first_name__icontains=potential_first_name) &
                                Q(last_name__icontains=potential_last_name)
                            ) | (
                                Q(first_name__icontains=potential_last_name) &
                                Q(last_name__icontains=potential_first_name)
                            )
            
            # Ajouter aussi la recherche classique sur tous les champs
            adherent_query |= (
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(identifiant__icontains=query) |
                Q(phone1__icontains=query) |
                Q(phone2__icontains=query) |
                Q(email__icontains=query) |
                Q(commune__icontains=query) |
                Q(quartier__icontains=query) |
                Q(secteur__icontains=query) |
                Q(medical_info__icontains=query) |
                Q(formation_pro__icontains=query) |
                Q(distinction__icontains=query) |
                Q(langues__icontains=query) |
                Q(activity_name__icontains=query) |
                Q(organisation__name__icontains=query)
            )
            
            adherents = Adherent.objects.filter(adherent_query).select_related('organisation').distinct()[:10]
            
            results['adherents'] = adherents
        
        # Recherche dans les organisations
        if search_type in ['all', 'organizations']:
            organizations = Organization.objects.filter(
                Q(name__icontains=query) |
                Q(identifiant__icontains=query) |
                Q(address__icontains=query) |
                Q(phone__icontains=query) |
                Q(whatsapp__icontains=query) |
                Q(infos_annexes__icontains=query) |
                Q(category__name__icontains=query)
            ).select_related('category')[:10]
            
            results['organizations'] = organizations
        
        # Recherche dans les utilisateurs
        if search_type in ['all', 'users']:
            user_query = Q()
            
            # Si plusieurs mots, essayer de chercher prénom + nom
            if len(query_words) >= 2:
                for i in range(len(query_words)):
                    for j in range(i+1, len(query_words)+1):
                        potential_first_name = ' '.join(query_words[:i+1])
                        potential_last_name = ' '.join(query_words[i+1:j])
                        
                        if potential_first_name and potential_last_name:
                            user_query |= (
                                Q(first_name__icontains=potential_first_name) &
                                Q(last_name__icontains=potential_last_name)
                            ) | (
                                Q(first_name__icontains=potential_last_name) &
                                Q(last_name__icontains=potential_first_name)
                            )
            
            # Ajouter aussi la recherche classique sur tous les champs
            user_query |= (
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(matricule__icontains=query) |
                Q(profession__icontains=query) |
                Q(fonction__icontains=query) |
                Q(telephone__icontains=query) |
                Q(email__icontains=query) |
                Q(adresse__icontains=query) |
                Q(nom_urg1__icontains=query) |
                Q(prenom_urg1__icontains=query) |
                Q(telephone_urg1__icontains=query) |
                Q(nom_urg2__icontains=query) |
                Q(prenom_urg2__icontains=query) |
                Q(telephone_urg2__icontains=query)
            )
            
            users = User.objects.filter(user_query).distinct()[:10]
            
            results['users'] = users
        
        # Recherche dans les interactions
        if search_type in ['all', 'interactions']:
            interactions = Interaction.objects.filter(
                Q(identifiant__icontains=query) |
                Q(report__icontains=query) |
                Q(adherent__first_name__icontains=query) |
                Q(adherent__last_name__icontains=query) |
                Q(personnel__first_name__icontains=query) |
                Q(personnel__last_name__icontains=query) |
                Q(auteur__first_name__icontains=query) |
                Q(auteur__last_name__icontains=query)
            ).select_related('adherent', 'personnel', 'auteur')[:10]
            
            results['interactions'] = interactions
        
        # Recherche dans les badges
        if search_type in ['all', 'badges']:
            badges = Badge.objects.filter(
                Q(badge_number__icontains=query) |
                Q(activity_name__icontains=query) |
                Q(notes__icontains=query) |
                Q(adherent__first_name__icontains=query) |
                Q(adherent__last_name__icontains=query) |
                Q(adherent__identifiant__icontains=query) |
                Q(issued_by__first_name__icontains=query) |
                Q(issued_by__last_name__icontains=query)
            ).select_related('adherent', 'issued_by')[:10]
            
            results['badges'] = badges
    
    # Compter les résultats par type
    counts = {
        'adherents': len(results['adherents']),
        'organizations': len(results['organizations']),
        'users': len(results['users']),
        'interactions': len(results['interactions']),
        'badges': len(results['badges'])
    }
    
    total_results = sum(counts.values())
    
    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
        'counts': counts,
        'total_results': total_results,
        'search_types': [
            ('all', 'Tout'),
            ('adherents', 'Adhérents'),
            ('organizations', 'Organisations'),
            ('users', 'Utilisateurs'),
            ('interactions', 'Interactions'),
            ('badges', 'Badges')
        ]
    }
    
    return render(request, 'core/search_results.html', context)

@login_required
def search_suggestions(request):
    """
    API pour les suggestions de recherche en temps réel.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'all')
    
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    suggestions = []
    
    if search_type in ['all', 'adherents']:
        adherents = Adherent.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(identifiant__icontains=query)
        )[:5]
        
        for adherent in adherents:
            suggestions.append({
                'type': 'adherent',
                'id': adherent.id,
                'text': f"{adherent.full_name} ({adherent.identifiant})",
                'url': reverse_lazy('core:adherent_detail', kwargs={'adherent_id': adherent.id})
            })
    
    if search_type in ['all', 'organizations']:
        organizations = Organization.objects.filter(
            Q(name__icontains=query) |
            Q(identifiant__icontains=query)
        )[:5]
        
        for org in organizations:
            suggestions.append({
                'type': 'organization',
                'id': org.id,
                'text': f"{org.name} ({org.identifiant})",
                'url': reverse_lazy('core:organization_detail', kwargs={'organization_id': org.id})
            })
    
    if search_type in ['all', 'users']:
        users = User.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(matricule__icontains=query)
        )[:5]
        
        for user in users:
            suggestions.append({
                'type': 'user',
                'id': user.id,
                'text': f"{user.get_full_name()} ({user.matricule})",
                'url': reverse_lazy('core:user_detail', kwargs={'pk': user.id})
            })
    
    return JsonResponse({'suggestions': suggestions})


def test_final(request):
    """
    Vue pour tester les champs select avec recherche
    """
    return render(request, 'core/test_final.html')
    