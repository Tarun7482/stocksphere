// orders.js - Handles orders functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize date range picker if it exists
    const dateRangePicker = document.getElementById('date-range');
    if (dateRangePicker) {
        // Note: In a real app, we'd use a date range picker library
        // For simplicity, we're using native date inputs
        dateRangePicker.addEventListener('submit', function(e) {
            e.preventDefault();
            filterOrdersByDate();
        });
    }
    
    // Handle order search
    const searchInput = document.getElementById('order-search');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(handleOrderSearch, 300));
    }
    
    // Handle order type filters
    const typeFilters = document.querySelectorAll('.order-type-filter');
    typeFilters.forEach(filter => {
        filter.addEventListener('click', function() {
            const type = this.getAttribute('data-type');
            filterOrdersByType(type);
            
            // Update active filter button
            typeFilters.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
        });
    });
});

// Filter orders by date range
function filterOrdersByDate() {
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;
    
    if (!startDate || !endDate) {
        showAlert('Please select both start and end dates', 'warning');
        return;
    }
    
    const start = new Date(startDate);
    const end = new Date(endDate);
    end.setHours(23, 59, 59); // Include the full end day
    
    const rows = document.querySelectorAll('#orders-table tbody tr');
    
    rows.forEach(row => {
        const dateStr = row.getAttribute('data-date');
        const orderDate = new Date(dateStr);
        
        if (orderDate >= start && orderDate <= end) {
            row.classList.remove('d-none');
        } else {
            row.classList.add('d-none');
        }
    });
}

// Filter orders by type (BUY/SELL/ALL)
function filterOrdersByType(type) {
    const rows = document.querySelectorAll('#orders-table tbody tr');
    
    rows.forEach(row => {
        if (type === 'ALL') {
            row.classList.remove('d-none');
        } else {
            const orderType = row.getAttribute('data-type');
            if (orderType === type) {
                row.classList.remove('d-none');
            } else {
                row.classList.add('d-none');
            }
        }
    });
}

// Handle order search
function handleOrderSearch() {
    const query = document.getElementById('order-search').value.trim().toLowerCase();
    const rows = document.querySelectorAll('#orders-table tbody tr');
    
    rows.forEach(row => {
        const symbol = row.querySelector('.order-symbol').textContent.toLowerCase();
        const orderType = row.querySelector('.order-type').textContent.toLowerCase();
        const orderStatus = row.querySelector('.order-status').textContent.toLowerCase();
        
        if (symbol.includes(query) || 
            orderType.includes(query) || 
            orderStatus.includes(query)) {
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
