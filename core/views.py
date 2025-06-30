from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.http import FileResponse
import os
import json
from datetime import datetime, timedelta
from .models import User, Adherent, Organization, Category, Interaction, Badge, UserObjective, SupervisorStats
from .forms import (
    UserProfileForm, CustomPasswordChangeForm, AdherentForm, OrganizationForm, 
    CategoryForm, InteractionForm, UserForm, UserRegistrationForm, UserEditForm,
    BadgeForm, ProfileEditForm, AdherentSearchForm, OrganizationSearchForm, UserObjectiveForm,
    BadgeGenerationForm
)
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

# Create your views here.
def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

def is_supervisor(user):
    return user.is_authenticated and user.role == 'superviseur'

def is_agent(user):
    return user.is_authenticated and user.role == 'agent'

def can_manage_users(user):
    """Vérifie si l'utilisateur peut gérer les utilisateurs"""
    return user.is_authenticated and (user.role == 'admin' or user.role == 'superviseur')

def can_access_user_data(user, target_user):
    """Vérifie si l'utilisateur peut accéder aux données d'un autre utilisateur"""
    if user.role == 'admin':
        return True
    elif user.role == 'superviseur':
        # Les superviseurs peuvent voir les agents qu'ils ont créés ou qui leur sont assignés
        return target_user.role == 'agent' and (
            target_user.created_by == user or 
            target_user in user.created_users.filter(role='agent')
        )
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
        Q(created_by=request.user) | Q(role='agent')
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
    
    # Objectifs assignés
    objectives = UserObjective.objects.filter(
        assigned_by=request.user
    ).order_by('-created_at')[:10]
    
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
    adherents_count = Adherent.objects.filter(
        organisation__in=Organization.objects.filter(created_by=request.user)
    ).count()
    interactions_count = Interaction.objects.filter(personnel=request.user).count()
    
    # Objectifs assignés
    objectives = UserObjective.objects.filter(user=request.user).order_by('-created_at')
    
    # Dernières activités
    recent_organizations = Organization.objects.filter(created_by=request.user).order_by('-created_at')[:5]
    recent_adherents = Adherent.objects.filter(
        organisation__in=Organization.objects.filter(created_by=request.user)
    ).order_by('-created_at')[:5]
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
        form = ProfileEditForm(request.POST, instance=request.user)
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

# Vues pour les adhérents (superviseurs et admins)
@login_required
def adherent_list(request):
    """Liste des adhérents"""
    # if request.user.role not in ['agent','superviseur', 'admin'] and not request.user.is_superuser:
    #     return HttpResponseForbidden("Accès refusé")
    
    adherents = Adherent.objects.all().order_by('last_name', 'first_name')
    context = {
        'adherents': adherents,
        'total_adherents': adherents.count(),
    }
    return render(request, 'core/adherents/adherent_list.html', context)

@login_required
def adherent_detail(request, adherent_id):
    """Détail d'un adhérent"""
    # if request.user.role not in ['agent', 'admin'] and not request.user.is_superuser:
    #     return HttpResponseForbidden("Accès refusé")
    
    try:
        adherent = Adherent.objects.get(id=adherent_id)
        interactions = adherent.interactions.all().order_by('-created_at')
    except Adherent.DoesNotExist:
        messages.error(request, 'Adhérent non trouvé.')
        return redirect('adherent_list')
    
    context = {
        'adherent': adherent,
        'interactions': interactions,
    }
    return render(request, 'core/adherents/adherent_detail.html', context)

# Vues pour les organisations (agents et admins)
@login_required
def organization_list(request):
    """Liste des organisations"""
    # if request.user.role not in ['agent', 'admin'] and not request.user.is_superuser:
    #     return HttpResponseForbidden("Accès refusé")
    
    organizations = Organization.objects.all().order_by('name')
    context = {
        'organizations': organizations,
        'total_organizations': organizations.count(),
        'total_personel': Organization.objects.aggregate(Sum('number_personnel'))['number_personnel__sum'] or 0,
        'total_revenue': Organization.objects.aggregate(Sum('monthly_revenue'))['monthly_revenue__sum'] or 0,
    }
    return render(request, 'core/organizations/organization_list.html', context)

