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
    
    # Password Reset URLs
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/done/', views.password_reset_done, name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-reset/complete/', views.password_reset_complete, name='password_reset_complete'),
    
    # ==================== PARAMÈTRES DE L'APPLICATION ====================
    
    # Tableau de bord des paramètres
    path('settings/', views.settings_dashboard, name='settings_dashboard'),
    
    # Gestion des rôles et permissions
    path('settings/roles/', views.role_permissions_list, name='role_permissions_list'),
    path('settings/roles/create/', views.role_permission_create, name='role_permission_create'),
    path('settings/roles/<int:permission_id>/update/', views.role_permission_update, name='role_permission_update'),
    path('settings/roles/<int:permission_id>/delete/', views.role_permission_delete, name='role_permission_delete'),
    path('settings/roles/bulk/', views.bulk_role_permissions, name='bulk_role_permissions'),
    
    # Gestion des valeurs de référence
    path('settings/references/', views.reference_values_list, name='reference_values_list'),
    path('settings/references/create/', views.reference_value_create, name='reference_value_create'),
    path('settings/references/<int:reference_id>/update/', views.reference_value_update, name='reference_value_update'),
    path('settings/references/<int:reference_id>/delete/', views.reference_value_delete, name='reference_value_delete'),
    path('settings/references/import/', views.reference_value_import, name='reference_value_import'),
    
    # Gestion des paramètres généraux
    path('settings/parameters/', views.general_parameters_list, name='general_parameters_list'),
    path('settings/parameters/create/', views.general_parameter_create, name='general_parameter_create'),
    path('settings/parameters/<int:parameter_id>/update/', views.general_parameter_update, name='general_parameter_update'),
    path('settings/parameters/<int:parameter_id>/delete/', views.general_parameter_delete, name='general_parameter_delete'),
    
    # Gestion des journaux système
    path('settings/logs/', views.system_logs_list, name='system_logs_list'),
    path('settings/logs/<int:log_id>/', views.system_log_detail, name='system_log_detail'),
    path('settings/logs/export/', views.system_logs_export, name='system_logs_export'),
    path('settings/logs/clear/', views.system_logs_clear, name='system_logs_clear'),
    
    # Sauvegarde et restauration
    path('settings/backup/', views.settings_backup, name='settings_backup'),
    path('settings/restore/', views.settings_restore, name='settings_restore'),
    
    # Tableaux de bord
    path('', views.dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('superviseur-dashboard/', views.superviseur_dashboard, name='superviseur_dashboard'),
    path('agent-dashboard/', views.agent_dashboard, name='agent_dashboard'),
    
    # CRUD Adhérents (superviseurs et admins)
    path('adherents/', views.adherent_list, name='adherent_list'),
    path('adherents/create/', views.adherent_create, name='adherent_create'),
    path('adherents/<int:adherent_id>/', views.adherent_detail, name='adherent_detail'),
    path('adherents/<int:adherent_id>/interactions/', views.adherent_interactions, name='adherent_interactions'),
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
    path('interactions/notifications/', views.interaction_notifications, name='interaction_notifications'),
    
    # User Management URLs
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/create/', views.UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/<int:pk>/update/', views.UserUpdateView.as_view(), name='user_update'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
    path('users/<int:user_id>/permissions/', views.user_permissions, name='user_permissions'),
    
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
