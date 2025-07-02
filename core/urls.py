from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Authentification
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    
    # Tableaux de bord
    path('', views.dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('superviseur-dashboard/', views.superviseur_dashboard, name='superviseur_dashboard'),
    path('agent-dashboard/', views.agent_dashboard, name='agent_dashboard'),
    
    # CRUD Adhérents (superviseurs et admins)
    path('adherents/', views.adherent_list, name='adherent_list'),
    path('adherents/create/', views.adherent_create, name='adherent_create'),
    path('adherents/<int:adherent_id>/', views.adherent_detail, name='adherent_detail'),
    path('adherents/<int:adherent_id>/edit/', views.adherent_update, name='adherent_update'),
    path('adherents/<int:adherent_id>/delete/', views.adherent_delete, name='adherent_delete'),
    
    # CRUD Organisations (agents et admins)
    path('organizations/', views.organization_list, name='organization_list'),
    path('organizations/create/', views.organization_create, name='organization_create'),
    path('organizations/<int:organization_id>/', views.organization_detail, name='organization_detail'),
    path('organizations/<int:organization_id>/edit/', views.organization_update, name='organization_update'),
    path('organizations/<int:organization_id>/delete/', views.organization_delete, name='organization_delete'),
    
    # CRUD Catégories (agents et admins)
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:category_id>/edit/', views.category_update, name='category_update'),
    path('categories/<int:category_id>/delete/', views.category_delete, name='category_delete'),
    
    # CRUD Interactions (superviseurs et admins)
    path('interactions/', views.interaction_list, name='interaction_list'),
    path('interactions/create/', views.interaction_create, name='interaction_create'),
    path('interactions/<int:interaction_id>/', views.interaction_detail, name='interaction_detail'),
    path('interactions/<int:interaction_id>/edit/', views.interaction_update, name='interaction_update'),
    path('interactions/<int:interaction_id>/delete/', views.interaction_delete, name='interaction_delete'),
    
    # User Management URLs
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/create/', views.UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/<int:pk>/update/', views.UserUpdateView.as_view(), name='user_update'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
    
    # Objective Management URLs (Superviseur)
    path('objectives/', views.ObjectiveListView.as_view(), name='objective_list'),
    path('objectives/create/', views.ObjectiveCreateView.as_view(), name='objective_create'),
    path('objectives/<int:pk>/', views.ObjectiveDetailView.as_view(), name='objective_detail'),
    path('objectives/<int:pk>/update/', views.ObjectiveUpdateView.as_view(), name='objective_update'),
    path('objectives/<int:pk>/delete/', views.ObjectiveDeleteView.as_view(), name='objective_delete'),
    path('objectives/refresh/', views.refresh_objectives, name='refresh_objectives'),
    
    # Badge Management URLs
    path('badges/', views.badge_list, name='badge_list'),
    path('badges/<int:badge_id>/', views.badge_detail, name='badge_detail'),
    path('badges/<int:badge_id>/card/', views.badge_card, name='badge_card'),
    path('badges/<int:badge_id>/revoke/', views.revoke_badge, name='revoke_badge'),
    path('badges/<int:badge_id>/reactivate/', views.reactivate_badge, name='reactivate_badge'),
    path('badges/<int:badge_id>/download/', views.download_badge_pdf, name='download_badge_pdf'),
    path('badges/scan/', views.badge_qr_scan, name='badge_qr_scan'),
    
    # Badge Generation for Adherents
    path('adherents/<int:adherent_id>/generate-badge/', views.generate_badge, name='generate_badge'),
]