@login_required
def organization_detail(request, organization_id):
    """Détail d'une organisation"""
    # if request.user.role not in ['agent', 'admin'] and not request.user.is_superuser:
    #     return HttpResponseForbidden("Accès refusé")
    
    try:
        organization = Organization.objects.get(id=organization_id)
        adherents = organization.adherents.all().order_by('last_name', 'first_name')
    except Organization.DoesNotExist:
        messages.error(request, 'Organisation non trouvée.')
        return redirect('organization_list')
    
    context = {
        'organization': organization,
        'adherents': adherents,
    }
    return render(request, 'core/organizations/organization_detail.html', context)

# Vues pour les catégories (agents et admins)
@login_required
def category_list(request):
    """Liste des catégories"""
    # if request.user.role not in ['agent', 'admin'] and not request.user.is_superuser:
    #     return HttpResponseForbidden("Accès refusé")
    
    categories = Category.objects.all().order_by('name')
    context = {
        'categories': categories,
        'total_categories': categories.count(),
    }
    return render(request, 'core/categories/category_list.html', context)

# Vues pour les interactions (superviseurs et admins)
@login_required
def interaction_list(request):
    """Liste des interactions"""
    # if request.user.role not in ['agent', 'admin'] and not request.user.is_superuser:
    #     return HttpResponseForbidden("Accès refusé")
    
    interactions = Interaction.objects.all().order_by('-created_at')
    context = {
        'interactions': interactions,
        'total_interactions': interactions.count(),
        'now': timezone.now(),
    }
    return render(request, 'core/interactions/interaction_list.html', context)

@login_required
def interaction_detail(request, interaction_id):
    """Détail d'une interaction"""
    # if request.user.role not in ['agent', 'admin'] and not request.user.is_superuser:
    #     return HttpResponseForbidden("Accès refusé")
    
    try:
        interaction = Interaction.objects.get(id=interaction_id)
    except Interaction.DoesNotExist:
        messages.error(request, 'Interaction non trouvée.')
        return redirect('interaction_list')
    
    context = {
        'interaction': interaction,
    }
    return render(request, 'core/interactions/interaction_detail.html', context)

# ==================== CRUD ADHÉRENTS ====================

@login_required
def adherent_create(request):
    """Créer un nouvel adhérent"""
    # if not (is_admin(request.user) or is_agent(request.user)):
    #     return HttpResponseForbidden("Accès refusé")
    
    if request.method == 'POST':
        form = AdherentForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            adherent = form.save(commit=False)
            adherent.save()
            messages.success(request, 'Adhérent créé avec succès.')
            return redirect('core:adherent_detail', adherent_id=adherent.id)
    else:
        form = AdherentForm(user=request.user)
    
    return render(request, 'core/adherents/adherent_form.html', {'form': form, 'title': 'Créer un adhérent'})

