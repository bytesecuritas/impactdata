#!/usr/bin/env python3
"""
Script pour mettre à jour tous les templates avec les vérifications de permissions
"""

import os
import re

def update_template_file(file_path):
    """Met à jour un template avec les vérifications de permissions"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remplacer les boutons de création
    content = re.sub(
        r'<a href="{% url \'core:(\w+)_create\' %}" class="btn[^>]*>',
        r'{% if can_create %}\n<a href="{% url \'core:\1_create\' %}" class="btn',
        content
    )
    content = re.sub(
        r'(<a href="{% url \'core:\w+_create\' %}" class="btn[^>]*>.*?</a>)',
        r'\1\n{% endif %}',
        content
    )
    
    # Remplacer les boutons d'édition
    content = re.sub(
        r'<a href="{% url \'core:(\w+)_update\' (\w+)\.id %}" class="btn[^>]*>',
        r'{% if can_edit %}\n<a href="{% url \'core:\1_update\' \2.id %}" class="btn',
        content
    )
    content = re.sub(
        r'(<a href="{% url \'core:\w+_update\' \w+\.id %}" class="btn[^>]*>.*?</a>)',
        r'\1\n{% endif %}',
        content
    )
    
    # Remplacer les boutons de suppression
    content = re.sub(
        r'<a href="{% url \'core:(\w+)_delete\' (\w+)\.id %}" class="btn[^>]*>',
        r'{% if can_delete %}\n<a href="{% url \'core:\1_delete\' \2.id %}" class="btn',
        content
    )
    content = re.sub(
        r'(<a href="{% url \'core:\w+_delete\' \w+\.id %}" class="btn[^>]*>.*?</a>)',
        r'\1\n{% endif %}',
        content
    )
    
    # Remplacer les boutons de révocation de badge
    content = re.sub(
        r'<a href="{% url \'core:badge_revoke\' (\w+)\.id %}" class="btn[^>]*>',
        r'{% if can_revoke %}\n<a href="{% url \'core:badge_revoke\' \1.id %}" class="btn',
        content
    )
    content = re.sub(
        r'(<a href="{% url \'core:badge_revoke\' \w+\.id %}" class="btn[^>]*>.*?</a>)',
        r'\1\n{% endif %}',
        content
    )
    
    # Remplacer les boutons de réactivation de badge
    content = re.sub(
        r'<a href="{% url \'core:badge_reactivate\' (\w+)\.id %}" class="btn[^>]*>',
        r'{% if can_reactivate %}\n<a href="{% url \'core:badge_reactivate\' \1.id %}" class="btn',
        content
    )
    content = re.sub(
        r'(<a href="{% url \'core:badge_reactivate\' \w+\.id %}" class="btn[^>]*>.*?</a>)',
        r'\1\n{% endif %}',
        content
    )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def update_all_templates():
    """Met à jour tous les templates"""
    
    template_dirs = [
        'core/templates/core/adherents/',
        'core/templates/core/organizations/',
        'core/templates/core/interactions/',
        'core/templates/core/badges/',
        'core/templates/core/objectives/',
        'core/templates/core/users/',
        'core/templates/core/settings/',
    ]
    
    for template_dir in template_dirs:
        if os.path.exists(template_dir):
            for filename in os.listdir(template_dir):
                if filename.endswith('.html'):
                    file_path = os.path.join(template_dir, filename)
                    print(f"Mise à jour de {file_path}")
                    update_template_file(file_path)
    
    print("✅ Tous les templates ont été mis à jour!")

if __name__ == '__main__':
    update_all_templates() 