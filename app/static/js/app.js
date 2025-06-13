// NEURAL PLUGIN SYSTEM - CYBERPUNK INTERFACE
// Enhanced JavaScript with futuristic effects and animations

document.addEventListener('DOMContentLoaded', function() {
    // Initialize cyberpunk effects
    initializeCyberpunkEffects();
    
    // Auto-resize textareas with cyberpunk enhancements
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        autoResize(textarea);
        textarea.addEventListener('input', () => autoResize(textarea));
        addCyberpunkInputEffects(textarea);
    });
    
    // Enhance all form inputs
    enhanceFormInputs();
    
    // Initialize dynamic background effects
    initializeBackgroundEffects();
    
    // Start system monitoring
    startSystemMonitoring();
});

// Initialize cyberpunk visual effects
function initializeCyberpunkEffects() {
    // Add particle effect canvas
    createParticleCanvas();
    
    // Initialize card hover effects
    initializeCardEffects();
    
    // Add typing animation to code blocks
    initializeCodeBlockEffects();
    
    // Initialize button click effects
    initializeButtonEffects();
    
    // Start random glitch effects
    startRandomGlitchEffects();
}

// Create animated particle background
function createParticleCanvas() {
    const canvas = document.createElement('canvas');
    canvas.id = 'particle-canvas';
    canvas.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: -1;
        opacity: 0.3;
    `;
    document.body.appendChild(canvas);
    
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    
    const particles = [];
    const particleCount = 50;
    
    // Create particles
    for (let i = 0; i < particleCount; i++) {
        particles.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            vx: (Math.random() - 0.5) * 0.5,
            vy: (Math.random() - 0.5) * 0.5,
            size: Math.random() * 2 + 1,
            opacity: Math.random() * 0.5 + 0.2
        });
    }
    
    function animateParticles() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        particles.forEach(particle => {
            // Update position
            particle.x += particle.vx;
            particle.y += particle.vy;
            
            // Wrap around edges
            if (particle.x > canvas.width) particle.x = 0;
            if (particle.x < 0) particle.x = canvas.width;
            if (particle.y > canvas.height) particle.y = 0;
            if (particle.y < 0) particle.y = canvas.height;
            
            // Draw particle
            ctx.beginPath();
            ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(0, 245, 255, ${particle.opacity})`;
            ctx.fill();
            
            // Draw connections
            particles.forEach(otherParticle => {
                const distance = Math.sqrt(
                    Math.pow(particle.x - otherParticle.x, 2) +
                    Math.pow(particle.y - otherParticle.y, 2)
                );
                
                if (distance < 100) {
                    ctx.beginPath();
                    ctx.moveTo(particle.x, particle.y);
                    ctx.lineTo(otherParticle.x, otherParticle.y);
                    ctx.strokeStyle = `rgba(0, 245, 255, ${0.1 * (1 - distance / 100)})`;
                    ctx.stroke();
                }
            });
        });
        
        requestAnimationFrame(animateParticles);
    }
    
    animateParticles();
    
    // Resize canvas on window resize
    window.addEventListener('resize', () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    });
}

// Enhanced card effects
function initializeCardEffects() {
    document.querySelectorAll('.card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-10px) scale(1.02)';
            this.style.boxShadow = '0 20px 40px rgba(0, 245, 255, 0.3), 0 0 50px rgba(255, 0, 110, 0.2)';
            
            // Add scanning line effect
            const scanLine = document.createElement('div');
            scanLine.style.cssText = `
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 2px;
                background: linear-gradient(90deg, transparent, var(--neon-blue), transparent);
                animation: scan 1s ease-in-out;
                z-index: 10;
            `;
            this.appendChild(scanLine);
            
            setTimeout(() => {
                if (scanLine.parentNode) {
                    scanLine.parentNode.removeChild(scanLine);
                }
            }, 1000);
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = '';
            this.style.boxShadow = '';
        });
    });
}

// Enhanced form input effects
function enhanceFormInputs() {
    document.querySelectorAll('input, textarea, select').forEach(input => {
        addCyberpunkInputEffects(input);
    });
}

