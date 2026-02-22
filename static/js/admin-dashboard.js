// Auto-close alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    // Handle alerts
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Initialize charts
    initRevenueChart();
    initStockChart();
    
    // Add active class to current nav item
    highlightCurrentNav();
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Revenue Chart
function initRevenueChart() {
    const ctx = document.getElementById('revenueChart')?.getContext('2d');
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Billing Revenue',
                data: [12000, 19000, 15000, 25000, 22000, 30000, 28000],
                borderColor: '#4361ee',
                backgroundColor: 'rgba(67, 97, 238, 0.1)',
                tension: 0.4,
                fill: true
            }, {
                label: 'Pharmacy Revenue',
                data: [8000, 12000, 10000, 18000, 15000, 22000, 20000],
                borderColor: '#4cc9f0',
                backgroundColor: 'rgba(76, 201, 240, 0.1)',
                tension: 0.4,
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
                y: {
                    beginAtZero: true,
                    grid: {
                        display: true,
                        color: 'rgba(0,0,0,0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// Stock Chart
function initStockChart() {
    const ctx = document.getElementById('stockChart')?.getContext('2d');
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['In Stock', 'Low Stock', 'Expired', 'Reorder'],
            datasets: [{
                data: [65, 15, 5, 15],
                backgroundColor: [
                    '#4cc9f0',
                    '#f8961e',
                    '#f94144',
                    '#4361ee'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                }
            }
        }
    });
}

// Highlight current navigation item
function highlightCurrentNav() {
    const currentUrl = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar .list-group-item');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentUrl) {
            link.classList.add('active');
        }
    });
}

// Refresh data with animation
function refreshData() {
    const refreshBtn = document.querySelector('.btn-refresh');
    if (refreshBtn) {
        refreshBtn.classList.add('loading');
        setTimeout(() => {
            location.reload();
        }, 500);
    }
}

// Handle quick action clicks
document.querySelectorAll('.quick-action-btn').forEach(btn => {
    btn.addEventListener('click', function(e) {
        e.preventDefault();
        const href = this.getAttribute('href');
        if (href) {
            window.location.href = href;
        }
    });
});

// Toggle sidebar on mobile
if (window.innerWidth <= 768) {
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.createElement('button');
    toggleBtn.innerHTML = '<i class="bi bi-list"></i>';
    toggleBtn.className = 'btn btn-primary sidebar-toggle';
    toggleBtn.style.position = 'fixed';
    toggleBtn.style.bottom = '20px';
    toggleBtn.style.right = '20px';
    toggleBtn.style.zIndex = '1000';
    toggleBtn.style.borderRadius = '50%';
    toggleBtn.style.width = '50px';
    toggleBtn.style.height = '50px';
    toggleBtn.style.display = 'flex';
    toggleBtn.style.alignItems = 'center';
    toggleBtn.style.justifyContent = 'center';
    
    document.body.appendChild(toggleBtn);
    
    toggleBtn.addEventListener('click', function() {
        sidebar.classList.toggle('show');
    });
}

// Handle window resize
window.addEventListener('resize', function() {
    if (window.innerWidth > 768) {
        const toggleBtn = document.querySelector('.sidebar-toggle');
        if (toggleBtn) toggleBtn.remove();
    }
});