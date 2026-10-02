// watchlist.js - Handles watchlist functionality

document.addEventListener('DOMContentLoaded', function() {
    // Setup watchlist functionality
    setupWatchlist();
});

function setupWatchlist() {
    // Handle add stock to watchlist
    const addStockForm = document.getElementById('add-to-watchlist-form');
    if (addStockForm) {
        addStockForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const symbol = document.getElementById('stock-symbol').value.trim().toUpperCase();
            const watchlistId = document.getElementById('watchlist-id').value;
            
            if (!symbol) {
                showAlert('Please enter a valid stock symbol', 'danger');
                return;
            }
            
            addToWatchlist(watchlistId, symbol);
        });
    }
    
    // Handle remove from watchlist buttons
    const removeButtons = document.querySelectorAll('.remove-from-watchlist');
    removeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const symbol = this.getAttribute('data-symbol');
            const watchlistId = this.getAttribute('data-watchlist-id');
            removeFromWatchlist(watchlistId, symbol);
        });
    });
    
    // Handle stock search in watchlist
    const searchInput = document.getElementById('watchlist-search');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(handleWatchlistSearch, 300));
    }
}

// Add stock to watchlist
function addToWatchlist(watchlistId, symbol) {
    fetch('/api/watchlist/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            watchlist_id: watchlistId,
            symbol: symbol
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(data.message, 'success');
            // Reload the page to show the updated watchlist
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showAlert(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error adding to watchlist:', error);
        showAlert('An error occurred while adding to watchlist', 'danger');
    });
}

// Remove stock from watchlist
function removeFromWatchlist(watchlistId, symbol) {
    fetch('/api/watchlist/remove', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            watchlist_id: watchlistId,
            symbol: symbol
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(data.message, 'success');
            // Find the row and remove it with animation
            const row = document.querySelector(`tr[data-symbol="${symbol}"]`);
            if (row) {
                row.classList.add('fade-out');
                setTimeout(() => {
                    row.remove();
                }, 500);
            }
        } else {
            showAlert(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error removing from watchlist:', error);
        showAlert('An error occurred while removing from watchlist', 'danger');
    });
}

// Handle watchlist search
function handleWatchlistSearch() {
    const query = document.getElementById('watchlist-search').value.trim().toLowerCase();
    const rows = document.querySelectorAll('#watchlist-table tbody tr');
    
    rows.forEach(row => {
        const symbol = row.getAttribute('data-symbol').toLowerCase();
        const name = row.querySelector('.company-name').textContent.toLowerCase();
        
        if (symbol.includes(query) || name.includes(query)) {
            row.classList.remove('d-none');
        } else {
            row.classList.add('d-none');
        }
    });
}

// Show alert message
function showAlert(message, type) {
    const alertsContainer = document.getElementById('alerts-container');
    if (!alertsContainer) return;
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    alertsContainer.appendChild(alert);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        alert.classList.remove('show');
        setTimeout(() => alert.remove(), 300);
    }, 3000);
}

// Debounce function to limit function calls
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        const context = this;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
}
