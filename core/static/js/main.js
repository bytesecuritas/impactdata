// ===== FONCTIONNALITÉS PRINCIPALES DE L'APPLICATION =====

document.addEventListener('DOMContentLoaded', function() {
    
    // ===== GESTION DE LA SIDEBAR =====
    
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.querySelector('.col-md-9, .col-lg-10');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            if (mainContent) {
                mainContent.classList.toggle('expanded');
            }
        });
    }
    
    // ===== GESTION DE LA SIDEBAR MOBILE =====
    
    const sidebarClose = document.getElementById('sidebarClose');
    if (sidebarClose && sidebar) {
        sidebarClose.addEventListener('click', function() {
            sidebar.classList.remove('show');
        });
    }
    
    // ===== GESTION DES NOTIFICATIONS =====
    
    function updateNotificationBadge() {
        const badge = document.getElementById('notification-badge');
        if (badge) {
            // Simuler la récupération du nombre de notifications
            fetch('/api/notifications/count/')
                .then(response => response.json())
                .then(data => {
                    if (data.count > 0) {
                        badge.textContent = data.count;
                        badge.style.display = 'inline-block';
                    } else {
                        badge.style.display = 'none';
                    }
                })
                .catch(error => {
                    console.error('Erreur lors de la récupération des notifications:', error);
                });
        }
    }
    
    // Mettre à jour les notifications toutes les 30 secondes
    setInterval(updateNotificationBadge, 30000);
    
    // ===== GESTION DES FORMULAIRES =====
    
    function enhanceForms() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            // Ajouter des classes pour le style
            form.classList.add('enhanced-form');
            
            // Gestion de la soumission
            form.addEventListener('submit', function(e) {
                const submitBtn = this.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Envoi...';
                }
            });
        });
    }
    
    // ===== GESTION DES TABLEAUX =====
    
    function enhanceTables() {
        const tables = document.querySelectorAll('.table');
        
        tables.forEach(table => {
            // Ajouter des classes pour le style
            table.classList.add('enhanced-table');
            
            // Gestion du tri (si nécessaire)
            const sortableHeaders = table.querySelectorAll('th[data-sortable]');
            sortableHeaders.forEach(header => {
                header.style.cursor = 'pointer';
                header.addEventListener('click', function() {
                    sortTable(table, this);
                });
            });
        });
    }
    
    function sortTable(table, header) {
        const column = Array.from(header.parentElement.children).indexOf(header);
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        
        // Déterminer la direction du tri
        const isAscending = !header.classList.contains('sort-asc');
        
        // Supprimer les classes de tri précédentes
        header.parentElement.querySelectorAll('th').forEach(th => {
            th.classList.remove('sort-asc', 'sort-desc');
        });
        
        // Ajouter la classe appropriée
        header.classList.add(isAscending ? 'sort-asc' : 'sort-desc');
        
        // Trier les lignes
        rows.sort((a, b) => {
            const aValue = a.children[column].textContent.trim();
            const bValue = b.children[column].textContent.trim();
            
            if (isAscending) {
                return aValue.localeCompare(bValue);
            } else {
                return bValue.localeCompare(aValue);
            }
        });
        
        // Réorganiser les lignes
        rows.forEach(row => tbody.appendChild(row));
    }
    
    // ===== GESTION DES MODALES =====
    
    function enhanceModals() {
        const modals = document.querySelectorAll('.modal');
        
        modals.forEach(modal => {
            // Ajouter des classes pour le style
            modal.classList.add('enhanced-modal');
            
            // Gestion de la fermeture
            const closeButtons = modal.querySelectorAll('[data-bs-dismiss="modal"]');
            closeButtons.forEach(btn => {
                btn.addEventListener('click', function() {
                    // Nettoyer les formulaires dans la modale
                    const forms = modal.querySelectorAll('form');
                    forms.forEach(form => form.reset());
                });
            });
        });
    }
    
    // ===== GESTION DES TOOLTIPS =====
    
    function enhanceTooltips() {
        const tooltipElements = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        
        tooltipElements.forEach(element => {
            new bootstrap.Tooltip(element, {
                placement: 'top',
                trigger: 'hover'
            });
        });
    }
    
    // ===== GESTION DES POPOVERS =====
    
    function enhancePopovers() {
        const popoverElements = document.querySelectorAll('[data-bs-toggle="popover"]');
        
        popoverElements.forEach(element => {
            new bootstrap.Popover(element, {
                placement: 'top',
                trigger: 'click'
            });
        });
    }
    
    // ===== GESTION DES ALERTES =====
    
    function enhanceAlerts() {
        const alerts = document.querySelectorAll('.alert');
        
        alerts.forEach(alert => {
            // Ajouter un bouton de fermeture automatique
            if (!alert.querySelector('.btn-close')) {
                const closeBtn = document.createElement('button');
                closeBtn.type = 'button';
                closeBtn.className = 'btn-close';
                closeBtn.setAttribute('data-bs-dismiss', 'alert');
                closeBtn.setAttribute('aria-label', 'Fermer');
                alert.appendChild(closeBtn);
            }
            
            // Auto-fermeture après 5 secondes pour les alertes de succès
            if (alert.classList.contains('alert-success')) {
                setTimeout(() => {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                }, 5000);
            }
        });
    }
    
    // ===== GESTION DES BOUTONS =====
    
    function enhanceButtons() {
        const buttons = document.querySelectorAll('.btn');
        
        buttons.forEach(button => {
            // Ajouter des classes pour le style
            button.classList.add('enhanced-btn');
            
            // Gestion des boutons de suppression
            if (button.classList.contains('btn-danger') || button.textContent.includes('Supprimer')) {
                button.addEventListener('click', function(e) {
                    if (!confirm('Êtes-vous sûr de vouloir effectuer cette action ?')) {
                        e.preventDefault();
                        return false;
                    }
                });
            }
        });
    }
    
    // ===== GESTION DES LIENS =====
    
    function enhanceLinks() {
        const links = document.querySelectorAll('a[href]');
        
        links.forEach(link => {
            // Ajouter des classes pour le style
            link.classList.add('enhanced-link');
            
            // Gestion des liens externes
            if (link.hostname !== window.location.hostname) {
                link.setAttribute('target', '_blank');
                link.setAttribute('rel', 'noopener noreferrer');
            }
        });
    }
    
    // ===== GESTION DES IMAGES =====
    
    function enhanceImages() {
        const images = document.querySelectorAll('img');
        
        images.forEach(img => {
            // Ajouter des classes pour le style
            img.classList.add('enhanced-img');
            
            // Gestion des erreurs de chargement
            img.addEventListener('error', function() {
                this.src = '/static/images/placeholder.png';
                this.alt = 'Image non disponible';
            });
        });
    }
    
    // ===== GESTION DES CHAMPS DE FORMULAIRE =====
    
    function enhanceFormFields() {
        const formFields = document.querySelectorAll('input, select, textarea');
        
        formFields.forEach(field => {
            // Ajouter des classes pour le style
            field.classList.add('enhanced-field');
            
            // Gestion de la validation en temps réel
            field.addEventListener('blur', function() {
                validateField(this);
            });
        });
    }
    
    function validateField(field) {
        // Validation basique
        if (field.hasAttribute('required') && !field.value.trim()) {
            field.classList.add('is-invalid');
        } else {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
        }
    }
    
    // ===== GESTION DES ANIMATIONS =====
    
    function enhanceAnimations() {
        // Animation d'apparition pour les éléments
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                }
            });
        }, observerOptions);
        
        // Observer les éléments avec la classe 'animate-on-scroll'
        const animatedElements = document.querySelectorAll('.animate-on-scroll');
        animatedElements.forEach(el => observer.observe(el));
    }
    
    // ===== GESTION DES THEMES =====
    
    function enhanceThemes() {
        // Détection du thème système
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        // Appliquer le thème approprié
        if (prefersDark) {
            document.body.classList.add('dark-theme');
        } else {
            document.body.classList.add('light-theme');
        }
        
        // Écouter les changements de thème
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (e.matches) {
                document.body.classList.remove('light-theme');
                document.body.classList.add('dark-theme');
            } else {
                document.body.classList.remove('dark-theme');
                document.body.classList.add('light-theme');
            }
        });
    }
    
    // ===== INITIALISATION =====
    
    function init() {
        enhanceForms();
        enhanceTables();
        enhanceModals();
        enhanceTooltips();
        enhancePopovers();
        enhanceAlerts();
        enhanceButtons();
        enhanceLinks();
        enhanceImages();
        enhanceFormFields();
        enhanceAnimations();
        enhanceThemes();
        
        // Mettre à jour les notifications au chargement
        updateNotificationBadge();
    }
    
    // Démarrer l'initialisation
    init();
    
}); 