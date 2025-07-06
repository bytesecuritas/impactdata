#!/usr/bin/env python3
"""
Script pour mettre à jour toutes les vues restantes avec le système de permissions
"""

import re

def update_views_file():
    """Met à jour le fichier views.py avec toutes les permissions"""
    
    # Lire le fichier views.py
    with open('core/views.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remplacer les vues restantes
    replacements = [
        # Badges
        (r'@login_required\s+def badge_list\(request\):',
         '@login_required\n@require_permission(\'badge_view\')\ndef badge_list(request):'),
        
        (r'@login_required\s+def badge_detail\(request, badge_id\):',
         '@login_required\n@require_permission(\'badge_view\')\ndef badge_detail(request, badge_id):'),
        
        (r'@login_required\s+def badge_card\(request, badge_id\):',
         '@login_required\n@require_permission(\'badge_view\')\ndef badge_card(request, badge_id):'),
        
        (r'@login_required\s+def generate_badge\(request, adherent_id\):',
         '@login_required\n@require_permission(\'badge_create\')\ndef generate_badge(request, adherent_id):'),
        
        (r'@login_required\s+def revoke_badge\(request, badge_id\):',
         '@login_required\n@require_permission(\'badge_revoke\')\ndef revoke_badge(request, badge_id):'),
        
        (r'@login_required\s+def reactivate_badge\(request, badge_id\):',
         '@login_required\n@require_permission(\'badge_edit\')\ndef reactivate_badge(request, badge_id):'),
        
        (r'@login_required\s+def download_badge_pdf\(request, badge_id\):',
         '@login_required\n@require_permission(\'badge_view\')\ndef download_badge_pdf(request, badge_id):'),
        
        (r'@login_required\s+def badge_qr_scan\(request\):',
         '@login_required\n@require_permission(\'badge_view\')\ndef badge_qr_scan(request):'),
        
        # Objectifs - Vues basées sur les classes
        (r'class ObjectiveListView\(LoginRequiredMixin, ListView\):',
         'class ObjectiveListView(PermissionRequiredMixin, ListView):\n    permission_required = \'objective_view\''),
        
        (r'class ObjectiveDetailView\(LoginRequiredMixin, DetailView\):',
         'class ObjectiveDetailView(PermissionRequiredMixin, DetailView):\n    permission_required = \'objective_view\''),
        
        (r'class ObjectiveCreateView\(LoginRequiredMixin, CreateView\):',
         'class ObjectiveCreateView(PermissionRequiredMixin, CreateView):\n    permission_required = \'objective_create\''),
        
        (r'class ObjectiveUpdateView\(LoginRequiredMixin, UpdateView\):',
         'class ObjectiveUpdateView(PermissionRequiredMixin, UpdateView):\n    permission_required = \'objective_edit\''),
        
        (r'class ObjectiveDeleteView\(LoginRequiredMixin, DeleteView\):',
         'class ObjectiveDeleteView(PermissionRequiredMixin, DeleteView):\n    permission_required = \'objective_delete\''),
        
        # Utilisateurs - Vues basées sur les classes
        (r'class UserListView\(LoginRequiredMixin, ListView\):',
         'class UserListView(PermissionRequiredMixin, ListView):\n    permission_required = \'user_view\''),
        
        (r'class UserDetailView\(LoginRequiredMixin, DetailView\):',
         'class UserDetailView(PermissionRequiredMixin, DetailView):\n    permission_required = \'user_view\''),
        
        (r'class UserCreateView\(LoginRequiredMixin, CreateView\):',
         'class UserCreateView(PermissionRequiredMixin, CreateView):\n    permission_required = \'user_create\''),
        
        (r'class UserUpdateView\(LoginRequiredMixin, UpdateView\):',
         'class UserUpdateView(PermissionRequiredMixin, UpdateView):\n    permission_required = \'user_edit\''),
        
        (r'class UserDeleteView\(LoginRequiredMixin, DeleteView\):',
         'class UserDeleteView(PermissionRequiredMixin, DeleteView):\n    permission_required = \'user_delete\''),
        
        # Paramètres
        (r'@login_required\s+def settings_dashboard\(request\):',
         '@login_required\n@require_permission(\'settings_view\')\ndef settings_dashboard(request):'),
        
        (r'@login_required\s+def role_permissions_list\(request\):',
         '@login_required\n@require_permission(\'settings_roles\')\ndef role_permissions_list(request):'),
        
        (r'@login_required\s+def role_permission_create\(request\):',
         '@login_required\n@require_permission(\'settings_roles\')\ndef role_permission_create(request):'),
        
        (r'@login_required\s+def role_permission_update\(request, permission_id\):',
         '@login_required\n@require_permission(\'settings_roles\')\ndef role_permission_update(request, permission_id):'),
        
        (r'@login_required\s+def role_permission_delete\(request, permission_id\):',
         '@login_required\n@require_permission(\'settings_roles\')\ndef role_permission_delete(request, permission_id):'),
        
        (r'@login_required\s+def bulk_role_permissions\(request\):',
         '@login_required\n@require_permission(\'settings_roles\')\ndef bulk_role_permissions(request):'),
        
        (r'@login_required\s+def reference_values_list\(request\):',
         '@login_required\n@require_permission(\'settings_references\')\ndef reference_values_list(request):'),
        
        (r'@login_required\s+def reference_value_create\(request\):',
         '@login_required\n@require_permission(\'settings_references\')\ndef reference_value_create(request):'),
        
        (r'@login_required\s+def reference_value_update\(request, reference_id\):',
         '@login_required\n@require_permission(\'settings_references\')\ndef reference_value_update(request, reference_id):'),
        
        (r'@login_required\s+def reference_value_delete\(request, reference_id\):',
         '@login_required\n@require_permission(\'settings_references\')\ndef reference_value_delete(request, reference_id):'),
        
        (r'@login_required\s+def reference_value_import\(request\):',
         '@login_required\n@require_permission(\'settings_references\')\ndef reference_value_import(request):'),
        
        (r'@login_required\s+def general_parameters_list\(request\):',
         '@login_required\n@require_permission(\'settings_view\')\ndef general_parameters_list(request):'),
        
        (r'@login_required\s+def general_parameter_create\(request\):',
         '@login_required\n@require_permission(\'settings_edit\')\ndef general_parameter_create(request):'),
        
        (r'@login_required\s+def general_parameter_update\(request, parameter_id\):',
         '@login_required\n@require_permission(\'settings_edit\')\ndef general_parameter_update(request, parameter_id):'),
        
        (r'@login_required\s+def general_parameter_delete\(request, parameter_id\):',
         '@login_required\n@require_permission(\'settings_edit\')\ndef general_parameter_delete(request, parameter_id):'),
        
        (r'@login_required\s+def system_logs_list\(request\):',
         '@login_required\n@require_permission(\'system_admin\')\ndef system_logs_list(request):'),
        
        (r'@login_required\s+def system_log_detail\(request, log_id\):',
         '@login_required\n@require_permission(\'system_admin\')\ndef system_log_detail(request, log_id):'),
        
        (r'@login_required\s+def system_logs_export\(request\):',
         '@login_required\n@require_permission(\'system_admin\')\ndef system_logs_export(request):'),
        
        (r'@login_required\s+def system_logs_clear\(request\):',
         '@login_required\n@require_permission(\'system_admin\')\ndef system_logs_clear(request):'),
        
        (r'@login_required\s+def settings_backup\(request\):',
         '@login_required\n@require_permission(\'data_backup\')\ndef settings_backup(request):'),
        
        (r'@login_required\s+def settings_restore\(request\):',
         '@login_required\n@require_permission(\'data_restore\')\ndef settings_restore(request):'),
    ]
    
    # Appliquer les remplacements
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # Ajouter les contextes avec les permissions pour les vues de liste
    # Badge list
    content = re.sub(
        r'context = \{\s*\'badges\': badges,\s*\'total_badges\': badges\.count\(\),\s*\};',
        '''context = {
        'badges': badges,
        'total_badges': badges.count(),
        'can_create': has_permission(request.user, 'badge_create'),
        'can_edit': has_permission(request.user, 'badge_edit'),
        'can_delete': has_permission(request.user, 'badge_delete'),
        'can_revoke': has_permission(request.user, 'badge_revoke'),
    };''',
        content
    )
    
    # Écrire le fichier mis à jour
    with open('core/views.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Toutes les vues ont été mises à jour avec les permissions!")

if __name__ == '__main__':
    update_views_file() 