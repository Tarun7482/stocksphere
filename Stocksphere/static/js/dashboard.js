// dashboard.js - Handles dashboard functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Handle search functionality
    const searchInput = document.getElementById('stock-search');
    const searchResults = document.getElementById('search-results');
    
    if (searchInput) {
        searchInput.addEventListener('input', debounce(handleSearch, 300));
        
        // Close search results when clicking outside
        document.addEventListener('click', function(event) {
            if (!searchInput.contains(event.target) && !searchResults.contains(event.target)) {
                searchResults.innerHTML = '';
                searchResults.classList.add('d-none');
            }
        });
    }
    
    // Initialize market summary charts
    initMarketCharts();
});

// Debounce function to limit API calls
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        const context = this;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
}

// Handle stock search
function handleSearch() {
    const query = document.getElementById('stock-search').value.trim();
    const searchResults = document.getElementById('search-results');
    
    if (query.length < 2) {
        searchResults.innerHTML = '';
        searchResults.classList.add('d-none');
        return;
    }
    
    // Fetch search results from the API
    fetch(`/api/search?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            searchResults.innerHTML = '';
            
            if (data.length === 0) {
                searchResults.innerHTML = '<p class="text-center p-2">No results found</p>';
            } else {
                data.forEach(item => {
                    const resultItem = document.createElement('a');
                    resultItem.href = `/chart/${item.symbol}`;
                    resultItem.classList.add('dropdown-item', 'd-flex', 'justify-content-between', 'align-items-center');
                    resultItem.innerHTML = `
                        <span><strong>${item.symbol}</strong></span>
                        <span class="text-muted">${item.name}</span>
                    `;
                    searchResults.appendChild(resultItem);
                });
            }
            
            searchResults.classList.remove('d-none');
        })
        .catch(error => {
            console.error('Error searching stocks:', error);
            searchResults.innerHTML = '<p class="text-center p-2 text-danger">Error searching stocks</p>';
            searchResults.classList.remove('d-none');
        });
}

// Initialize market summary charts
function initMarketCharts() {
    const marketCharts = document.querySelectorAll('.market-chart');
    
    marketCharts.forEach(chartElement => {
        const ctx = chartElement.getContext('2d');
        const symbol = chartElement.getAttribute('data-symbol');
        
        // Create placeholder chart with loading state
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: symbol,
                    data: [],
                    borderColor: 'rgba(75, 192, 192, 1)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.1,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        display: false
                    },
                    y: {
                        display: false
                    }
                },
                animation: {
                    duration: 1000
                }
            }
        });
        
        // Fetch data for the chart
        fetchChartData(symbol, '5d', '1d', chart);
    });
}

// Fetch chart data from API
function fetchChartData(symbol, period, interval, chart) {
    // Using the chart endpoint, but only extracting the data we need
    fetch(`/chart/${symbol}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.text();
        })
        .then(html => {
            // Extract the historical data from the HTML
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const dataElement = doc.getElementById('historical-data');
            
            if (dataElement) {
                const historicalData = JSON.parse(dataElement.textContent);
                
                // Update chart with the new data
                chart.data.labels = historicalData.dates;
                chart.data.datasets[0].data = historicalData.prices;
                chart.update();
            }
        })
        .catch(error => {
            console.error('Error fetching chart data:', error);
        });
}
