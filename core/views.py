from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponse
from django.urls import reverse
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from .models import User, Adherent, Organization, Category, Interaction, Badge
from django.utils import timezone
from .forms import UserProfileForm, CustomPasswordChangeForm, AdherentForm, OrganizationForm, CategoryForm, InteractionForm, UserForm
from django.db.models import Count
from datetime import datetime, timedelta
import calendar
import json
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
from django.http import FileResponse
import os

# Create your views here.
def is_admin(user):
    return user.is_authenticated and user.can_manage_users()
    

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
                    messages.success(request, f'Bienvenue {user.name}!')
                    
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
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre profil a été mis à jour avec succès.')
            return redirect('core:profile')
    else:
        form = UserProfileForm(instance=request.user)
    
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

@login_required
def superviseur_dashboard(request):
    """Tableau de bord superviseur"""
    if request.user.role != 'superviseur' and not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé")
    
    context = {
        'total_adherents': Adherent.objects.count(),
        'total_interactions': Interaction.objects.count(),
        'recent_adherents': Adherent.objects.order_by('-created_at')[:10],
        'recent_interactions': Interaction.objects.order_by('-created_at')[:10],
        'expired_badges': Adherent.objects.filter(badge_validity__lt=timezone.now().date()).count(),
    }
    return render(request, 'core/dashboard/superviseur_dashboard.html', context)


@login_required
def agent_dashboard(request):
    """Tableau de bord agent"""
    if request.user.role != 'agent' and not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé")
    
    context = {
        'total_organizations': Organization.objects.count(),
        'total_categories': Category.objects.count(),
        'recent_organizations': Organization.objects.order_by('-created_at')[:10],
        'recent_categories': Category.objects.order_by('-created_at')[:10],
    }
    return render(request, 'core/dashboard/agent_dashboard.html', context)


# Vues pour les adhérents (superviseurs et admins)
@login_required
def adherent_list(request):
    """Liste des adhérents"""
    if request.user.role not in ['superviseur', 'admin'] and not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé")
    
    adherents = Adherent.objects.all().order_by('last_name', 'first_name')
    context = {
        'adherents': adherents,
        'total_adherents': adherents.count(),
    }
    return render(request, 'core/adherents/adherent_list.html', context)


@login_required
def adherent_detail(request, adherent_id):
    """Détail d'un adhérent"""
    if request.user.role not in ['superviseur', 'admin'] and not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé")
    
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
    if request.user.role not in ['agent', 'admin'] and not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé")
    
    organizations = Organization.objects.all().order_by('name')
    context = {
        'organizations': organizations,
        'total_organizations': organizations.count(),
    }
    return render(request, 'core/organizations/organization_list.html', context)


@login_required
def organization_detail(request, organization_id):
    """Détail d'une organisation"""
    if request.user.role not in ['agent', 'admin'] and not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé")
    
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
    if request.user.role not in ['agent', 'admin'] and not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé")
    
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
    if request.user.role not in ['superviseur', 'admin'] and not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé")
    
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
    if request.user.role not in ['superviseur', 'admin'] and not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé")
    
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
    if request.user.role not in ['superviseur', 'admin'] and not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé")
    
    if request.method == 'POST':
        form = AdherentForm(request.POST, request.FILES)
        if form.is_valid():
            adherent = form.save()
            messages.success(request, f'Adhérent "{adherent.full_name}" créé avec succès.')
            return redirect('core:adherent_list')
    else:
        form = AdherentForm()
    
    context = {
        'form': form,
        'title': 'Créer un nouvel adhérent',
        'submit_text': 'Créer l\'adhérent'
    }
    return render(request, 'core/adherents/adherent_form.html', context)

@login_required
def adherent_update(request, adherent_id):
    """Modifier un adhérent"""
    if request.user.role not in ['superviseur', 'admin'] and not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé")
    
    adherent = get_object_or_404(Adherent, id=adherent_id)
    
    if request.method == 'POST':
        form = AdherentForm(request.POST, request.FILES, instance=adherent)
        if form.is_valid():
            form.save()
            messages.success(request, f'Adhérent "{adherent.full_name}" modifié avec succès.')
            return redirect('core:adherent_list')
    else:
        form = AdherentForm(instance=adherent)
    
    context = {
        'form': form,
        'adherent': adherent,
        'title': f'Modifier l\'adhérent {adherent.full_name}',
        'submit_text': 'Mettre à jour'
    }
    return render(request, 'core/adherents/adherent_form.html', context)

@login_required
def adherent_delete(request, adherent_id):
    """Supprimer un adhérent"""
    if request.user.role not in ['superviseur', 'admin'] and not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé")
    
    adherent = get_object_or_404(Adherent, id=adherent_id)
    
    if request.method == 'POST':
        adherent_name = adherent.full_name
        adherent.delete()
        messages.success(request, f'Adhérent "{adherent_name}" supprimé avec succès.')
        return redirect('core:adherent_list')
    
    context = {
        'adherent': adherent,
        'title': f'Supprimer l\'adhérent {adherent.full_name}'
    }
    return render(request, 'core/adherents/adherent_confirm_delete.html', context)

