/**
 * JavaScript simple pour les champs select avec recherche
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialiser tous les champs searchable-select
    const searchableSelects = document.querySelectorAll('.searchable-select');
    
    searchableSelects.forEach(select => {
        initSearchableSelect(select);
    });
});

function initSearchableSelect(selectElement) {
    const container = selectElement.closest('.searchable-select-container');
    const searchOverlay = container.querySelector('.search-overlay');
    const searchInput = searchOverlay.querySelector('.search-input');
    const resultsContainer = searchOverlay.querySelector('.search-results');
    const searchUrl = selectElement.dataset.searchUrl;
    
    // Événement sur le select pour afficher la recherche
    selectElement.addEventListener('focus', function() {
        showSearch();
    });
    
    selectElement.addEventListener('click', function(e) {
        e.preventDefault();
        showSearch();
    });
    
    // Événement sur l'input de recherche
    searchInput.addEventListener('input', function(e) {
        handleSearch(e.target.value);
    });
    
    searchInput.addEventListener('keydown', function(e) {
        handleKeydown(e);
    });
    
    // Fermer la recherche en cliquant ailleurs
    document.addEventListener('click', function(e) {
        if (!container.contains(e.target)) {
            hideSearch();
        }
    });
    
    function showSearch() {
        searchOverlay.style.display = 'block';
        searchInput.focus();
        searchInput.value = '';
        resultsContainer.innerHTML = '';
    }
    
    function hideSearch() {
        searchOverlay.style.display = 'none';
    }
    
    async function handleSearch(query) {
        if (query.length < 2) {
            resultsContainer.innerHTML = '';
            return;
        }
        
        try {
            const response = await fetch(`${searchUrl}?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            displayResults(data.results);
        } catch (error) {
            console.error('Erreur lors de la recherche:', error);
            resultsContainer.innerHTML = '<div class="search-error">Erreur lors de la recherche</div>';
        }
    }
    
    function displayResults(results) {
        if (results.length === 0) {
            resultsContainer.innerHTML = '<div class="search-no-results">Aucun résultat trouvé</div>';
            return;
        }
        
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
                selectResult(item);
            });
        });
    }
    
    function selectResult(resultItem) {
        const value = resultItem.dataset.value;
        const text = resultItem.dataset.text;
        
        // Mettre à jour le select
        selectElement.value = value;
        
        // Déclencher l'événement change
        selectElement.dispatchEvent(new Event('change', { bubbles: true }));
        
        // Masquer la recherche
        hideSearch();
    }
    
    function handleKeydown(e) {
        const results = resultsContainer.querySelectorAll('.search-result-item');
        
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            const current = resultsContainer.querySelector('.search-result-item.highlighted');
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
            const current = resultsContainer.querySelector('.search-result-item.highlighted');
            if (current) {
                current.classList.remove('highlighted');
                const prev = current.previousElementSibling;
                if (prev) {
                    prev.classList.add('highlighted');
                }
            }
        } else if (e.key === 'Enter') {
            e.preventDefault();
            const highlighted = resultsContainer.querySelector('.search-result-item.highlighted');
            if (highlighted) {
                selectResult(highlighted);
            }
        } else if (e.key === 'Escape') {
            hideSearch();
        }
    }
}
