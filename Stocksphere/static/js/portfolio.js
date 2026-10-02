// portfolio.js - Handles portfolio functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Create portfolio summary chart
    createPortfolioChart();
    
    // Handle portfolio search
    const searchInput = document.getElementById('portfolio-search');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(handlePortfolioSearch, 300));
    }
});

// Create portfolio summary chart
function createPortfolioChart() {
    const chartContainer = document.getElementById('portfolio-chart');
    if (!chartContainer) return;
    
    // Get portfolio data from the table
    const portfolioTable = document.getElementById('portfolio-table');
    if (!portfolioTable) return;
    
    const rows = portfolioTable.querySelectorAll('tbody tr');
    const labels = [];
    const data = [];
    const backgroundColors = [
        'rgba(75, 192, 192, 0.7)',
        'rgba(54, 162, 235, 0.7)',
        'rgba(255, 99, 132, 0.7)',
        'rgba(255, 206, 86, 0.7)',
        'rgba(153, 102, 255, 0.7)',
        'rgba(255, 159, 64, 0.7)',
        'rgba(199, 199, 199, 0.7)',
        'rgba(83, 102, 255, 0.7)',
        'rgba(40, 159, 64, 0.7)',
        'rgba(210, 199, 199, 0.7)'
    ];
    
    rows.forEach((row, index) => {
        const symbol = row.getAttribute('data-symbol');
        const valueCell = row.querySelector('.current-value');
        if (symbol && valueCell) {
            const value = parseFloat(valueCell.getAttribute('data-value')) || 0;
            if (value > 0) {
                labels.push(symbol);
                data.push(value);
            }
        }
    });
    
    // Create the chart
    const ctx = chartContainer.getContext('2d');
    const portfolioChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: backgroundColors,
                borderColor: 'rgba(255, 255, 255, 0.5)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        boxWidth: 12,
                        padding: 10
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.raw;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${context.label}: $${value.toLocaleString()} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Handle portfolio search
function handlePortfolioSearch() {
    const query = document.getElementById('portfolio-search').value.trim().toLowerCase();
    const rows = document.querySelectorAll('#portfolio-table tbody tr');
    
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

// Debounce function to limit function calls
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        const context = this;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
}

// Format currency
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', { 
        style: 'currency', 
        currency: 'USD' 
    }).format(value);
}

// Format percentage
function formatPercentage(value) {
    return new Intl.NumberFormat('en-US', { 
        style: 'percent', 
        minimumFractionDigits: 2, 
        maximumFractionDigits: 2 
    }).format(value / 100);
}