# ==================== CRUD ORGANISATIONS ====================

@login_required
def organization_create(request):
    """Créer une nouvelle organisation"""
    if request.user.role not in ['agent', 'admin'] and not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé")
    
    if request.method == 'POST':
        form = OrganizationForm(request.POST)
        if form.is_valid():
            organization = form.save()
            messages.success(request, f'Organisation "{organization.name}" créée avec succès.')
            return redirect('core:organization_list')
    else:
        form = OrganizationForm()
    
    context = {
        'form': form,
        'title': 'Créer une nouvelle organisation',
        'submit_text': 'Créer l\'organisation'
    }
    return render(request, 'core/organizations/organization_form.html', context)

@login_required
def organization_update(request, organization_id):
    """Modifier une organisation"""
    if request.user.role not in ['agent', 'admin'] and not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé")
    
    organization = get_object_or_404(Organization, id=organization_id)
    
    if request.method == 'POST':
        form = OrganizationForm(request.POST, instance=organization)
        if form.is_valid():
            form.save()
            messages.success(request, f'Organisation "{organization.name}" modifiée avec succès.')
            return redirect('core:organization_list')
    else:
        form = OrganizationForm(instance=organization)
    
    context = {
        'form': form,
        'organization': organization,
        'title': f'Modifier l\'organisation {organization.name}',
        'submit_text': 'Mettre à jour'
    }
    return render(request, 'core/organizations/organization_form.html', context)

@login_required
def organization_delete(request, organization_id):
    """Supprimer une organisation"""
    if request.user.role not in ['agent', 'admin'] and not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé")
    
    organization = get_object_or_404(Organization, id=organization_id)
    
    if request.method == 'POST':
        organization_name = organization.name
        organization.delete()
        messages.success(request, f'Organisation "{organization_name}" supprimée avec succès.')
        return redirect('core:organization_list')
    
    context = {
        'organization': organization,
        'title': f'Supprimer l\'organisation {organization.name}'
    }
    return render(request, 'core/organizations/organization_confirm_delete.html', context)

# ==================== CRUD CATÉGORIES ====================

@login_required
def category_create(request):
    """Créer une nouvelle catégorie"""
    if request.user.role not in ['agent', 'admin'] and not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé")
    
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
    if request.user.role not in ['agent', 'admin'] and not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé")
    
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
    if request.user.role not in ['agent', 'admin'] and not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé")
    
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
    if request.user.role not in ['superviseur', 'admin'] and not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé")
    
    if request.method == 'POST':
        form = InteractionForm(request.POST)
        if form.is_valid():
            interaction = form.save()
            messages.success(request, f'Interaction "{interaction.identifiant}" créée avec succès.')
            return redirect('core:interaction_list')
    else:
        form = InteractionForm()
        # Pré-remplir le personnel avec l'utilisateur connecté
        form.fields['personnel'].initial = request.user
    
    context = {
        'form': form,
        'title': 'Créer une nouvelle interaction',
        'submit_text': 'Créer l\'interaction'
    }
    return render(request, 'core/interactions/interaction_form.html', context)

@login_required
def interaction_update(request, interaction_id):
    """Modifier une interaction"""
    if request.user.role not in ['superviseur', 'admin'] and not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé")
    
    interaction = get_object_or_404(Interaction, id=interaction_id)
    
    if request.method == 'POST':
        form = InteractionForm(request.POST, instance=interaction)
        if form.is_valid():
            form.save()
            messages.success(request, f'Interaction "{interaction.identifiant}" modifiée avec succès.')
            return redirect('core:interaction_list')
    else:
        form = InteractionForm(instance=interaction)
    
    context = {
        'form': form,
        'interaction': interaction,
        'title': f'Modifier l\'interaction {interaction.identifiant}',
        'submit_text': 'Mettre à jour'
    }
    return render(request, 'core/interactions/interaction_form.html', context)

@login_required
def interaction_delete(request, interaction_id):
    """Supprimer une interaction"""
    if request.user.role not in ['superviseur', 'admin'] and not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé")
    
    interaction = get_object_or_404(Interaction, id=interaction_id)
    
    if request.method == 'POST':
        interaction_id_str = interaction.identifiant
        interaction.delete()
        messages.success(request, f'Interaction "{interaction_id_str}" supprimée avec succès.')
        return redirect('core:interaction_list')
    
    context = {
        'interaction': interaction,
        'title': f'Supprimer l\'interaction {interaction.identifiant}'
    }
    return render(request, 'core/interactions/interaction_confirm_delete.html', context)

# User Management Views (Admin only)
@login_required
def user_list(request):
    """Liste des utilisateurs (Admin uniquement)"""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden("Accès refusé")
    
    users = User.objects.all().order_by('-date_joined')
    context = {
        'users': users,
        'total_users': users.count(),
    }
    return render(request, 'core/users/user_list.html', context)

@login_required
def user_create(request):
    """Créer un nouvel utilisateur (Admin uniquement)"""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden("Accès refusé")
    
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, f"L'utilisateur {user.name} a été créé avec succès.")
            return redirect('core:user_list')
    else:
        form = UserForm()
    
    context = {
        'form': form,
        'title': 'Créer un Utilisateur',
    }
    return render(request, 'core/users/user_form.html', context)

