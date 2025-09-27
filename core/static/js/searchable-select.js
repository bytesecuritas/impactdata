/**
 * JavaScript pour les champs select avec recherche
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('🔍 Initialisation des champs select avec recherche...');
    
    // Attendre un peu pour que le DOM soit complètement chargé
    setTimeout(function() {
        initAllSearchableSelects();
    }, 100);
});

function initAllSearchableSelects() {
    const searchableSelects = document.querySelectorAll('.searchable-select');
    console.log(`📋 Trouvé ${searchableSelects.length} champs select avec recherche`);
    
    searchableSelects.forEach((select, index) => {
        console.log(`🔧 Initialisation du champ ${index + 1}`);
        initSearchableSelect(select);
    });
}

function initSearchableSelect(selectElement) {
    console.log('🚀 Initialisation d\'un champ select:', selectElement);
    
    const container = selectElement.closest('.searchable-select-container');
    if (!container) {
        console.error('❌ Conteneur non trouvé pour:', selectElement);
        return;
    }
    
    const searchOverlay = container.querySelector('.search-overlay');
    if (!searchOverlay) {
        console.error('❌ Overlay de recherche non trouvé');
        return;
    }
    
    const searchInput = searchOverlay.querySelector('.search-input');
    const resultsContainer = searchOverlay.querySelector('.search-results');
    const searchUrl = selectElement.dataset.searchUrl;
    
    console.log('✅ Éléments trouvés:', {
        container: !!container,
        searchOverlay: !!searchOverlay,
        searchInput: !!searchInput,
        resultsContainer: !!resultsContainer,
        searchUrl: searchUrl
    });
    
    // Événement sur le select pour afficher la recherche
    selectElement.addEventListener('focus', function() {
        console.log('👆 Focus sur le select');
        showSearch();
    });
    
    selectElement.addEventListener('click', function(e) {
        console.log('🖱️ Clic sur le select');
        e.preventDefault();
        showSearch();
    });
    
    // Événement sur l'input de recherche
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            console.log('⌨️ Saisie dans la recherche:', e.target.value);
            handleSearch(e.target.value);
        });
        
        searchInput.addEventListener('keydown', function(e) {
            handleKeydown(e);
        });
        
        // IMPORTANT: Empêcher la propagation des événements
        searchInput.addEventListener('click', function(e) {
            e.stopPropagation();
        });
        
        searchInput.addEventListener('focus', function(e) {
            e.stopPropagation();
        });
    }
    
    // Fermer la recherche en cliquant ailleurs
    document.addEventListener('click', function(e) {
        if (!container.contains(e.target)) {
            hideSearch();
        }
    });
    
    function showSearch() {
        console.log('👁️ Affichage de la recherche');
        if (searchOverlay) {
            searchOverlay.style.display = 'block';
            if (searchInput) {
                // Délai pour s'assurer que l'overlay est affiché
                setTimeout(function() {
                    searchInput.focus();
                    searchInput.value = '';
                }, 10);
            }
            if (resultsContainer) {
                resultsContainer.innerHTML = '';
            }
        }
    }
    
    function hideSearch() {
        console.log('🙈 Masquage de la recherche');
        if (searchOverlay) {
            searchOverlay.style.display = 'none';
        }
    }
    
    async function handleSearch(query) {
        if (!searchUrl) {
            console.error('❌ URL de recherche non définie');
            return;
        }
        
        if (query.length < 2) {
            if (resultsContainer) {
                resultsContainer.innerHTML = '';
            }
            return;
        }
        
        console.log('🔍 Recherche:', query);
        
        try {
            // Corriger l'URL pour inclure le préfixe /core/
            let fullUrl = searchUrl;
            if (!searchUrl.includes('/core/')) {
                fullUrl = searchUrl.startsWith('/') ? `/core${searchUrl}` : `/core/${searchUrl}`;
            }
            console.log('🔗 URL complète:', fullUrl);
            
            const response = await fetch(`${fullUrl}?q=${encodeURIComponent(query)}`);
            console.log('📡 Réponse:', response.status, response.statusText);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('📊 Résultats:', data);
            displayResults(data.results);
        } catch (error) {
            console.error('❌ Erreur lors de la recherche:', error);
            if (resultsContainer) {
                resultsContainer.innerHTML = `<div class="search-error">Erreur: ${error.message}</div>`;
            }
        }
    }
    
    function displayResults(results) {
        if (!resultsContainer) {
            console.error('❌ Conteneur de résultats non trouvé');
            return;
        }
        
        if (results.length === 0) {
            resultsContainer.innerHTML = '<div class="search-no-results">Aucun résultat trouvé</div>';
            return;
        }
        
        console.log('📋 Affichage de', results.length, 'résultats');
        
        const resultsHtml = results.map(result => `
            <div class="search-result-item" data-value="${result.id}" data-text="${result.text}">
                <div class="result-text">${result.text}</div>
                ${result.matricule ? `<div class="result-matricule">Matricule: ${result.matricule}</div>` : ''}
                ${result.phone ? `<div class="result-phone">Tél: ${result.phone}</div>` : ''}
            </div>
        `).join('');
        
        resultsContainer.innerHTML = resultsHtml;
        
        // Ajouter les événements aux résultats
        resultsContainer.querySelectorAll('.search-result-item').forEach(item => {
            item.addEventListener('click', function() {
                console.log('✅ Sélection d\'un résultat:', item.dataset.text);
                selectResult(item);
            });
        });
    }
    
    function selectResult(resultItem) {
        const value = resultItem.dataset.value;
        const text = resultItem.dataset.text;
        
        console.log('🎯 Sélection:', { value, text });
        
        // Mettre à jour le select
        selectElement.value = value;
        
        // Déclencher l'événement change
        selectElement.dispatchEvent(new Event('change', { bubbles: true }));
        
        // Masquer la recherche
        hideSearch();
    }
    
    function handleKeydown(e) {
        const results = resultsContainer ? resultsContainer.querySelectorAll('.search-result-item') : [];
        
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            const current = resultsContainer ? resultsContainer.querySelector('.search-result-item.highlighted') : null;
            if (current) {
                current.classList.remove('highlighted');
                const next = current.nextElementSibling;
                if (next) {
                    next.classList.add('highlighted');
                }
            } else if (results.length > 0) {
                results[0].classList.add('highlighted');
            }
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            const current = resultsContainer ? resultsContainer.querySelector('.search-result-item.highlighted') : null;
            if (current) {
                current.classList.remove('highlighted');
                const prev = current.previousElementSibling;
                if (prev) {
                    prev.classList.add('highlighted');
                }
            }
        } else if (e.key === 'Enter') {
            e.preventDefault();
            const highlighted = resultsContainer ? resultsContainer.querySelector('.search-result-item.highlighted') : null;
            if (highlighted) {
                selectResult(highlighted);
            }
        } else if (e.key === 'Escape') {
            hideSearch();
        }
    }
}