// ===== AMÉLIORATION DE LA PAGE DE DÉTAIL D'ORGANISATION =====

document.addEventListener('DOMContentLoaded', function() {
    
    // ===== ANIMATIONS D'ENTRÉE =====
    
    function animateElements() {
        const elements = document.querySelectorAll('.info-section, .stats-card-professional, .adherent-row');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry, index) => {
                if (entry.isIntersecting) {
                    setTimeout(() => {
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }, index * 100);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });
        
        elements.forEach(el => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(20px)';
            el.style.transition = 'all 0.6s ease';
            observer.observe(el);
        });
    }
    
    // ===== AMÉLIORATION DES LIENS DE CONTACT =====
    
    function enhanceContactLinks() {
        const contactLinks = document.querySelectorAll('.contact-link');
        
        contactLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                // Ajouter un effet de clic
                this.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    this.style.transform = '';
                }, 150);
            });
            
            // Effet hover
            link.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-1px)';
            });
            
            link.addEventListener('mouseleave', function() {
                this.style.transform = '';
            });
        });
    }
    
    // ===== AMÉLIORATION DU TABLEAU DES ADHÉRENTS =====
    
    function enhanceAdherentsTable() {
        const table = document.querySelector('.adherents-table');
        if (!table) return;
        
        const rows = table.querySelectorAll('.adherent-row');
        
        rows.forEach((row, index) => {
            // Animation d'entrée progressive
            row.style.opacity = '0';
            row.style.transform = 'translateX(-20px)';
            
            setTimeout(() => {
                row.style.transition = 'all 0.5s ease';
                row.style.opacity = '1';
                row.style.transform = 'translateX(0)';
            }, index * 100);
            
            // Effet hover amélioré
            row.addEventListener('mouseenter', function() {
                this.style.transform = 'scale(1.02) translateX(5px)';
                this.style.boxShadow = '0 8px 24px rgba(0, 0, 0, 0.12)';
            });
            
            row.addEventListener('mouseleave', function() {
                this.style.transform = 'scale(1) translateX(0)';
                this.style.boxShadow = '';
            });
        });
    }
    
    // ===== AMÉLIORATION DES BADGES =====
    
    function enhanceBadges() {
        const badges = document.querySelectorAll('.type-badge, .badge-success, .badge-danger');
        
        badges.forEach(badge => {
            badge.addEventListener('mouseenter', function() {
                this.style.transform = 'scale(1.1)';
                this.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.2)';
            });
            
            badge.addEventListener('mouseleave', function() {
                this.style.transform = 'scale(1)';
                this.style.boxShadow = '';
            });
        });
    }
    
    // ===== AMÉLIORATION DES BOUTONS D'ACTION =====
    
    function enhanceActionButtons() {
        const actionButtons = document.querySelectorAll('.action-buttons .btn');
        
        actionButtons.forEach(btn => {
            btn.addEventListener('click', function(e) {
                // Effet de clic
                this.style.transform = 'scale(0.9)';
                setTimeout(() => {
                    this.style.transform = '';
                }, 150);
            });
        });
    }
    
    // ===== AMÉLIORATION DES STATISTIQUES =====
    
    function enhanceStatsCards() {
        const statsCards = document.querySelectorAll('.stats-card-professional');
        
        statsCards.forEach((card, index) => {
            // Animation d'entrée
            card.style.opacity = '0';
            card.style.transform = 'translateY(30px)';
            
            setTimeout(() => {
                card.style.transition = 'all 0.6s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 200);
            
            // Effet hover
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-5px) scale(1.02)';
            });
            
            card.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0) scale(1)';
            });
        });
    }
    
    // ===== AMÉLIORATION DE L'EN-TÊTE =====
    
    function enhanceHeader() {
        const header = document.querySelector('.organization-header');
        if (!header) return;
        
        // Animation d'entrée
        header.style.opacity = '0';
        header.style.transform = 'translateY(-20px)';
        
        setTimeout(() => {
            header.style.transition = 'all 0.8s ease';
            header.style.opacity = '1';
            header.style.transform = 'translateY(0)';
        }, 100);
        
        // Effet parallaxe léger
        window.addEventListener('scroll', function() {
            const scrolled = window.pageYOffset;
            const rate = scrolled * -0.5;
            header.style.transform = `translateY(${rate}px)`;
        });
    }
    
    // ===== AMÉLIORATION DES SECTIONS D'INFORMATIONS =====
    
    function enhanceInfoSections() {
        const infoSections = document.querySelectorAll('.info-section');
        
        infoSections.forEach((section, index) => {
            // Animation d'entrée
            section.style.opacity = '0';
            section.style.transform = 'translateX(-30px)';
            
            setTimeout(() => {
                section.style.transition = 'all 0.6s ease';
                section.style.opacity = '1';
                section.style.transform = 'translateX(0)';
            }, index * 150);
            
            // Effet hover
            section.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-3px) scale(1.01)';
            });
            
            section.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0) scale(1)';
            });
        });
    }
    
    // ===== AMÉLIORATION DES AVATARS =====
    
    function enhanceAvatars() {
        const avatars = document.querySelectorAll('.adherent-avatar');
        
        avatars.forEach(avatar => {
            avatar.addEventListener('mouseenter', function() {
                this.style.transform = 'scale(1.1)';
                this.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.2)';
            });
            
            avatar.addEventListener('mouseleave', function() {
                this.style.transform = 'scale(1)';
                this.style.boxShadow = '';
            });
        });
    }
    
    // ===== AMÉLIORATION DE LA NAVIGATION =====
    
    function enhanceNavigation() {
        const backButton = document.querySelector('.navigation-footer .btn');
        if (!backButton) return;
        
        backButton.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px) scale(1.05)';
        });
        
        backButton.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    }
    
    // ===== COMPTEUR ANIMÉ =====
    
    function animateCounters() {
        const counters = document.querySelectorAll('.stats-card-professional h3');
        
        counters.forEach(counter => {
            const target = parseInt(counter.textContent.replace(/\D/g, ''));
            const duration = 2000;
            const step = target / (duration / 16);
            let current = 0;
            
            const timer = setInterval(() => {
                current += step;
                if (current >= target) {
                    current = target;
                    clearInterval(timer);
                }
                counter.textContent = Math.floor(current).toLocaleString();
            }, 16);
        });
    }
    
    // ===== AMÉLIORATION DES BREADCRUMBS =====
    
    function enhanceBreadcrumbs() {
        const breadcrumbItems = document.querySelectorAll('.breadcrumb-item');
        
        breadcrumbItems.forEach((item, index) => {
            item.style.opacity = '0';
            item.style.transform = 'translateX(-10px)';
            
            setTimeout(() => {
                item.style.transition = 'all 0.4s ease';
                item.style.opacity = '1';
                item.style.transform = 'translateX(0)';
            }, index * 100);
        });
    }
    
    // ===== GESTION DES ÉTATS DE CHARGEMENT =====
    
    function showLoadingState() {
        const content = document.querySelector('.container-fluid');
        if (content) {
            content.style.opacity = '0.7';
            content.style.pointerEvents = 'none';
        }
    }
    
    function hideLoadingState() {
        const content = document.querySelector('.container-fluid');
        if (content) {
            content.style.opacity = '1';
            content.style.pointerEvents = 'auto';
        }
    }
    
    // ===== AMÉLIORATION DES LIENS DE CONTACT =====
    
    function enhanceContactLinks() {
        const phoneLinks = document.querySelectorAll('a[href^="tel:"]');
        const whatsappLinks = document.querySelectorAll('a[href^="https://wa.me/"]');
        
        phoneLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                // Confirmation pour les appels
                if (!confirm('Voulez-vous appeler ce numéro ?')) {
                    e.preventDefault();
                }
            });
        });
        
        whatsappLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                // Confirmation pour WhatsApp
                if (!confirm('Voulez-vous ouvrir WhatsApp ?')) {
                    e.preventDefault();
                }
            });
        });
    }
    
    // ===== INITIALISATION =====
    
    function init() {
        // Démarrer les animations après un court délai
        setTimeout(() => {
            animateElements();
            enhanceHeader();
            enhanceInfoSections();
            enhanceStatsCards();
            enhanceBreadcrumbs();
        }, 100);
        
        // Initialiser les autres améliorations
        enhanceContactLinks();
        enhanceAdherentsTable();
        enhanceBadges();
        enhanceActionButtons();
        enhanceAvatars();
        enhanceNavigation();
        
        // Démarrer les compteurs animés
        setTimeout(animateCounters, 500);
    }
    
    // Démarrer l'initialisation
    init();
    
}); 