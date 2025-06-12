// Plugin System Web Application JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Add fade-in animation to main content
    const mainContent = document.querySelector('main');
    if (mainContent) {
        mainContent.classList.add('fade-in');
    }
    
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Form validation enhancement
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
    
    // Auto-resize textareas
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        autoResize(textarea);
        textarea.addEventListener('input', () => autoResize(textarea));
    });
    
    // Add character count to textareas
    textareas.forEach(textarea => {
        addCharacterCounter(textarea);
    });
    
    // Plugin card hover effects
    const pluginCards = document.querySelectorAll('.card');
    pluginCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-4px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});

// Auto-resize textarea function
function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 300) + 'px';
}

// Add character counter to textarea
function addCharacterCounter(textarea) {
    const maxLength = textarea.getAttribute('maxlength');
    if (!maxLength) return;
    
    const counter = document.createElement('div');
    counter.className = 'form-text text-end mt-1';
    counter.id = textarea.id + '_counter';
    
    const updateCounter = () => {
        const current = textarea.value.length;
        const max = parseInt(maxLength);
        counter.textContent = `${current}/${max} characters`;
        
        if (current > max * 0.9) {
            counter.className = 'form-text text-end mt-1 text-warning';
        } else if (current === max) {
            counter.className = 'form-text text-end mt-1 text-danger';
        } else {
            counter.className = 'form-text text-end mt-1 text-muted';
        }
    };
    
    textarea.parentNode.appendChild(counter);
    textarea.addEventListener('input', updateCounter);
    updateCounter();
}

// API helper functions
const API = {
    async get(url) {
        try {
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            return await response.json();
        } catch (error) {
            console.error('API GET Error:', error);
            throw error;
        }
    },
    
    async post(url, data) {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            return await response.json();
        } catch (error) {
            console.error('API POST Error:', error);
            throw error;
        }
    },
    
    async postForm(url, formData) {
        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData
            });
            return await response.json();
        } catch (error) {
            console.error('API POST Form Error:', error);
            throw error;
        }
    }
};

// Notification system
const Notifications = {
    show(message, type = 'info', duration = 5000) {
        const container = this.getContainer();
        const notification = this.create(message, type);
        
        container.appendChild(notification);
        
        // Trigger animation
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        // Auto remove
        setTimeout(() => {
            this.remove(notification);
        }, duration);
        
        return notification;
    },
    
    create(message, type) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" onclick="Notifications.remove(this.parentElement)"></button>
        `;
        return notification;
    },
    
    remove(notification) {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 150);
    },
    
    getContainer() {
        let container = document.getElementById('notifications-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notifications-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                min-width: 300px;
            `;
            document.body.appendChild(container);
        }
        return container;
    }
};

// Plugin management functions
async function refreshPlugins() {
    try {
        const result = await API.post('/api/refresh-plugins');
        if (result.success) {
            Notifications.show(`Refreshed ${result.count} plugins successfully`, 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            Notifications.show('Failed to refresh plugins', 'danger');
        }
    } catch (error) {
        Notifications.show('Error refreshing plugins', 'danger');
        console.error('Error refreshing plugins:', error);
    }
}

async function executePlugin(pluginId, formData) {
    try {
        const result = await API.postForm(`/api/plugin/${pluginId}/execute`, formData);
        return result;
    } catch (error) {
        console.error('Error executing plugin:', error);
        throw error;
    }
}

// Utility functions
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

function formatTime(seconds) {
    if (seconds < 1) {
        return Math.round(seconds * 1000) + 'ms';
    } else if (seconds < 60) {
        return seconds.toFixed(2) + 's';
    } else {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Export functions for global use
window.API = API;
window.Notifications = Notifications;
window.refreshPlugins = refreshPlugins;
window.executePlugin = executePlugin;
window.formatBytes = formatBytes;
window.formatTime = formatTime;
window.escapeHtml = escapeHtml; 