from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.urls import reverse
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from .models import User, Adherent, Organization, Category, Interaction
from django.utils import timezone
from .forms import UserProfileForm, CustomPasswordChangeForm, AdherentForm, OrganizationForm, CategoryForm, InteractionForm

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
    
    context = {
        'total_users': User.objects.count(),
        'total_adherents': Adherent.objects.count(),
        'total_organizations': Organization.objects.count(),
        'total_categories': Category.objects.count(),
        'recent_adherents': Adherent.objects.order_by('-created_at')[:5],
        'recent_organizations': Organization.objects.order_by('-created_at')[:5],
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
    