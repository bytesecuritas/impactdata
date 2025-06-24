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
    
    # Adhérents (superviseurs et admins)
    path('adherents/', views.adherent_list, name='adherent_list'),
    path('adherents/<int:adherent_id>/', views.adherent_detail, name='adherent_detail'),
    
    # Organisations (agents et admins)
    path('organizations/', views.organization_list, name='organization_list'),
    path('organizations/<int:organization_id>/', views.organization_detail, name='organization_detail'),
    
    # Catégories (agents et admins)
    path('categories/', views.category_list, name='category_list'),
    
    # Interactions (superviseurs et admins)
    path('interactions/', views.interaction_list, name='interaction_list'),
    path('interactions/<int:interaction_id>/', views.interaction_detail, name='interaction_detail'),
]