@login_required
def user_update(request, pk):
    """Modifier un utilisateur (Admin uniquement)"""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden("Accès refusé")
    
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            if form.cleaned_data.get('password'):
                user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, f"L'utilisateur {user.name} a été modifié avec succès.")
            return redirect('core:user_list')
    else:
        form = UserForm(instance=user)
    
    context = {
        'form': form,
        'user': user,
        'title': 'Modifier l\'Utilisateur',
    }
    return render(request, 'core/users/user_form.html', context)

@login_required
def user_delete(request, pk):
    """Supprimer un utilisateur (Admin uniquement)"""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden("Accès refusé")
    
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        if user == request.user:
            messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
            return redirect('core:user_list')
        
        user_name = user.name
        user.delete()
        messages.success(request, f"L'utilisateur {user_name} a été supprimé avec succès.")
        return redirect('core:user_list')
    
    context = {
        'user': user,
    }
    return render(request, 'core/users/user_confirm_delete.html', context)

@login_required
def user_detail(request, pk):
    """Détails d'un utilisateur (Admin uniquement)"""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return HttpResponseForbidden("Accès refusé")
    
    user = get_object_or_404(User, pk=pk)
    
    context = {
        'user_detail': user,
    }
    return render(request, 'core/users/user_detail.html', context)

@login_required
def badge_list(request):
    """Liste des badges"""
    if request.user.role not in ['superviseur', 'admin'] and not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé")
    
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
    if request.user.role not in ['superviseur', 'admin'] and not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé")
    
    badge = get_object_or_404(Badge, id=badge_id)
    context = {
        'badge': badge,
    }
    return render(request, 'core/badges/badge_detail.html', context)


@login_required
def generate_badge(request, adherent_id):
    """Générer un badge pour un adhérent"""
    if request.user.role not in ['superviseur', 'admin'] and not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé")
    
    adherent = get_object_or_404(Adherent, id=adherent_id)
    
    # Vérifier si l'adhérent a déjà un badge actif
    existing_badge = Badge.objects.filter(adherent=adherent, status='active').first()
    if existing_badge and existing_badge.is_valid:
        messages.warning(request, f"{adherent.full_name} a déjà un badge actif valide jusqu'au {adherent.badge_validity}.")
        return redirect('core:adherent_detail', adherent_id=adherent_id)
    
    try:
        # Créer un nouveau badge
        badge = Badge.objects.create(
            adherent=adherent,
            issued_by=request.user,
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


@login_required
def revoke_badge(request, badge_id):
    """Révoquer un badge"""
    if request.user.role not in ['superviseur', 'admin'] and not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé")
    
    badge = get_object_or_404(Badge, id=badge_id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        badge.revoke(reason=reason, revoked_by=request.user.name)
        messages.success(request, f"Badge {badge.badge_number} révoqué avec succès.")
        return redirect('core:badge_list')
    
    context = {
        'badge': badge,
    }
    return render(request, 'core/badges/badge_revoke.html', context)


@login_required
def reactivate_badge(request, badge_id):
    """Réactiver un badge"""
    if request.user.role not in ['superviseur', 'admin'] and not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé")
    
    badge = get_object_or_404(Badge, id=badge_id)
    badge.reactivate(reactivated_by=request.user.name)
    messages.success(request, f"Badge {badge.badge_number} réactivé avec succès.")
    return redirect('core:badge_list')


@login_required
def download_badge_pdf(request, badge_id):
    """Télécharger le badge en PDF"""
    if request.user.role not in ['superviseur', 'admin'] and not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé")
    
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
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    # Titre
    elements.append(Paragraph("BADGE D'ADHÉRENT", title_style))
    elements.append(Spacer(1, 20))
    
    # Informations du badge
    badge_data = [
        ['Numéro de badge:', badge.badge_number],
        ['Nom complet:', badge.adherent.full_name],
        ['Identifiant:', badge.adherent.identifiant],
        ['Organisation:', badge.adherent.organisation.name],
        ['Activité:', badge.adherent.activity_name],
        ['Date d\'émission:', badge.issued_date.strftime('%d/%m/%Y')],
        ['Validité jusqu\'au:', badge.adherent.badge_validity.strftime('%d/%m/%Y')],
        ['Statut:', badge.get_status_display()],
    ]
    
    # Créer le tableau
    badge_table = Table(badge_data, colWidths=[4*cm, 8*cm])
    badge_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(badge_table)
    elements.append(Spacer(1, 30))
    
    # Notes si présentes
    if badge.notes:
        elements.append(Paragraph("Notes:", styles['Heading3']))
        elements.append(Paragraph(badge.notes, styles['Normal']))
        elements.append(Spacer(1, 20))
    
    # Construire le PDF
    doc.build(elements)
    return response


@login_required
def badge_qr_scan(request):
    """Scanner un QR code de badge"""
    if request.user.role not in ['superviseur', 'admin', 'agent'] and not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé")
    
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
    