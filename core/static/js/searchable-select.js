/**
 * JavaScript pour les champs select avec fonctionnalité de recherche
 * Comportement : Affiche tous les éléments au clic, filtre en temps réel pendant la saisie
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('🔍 Initialisation des champs searchable-select...');
    
    const searchableSelects = document.querySelectorAll('.searchable-select');
    console.log(`📋 Trouvé ${searchableSelects.length} champs select`);
    
    searchableSelects.forEach((select, index) => {
        console.log(`🔧 Initialisation du champ ${index + 1}`);
        initSearchableSelect(select);
    });
});

function initSearchableSelect(selectElement) {
    const container = selectElement.closest('.searchable-select-container');
    const searchOverlay = container.querySelector('.search-overlay');
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
    
    // Variable pour stocker tous les éléments
    let allItems = [];
    let isInitialized = false;
    
    // Événement sur le select
    selectElement.addEventListener('click', function(e) {
        console.log('🖱️ Clic sur le select');
        e.preventDefault();
        showSearch();
    });
    
    // Événement sur l'input
    searchInput.addEventListener('input', function(e) {
        console.log('⌨️ Saisie:', e.target.value);
        handleSearch(e.target.value);
    });
    
    // Fermer en cliquant ailleurs
    document.addEventListener('click', function(e) {
        if (!container.contains(e.target)) {
            hideSearch();
        }
    });
    
    function showSearch() {
        console.log('👁️ Affichage de la recherche');
        searchOverlay.style.display = 'block';
        setTimeout(function() {
            searchInput.focus();
            searchInput.value = '';
        }, 10);
        
        // Charger tous les éléments au premier clic
        if (!isInitialized) {
            loadAllItems();
        } else {
            // Afficher tous les éléments
            displayResults(allItems);
        }
    }
    
    function hideSearch() {
        console.log('🙈 Masquage de la recherche');
        searchOverlay.style.display = 'none';
    }
    
    async function loadAllItems() {
        try {
            // Corriger l'URL pour inclure le préfixe /core/
            let fullUrl = searchUrl;
            if (!searchUrl.includes('/core/')) {
                fullUrl = searchUrl.startsWith('/') ? `/core${searchUrl}` : `/core/${searchUrl}`;
            }
            console.log('🔗 URL complète:', fullUrl);
            
            // Charger tous les éléments (sans paramètre q ou avec q vide)
            const response = await fetch(`${fullUrl}?q=`);
            console.log('📡 Réponse:', response.status, response.statusText);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('📊 Tous les éléments:', data);
            allItems = data.results || [];
            isInitialized = true;
            
            // Afficher tous les éléments
            displayResults(allItems);
        } catch (error) {
            console.error('❌ Erreur lors du chargement:', error);
            allItems = [];
            if (resultsContainer) {
                resultsContainer.innerHTML = `<div class="search-error">Erreur: ${error.message}</div>`;
            }
        }
    }
    
    function handleSearch(query) {
        console.log('🔍 Recherche:', query);
        
        if (!isInitialized) {
            return;
        }
        
        // Filtrer les éléments localement
        const filteredItems = filterItemsLocally(query);
        displayResults(filteredItems);
    }
    
    function filterItemsLocally(query) {
        if (!query || query.length < 2) {
            return allItems;
        }
        
        const lowerQuery = query.toLowerCase();
        return allItems.filter(item => {
            // Convertir en string et vérifier si la valeur existe avant d'appeler toLowerCase
            const text = String(item.text || '').toLowerCase();
            const matricule = String(item.matricule || '').toLowerCase();
            const identifiant = String(item.identifiant || '').toLowerCase();
            const phone = String(item.phone || '');
            const name = String(item.name || '').toLowerCase();

            return text.includes(lowerQuery) ||
                   matricule.includes(lowerQuery) ||
                   identifiant.includes(lowerQuery) ||
                   phone.includes(query) ||
                   name.includes(lowerQuery);
        });
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
                ${result.identifiant ? `<div class="result-identifiant">ID: ${result.identifiant}</div>` : ''}
                ${result.phone ? `<div class="result-phone">Tél: ${result.phone}</div>` : ''}
            </div>
        `).join('');
        
        resultsContainer.innerHTML = resultsHtml;
        
        // Événements sur les résultats
        resultsContainer.querySelectorAll('.search-result-item').forEach(item => {
            item.addEventListener('click', function() {
                console.log('✅ Sélection:', item.dataset.text);
                selectResult(item);
            });
        });
    }
    
    function selectResult(resultItem) {
        const value = resultItem.dataset.value;
        const text = resultItem.dataset.text;
        
        selectElement.value = value;
        selectElement.dispatchEvent(new Event('change', { bubbles: true }));
        hideSearch();
    }
}