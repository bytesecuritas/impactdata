// ===== AMÉLIORATION DES CHAMPS DE RECHERCHE ET TRI =====

document.addEventListener('DOMContentLoaded', function() {
    
    // ===== GESTION DES FILTRES ACTIFS =====
    
    function updateActiveFiltersCount() {
        const form = document.querySelector('.search-form');
        if (!form) return;
        
        const formData = new FormData(form);
        let activeFilters = 0;
        
        // Compter les champs avec des valeurs
        for (let [key, value] of formData.entries()) {
            if (value && value.trim() !== '' && key !== 'csrfmiddlewaretoken') {
                activeFilters++;
            }
        }
        
        // Mettre à jour le compteur
        const filterCount = document.getElementById('activeFilters');
        if (filterCount) {
            filterCount.textContent = `${activeFilters} filtre${activeFilters > 1 ? 's' : ''} actif${activeFilters > 1 ? 's' : ''}`;
        }
    }
    
    // ===== AMÉLIORATION DES CHAMPS DE DATE =====
    
    function enhanceDateFields() {
        const dateFields = document.querySelectorAll('input[type="date"]');
        
        dateFields.forEach(field => {
            // Ajouter une classe pour le style
            field.classList.add('enhanced-date');
            
            // Améliorer l'expérience utilisateur
            field.addEventListener('focus', function() {
                this.parentElement.classList.add('focused');
            });
            
            field.addEventListener('blur', function() {
                this.parentElement.classList.remove('focused');
            });
            
            // Validation en temps réel
            field.addEventListener('change', function() {
                validateDateField(this);
            });
        });
    }
    
    function validateDateField(field) {
        const value = field.value;
        if (!value) return;
        
        const date = new Date(value);
        const today = new Date();
        
        // Supprimer les classes d'erreur précédentes
        field.classList.remove('is-invalid', 'is-valid');
        
        // Validation basique
        if (isNaN(date.getTime())) {
            field.classList.add('is-invalid');
            showFieldError(field, 'Date invalide');
        } else {
            field.classList.add('is-valid');
            hideFieldError(field);
        }
    }
    
    // ===== AMÉLIORATION DES CHECKBOXES =====
    
    function enhanceCheckboxes() {
        const checkboxes = document.querySelectorAll('.custom-checkbox input[type="checkbox"]');
        
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                const container = this.closest('.custom-checkbox');
                
                if (this.checked) {
                    container.classList.add('checked');
                } else {
                    container.classList.remove('checked');
                }
                
                updateActiveFiltersCount();
            });
        });
    }
    
    // ===== AMÉLIORATION DES CHAMPS DE SÉLECTION =====
    
    function enhanceSelectFields() {
        const selectFields = document.querySelectorAll('.search-form select');
        
        selectFields.forEach(select => {
            // Ajouter une classe pour le style
            select.classList.add('enhanced-select');
            
            // Améliorer l'expérience utilisateur
            select.addEventListener('focus', function() {
                this.parentElement.classList.add('focused');
            });
            
            select.addEventListener('blur', function() {
                this.parentElement.classList.remove('focused');
            });
            
            select.addEventListener('change', function() {
                updateActiveFiltersCount();
            });
        });
    }
    
    // ===== AMÉLIORATION DES CHAMPS DE TEXTE =====
    
    function enhanceTextFields() {
        const textFields = document.querySelectorAll('.search-form input[type="text"], .search-form input[type="search"]');
        
        textFields.forEach(field => {
            // Ajouter une classe pour le style
            field.classList.add('enhanced-text');
            
            // Améliorer l'expérience utilisateur
            field.addEventListener('focus', function() {
                this.parentElement.classList.add('focused');
            });
            
            field.addEventListener('blur', function() {
                this.parentElement.classList.remove('focused');
            });
            
            // Recherche en temps réel (optionnel)
            field.addEventListener('input', function() {
                debounce(() => {
                    updateActiveFiltersCount();
                }, 300)();
            });
        });
    }
    
    // ===== GESTION DES ERREURS =====
    
    function showFieldError(field, message) {
        // Supprimer les erreurs précédentes
        hideFieldError(field);
        
        // Créer le message d'erreur
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error';
        errorDiv.textContent = message;
        errorDiv.style.color = '#e53e3e';
        errorDiv.style.fontSize = '0.75rem';
        errorDiv.style.marginTop = '0.25rem';
        
        // Insérer après le champ
        field.parentNode.appendChild(errorDiv);
    }
    
    function hideFieldError(field) {
        const existingError = field.parentNode.querySelector('.field-error');
        if (existingError) {
            existingError.remove();
        }
    }
    
    // ===== FONCTION DEBOUCE =====
    
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // ===== AMÉLIORATION DU BOUTON DE RECHERCHE =====
    
    function enhanceSearchButton() {
        const searchBtn = document.querySelector('.search-btn');
        if (!searchBtn) return;
        
        searchBtn.addEventListener('click', function(e) {
            // Ajouter un état de chargement
            this.classList.add('loading');
            this.disabled = true;
            
            // Remplacer le texte par un indicateur de chargement
            const originalContent = this.innerHTML;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Recherche...';
            
            // Simuler un délai (à retirer en production)
            setTimeout(() => {
                this.classList.remove('loading');
                this.disabled = false;
                this.innerHTML = originalContent;
            }, 1000);
        });
    }
    
    // ===== AMÉLIORATION DU BOUTON DE RÉINITIALISATION =====
    
    function enhanceClearButton() {
        const clearBtn = document.querySelector('.clear-btn');
        if (!clearBtn) return;
        
        clearBtn.addEventListener('click', function(e) {
            // Confirmation avant réinitialisation
            if (!confirm('Êtes-vous sûr de vouloir réinitialiser tous les filtres ?')) {
                e.preventDefault();
                return;
            }
            
            // Ajouter un effet visuel
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
        });
    }
    
    // ===== GESTION DE L'EXPANSION/RÉDUCTION =====
    
    function enhanceToggleButton() {
        const toggleBtn = document.querySelector('.toggle-search');
        if (!toggleBtn) return;
        
        toggleBtn.addEventListener('click', function() {
            const icon = this.querySelector('.transition-icon');
            if (icon) {
                // L'animation est gérée par CSS
            }
        });
    }
    
    // ===== AMÉLIORATION DES CHAMPS DE TRI =====
    
    function enhanceSortFields() {
        const sortFields = document.querySelectorAll('.sort-field select');
        
        sortFields.forEach(select => {
            select.addEventListener('change', function() {
                const container = this.closest('.sort-field');
                
                // Supprimer les classes précédentes
                container.classList.remove('asc', 'desc');
                
                // Ajouter la classe appropriée
                if (this.value.includes('asc')) {
                    container.classList.add('asc');
                } else if (this.value.includes('desc')) {
                    container.classList.add('desc');
                }
            });
        });
    }
    
    // ===== GESTION DES BADGES DE FILTRES ACTIFS =====
    
    function createActiveFilterBadges() {
        const form = document.querySelector('.search-form');
        if (!form) return;
        
        const formData = new FormData(form);
        const badgesContainer = document.createElement('div');
        badgesContainer.className = 'active-filter-badges';
        badgesContainer.style.marginTop = '1rem';
        badgesContainer.style.display = 'flex';
        badgesContainer.style.flexWrap = 'wrap';
        badgesContainer.style.gap = '0.5rem';
        
        let hasActiveFilters = false;
        
        for (let [key, value] of formData.entries()) {
            if (value && value.trim() !== '' && key !== 'csrfmiddlewaretoken') {
                hasActiveFilters = true;
                
                const badge = document.createElement('span');
                badge.className = 'active-filter-badge';
                badge.innerHTML = `
                    ${getFieldLabel(key)}: ${value}
                    <button type="button" class="remove-filter" data-field="${key}">
                        <i class="fas fa-times"></i>
                    </button>
                `;
                
                // Gestion de la suppression
                const removeBtn = badge.querySelector('.remove-filter');
                removeBtn.addEventListener('click', function() {
                    const fieldName = this.dataset.field;
                    const field = form.querySelector(`[name="${fieldName}"]`);
                    if (field) {
                        field.value = '';
                        field.dispatchEvent(new Event('change'));
                    }
                    badge.remove();
                    updateActiveFiltersCount();
                });
                
                badgesContainer.appendChild(badge);
            }
        }
        
        // Afficher les badges si il y en a
        const existingBadges = form.querySelector('.active-filter-badges');
        if (existingBadges) {
            existingBadges.remove();
        }
        
        if (hasActiveFilters) {
            form.appendChild(badgesContainer);
        }
    }
    
    function getFieldLabel(fieldName) {
        const labels = {
            'keywords': 'Mots-clés',
            'status': 'Statut',
            'personnel': 'Personnel',
            'adherent': 'Adhérent',
            'due_date_from': 'Date début',
            'due_date_to': 'Date fin',
            'overdue_only': 'En retard',
            'due_soon': 'Échéance proche'
        };
        
        return labels[fieldName] || fieldName;
    }
    
    // ===== INITIALISATION =====
    
    function init() {
        updateActiveFiltersCount();
        enhanceDateFields();
        enhanceCheckboxes();
        enhanceSelectFields();
        enhanceTextFields();
        enhanceSearchButton();
        enhanceClearButton();
        enhanceToggleButton();
        enhanceSortFields();
        
        // Écouter les changements de formulaire
        const form = document.querySelector('.search-form');
        if (form) {
            form.addEventListener('change', function() {
                updateActiveFiltersCount();
                createActiveFilterBadges();
            });
            
            form.addEventListener('input', debounce(function() {
                updateActiveFiltersCount();
                createActiveFilterBadges();
            }, 300));
        }
    }
    
    // Démarrer l'initialisation
    init();
    
}); 