function addCyberpunkInputEffects(input) {
    input.addEventListener('focus', function() {
        this.style.boxShadow = '0 0 20px rgba(0, 245, 255, 0.6), inset 0 0 10px rgba(0, 245, 255, 0.2)';
        this.style.borderColor = 'var(--neon-blue)';
        
        // Add electric effect
        const parent = this.parentElement;
        parent.classList.add('electric-border');
    });
    
    input.addEventListener('blur', function() {
        this.style.boxShadow = '';
        this.style.borderColor = '';
        
        const parent = this.parentElement;
        parent.classList.remove('electric-border');
    });
    
    // Add typing sound effect (visual feedback)
    input.addEventListener('input', function() {
        this.style.animation = 'pulse 0.1s ease-in-out';
        setTimeout(() => {
            this.style.animation = '';
        }, 100);
    });
}

// Enhanced button effects
function initializeButtonEffects() {
    document.querySelectorAll('.btn, button').forEach(button => {
        button.addEventListener('click', function(e) {
            // Create ripple effect
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                left: ${x}px;
                top: ${y}px;
                background: radial-gradient(circle, rgba(0, 245, 255, 0.6) 0%, transparent 70%);
                border-radius: 50%;
                transform: scale(0);
                animation: ripple 0.6s ease-out;
                pointer-events: none;
                z-index: 1;
            `;
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                if (ripple.parentNode) {
                    ripple.parentNode.removeChild(ripple);
                }
            }, 600);
        });
    });
    
    // Add ripple animation keyframes
    if (!document.getElementById('ripple-styles')) {
        const style = document.createElement('style');
        style.id = 'ripple-styles';
        style.textContent = `
            @keyframes ripple {
                to {
                    transform: scale(2);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
}

// Code block typing effect
function initializeCodeBlockEffects() {
    document.querySelectorAll('pre code').forEach(codeBlock => {
        codeBlock.addEventListener('mouseenter', function() {
            this.style.boxShadow = '0 0 20px rgba(0, 245, 255, 0.4)';
            this.style.background = 'rgba(0, 245, 255, 0.05)';
        });
        
        codeBlock.addEventListener('mouseleave', function() {
            this.style.boxShadow = '';
            this.style.background = '';
        });
    });
}

// Random glitch effects
function startRandomGlitchEffects() {
    setInterval(() => {
        if (Math.random() < 0.02) { // 2% chance every 5 seconds
            const elements = document.querySelectorAll('h1, h2, .card-title');
            if (elements.length > 0) {
                const randomElement = elements[Math.floor(Math.random() * elements.length)];
                randomElement.style.animation = 'glitch-1 0.3s ease-in-out';
                setTimeout(() => {
                    randomElement.style.animation = '';
                }, 300);
            }
        }
    }, 5000);
}

// System monitoring effects
function startSystemMonitoring() {
    // Update system status indicators
    setInterval(() => {
        const statusElements = document.querySelectorAll('.text-success, .text-accent');
        statusElements.forEach(element => {
            if (element.textContent.includes('OPERATIONAL')) {
                element.style.textShadow = `0 0 10px var(--neon-green)`;
                setTimeout(() => {
                    element.style.textShadow = '';
                }, 100);
            }
        });
    }, 3000);
}

// Background matrix rain effect
function initializeBackgroundEffects() {
    const matrixContainer = document.createElement('div');
    matrixContainer.id = 'matrix-rain';
    matrixContainer.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: -2;
        opacity: 0.1;
        overflow: hidden;
    `;
    
    document.body.appendChild(matrixContainer);
    
    // Create matrix columns
    for (let i = 0; i < 20; i++) {
        const column = document.createElement('div');
        column.style.cssText = `
            position: absolute;
            top: -100px;
            left: ${i * 5}%;
            width: 2px;
            height: 100px;
            background: linear-gradient(transparent, var(--neon-green), transparent);
            animation: matrix-fall ${Math.random() * 3 + 2}s linear infinite;
            animation-delay: ${Math.random() * 2}s;
        `;
        matrixContainer.appendChild(column);
    }
    
    // Add matrix fall animation
    if (!document.getElementById('matrix-styles')) {
        const style = document.createElement('style');
        style.id = 'matrix-styles';
        style.textContent = `
            @keyframes matrix-fall {
                0% {
                    transform: translateY(-100vh);
                    opacity: 0;
                }
                10%, 90% {
                    opacity: 1;
                }
                100% {
                    transform: translateY(100vh);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
}

// Auto-resize textarea function with cyberpunk enhancement
function autoResize(textarea) {
    const newHeight = Math.min(textarea.scrollHeight, 300);
    if (newHeight > 0) {
        textarea.setAttribute('rows', Math.ceil(newHeight / 20));
        
        // Add glow effect while typing
        textarea.style.boxShadow = '0 0 10px rgba(0, 245, 255, 0.3)';
        setTimeout(() => {
            textarea.style.boxShadow = '';
        }, 200);
    }
}

// Enhanced API helper functions with cyberpunk loading effects
const API = {
    async get(url) {
        this.showLoadingEffect();
        try {
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            this.hideLoadingEffect();
            return await response.json();
        } catch (error) {
            this.hideLoadingEffect();
            console.error('API GET Error:', error);
            throw error;
        }
    },
    
    async post(url, data) {
        this.showLoadingEffect();
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            this.hideLoadingEffect();
            return await response.json();
        } catch (error) {
            this.hideLoadingEffect();
            console.error('API POST Error:', error);
            throw error;
        }
    },
    
    async postForm(url, formData) {
        this.showLoadingEffect();
        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData
            });
            this.hideLoadingEffect();
            return await response.json();
        } catch (error) {
            this.hideLoadingEffect();
            console.error('API POST Form Error:', error);
            throw error;
        }
    },
    
    showLoadingEffect() {
        // Add neural loading indicator
        if (!document.getElementById('neural-loader')) {
            const loader = document.createElement('div');
            loader.id = 'neural-loader';
            loader.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                width: 60px;
                height: 60px;
                border: 3px solid var(--darker-bg);
                border-top: 3px solid var(--neon-blue);
                border-right: 3px solid var(--neon-pink);
                border-radius: 50%;
                animation: spin-glow 1s linear infinite;
                z-index: 9999;
                box-shadow: 0 0 20px rgba(0, 245, 255, 0.5);
            `;
            document.body.appendChild(loader);
        }
    },
    
    hideLoadingEffect() {
        const loader = document.getElementById('neural-loader');
        if (loader) {
            loader.remove();
        }
    }
};

// Enhanced notification system with cyberpunk styling
const Notifications = {
    show(message, type = 'info', duration = 5000) {
        const container = this.getContainer();
        const notification = this.create(message, type);
        
        container.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
            notification.style.opacity = '1';
        }, 10);
        
        // Auto remove
        setTimeout(() => {
            this.remove(notification);
        }, duration);
        
        return notification;
    },
    
    create(message, type) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            background: var(--card-bg);
            border: 2px solid var(--border-glow);
            color: var(--text-primary);
            padding: 15px 20px;
            margin-bottom: 10px;
            border-radius: 0;
            clip-path: polygon(0 0, calc(100% - 15px) 0, 100% 100%, 15px 100%);
            transform: translateX(400px);
            opacity: 0;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0, 245, 255, 0.2);
        `;
        
        // Add type-specific styling
        if (type === 'success') {
            notification.style.borderColor = 'var(--neon-green)';
            notification.style.boxShadow = '0 4px 20px rgba(58, 134, 255, 0.3)';
        } else if (type === 'danger') {
            notification.style.borderColor = 'var(--neon-pink)';
            notification.style.boxShadow = '0 4px 20px rgba(255, 0, 110, 0.3)';
        }
        
        notification.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>${message}</span>
                <button type="button" onclick="Notifications.remove(this.parentElement.parentElement)" 
                        style="background: none; border: none; color: var(--neon-blue); font-size: 18px; cursor: pointer; padding: 0 5px;">×</button>
            </div>
        `;
        
        return notification;
    },
    
    remove(notification) {
        if (notification.parentNode) {
            notification.style.transform = 'translateX(400px)';
            notification.style.opacity = '0';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }
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
                z-index: 10000;
                max-width: 400px;
            `;
            document.body.appendChild(container);
        }
        return container;
    }
};

// Enhanced plugin management functions
async function refreshPlugins() {
    try {
        const result = await API.post('/api/refresh-plugins');
        if (result.success) {
            Notifications.show(`⚡ Refreshed ${result.count} neural modules successfully`, 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            Notifications.show('🚨 Failed to refresh neural modules', 'danger');
        }
    } catch (error) {
        Notifications.show('💀 Error refreshing neural modules', 'danger');
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

// Enhanced utility functions
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