// charts.js - Handles chart functionality on the chart page

document.addEventListener('DOMContentLoaded', function() {
    // Get the chart container and data
    const chartContainer = document.getElementById('stock-chart');
    const volumeChartContainer = document.getElementById('volume-chart');
    const historicalDataElem = document.getElementById('historical-data');
    
    if (chartContainer && historicalDataElem) {
        // Parse the historical data
        const historicalData = JSON.parse(historicalDataElem.textContent);
        
        // Create the price chart
        createPriceChart(chartContainer, historicalData);
        
        // Create the volume chart if container exists
        if (volumeChartContainer) {
            createVolumeChart(volumeChartContainer, historicalData);
        }
        
        // Setup period selectors
        setupPeriodSelectors(historicalData);
    }
    
    // Add event listeners for buy/sell form
    setupOrderForm();
});

// Create the main price chart
function createPriceChart(container, data) {
    const ctx = container.getContext('2d');
    
    // Calculate moving averages
    const ma20 = calculateMovingAverage(data.prices, 20);
    const ma50 = calculateMovingAverage(data.prices, 50);
    
    // Create the chart
    window.priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [
                {
                    label: 'Price',
                    data: data.prices,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    pointRadius: 0,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.1
                },
                {
                    label: '20-day MA',
                    data: ma20,
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1.5,
                    pointRadius: 0,
                    fill: false
                },
                {
                    label: '50-day MA',
                    data: ma50,
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1.5,
                    pointRadius: 0,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                tooltip: {
                    mode: 'index',
                    intersect: false
                },
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        maxTicksLimit: 10
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    position: 'right',
                    beginAtZero: false
                }
            }
        }
    });
}

// Create the volume chart
function createVolumeChart(container, data) {
    const ctx = container.getContext('2d');
    
    // Create gradient for volume bars
    const gradient = ctx.createLinearGradient(0, 0, 0, 200);
    gradient.addColorStop(0, 'rgba(128, 203, 196, 0.8)');
    gradient.addColorStop(1, 'rgba(128, 203, 196, 0.2)');
    
    // Create the chart
    window.volumeChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.dates,
            datasets: [
                {
                    label: 'Volume',
                    data: data.volumes,
                    backgroundColor: gradient,
                    borderColor: 'rgba(128, 203, 196, 1)',
                    borderWidth: 1
                }
            ]
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
                    position: 'right',
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatVolume(value);
                        }
                    }
                }
            }
        }
    });
}

// Setup period selectors (1D, 1W, 1M, 3M, 1Y, 5Y)
function setupPeriodSelectors() {
    const periodButtons = document.querySelectorAll('.period-selector button');
    const symbol = document.getElementById('stock-symbol').textContent;
    
    periodButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            periodButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Get period from button
            const period = this.getAttribute('data-period');
            
            // Show loading state
            document.getElementById('chart-loading').classList.remove('d-none');
            
            // Determine interval based on period
            let interval = '1d';
            if (period === '1d') interval = '5m';
            else if (period === '5d') interval = '30m';
            else if (period === '1mo') interval = '1d';
            else if (period === '3mo') interval = '1d';
            else if (period === '1y') interval = '1wk';
            else if (period === '5y') interval = '1mo';
            
            // Fetch new data
            updateChartData(symbol, period, interval);
        });
    });
}

// Update chart with new period data
function updateChartData(symbol, period, interval) {
    // For a real app, this would call an API endpoint
    // Here we'll simulate by reloading the page with query params
    window.location.href = `/chart/${symbol}?period=${period}&interval=${interval}`;
}

// Calculate simple moving average
function calculateMovingAverage(data, window) {
    const result = [];
    
    // Fill with null values until we have enough data points
    for (let i = 0; i < window - 1; i++) {
        result.push(null);
    }
    
    for (let i = window - 1; i < data.length; i++) {
        let sum = 0;
        for (let j = 0; j < window; j++) {
            sum += data[i - j];
        }
        result.push(sum / window);
    }
    
    return result;
}

// Format volume for display
function formatVolume(value) {
    if (value >= 1_000_000_000) {
        return (value / 1_000_000_000).toFixed(1) + 'B';
    }
    if (value >= 1_000_000) {
        return (value / 1_000_000).toFixed(1) + 'M';
    }
    if (value >= 1_000) {
        return (value / 1_000).toFixed(1) + 'K';
    }
    return value;
}

// Setup buy/sell order form
function setupOrderForm() {
    const buyButton = document.getElementById('buy-button');
    const sellButton = document.getElementById('sell-button');
    const orderForm = document.getElementById('order-form');
    const orderTypeInput = document.getElementById('order-type');
    const quantityInput = document.getElementById('quantity');
    const priceInput = document.getElementById('price');
    const totalValue = document.getElementById('total-value');
    
    if (buyButton && sellButton && orderForm) {
        // Set up buy button
        buyButton.addEventListener('click', function() {
            orderTypeInput.value = 'BUY';
            document.getElementById('order-title').textContent = 'Buy';
            document.getElementById('order-form-container').classList.remove('d-none');
            document.querySelector('.modal-header').classList.remove('bg-danger');
            document.querySelector('.modal-header').classList.add('bg-success');
        });
        
        // Set up sell button
        sellButton.addEventListener('click', function() {
            orderTypeInput.value = 'SELL';
            document.getElementById('order-title').textContent = 'Sell';
            document.getElementById('order-form-container').classList.remove('d-none');
            document.querySelector('.modal-header').classList.remove('bg-success');
            document.querySelector('.modal-header').classList.add('bg-danger');
        });
        
        // Update total value when quantity or price changes
        function updateTotal() {
            const quantity = parseInt(quantityInput.value) || 0;
            const price = parseFloat(priceInput.value) || 0;
            const total = quantity * price;
            totalValue.textContent = total.toFixed(2);
        }
        
        quantityInput.addEventListener('input', updateTotal);
        priceInput.addEventListener('input', updateTotal);
        
        // Handle form submission
        orderForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const orderType = orderTypeInput.value;
            const symbol = document.getElementById('stock-symbol').textContent;
            const quantity = parseInt(quantityInput.value) || 0;
            const price = parseFloat(priceInput.value) || 0;
            
            if (quantity <= 0 || price <= 0) {
                alert('Please enter valid quantity and price.');
                return;
            }
            
            // Send order to the server
            fetch('/api/place_order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    symbol: symbol,
                    order_type: orderType,
                    quantity: quantity,
                    price: price
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Show success message
                    const successAlert = document.createElement('div');
                    successAlert.className = 'alert alert-success';
                    successAlert.textContent = data.message;
                    document.getElementById('order-messages').appendChild(successAlert);
                    
                    // Clear form
                    orderForm.reset();
                    updateTotal();
                    
                    // Close modal after delay
                    setTimeout(() => {
                        const orderModal = bootstrap.Modal.getInstance(document.getElementById('orderModal'));
                        orderModal.hide();
                        // Reload page to update funds
                        window.location.reload();
                    }, 2000);
                } else {
                    // Show error message
                    const errorAlert = document.createElement('div');
                    errorAlert.className = 'alert alert-danger';
                    errorAlert.textContent = data.message;
                    document.getElementById('order-messages').appendChild(errorAlert);
                }
            })
            .catch(error => {
                console.error('Error placing order:', error);
                const errorAlert = document.createElement('div');
                errorAlert.className = 'alert alert-danger';
                errorAlert.textContent = 'An error occurred while placing your order.';
                document.getElementById('order-messages').appendChild(errorAlert);
            });
        });
    }
}