@login_required
def adherent_update(request, adherent_id):
    """Modifier un adhérent"""
    # if not (is_admin(request.user) or is_agent(request.user)):
    #     return HttpResponseForbidden("Accès refusé")
    
    adherent = get_object_or_404(Adherent, id=adherent_id)
    
    if request.method == 'POST':
        form = AdherentForm(request.POST, request.FILES, instance=adherent, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Adhérent mis à jour avec succès.')
            return redirect('core:adherent_detail', adherent_id=adherent.id)
    else:
        form = AdherentForm(instance=adherent, user=request.user)
    
    return render(request, 'core/adherents/adherent_form.html', {'form': form, 'title': 'Modifier l\'adhérent'})

@login_required
def adherent_delete(request, adherent_id):
    """Supprimer un adhérent"""
    # if not (is_admin(request.user) or is_agent(request.user)):
    #     return HttpResponseForbidden("Accès refusé")
    
    adherent = get_object_or_404(Adherent, id=adherent_id)
    
    if request.method == 'POST':
        adherent.delete()
        messages.success(request, 'Adhérent supprimé avec succès.')
        return redirect('core:adherent_list')
    
    return render(request, 'core/adherents/adherent_confirm_delete.html', {'adherent': adherent})

# ==================== CRUD ORGANISATIONS ====================

@login_required
def organization_create(request):
    """Créer une nouvelle organisation"""
    # if not (is_admin(request.user) or is_agent(request.user)):
    #     return HttpResponseForbidden("Accès refusé")
    
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
def organization_update(request, organization_id):
    """Modifier une organisation"""
    # if not (is_admin(request.user) or is_agent(request.user)):
    #     return HttpResponseForbidden("Accès refusé")
    
    organization = get_object_or_404(Organization, id=organization_id)
    
    # Vérifier que l'agent ne peut modifier que ses propres organisations
    if is_agent(request.user) and organization.created_by != request.user:
        return HttpResponseForbidden("Accès refusé")
    
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
def organization_delete(request, organization_id):
    """Supprimer une organisation"""
    # if not (is_admin(request.user) or is_agent(request.user)):
    #     return HttpResponseForbidden("Accès refusé")
    
    organization = get_object_or_404(Organization, id=organization_id)
    
    # Vérifier que l'agent ne peut supprimer que ses propres organisations
    if is_agent(request.user) and organization.created_by != request.user:
        return HttpResponseForbidden("Accès refusé")
    
    if request.method == 'POST':
        organization.delete()
        messages.success(request, 'Organisation supprimée avec succès.')
        return redirect('core:organization_list')
    
    return render(request, 'core/organizations/organization_confirm_delete.html', {'organization': organization})

# ==================== CRUD CATÉGORIES ====================

@login_required
def category_create(request):
    """Créer une nouvelle catégorie"""
    # if request.user.role not in ['agent', 'admin'] and not request.user.is_superuser:
    #     return HttpResponseForbidden("Accès refusé")
    
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
def category_update(request, category_id):
    """Modifier une catégorie"""
    # if request.user.role not in ['agent', 'adherent', 'admin'] and not request.user.is_superuser:
    #     return HttpResponseForbidden("Accès refusé")
    
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
def category_delete(request, category_id):
    """Supprimer une catégorie"""
    # if request.user.role not in ['agent', 'adherent', 'admin'] and not request.user.is_superuser:
    #     return HttpResponseForbidden("Accès refusé")
    
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
            interaction.personnel = request.user
            interaction.save()
            messages.success(request, 'Interaction créée avec succès.')
            return redirect('core:interaction_detail', interaction_id=interaction.id)
    else:
        form = InteractionForm(user=request.user)
    
    return render(request, 'core/interactions/interaction_form.html', {'form': form, 'title': 'Créer une interaction'})

@login_required
def interaction_update(request, interaction_id):
    """Modifier une interaction"""
    # if not (is_admin(request.user) or is_agent(request.user) or is_supervisor(request.user)):
    #     return HttpResponseForbidden("Accès refusé")
    
    interaction = get_object_or_404(Interaction, id=interaction_id)
    
    # Vérifier que le superviseur ne peut modifier que ses propres interactions
    if is_agent(request.user) and interaction.personnel != request.user:
        return HttpResponseForbidden("Accès refusé")
    
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
    # if not (is_admin(request.user) or is_agent(request.user) or is_supervisor(request.user)):
    #     return HttpResponseForbidden("Accès refusé")
    
    interaction = get_object_or_404(Interaction, id=interaction_id)
    
    # Vérifier que le superviseur ne peut supprimer que ses propres interactions
    if is_agent(request.user) and interaction.personnel != request.user:
        return HttpResponseForbidden("Accès refusé")
    
    if request.method == 'POST':
        interaction.delete()
        messages.success(request, 'Interaction supprimée avec succès.')
        return redirect('core:interaction_list')
    
    return render(request, 'core/interactions/interaction_confirm_delete.html', {'interaction': interaction})

# User Management Views (Admin only)
class UserListView(LoginRequiredMixin, ListView):
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

class UserDetailView(LoginRequiredMixin, DetailView):
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
                'adherents_count': Adherent.objects.filter(
                    organisation__in=Organization.objects.filter(created_by=user_obj)
                ).count(),
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

class UserCreateView(LoginRequiredMixin, CreateView):
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
        
        # Afficher le mot de passe généré si applicable
        if hasattr(user, '_password_generated'):
            messages.success(
                self.request,
                f"Utilisateur créé avec succès. Mot de passe généré : {user._password_generated}"
            )
        else:
            messages.success(self.request, "Utilisateur créé avec succès.")
        
        return redirect('core:user_detail', pk=user.pk)

class UserUpdateView(LoginRequiredMixin, UpdateView):
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
    
    def form_valid(self, form):
        user = form.save(commit=False)
        user.last_modified_by = self.request.user
        user.save()
        messages.success(self.request, "Utilisateur mis à jour avec succès.")
        return redirect('core:user_detail', pk=user.pk)

class UserDeleteView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = 'core/users/user_confirm_delete.html'
    context_object_name = 'user_obj'
    success_url = reverse_lazy('core:user_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not is_admin(request.user):
            raise PermissionDenied("Seuls les administrateurs peuvent supprimer des utilisateurs.")
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Utilisateur supprimé avec succès.")
        return super().delete(request, *args, **kwargs)

@login_required
def badge_list(request):
    """Liste des badges"""
    # if request.user.role not in ['agent', 'admin'] and not request.user.is_superuser:
    #     return HttpResponseForbidden("Accès refusé")
    
    badges = Badge.objects.select_related('adherent', 'issued_by').all()
    
    # Filtres
    status_filter = request.GET.get('status')
    if status_filter:
        badges = badges.filter(status=status_filter)
    
    context = {
        'badges': badges,
        'status_choices': Badge.STATUS_CHOICES,
    }
    return render(request, 'core/badges/badge_list.html', context)

@login_required
def badge_detail(request, badge_id):
    """Détails d'un badge"""
    # if request.user.role not in ['agent', 'admin'] and not request.user.is_superuser:
    #     return HttpResponseForbidden("Accès refusé")
    
    badge = get_object_or_404(Badge, id=badge_id)
    context = {
        'badge': badge,
    }
    return render(request, 'core/badges/badge_detail.html', context)

@login_required
def badge_card(request, badge_id):
    """Afficher le badge comme une carte d'identité"""
    # if request.user.role not in ['agent', 'admin'] and not request.user.is_superuser:
    #     return HttpResponseForbidden("Accès refusé")
    
    badge = get_object_or_404(Badge, id=badge_id)
    context = {
        'badge': badge,
    }
    return render(request, 'core/badges/badge_card.html', context)

@login_required
def generate_badge(request, adherent_id):
    """Générer un badge pour un adhérent"""
    # if request.user.role not in ['agent', 'admin'] and not request.user.is_superuser:
    #     return HttpResponseForbidden("Accès refusé")
    
    adherent = get_object_or_404(Adherent, id=adherent_id)
    
    # Vérifier que l'adhérent a déjà un badge actif
    existing_badge = Badge.objects.filter(adherent=adherent, status='active').first()
    if existing_badge and existing_badge.is_valid:
        messages.warning(request, f"{adherent.full_name} a déjà un badge actif valide jusqu'au {adherent.badge_validity}.")
        return redirect('core:adherent_detail', adherent_id=adherent_id)
    
    # Vérifier que l'adhérent a bien une activité et une validité de badge
    if not adherent.activity_name or not adherent.badge_validity:
        messages.error(request, "Veuillez d'abord renseigner l'activité et la validité du badge pour cet adhérent.")
        return redirect('core:adherent_detail', adherent_id=adherent_id)
    
    if request.method == 'POST':
        form = BadgeGenerationForm(request.POST)
        if form.is_valid():
            template = form.cleaned_data['template']
            
            try:
                # Créer un nouveau badge
                badge = Badge.objects.create(
                    adherent=adherent,
                    issued_by=request.user,
                    template=template,
                    badge_validity=adherent.badge_validity,  # Utiliser la validité de l'adhérent
                    activity_name=adherent.activity_name,    # Utiliser l'activité de l'adhérent
                    notes=f"Badge généré le {timezone.now().strftime('%d/%m/%Y à %H:%M')}"
                )
                
                # Générer le QR code
                qr_data = f"ADHERENT:{adherent.identifiant}|BADGE:{badge.badge_number}|VALID:{adherent.badge_validity}"
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(qr_data)
                qr.make(fit=True)
                
                # Créer l'image du QR code
                img = qr.make_image(fill='black', back_color='white')
                img_io = BytesIO()
                img.save(img_io, 'PNG')
                img_io.seek(0)
                
                # Sauvegarder le QR code
                filename = f"qr_badge_{badge.badge_number}.png"
                badge.qr_code.save(filename, File(img_io), save=True)
                
                messages.success(request, f"Badge {badge.badge_number} généré avec succès pour {adherent.full_name}.")
                return redirect('core:badge_detail', badge_id=badge.id)
                
            except Exception as e:
                messages.error(request, f"Erreur lors de la génération du badge: {str(e)}")
                return redirect('core:adherent_detail', adherent_id=adherent_id)
    else:
        form = BadgeGenerationForm()
    
    context = {
        'adherent': adherent,
        'form': form,
    }
    return render(request, 'core/badges/badge_generation.html', context)

@login_required
def revoke_badge(request, badge_id):
    """Révoquer un badge"""
    # if request.user.role not in ['agent', 'admin'] and not request.user.is_superuser:
    #     return HttpResponseForbidden("Accès refusé")
    
    badge = get_object_or_404(Badge, id=badge_id)
    
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
def reactivate_badge(request, badge_id):
    """Réactiver un badge"""
    # if request.user.role not in ['agent', 'admin'] and not request.user.is_superuser:
    #     return HttpResponseForbidden("Accès refusé")
    
    badge = get_object_or_404(Badge, id=badge_id)
    badge.reactivate(reactivated_by=request.user.get_full_name())
    messages.success(request, f"Badge {badge.badge_number} réactivé avec succès.")
    return redirect('core:badge_list')

@login_required
def download_badge_pdf(request, badge_id):
    """Télécharger le badge en PDF"""
    # if request.user.role not in ['agent', 'admin'] and not request.user.is_superuser:
    #     return HttpResponseForbidden("Accès refusé")
    
    badge = get_object_or_404(Badge, id=badge_id)
    
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
                badge = Badge.objects.get(badge_number=badge_number)
                
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
class ObjectiveListView(LoginRequiredMixin, ListView):
    model = UserObjective
    template_name = 'core/objectives/objective_list.html'
    context_object_name = 'objectives'
    paginate_by = 20
    
    def get_queryset(self):
        if self.request.user.role == 'admin':
            return UserObjective.objects.all()
        elif self.request.user.role == 'superviseur':
            return UserObjective.objects.filter(assigned_by=self.request.user)
        else:
            return UserObjective.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_create_objectives'] = self.request.user.role in ['admin', 'superviseur']
        return context

class ObjectiveDetailView(LoginRequiredMixin, DetailView):
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

class ObjectiveCreateView(LoginRequiredMixin, CreateView):
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

class ObjectiveUpdateView(LoginRequiredMixin, UpdateView):
    model = UserObjective
    template_name = 'core/objectives/objective_form.html'
    form_class = UserObjectiveForm
    
    def get_queryset(self):
        if self.request.user.role == 'admin':
            return UserObjective.objects.all()
        elif self.request.user.role == 'superviseur':
            return UserObjective.objects.filter(assigned_by=self.request.user)
        else:
            return UserObjective.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, "Objectif mis à jour avec succès.")
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('core:objective_detail', kwargs={'pk': self.object.pk})

class ObjectiveDeleteView(LoginRequiredMixin, DeleteView):
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
            return UserObjective.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Objectif supprimé avec succès.")
        return super().delete(request, *args, **kwargs)
    